/**
 * Knowledge Pack data loader.
 *
 * M-0: Loads from a local JSON file bundled with the project.
 * M-2: Supports loading from file upload or bundled mock pack.
 *       Includes normalization layer to handle real packs that may
 *       differ slightly from the mock fixture.
 *
 * @module data-loader
 */

import mockKnowledgePack from './data/knowledge_pack.json';

// ─── Type Definitions ──────────────────────────────────────────────

/**
 * @typedef {Object} Element
 * @property {string} id
 * @property {string} role
 * @property {string} label
 * @property {number[]} [bounds]
 * @property {string[]} [actions]
 * @property {string} [content_desc]
 */

/**
 * @typedef {Object} Form
 * @property {string} id
 * @property {string} name
 * @property {string[]} [fields]
 * @property {string} [submit_button]
 * @property {string[]} [validation_rules]
 */

/**
 * @typedef {Object} DesignTokens
 * @property {string} [background_color]
 * @property {string} [primary_color]
 * @property {string} [accent_color]
 * @property {string} [text_color]
 * @property {string} [negative_color]
 * @property {string} [positive_color]
 * @property {string} [mode]
 */

/**
 * @typedef {Object} Screen
 * @property {string} id
 * @property {string} [fingerprint]
 * @property {string} name
 * @property {string} [purpose]
 * @property {string} [screenshot_url]
 * @property {Element[]} [elements]
 * @property {Form[]} [forms]
 * @property {DesignTokens} [design_tokens]
 */

/**
 * @typedef {Object} Transition
 * @property {string} from
 * @property {string} to
 * @property {Object} [action]
 */

/**
 * @typedef {Object} Journey
 * @property {string} [id]
 * @property {string} [name]
 * @property {string} [description]
 * @property {string[]} [steps]
 */

/**
 * @typedef {Object} KnowledgePack
 * @property {string} schema_version
 * @property {Object} [app_metadata]
 * @property {Screen[]} screens
 * @property {Transition[]} [transitions]
 * @property {Journey[]} [journeys]
 * @property {Object} [global_design_system]
 * @property {Object} [scan_metadata]
 * @property {boolean} [_is_mock] - Internal flag: true when using bundled mock data
 * @property {number} [_file_size_bytes] - Internal: file size if loaded from file
 * @property {string[]} [_validation_warnings] - Internal: non-fatal issues found during validation
 */

// ─── Pack Source ───────────────────────────────────────────────────

/** @type {'mock' | 'file'} */
let currentSource = 'mock';

/**
 * Returns the current pack source type.
 * @returns {'mock' | 'file'}
 */
export function getPackSource() {
  return currentSource;
}

// ─── Load: Default (bundled mock pack) ─────────────────────────────

/**
 * Loads the bundled mock Knowledge Pack.
 *
 * @returns {Promise<KnowledgePack>} The validated & normalized pack
 * @throws {Error} If the pack is invalid
 */
export async function loadKnowledgePack() {
  currentSource = 'mock';
  const raw = structuredClone(mockKnowledgePack);
  raw._is_mock = true;
  return validateAndNormalize(raw);
}

// ─── Load: From File ───────────────────────────────────────────────

/**
 * Loads a Knowledge Pack from a user-selected File object.
 *
 * @param {File} file - A JSON file selected via file input
 * @returns {Promise<KnowledgePack>} The validated & normalized pack
 * @throws {Error} If the file is not valid JSON or fails validation
 */
export async function loadKnowledgePackFromFile(file) {
  if (!file) throw new Error('No file provided.');

  const text = await file.text();
  let raw;
  try {
    raw = JSON.parse(text);
  } catch (e) {
    throw new Error(`Invalid JSON file: ${e.message}`);
  }

  raw._is_mock = false;
  raw._file_size_bytes = file.size;
  currentSource = 'file';

  return validateAndNormalize(raw);
}

// ─── Load: From raw JSON string ────────────────────────────────────

/**
 * Loads a Knowledge Pack from a raw JSON string.
 * Useful for pasting or programmatic loading.
 *
 * @param {string} jsonString - Raw JSON
 * @param {number} [sizeBytes] - Optional byte size
 * @returns {Promise<KnowledgePack>}
 */
export async function loadKnowledgePackFromString(jsonString, sizeBytes) {
  let raw;
  try {
    raw = JSON.parse(jsonString);
  } catch (e) {
    throw new Error(`Invalid JSON: ${e.message}`);
  }

  raw._is_mock = false;
  raw._file_size_bytes = sizeBytes || new Blob([jsonString]).size;
  currentSource = 'file';

  return validateAndNormalize(raw);
}

// ─── Validate & Normalize ──────────────────────────────────────────

/**
 * Validates and normalizes a raw Knowledge Pack object.
 * Applies safe defaults for missing optional fields and
 * filters out invalid references.
 *
 * @param {any} raw - The raw pack data
 * @returns {KnowledgePack} The validated & normalized pack
 * @throws {Error} If critical validation fails
 */
