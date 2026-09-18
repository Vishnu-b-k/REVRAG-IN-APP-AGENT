/**
 * RevRag Knowledge Pack Viewer — Main Application
 *
 * M-0: Viewer Bootstrap — page shell, sidebar, screen detail, local JSON loading
 * M-1: Core Viewer — app map, enhanced screen profile, transitions, journeys,
 *       design tokens visualization, improved element/form rendering
 *
 * @module main
 */

import { loadKnowledgePack, loadKnowledgePackFromFile, getPackSource, loadKnowledgePackFromAPI } from './data-loader.js';

// ─── State ─────────────────────────────────────────────────────────
/** @type {import('./data-loader.js').KnowledgePack | null} */
let pack = null;

/** @type {string | null} */
let selectedScreenId = null;

/** @type {'profile' | 'map'} */
let activeView = 'map';

// ─── Bootstrap ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  try {
    pack = await loadKnowledgePack();
    renderApp();
  } catch (err) {
    renderError(err);
  }
});

// ─── Helpers ───────────────────────────────────────────────────────
/**
 * @param {string} screenId
 * @returns {import('./data-loader.js').Screen | undefined}
 */
function getScreen(screenId) {
  return pack?.screens.find(s => s.id === screenId);
}

/** @param {string} screenId */
function screenName(screenId) {
  return getScreen(screenId)?.name || screenId;
}

/**
 * @param {string} screenId
 * @returns {import('./data-loader.js').Transition[]}
 */
function getOutgoingTransitions(screenId) {
  return (pack?.transitions || []).filter(t => t.from === screenId);
}

/**
 * @param {string} screenId
 * @returns {import('./data-loader.js').Transition[]}
 */
function getIncomingTransitions(screenId) {
  return (pack?.transitions || []).filter(t => t.to === screenId);
}

/**
 * @param {string} screenId
 * @returns {import('./data-loader.js').Journey[]}
 */
function getScreenJourneys(screenId) {
  return (pack?.journeys || []).filter(j => (j.steps || []).includes(screenId));
}

/**
 * Resolves a field ID to its element label.
 * @param {string} fieldId
 * @param {import('./data-loader.js').Element[]} elements
 * @returns {string}
 */
function resolveFieldLabel(fieldId, elements) {
  const el = (elements || []).find(e => e.id === fieldId);
  return el ? el.label : fieldId;
}

