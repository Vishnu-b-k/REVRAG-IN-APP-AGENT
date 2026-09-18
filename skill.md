# RevRag Viewer UI Design Skill

## Purpose

Use this skill when designing, refactoring, or visually enhancing the RevRag Viewer.

The current Viewer should feel **intentional, editorial, bold, warm, and product-designed**, not like a generic AI-generated dashboard.

The attached visual reference is the primary aesthetic direction for this skill. **Refer to the supplied image whenever making visual decisions.**

The reference uses large typographic statements, strong solid-color blocks, high contrast, generous spacing, and a small expressive palette. It does **not** rely on gradients, glassmorphism, neon effects, or generic SaaS-card styling.

---

# 1. Core Visual Direction

### Desired feeling

- Bold
- Warm
- Editorial
- Contemporary
- Confident
- Minimal but expressive
- Structured
- Slightly playful
- High visual contrast

### Avoid

Do **not** make the UI look like:

- a generic AI dashboard
- a template SaaS admin panel
- a glassmorphism interface
- a cyberpunk interface
- a neon developer tool
- a gradient-heavy landing page
- a collection of floating cards
- an over-animated AI product

### Golden rule

**Typography + spacing + color should create the visual personality.**

Do not depend on decorative effects to make the UI interesting.

---

# 2. Reference Palette

The palette below is extracted from the supplied reference image and should become the primary visual language.

## Brand colors

### Dynamic Black

```css
--color-black: #151314;
```

Use for:

- main navigation
- app shell
- primary dark surfaces
- high-contrast sections
- typography on light surfaces where appropriate

This should replace generic `#0f172a`, `#111827`, or blue-gray dashboard blacks.

---

### Honey Beige

```css
--color-honey: #F2E2CC;
```

Use for:

- warm content surfaces
- selected/featured areas
- large visual sections
- subtle backgrounds
- highlighted information blocks

---

### Egg Liqueur

```css
--color-egg: #DBCBAD;
```

Use for:

- secondary surfaces
- map/background areas
- grouped information sections
- soft visual separation

---

### Apocalyptic Orange

```css
--color-orange: #DF5E39;
```

Use as the primary accent.

Use for:

- important actions
- active states
- selected nodes
- key labels
- links
- attention indicators
- small visual accents

Do **not** use orange for every element.

Orange should feel intentional because the rest of the interface is quieter.

---

## Supporting neutrals

Build additional neutrals around the palette rather than introducing unrelated colors.

Example:

```css
--color-white: #FFF9F2;
--color-cream: #F8F0E5;
--color-ink: #151314;
--color-muted: #6E665D;
--color-border: #CFC1A7;
```

These are supporting values, not replacement brand colors.

---

# 3. Absolute Color Rules

## NO GRADIENTS

This is mandatory.

Never use:

```css
linear-gradient(...)
radial-gradient(...)
conic-gradient(...)
```

Do not use gradient text, gradient borders, gradient buttons, or gradient backgrounds.

Prefer:

- solid fills
- contrast
- borders
- shadows
- typography
- spacing

---

## No default blue SaaS palette

Avoid:

- Tailwind blue-heavy interfaces
- purple/indigo AI branding
- generic cyan accents
- arbitrary rainbow status colors

Use the defined palette consistently.

---

# 4. Typography

Typography is a major part of the visual identity.

## Primary recommendation

Use:

### Display / headings
**Plus Jakarta Sans**

### Body / UI
**Plus Jakarta Sans**

### Technical metadata
**IBM Plex Mono**

This creates a modern geometric grotesk feel while giving IDs, counts, bounds, and technical values a deliberate technical character.

If the project already has a bundled local font, prefer the existing local font rather than adding another dependency.

Avoid depending on a remote font solely for basic functionality.

---

# 5. Type Scale

Use a strong editorial hierarchy.

### Hero / primary application heading

```css
font-size: 2rem–2.5rem;
font-weight: 800;
letter-spacing: -0.045em;
line-height: 0.98–1.05;
```

### Major section heading

```css
font-size: 1.25rem–1.5rem;
font-weight: 750–800;
letter-spacing: -0.025em;
```

### Screen title

```css
font-size: 1.75rem–2rem;
font-weight: 800;
letter-spacing: -0.04em;
```

### Body

```css
font-size: 0.9rem–1rem;
font-weight: 450–550;
line-height: 1.45;
```

### Small metadata

```css
font-size: 0.7rem–0.8rem;
font-weight: 600;
```

### Technical metadata

Use IBM Plex Mono for:

- screen IDs
- fingerprints
- bounds
- counts where appropriate
- action types
- schema values
- pack size

---

# 6. Typography Behavior