function validateAndNormalize(raw) {
  const warnings = [];

  // ── Critical checks ──
  if (!raw || typeof raw !== 'object') {
    throw new Error('Knowledge Pack is not a valid object.');
  }

  if (!raw.schema_version) {
    throw new Error('Knowledge Pack is missing "schema_version".');
  }

  if (!Array.isArray(raw.screens) || raw.screens.length === 0) {
    throw new Error('Knowledge Pack contains no screens.');
  }

  // ── Normalize screens ──
  const screenIds = new Set();
  raw.screens = raw.screens.map((s, i) => {
    if (!s || typeof s !== 'object') {
      warnings.push(`Screen at index ${i} is not a valid object, skipped.`);
      return null;
    }

    // Generate an ID if missing
    if (!s.id) {
      s.id = `scr_auto_${i + 1}`;
      warnings.push(`Screen "${s.name || i}" had no id, assigned "${s.id}".`);
    }

    // Generate a name if missing
    if (!s.name) {
      s.name = `Screen ${s.id}`;
      warnings.push(`Screen "${s.id}" had no name, assigned "${s.name}".`);
    }

    // Check for duplicate IDs
    if (screenIds.has(s.id)) {
      const newId = `${s.id}_dup_${i}`;
      warnings.push(`Duplicate screen ID "${s.id}" renamed to "${newId}".`);
      s.id = newId;
    }
    screenIds.add(s.id);

    // Normalize optional arrays
    s.elements = Array.isArray(s.elements) ? s.elements : [];
    s.forms = Array.isArray(s.forms) ? s.forms : [];
    s.design_tokens = (s.design_tokens && typeof s.design_tokens === 'object') ? s.design_tokens : {};

    // Normalize element fields
    s.elements = s.elements.map((el, j) => {
      if (!el || typeof el !== 'object') return null;
      return {
        id: el.id || `el_auto_${i}_${j}`,
        role: el.role || 'unknown',
        label: el.label || el.text || el.content_desc || el.id || `Element ${j}`,
        bounds: Array.isArray(el.bounds) ? el.bounds : [],
        actions: Array.isArray(el.actions) ? el.actions : [],
        content_desc: el.content_desc || el.description || '',
      };
    }).filter(Boolean);

    // Normalize form fields
    s.forms = s.forms.map((f, j) => {
      if (!f || typeof f !== 'object') return null;
      return {
        id: f.id || `form_auto_${i}_${j}`,
        name: f.name || `Form ${j + 1}`,
        fields: Array.isArray(f.fields) ? f.fields : [],
        submit_button: f.submit_button || null,
        validation_rules: Array.isArray(f.validation_rules) ? f.validation_rules : [],
      };
    }).filter(Boolean);

    // Normalize purpose
    s.purpose = s.purpose || s.description || '';

    // Normalize screenshot
    s.screenshot_url = s.screenshot_url || s.screenshot || '';

    // Normalize fingerprint
    s.fingerprint = s.fingerprint || '';

    return s;
  }).filter(Boolean);

  // Re-check after filtering
  if (raw.screens.length === 0) {
    throw new Error('Knowledge Pack has no valid screens after normalization.');
  }

  // ── Normalize transitions ──
  raw.transitions = Array.isArray(raw.transitions) ? raw.transitions : [];
  const validTransitions = [];
  for (const t of raw.transitions) {
    if (!t || typeof t !== 'object') continue;
    if (!t.from || !t.to) {
      warnings.push(`Transition missing "from" or "to", skipped.`);
      continue;
    }
    if (!screenIds.has(t.from)) {
      warnings.push(`Transition from unknown screen "${t.from}", skipped.`);
      continue;
    }
    if (!screenIds.has(t.to)) {
      warnings.push(`Transition to unknown screen "${t.to}", skipped.`);
      continue;
    }
    // Normalize action
    t.action = (t.action && typeof t.action === 'object') ? t.action : {};
    validTransitions.push(t);
  }
  raw.transitions = validTransitions;

  // ── Normalize journeys ──
  raw.journeys = Array.isArray(raw.journeys) ? raw.journeys : [];
  raw.journeys = raw.journeys.map((j, i) => {
    if (!j || typeof j !== 'object') return null;
    const steps = Array.isArray(j.steps) ? j.steps.filter(s => screenIds.has(s)) : [];
    if (steps.length === 0) {
      warnings.push(`Journey "${j.name || i}" has no valid steps, skipped.`);
      return null;
    }
    return {
      id: j.id || `journey_auto_${i}`,
      name: j.name || `Journey ${i + 1}`,
      description: j.description || '',
      steps,
    };
  }).filter(Boolean);

  // ── Normalize top-level optional fields ──
  raw.app_metadata = (raw.app_metadata && typeof raw.app_metadata === 'object') ? raw.app_metadata : {};
  raw.global_design_system = (raw.global_design_system && typeof raw.global_design_system === 'object') ? raw.global_design_system : {};
  raw.scan_metadata = (raw.scan_metadata && typeof raw.scan_metadata === 'object') ? raw.scan_metadata : {};

  // ── Compute/normalize pack size ──
  if (!raw.scan_metadata.pack_size_bytes && raw._file_size_bytes) {
    raw.scan_metadata.pack_size_bytes = raw._file_size_bytes;
  }

  // ── Attach warnings ──
  raw._validation_warnings = warnings;

  if (warnings.length > 0) {
    console.warn('[RevRag Viewer] Knowledge Pack normalization warnings:', warnings);
  }

  return /** @type {KnowledgePack} */ (raw);
}