// ─── Render: Full App Shell ────────────────────────────────────────
function renderApp() {
  const app = document.getElementById('app');
  if (!app || !pack) return;

  const screens = pack.screens;
  const meta = pack.scan_metadata || {};

  app.innerHTML = `
    <header class="app-header" id="app-header">
      <div class="app-logo">
        <div class="logo-icon" aria-hidden="true">RV</div>
        <span class="app-title">RevRag Viewer</span>
      </div>
      <div class="header-divider"></div>
      <span class="app-subtitle">${escapeHtml(pack.app_metadata?.app_name || 'Knowledge Pack')}</span>
      ${getPackSource() === 'mock' 
        ? '<div class="demo-badge" title="Using bundled mock data">Mock Pack</div>' 
        : '<div class="demo-badge real-badge" title="Loaded from file">Real Pack</div>'}
      <div class="header-stats">
        <div class="stat-chip">
          <span class="stat-dot"></span>
          <span class="stat-value">${screens.length}</span> screens
        </div>
        <div class="stat-chip">
          <span class="stat-value">${(pack.transitions || []).length}</span> transitions
        </div>
        ${meta.duplicates_merged != null ? `
        <div class="stat-chip">
          <span class="stat-value">${meta.duplicates_merged}</span> merged
        </div>` : ''}
        ${(pack.journeys || []).length > 0 ? `
        <div class="stat-chip">
          <span class="stat-value">${pack.journeys.length}</span> journeys
        </div>` : ''}
        ${meta.pack_size_bytes != null ? `
        <div class="stat-chip">
          <span class="stat-value">${formatBytes(meta.pack_size_bytes)}</span> size
        </div>` : ''}
        <div class="header-actions" style="margin-left: 8px; display: flex; gap: 8px;">
          <button class="btn-scan" id="btn-scan-app" aria-label="Scan App">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 2a10 10 0 0 1 10 10"/></svg>
            Scan App
          </button>
          <label class="btn-upload" for="pack-upload-input" tabindex="0" role="button" aria-label="Upload Knowledge Pack">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
            Upload
          </label>
          <input type="file" id="pack-upload-input" accept=".json,application/json" class="hidden" />
        </div>
      </div>
    </header>
    <div class="app-layout">
      <aside class="sidebar" id="sidebar">
        <div class="sidebar-header">
          <span class="sidebar-title">Screens<span class="screen-count">(${screens.length})</span></span>
        </div>
        <div class="screen-list" id="screen-list" role="listbox" aria-label="Discovered screens">
          ${screens.map((s, i) => renderScreenListItem(s, i)).join('')}
        </div>
        <div class="sidebar-footer">
          <button class="view-toggle-btn ${activeView === 'profile' ? 'active' : ''}" data-view="profile" id="btn-view-profile">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>
            Screen Profile
          </button>
          <button class="view-toggle-btn ${activeView === 'map' ? 'active' : ''}" data-view="map" id="btn-view-map">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="5" cy="6" r="3"/><circle cx="19" cy="6" r="3"/><circle cx="12" cy="18" r="3"/><line x1="7.5" y1="7.5" x2="10.5" y2="16.5"/><line x1="16.5" y1="7.5" x2="13.5" y2="16.5"/><line x1="8" y1="6" x2="16" y2="6"/></svg>
            App Map
          </button>
        </div>
      </aside>
      <main class="content-area" id="content-area" role="main">
        <div class="empty-state" id="empty-state">
          <div class="empty-state-icon" aria-hidden="true">📱</div>
          <h2 class="empty-state-title">Select a Screen</h2>
          <p class="empty-state-description">
            Choose a screen from the sidebar to view its details, elements, forms, and design tokens.
          </p>
        </div>
      </main>
    </div>
  `;

  // Bind sidebar click events
  const listEl = document.getElementById('screen-list');
  if (listEl) {
    listEl.addEventListener('click', handleScreenSelect);
    listEl.addEventListener('keydown', handleScreenKeydown);
  }

  // Bind view toggle
  document.getElementById('btn-view-profile')?.addEventListener('click', () => switchView('profile'));
  document.getElementById('btn-view-map')?.addEventListener('click', () => switchView('map'));

  // Bind upload event
  const uploadInput = document.getElementById('pack-upload-input');
  if (uploadInput) {
    uploadInput.addEventListener('change', handleFileUpload);
  }

  // Bind scan event
  const scanBtn = document.getElementById('btn-scan-app');
  if (scanBtn) {
    scanBtn.addEventListener('click', handleScan);
  }

  // Set initial state: select first screen (for sidebar highlight) and show App Map
  if (screens.length > 0) {
    selectedScreenId = screens[0].id;
    document.getElementById(`screen-item-${screens[0].id}`)?.classList.add('active');
    document.getElementById(`screen-item-${screens[0].id}`)?.setAttribute('aria-selected', 'true');
  }
  if (activeView === 'map') {
    renderAppMap();
  } else if (selectedScreenId) {
    const screen = getScreen(selectedScreenId);
    if (screen) {
      const contentArea = document.getElementById('content-area');
      if (contentArea) contentArea.innerHTML = renderScreenDetail(screen);
      bindDetailEvents();
    }
  }
}

// ─── File Upload Logic ─────────────────────────────────────────────
/** @param {Event} e */
async function handleFileUpload(e) {
  const input = /** @type {HTMLInputElement} */ (e.target);
  if (!input.files || input.files.length === 0) return;

  const file = input.files[0];
  try {
    // Show loading state temporarily
    const app = document.getElementById('app');
    if (app) {
      app.innerHTML = `
        <div class="loading-state">
          <div class="loading-spinner"></div>
          <p>Loading Knowledge Pack...</p>
        </div>
      `;
    }

    pack = await loadKnowledgePackFromFile(file);
    selectedScreenId = null; // Reset selection
    renderApp();
  } catch (err) {
    renderError(err);
  } finally {
    // Reset file input so the same file can be uploaded again if needed
    input.value = '';
  }
}

// ─── Scan App Logic ────────────────────────────────────────────────
async function handleScan() {
  const backendUrl = prompt("Enter Orchestrator Backend URL:", localStorage.getItem('revrag_backend_url') || "http://localhost:8000");
  if (!backendUrl) return;
  localStorage.setItem('revrag_backend_url', backendUrl);

  try {
    const app = document.getElementById('app');
    if (app) {
      app.innerHTML = `
        <div class="loading-state scan-loading-state">
          <div class="scanning-scanner"></div>
          <h2 style="margin-top: 20px; color: var(--text-color);">Scanning App...</h2>
          <p style="color: var(--text-muted);">Please wait while the orchestrator explores the application.</p>
        </div>
      `;
    }

    pack = await loadKnowledgePackFromAPI({ baseUrl: backendUrl, simulate: true });
    selectedScreenId = null;
    renderApp();
  } catch (err) {
    renderError(err);
  }
}