Prefer:

- large confident titles
- short labels
- tight heading tracking
- generous line height in body copy
- sentence case for normal UI
- uppercase only for small editorial labels

Avoid:

- excessive all-caps text
- tiny labels everywhere
- overly rounded "startup" typography
- weak heading/body contrast

The supplied reference demonstrates that **large text can itself become the visual element**.

---

# 7. Layout Philosophy

The layout should feel editorial rather than dashboard-heavy.

Use:

- large flat surfaces
- strong alignment
- generous padding
- asymmetric emphasis when useful
- clear visual zones
- fewer but larger sections

Avoid:

- endless equal-sized cards
- nested cards inside cards
- excessive borders
- excessive shadows
- excessive rounded corners

---

# 8. Radius Rules

Use modest corner radii.

Recommended:

```css
--radius-sm: 8px;
--radius-md: 12px;
--radius-lg: 16px;
```

Do not turn every component into a pill.

Pills should be reserved for:

- status
- tags
- compact metadata
- action labels

Primary structural containers should generally use small-to-medium radii.

---

# 9. Borders and Shadows

Prefer borders and contrast over heavy shadow systems.

### Borders

Use warm neutral borders:

```css
border: 1px solid var(--color-border);
```

### Shadows

Use restrained shadows.

Good:

```css
box-shadow: 0 8px 24px rgba(21, 19, 20, 0.10);
```

Avoid:

- huge blurred glows
- colored neon shadows
- excessive layered elevation

---

# 10. Viewer Shell

The Viewer should visually communicate:

**RevRag → discovered app → structured knowledge**

The application shell should not resemble a generic admin console.

### Header

Use:

- strong project name
- compact supporting metadata
- clear source/status badge
- restrained controls

The title should have enough size and weight to act as an anchor.

---

# 11. App Map

The App Map is the conceptual heart of the Viewer.

It should feel like a **visual application blueprint**, not a generic graph library demo.

### Recommended

- cream / warm background
- black text and node labels
- orange for active/selected states
- warm beige for secondary states
- solid connectors
- restrained arrows
- clear spacing

### Avoid

- glowing nodes
- neon edges
- rainbow nodes
- animated particles
- overly rounded bubble diagrams
- unnecessary graph animation

### Selected screen

A selected node should have:

- strong orange accent
- clear label
- stronger outline/contrast

Do not rely solely on animation to communicate selection.

---

# 12. Screen Profile

The Screen Profile should feel like an **editorial case study of one screen**.

Recommended visual order:

1. Screen name
2. Purpose
3. Screenshot
4. Semantic elements
5. Forms
6. Transitions
7. Journeys
8. Design tokens

Do not show everything at equal visual weight.

The screen name and screenshot should dominate.

---

# 13. Screenshot Presentation

Screenshots are important evidence.

Use:

- large presentation area
- clean framing
- subtle border
- restrained shadow
- correct aspect ratio
- enough surrounding breathing room

Avoid:

- tiny thumbnail grids
- aggressive cropping
- fake device chrome unless it adds value
- unnecessary glow effects

The screenshot should feel like evidence, not decoration.

---

# 14. Elements

Elements should be scannable.

Prefer a compact visual structure:

```text
ROLE
Label
Actions
Bounds
```

Use accent colors sparingly to differentiate roles.

Do not create a rainbow of colors for every role.

Possible role treatment:

- text / label → black
- interactive → orange
- container / structure → warm beige
- metadata → muted neutral

---

# 15. Forms

Forms should visually resemble a structured specification.

Show:

- field label
- field type
- required state
- validation information
- submit action

Use orange for important interactive actions.

Avoid generic blue form controls.

---

# 16. Transitions

Make transitions read naturally:

**Current Screen → Action → Destination**

The action should be visually distinct from the source/destination.

Recommended hierarchy:

```text
SCREEN
   ↓
ACTION
   ↓
SCREEN
```

Use the orange accent to guide the eye.

Avoid overly technical graph notation unless it genuinely helps understanding.

---

# 17. Journeys

Journeys should feel like a sequence/story.

Use:

- numbered or connected steps
- compact labels
- clear current-screen highlighting
- orange for progression
- warm neutrals for completed/secondary steps

Do not make journeys visually compete with the App Map.

---

# 18. Design Tokens

The token section should itself demonstrate the discovered design language.

Use:

### Color swatches

Large enough to immediately communicate palette.

Each swatch should include:

- color name
- hex value
- role

### Typography

Show:

- hierarchy
- style
- approximate weight/size

### Spacing

Show:

- compact spacing scale
- visual examples where useful

Avoid dumping raw JSON or implementation internals.

---

# 19. Global Design System