// ─── View Switching ────────────────────────────────────────────────
/** @param {'profile' | 'map'} view */
function switchView(view) {
  activeView = view;

  // Update toggle buttons
  document.querySelectorAll('.view-toggle-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-view') === view);
  });

  // Re-render content
  if (view === 'map') {
    renderAppMap();
  } else if (selectedScreenId) {
    const screen = getScreen(selectedScreenId);
    if (screen) {
      const contentArea = document.getElementById('content-area');
      if (contentArea) contentArea.innerHTML = renderScreenDetail(screen);
      bindDetailEvents();
    }
  }
}

// ─── Render: Screen List Item ──────────────────────────────────────
/**
 * @param {import('./data-loader.js').Screen} screen
 * @param {number} index
 */
function renderScreenListItem(screen, index) {
  const elementCount = (screen.elements || []).length;
  const initial = screen.name.charAt(0).toUpperCase();
  const outgoing = getOutgoingTransitions(screen.id).length;

  return `
    <div class="screen-item"
         id="screen-item-${screen.id}"
         data-screen-id="${screen.id}"
         role="option"
         tabindex="${index === 0 ? '0' : '-1'}"
         aria-selected="false"
         aria-label="${escapeHtml(screen.name)}">
      <div class="screen-item-icon" aria-hidden="true">${initial}</div>
      <div class="screen-item-info">
        <div class="screen-item-name">${escapeHtml(screen.name)}</div>
        <div class="screen-item-id">${escapeHtml(screen.id)}</div>
      </div>
      <div class="screen-item-badges">
        ${elementCount > 0 ? `<span class="screen-item-badge">${elementCount} el</span>` : ''}
        ${outgoing > 0 ? `<span class="screen-item-badge badge-transition">${outgoing} →</span>` : ''}
      </div>
    </div>
  `;
}

// ─── App Map ───────────────────────────────────────────────────────
function renderAppMap() {
  const contentArea = document.getElementById('content-area');
  if (!contentArea || !pack) return;

  const screens = pack.screens;
  const transitions = pack.transitions || [];

  // Calculate layout positions — layered/hierarchical arrangement
  const positions = calculateMapLayout(screens, transitions);

  contentArea.innerHTML = `
    <div class="app-map" id="app-map">
      <div class="app-map-header">
        <h1 class="detail-title">App Map</h1>
        <div class="detail-id">${screens.length} screens · ${transitions.length} transitions · ${(pack.journeys || []).length} journeys</div>
        <div class="detail-purpose map-purpose">
          Click any screen node to view its full profile, elements, forms, and design tokens.
        </div>
      </div>
      <div class="map-container" id="map-container">
        <svg class="map-svg" id="map-svg" width="100%" height="100%">
          <defs>
            <marker id="arrow" viewBox="0 0 10 6" refX="10" refY="3" markerWidth="8" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 0 L 10 3 L 0 6 z" fill="var(--color-accent-primary)" opacity="0.6"/>
            </marker>
            <marker id="arrow-active" viewBox="0 0 10 6" refX="10" refY="3" markerWidth="8" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 0 L 10 3 L 0 6 z" fill="var(--color-accent-primary)"/>
            </marker>
          </defs>
          ${renderMapEdges(transitions, positions, screens)}
        </svg>
        ${renderMapNodes(screens, positions)}
      </div>
      ${renderMapJourneys()}
    </div>
  `;

  // Bind node clicks
  document.querySelectorAll('.map-node').forEach(node => {
    node.addEventListener('click', () => {
      const sid = node.getAttribute('data-screen-id');
      if (sid) {
        selectScreen(sid);
        switchView('profile');
      }
    });
  });
}

/**
 * Calculate positions for map nodes using a layered arrangement.
 * @param {import('./data-loader.js').Screen[]} screens
 * @param {import('./data-loader.js').Transition[]} transitions
 * @returns {Map<string, {x: number, y: number}>}
 */
function calculateMapLayout(screens, transitions) {
  // BFS layering from the first screen (Login/entry point)
  const adjOut = new Map();
  const adjIn = new Map();
  screens.forEach(s => {
    adjOut.set(s.id, []);
    adjIn.set(s.id, []);
  });
  transitions.forEach(t => {
    if (adjOut.has(t.from)) adjOut.get(t.from).push(t.to);
    if (adjIn.has(t.to)) adjIn.get(t.to).push(t.from);
  });

  // Assign layers via BFS
  const layers = new Map();
  const queue = [];
  const startId = screens[0]?.id;
  if (startId) {
    layers.set(startId, 0);
    queue.push(startId);
  }

  while (queue.length > 0) {
    const current = queue.shift();
    const currentLayer = layers.get(current);
    for (const next of (adjOut.get(current) || [])) {
      if (!layers.has(next)) {
        layers.set(next, currentLayer + 1);
        queue.push(next);
      }
    }
  }

  // Assign unvisited screens
  let maxLayer = 0;
  layers.forEach(l => { if (l > maxLayer) maxLayer = l; });
  screens.forEach(s => {
    if (!layers.has(s.id)) {
      maxLayer++;
      layers.set(s.id, maxLayer);
    }
  });

  // Group by layer
  const layerGroups = new Map();
  layers.forEach((layer, id) => {
    if (!layerGroups.has(layer)) layerGroups.set(layer, []);
    layerGroups.get(layer).push(id);
  });

  // Position nodes
  const positions = new Map();
  const nodeW = 160;
  const nodeH = 80;
  const layerGap = 160;
  const nodeGap = 180;
  const totalLayers = layerGroups.size;
  const sortedLayers = [...layerGroups.keys()].sort((a, b) => a - b);

  // Calculate total width needed
  let maxPerLayer = 0;
  sortedLayers.forEach(l => {
    const count = layerGroups.get(l).length;
    if (count > maxPerLayer) maxPerLayer = count;
  });

  const svgW = Math.max(maxPerLayer * nodeGap, 600);
  const svgH = totalLayers * layerGap + 100;

  sortedLayers.forEach((layer, layerIndex) => {
    const ids = layerGroups.get(layer);
    const count = ids.length;
    const totalWidth = count * nodeGap;
    const startX = (svgW - totalWidth) / 2 + nodeGap / 2;

    ids.forEach((id, i) => {
      positions.set(id, {
        x: startX + i * nodeGap,
        y: 80 + layerIndex * layerGap,
      });
    });
  });

  return positions;
}

/**
 * @param {import('./data-loader.js').Transition[]} transitions
 * @param {Map<string, {x: number, y: number}>} positions
 * @param {import('./data-loader.js').Screen[]} screens
 */
function renderMapEdges(transitions, positions, screens) {
  return transitions.map(t => {
    const from = positions.get(t.from);
    const to = positions.get(t.to);
    if (!from || !to) return '';

    const nodeH = 36;
    // Calculate edge path with a slight curve
    const fromY = from.y + nodeH;
    const toY = to.y - nodeH;
    const midY = (fromY + toY) / 2;

    const isSelected = t.from === selectedScreenId || t.to === selectedScreenId;
    const cls = isSelected ? 'map-edge active' : 'map-edge';
    const marker = isSelected ? 'url(#arrow-active)' : 'url(#arrow)';

    // Use quadratic bezier for curved edges
    const dx = to.x - from.x;
    const cpX = from.x + dx * 0.5;

    return `<path class="${cls}"
      d="M ${from.x} ${fromY} C ${cpX} ${midY}, ${cpX} ${midY}, ${to.x} ${toY}"
      marker-end="${marker}"
      data-from="${escapeHtml(t.from)}" data-to="${escapeHtml(t.to)}">
      <title>${escapeHtml(screenName(t.from))} → ${escapeHtml(screenName(t.to))}: ${escapeHtml(t.action?.label || t.action?.type || '')}</title>
    </path>`;
  }).join('');
}

/**
 * @param {import('./data-loader.js').Screen[]} screens
 * @param {Map<string, {x: number, y: number}>} positions
 */
function renderMapNodes(screens, positions) {
  return screens.map(s => {
    const pos = positions.get(s.id);
    if (!pos) return '';
    const isSelected = s.id === selectedScreenId;
    const cls = isSelected ? 'map-node selected' : 'map-node';
    const initial = s.name.charAt(0).toUpperCase();

    return `
      <div class="${cls}" data-screen-id="${s.id}"
        style="left: ${pos.x}px; top: ${pos.y}px;">
        <div class="map-node-icon">${initial}</div>
        <div class="map-node-label">${escapeHtml(s.name)}</div>
        <div class="map-node-id">${escapeHtml(s.id)}</div>
      </div>
    `;
  }).join('');
}

function renderMapJourneys() {
  if (!pack || !pack.journeys || pack.journeys.length === 0) return '';

  return `
    <div class="map-journeys-section">
      <div class="section-card full-width">
        <div class="section-card-header">
          <span class="section-card-title">Journeys</span>
          <span class="section-card-count">${pack.journeys.length}</span>
        </div>
        <div class="section-card-body">
          <div class="journey-list">
            ${pack.journeys.map(j => `
              <div class="journey-item">
                <div class="journey-header">
                  <span class="journey-name">${escapeHtml(j.name)}</span>
                  <span class="journey-step-count">${(j.steps || []).length} steps</span>
                </div>
                <div class="journey-desc">${escapeHtml(j.description || '')}</div>
                <div class="journey-steps">
                  ${(j.steps || []).map((stepId, idx) => `
                    <span class="journey-step-chip" data-screen-id="${escapeHtml(stepId)}">${escapeHtml(screenName(stepId))}</span>
                    ${idx < j.steps.length - 1 ? '<span class="journey-arrow">→</span>' : ''}
                  `).join('')}
                </div>
              </div>
            `).join('')}
          </div>
        </div>
      </div>
    </div>
  `;
}