The global design system should feel like a **mini brand guide**, not a developer debug panel.

Prefer:

- large color blocks
- hierarchy examples
- concise labels
- visual spacing demonstrations
- mode/tone summary

This is where the reference image's strong color-block approach should influence the Viewer most directly.

---

# 20. Buttons

Primary button:

```css
background: var(--color-orange);
color: var(--color-white);
```

Secondary button:

```css
background: var(--color-honey);
color: var(--color-black);
```

Dark button:

```css
background: var(--color-black);
color: var(--color-honey);
```

Use solid colors only.

Buttons should be:

- compact
- confident
- readable
- moderately rounded

Avoid:

- gradient buttons
- giant pill buttons
- glowing buttons
- excessive icon decoration

---

# 21. Status Badges

The Mock/Real badge is important.

### Mock

Use warm orange/cream treatment that is visibly different from neutral UI.

Example:

```css
background: var(--color-honey);
color: var(--color-black);
border: 1px solid var(--color-orange);
```

### Real

Use a similarly strong but calm treatment.

Do not use a random green AI-dashboard badge unless the existing information architecture explicitly requires it.

The distinction between mock and real must remain unmistakable.

---

# 22. Animation

Animation should be minimal.

Allowed:

- subtle fade
- short transform on interaction
- active-state transition
- small status pulse when meaningful

Avoid:

- infinite decorative floating
- animated gradients
- particle effects
- excessive spring animations
- large page transitions

Animation must never become the personality of the UI.

---

# 23. Responsive Behavior

Maintain usability at:

- laptop
- large desktop
- projector/browser demo
- narrower browser widths

Prioritize the demo viewport first.

Do not simply shrink everything.

At smaller widths:

- stack sections
- preserve readable typography
- keep screenshots usable
- allow App Map to scroll if necessary
- preserve strong hierarchy

---

# 24. Accessibility

Maintain:

- visible focus states
- sufficient contrast
- keyboard navigation
- semantic buttons/links
- meaningful labels
- reduced-motion compatibility where practical

Do not sacrifice accessibility for visual styling.

---

# 25. Data Integrity Rule

The visual layer must never invent Knowledge Pack information.

UI may:

- rearrange
- summarize
- label
- format
- visualize

UI must not fabricate:

- elements
- transitions
- design tokens
- counts
- screen names
- AI confidence
- statistics

Source data remains authoritative.

---

# 26. Engineering Rule

When enhancing the Viewer:

1. Inspect the existing implementation first.
2. Preserve working data loading.
3. Preserve Knowledge Pack compatibility.
4. Make the smallest necessary code changes.
5. Avoid introducing new dependencies unless clearly necessary.
6. Avoid rewriting working modules for aesthetic reasons.
7. Verify the production build after UI changes.

A visual enhancement is successful only when **the UI looks better without breaking the existing data flow**.

---

# 27. Anti-Generic-AI Checklist

Before considering a UI enhancement complete, ask:

- Does it rely on gradients?
- Does it use generic blue/purple AI colors?
- Are there too many cards?
- Are all components equally rounded?
- Are there too many shadows?
- Is everything centered?
- Are headings too small?
- Are labels too numerous?
- Does it look like a SaaS template?
- Does the palette actually resemble the reference?
- Does typography have enough personality?
- Is orange being used intentionally?
- Are the large visual areas driven by solid color?
- Does the interface feel editorial rather than generated?

If several answers are unfavorable, redesign before finishing.

---

# 28. Reference-Inspired Design Tokens

Suggested base tokens:

```css
:root {
  --color-black: #151314;
  --color-honey: #F2E2CC;
  --color-egg: #DBCBAD;
  --color-orange: #DF5E39;

  --color-white: #FFF9F2;
  --color-cream: #F8F0E5;
  --color-muted: #6E665D;
  --color-border: #CFC1A7;

  --font-display: "Plus Jakarta Sans", sans-serif;
  --font-body: "Plus Jakarta Sans", sans-serif;
  --font-mono: "IBM Plex Mono", monospace;

  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;

  --shadow-sm: 0 4px 14px rgba(21, 19, 20, 0.08);
  --shadow-md: 0 8px 24px rgba(21, 19, 20, 0.10);
}
```

If the project has an existing token system, adapt these values into that system rather than creating a second competing system.

---

# 29. Final Visual Principle

The supplied reference image demonstrates a simple idea:

**Few colors + strong typography + large areas + confident spacing = distinctive visual identity.**

Apply that principle to the RevRag Viewer.

Do not try to make the interface "fancy."

Make it **recognizable**.

The final Viewer should look like a deliberately designed product with a clear visual language—not a default AI-generated dashboard with a new accent color.