// ─── Render: Screen Detail ─────────────────────────────────────────
/**
 * @param {import('./data-loader.js').Screen} screen
 */
function renderScreenDetail(screen) {
  const outgoing = getOutgoingTransitions(screen.id);
  const incoming = getIncomingTransitions(screen.id);
  const journeys = getScreenJourneys(screen.id);

  return `
    <div class="screen-detail" id="screen-detail">
      <!-- Hero -->
      <div class="detail-hero">
        <div class="detail-hero-content">
          <h1 class="detail-title">${escapeHtml(screen.name)}</h1>
          <div class="detail-id">${escapeHtml(screen.id)} · fingerprint: ${escapeHtml(screen.fingerprint || '—')}</div>
        </div>
        ${screen.purpose ? `<div class="detail-purpose">${escapeHtml(screen.purpose)}</div>` : ''}
      </div>

      <!-- Screenshot Presentation -->
      <div class="screenshot-presentation">
        ${renderScreenshot(screen)}
      </div>

      <!-- Elements -->
      <div class="editorial-section">
        <div class="editorial-section-title">
          <span>Elements</span>
          <span class="section-count-badge">${(screen.elements || []).length} recorded</span>
        </div>
        ${renderElements(screen.elements)}
      </div>

      <!-- Forms -->
      ${(screen.forms || []).length > 0 ? `
      <div class="editorial-section">
        <div class="editorial-section-title">
          <span>Forms</span>
          <span class="section-count-badge">${screen.forms.length} recorded</span>
        </div>
        ${renderForms(screen.forms, screen.elements)}
      </div>` : ''}

      <!-- Transitions -->
      ${(outgoing.length > 0 || incoming.length > 0) ? `
      <div class="editorial-section">
        <div class="editorial-section-title">
          <span>Transitions</span>
          <span class="section-count-badge">${outgoing.length + incoming.length} recorded</span>
        </div>
        ${renderTransitions(outgoing, incoming, screen.id)}
      </div>` : ''}

      <!-- Journeys -->
      ${journeys.length > 0 ? `
      <div class="editorial-section">
        <div class="editorial-section-title">
          <span>Journeys</span>
          <span class="section-count-badge">${journeys.length} recorded</span>
        </div>
        ${renderJourneys(journeys, screen.id)}
      </div>` : ''}

      <!-- Design Tokens -->
      ${screen.design_tokens && Object.keys(screen.design_tokens).length > 0 ? `
      <div class="editorial-section">
        <div class="editorial-section-title">
          <span>Design Tokens</span>
        </div>
        ${renderDesignTokens(screen.design_tokens)}
      </div>` : ''}

      <!-- Global Design System -->
      ${pack?.global_design_system && Object.keys(pack.global_design_system).length > 0 ? `
      <div class="editorial-section">
        <div class="editorial-section-title">
          <span>Global Design System</span>
        </div>
        ${renderGlobalDesignSystem(pack.global_design_system)}
      </div>` : ''}
    </div>
  `;
}

// ─── Render: Screenshot ────────────────────────────────────────────
/** @param {import('./data-loader.js').Screen} screen */
function renderScreenshot(screen) {
  if (!screen.screenshot_url) {
    return `
      <div class="screenshot-placeholder">
        <div class="screenshot-placeholder-icon">📷</div>
        <span>No screenshot available</span>
      </div>
    `;
  }

  return `
    <img
      class="screenshot-img"
      src="${escapeHtml(screen.screenshot_url)}"
      alt="Screenshot of ${escapeHtml(screen.name)}"
      loading="lazy"
      onerror="this.parentElement.innerHTML='<div class=\\'screenshot-placeholder\\'><div class=\\'screenshot-placeholder-icon\\'>📷</div><span>Screenshot not found</span></div>'"
    />
  `;
}

// ─── Render: Screen Metadata ───────────────────────────────────────
/** @param {import('./data-loader.js').Screen} screen */
function renderScreenMetadata(screen) {
  const outCount = getOutgoingTransitions(screen.id).length;
  const inCount = getIncomingTransitions(screen.id).length;
  const journeyCount = getScreenJourneys(screen.id).length;

  const items = [
    { label: 'Screen ID', value: screen.id },
    { label: 'Fingerprint', value: (screen.fingerprint || '—').substring(0, 12) + '…' },
    { label: 'Elements', value: String((screen.elements || []).length) },
    { label: 'Forms', value: String((screen.forms || []).length) },
    { label: 'Outgoing', value: String(outCount) },
    { label: 'Incoming', value: String(inCount) },
    { label: 'Journeys', value: String(journeyCount) },
    { label: 'Mode', value: screen.design_tokens?.mode || '—' },
  ];

  return `
    <div class="metadata-grid">
      ${items.map(item => `
        <div class="metadata-item">
          <div class="metadata-label">${escapeHtml(item.label)}</div>
          <div class="metadata-value">${escapeHtml(item.value)}</div>
        </div>
      `).join('')}
    </div>
  `;
}

// ─── Render: Elements ──────────────────────────────────────────────
/** @param {import('./data-loader.js').Element[]} elements */
function renderElements(elements) {
  if (!elements || elements.length === 0) {
    return '<p class="empty-text">No elements recorded.</p>';
  }

  return `
    <ul class="element-list">
      ${elements.map(el => {
        return `
        <li class="element-item">
          <div class="element-role-block" data-role="${escapeHtml(el.role)}">${escapeHtml(el.role)}</div>
          <div class="element-info">
            <div class="element-label">${escapeHtml(el.label)}</div>
            ${el.content_desc ? `<div class="element-desc">${escapeHtml(el.content_desc)}</div>` : ''}
            <div class="element-meta-row">
              <span class="element-tag">ID: ${escapeHtml(el.id)}</span>
              ${(el.actions || []).length > 0 ? el.actions.map(a =>
                `<span class="element-tag action">${escapeHtml(a)}</span>`
              ).join('') : ''}
            </div>
          </div>
        </li>`;
      }).join('')}
    </ul>
  `;
}

// ─── Render: Forms ─────────────────────────────────────────────────
/**
 * @param {import('./data-loader.js').Form[]} forms
 * @param {import('./data-loader.js').Element[]} elements
 */
function renderForms(forms, elements) {
  if (!forms || forms.length === 0) return '';

  return forms.map(form => {
    const fieldLabels = (form.fields || []).map(fid => resolveFieldLabel(fid, elements));
    const submitLabel = resolveFieldLabel(form.submit_button, elements);

    return `
    <div class="form-item">
      <div class="form-name">${escapeHtml(form.name)}</div>
      <div class="form-row">
        <div class="form-row-label">Fields</div>
        <div class="form-row-content">
          ${fieldLabels.map(label => `<span class="form-chip field">${escapeHtml(label)}</span>`).join('')}
        </div>
      </div>
      <div class="form-row">
        <div class="form-row-label">Submit</div>
        <div class="form-row-content">
          <span class="form-chip submit">${escapeHtml(submitLabel)}</span>
        </div>
      </div>
      ${(form.validation_rules || []).length > 0 ? `
      <div class="form-row">
        <div class="form-row-label">Validation</div>
        <div class="form-row-content">
          ${form.validation_rules.map(r => `<span class="form-chip rule">${escapeHtml(r.replace(/_/g, ' '))}</span>`).join('')}
        </div>
      </div>` : ''}
    </div>`;
  }).join('');
}

// ─── Render: Transitions ───────────────────────────────────────────
/**
 * @param {import('./data-loader.js').Transition[]} outgoing
 * @param {import('./data-loader.js').Transition[]} incoming
 * @param {string} currentScreenId
 */
function renderTransitions(outgoing, incoming, currentScreenId) {
  let html = '';

  if (outgoing.length > 0) {
    html += `
      ${outgoing.map(t => `
        <div class="transition-item" data-target-screen="${escapeHtml(t.to)}">
          <div class="transition-node source">${escapeHtml(screenName(t.from))}</div>
          <div class="transition-action">
            <span class="transition-action-badge">${escapeHtml(t.action?.label || t.action?.type || 'TAP')}</span>
          </div>
          <div class="transition-node destination" data-navigate="${escapeHtml(t.to)}">${escapeHtml(screenName(t.to))}</div>
        </div>
      `).join('')}
    `;
  }

  if (incoming.length > 0) {
    html += `
      ${incoming.map(t => `
        <div class="transition-item" data-target-screen="${escapeHtml(t.from)}">
          <div class="transition-node destination" data-navigate="${escapeHtml(t.from)}">${escapeHtml(screenName(t.from))}</div>
          <div class="transition-action">
            <span class="transition-action-badge">${escapeHtml(t.action?.label || t.action?.type || 'TAP')}</span>
          </div>
          <div class="transition-node source">${escapeHtml(screenName(t.to))}</div>
        </div>
      `).join('')}
    `;
  }

  return html;
}

// ─── Render: Journeys ──────────────────────────────────────────────
/**
 * @param {import('./data-loader.js').Journey[]} journeys
 * @param {string} currentScreenId
 */
function renderJourneys(journeys, currentScreenId) {
  return journeys.map(j => `
    <div class="journey-item">
      <div class="journey-name">${escapeHtml(j.name)}</div>
      <div class="journey-desc">${escapeHtml(j.description || '')}</div>
      <div class="journey-sequence">
        ${(j.steps || []).map((stepId, idx) => {
          const isCurrent = stepId === currentScreenId;
          return `
            <div class="journey-step ${isCurrent ? 'current' : ''}" data-screen-id="${escapeHtml(stepId)}">${escapeHtml(screenName(stepId))}</div>
            ${idx < j.steps.length - 1 ? '<div class="journey-arrow">→</div>' : ''}
          `;
        }).join('')}
      </div>
    </div>
  `).join('');
}

// ─── Render: Design Tokens ─────────────────────────────────────────
/** @param {import('./data-loader.js').DesignTokens} tokens */
function renderDesignTokens(tokens) {
  if (!tokens || typeof tokens !== 'object') return '';
  const entries = Object.entries(tokens);
  if (entries.length === 0) return '';

  const isColor = (val) => typeof val === 'string' && /^#[0-9a-fA-F]{3,8}$/.test(val);
  const colorEntries = entries.filter(([, v]) => isColor(v));
  const otherEntries = entries.filter(([, v]) => !isColor(v));

  let html = '';

  if (colorEntries.length > 0) {
    html += `
      <div class="gds-section-title">Colors</div>
      <div class="brand-grid" style="margin-bottom: var(--space-6);">
        ${colorEntries.map(([key, val]) => `
          <div class="brand-swatch-card">
            <div class="brand-swatch-color" style="background-color: ${val};" aria-label="${val}"></div>
            <div class="brand-swatch-info">
              <div class="brand-swatch-name">${escapeHtml(key.replace(/_/g, ' '))}</div>
              <div class="brand-swatch-hex">${escapeHtml(val)}</div>
            </div>
          </div>
        `).join('')}
      </div>
    `;
  }

  if (otherEntries.length > 0) {
    html += `
      <div class="gds-section">
        <div class="gds-section-title">Properties</div>
        <div class="gds-props-grid">
          ${otherEntries.map(([key, val]) => `
            <div class="gds-prop-item">
              <div class="gds-prop-label">${escapeHtml(key.replace(/_/g, ' '))}</div>
              <div class="gds-prop-value">${escapeHtml(String(val))}</div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  return html;
}

// ─── Render: Global Design System ──────────────────────────────────
/** @param {Object} gds */
function renderGlobalDesignSystem(gds) {
  if (!gds || typeof gds !== 'object') return '';

  let html = '';

  // Color palettes
  const palettes = ['primary_palette', 'accent_palette', 'neutral_palette'];
  const hasPalettes = palettes.some(p => Array.isArray(gds[p]) && gds[p].length > 0);

  if (hasPalettes) {
    palettes.forEach(pKey => {
      const colors = gds[pKey];
      if (!Array.isArray(colors) || colors.length === 0) return;
      html += `
        <div class="gds-section-title">${escapeHtml(pKey.replace(/_/g, ' '))}</div>
        <div class="brand-grid" style="margin-bottom: var(--space-6);">
          ${colors.map(c => `
            <div class="brand-swatch-card">
              <div class="brand-swatch-color" style="background-color: ${escapeHtml(c)};"></div>
              <div class="brand-swatch-info">
                <div class="brand-swatch-hex">${escapeHtml(c)}</div>
              </div>
            </div>
          `).join('')}
        </div>
      `;
    });
  }

  // Typography
  if (gds.typography && typeof gds.typography === 'object') {
    const typo = gds.typography;
    html += `
      <div class="gds-section">
        <div class="gds-section-title">Typography</div>
        <div class="gds-props-grid">
          ${Object.entries(typo).map(([k, v]) => `
            <div class="gds-prop-item">
              <div class="gds-prop-label">${escapeHtml(k.replace(/_/g, ' '))}</div>
              <div class="gds-prop-value">${escapeHtml(String(v))}</div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  // Spacing
  if (gds.spacing && typeof gds.spacing === 'object') {
    const sp = gds.spacing;
    html += `
      <div class="gds-section">
        <div class="gds-section-title">Spacing</div>
        <div class="gds-props-grid">
          ${sp.base_unit != null ? `
          <div class="gds-prop-item">
            <div class="gds-prop-label">base unit</div>
            <div class="gds-prop-value">${sp.base_unit}dp</div>
          </div>` : ''}
          ${Array.isArray(sp.common_values) ? `
          <div class="gds-prop-item">
            <div class="gds-prop-label">common values</div>
            <div class="gds-prop-value">${sp.common_values.join(', ')}dp</div>
          </div>` : ''}
        </div>
      </div>
    `;
  }

  // Mode & Tone
  const extras = [];
  if (gds.mode) extras.push({ label: 'Mode', value: gds.mode });
  if (gds.tone) extras.push({ label: 'Tone', value: gds.tone });
  if (extras.length > 0) {
    html += `
      <div class="gds-section">
        <div class="gds-section-title">Style</div>
        <div class="gds-props-grid">
          ${extras.map(e => `
            <div class="gds-prop-item">
              <div class="gds-prop-label">${escapeHtml(e.label)}</div>
              <div class="gds-prop-value">${escapeHtml(e.value)}</div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  return html;
}

// ─── Event Handlers ────────────────────────────────────────────────
/** @param {Event} e */
function handleScreenSelect(e) {
  const item = /** @type {HTMLElement} */ (e.target).closest('.screen-item');
  if (!item) return;
  const screenId = item.getAttribute('data-screen-id');
  if (screenId) {
    selectScreen(screenId);
    if (activeView === 'map') switchView('profile');
  }
}

/** @param {KeyboardEvent} e */
function handleScreenKeydown(e) {
  const current = /** @type {HTMLElement} */ (document.activeElement);
  if (!current?.classList.contains('screen-item')) return;

  let next = null;
  if (e.key === 'ArrowDown') {
    next = current.nextElementSibling;
  } else if (e.key === 'ArrowUp') {
    next = current.previousElementSibling;
  } else if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault();
    const screenId = current.getAttribute('data-screen-id');
    if (screenId) selectScreen(screenId);
    return;
  }

  if (next && next.classList.contains('screen-item')) {
    e.preventDefault();
    /** @type {HTMLElement} */ (next).focus();
    const screenId = next.getAttribute('data-screen-id');
    if (screenId) selectScreen(screenId);
  }
}

/** Bind click events inside the detail panel for navigable elements */
function bindDetailEvents() {
  // Transition navigate links
  document.querySelectorAll('[data-navigate]').forEach(el => {
    el.addEventListener('click', () => {
      const sid = el.getAttribute('data-navigate');
      if (sid) selectScreen(sid);
    });
  });

  // Journey step chips
  document.querySelectorAll('.journey-step-chip[data-screen-id]').forEach(el => {
    el.addEventListener('click', () => {
      const sid = el.getAttribute('data-screen-id');
      if (sid) selectScreen(sid);
    });
  });
}

// ─── Selection Logic ───────────────────────────────────────────────
/** @param {string} screenId */
function selectScreen(screenId) {
  if (!pack) return;

  const screen = pack.screens.find(s => s.id === screenId);
  if (!screen) return;

  selectedScreenId = screenId;

  // Update sidebar active state
  document.querySelectorAll('.screen-item').forEach(item => {
    const isActive = item.getAttribute('data-screen-id') === screenId;
    item.classList.toggle('active', isActive);
    item.setAttribute('aria-selected', String(isActive));
  });

  // Update content area
  if (activeView === 'profile') {
    const contentArea = document.getElementById('content-area');
    if (contentArea) {
      contentArea.innerHTML = renderScreenDetail(screen);
      bindDetailEvents();
    }
  } else if (activeView === 'map') {
    // Update node highlighting on the map
    document.querySelectorAll('.map-node').forEach(node => {
      node.classList.toggle('selected', node.getAttribute('data-screen-id') === screenId);
    });
  }
}

// ─── Error UI ──────────────────────────────────────────────────────
/** @param {Error} err */
function renderError(err) {
  const app = document.getElementById('app');
  if (!app) return;

  app.innerHTML = `
    <div class="error-state">
      <div class="error-icon">⚠️</div>
      <h1 class="error-title">Failed to Load Knowledge Pack</h1>
      <p class="error-message">${escapeHtml(err.message)}</p>
    </div>
  `;

  console.error('[RevRag Viewer] Knowledge Pack load error:', err);
}

// ─── Utility ───────────────────────────────────────────────────────
/**
 * Escapes HTML special characters to prevent XSS.
 * @param {string} str
 * @returns {string}
 */
function escapeHtml(str) {
  if (typeof str !== 'string') return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

/**
 * Formats bytes into a human-readable string.
 * @param {number} bytes
 * @returns {string}
 */
function formatBytes(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}
