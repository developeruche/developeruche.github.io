# Developer Uche — Design System

> Extracted from the v2 portfolio (`index.html`, `projects.html`, `blog.html`,
> `publications.html`, `styles.css`, `index.js`). Every value below traces to
> that source. Recommendations that improve on source inconsistencies are
> labelled **REC** and kept separate from extracted truth.

---

## 1. Brand & Voice

A **light terminal / blueprint** personal brand for a blockchain protocol
engineer. The interface reads like ink on paper: off-white canvas, pixel-mono
typefaces, **everything uppercase**, very dark **navy blue** as the single
accent, and `//` comment prefixes + `→` arrows borrowed from source code.

- **Tone:** technical, terse, confident. Labels read like code comments
  (`// 01  HIGHLIGHT`, `// FEATURED PROJECTS`).
- **Mood:** calm, editorial, low-chroma. Contrast is gentle — navy ink and a
  navy-blue accent on warm off-white, not the old neon black-on-yellow shock.
- **Motion:** restrained and "instrument-like" — slow scroll reveals, SVG line
  draws, pulsing nodes, drifting particles. Nothing bouncy.
- **RATIONALE:** the identity *is* the constraint — one hue (navy) + paper +
  mono type. When in doubt, deepen the navy or add weight, don't add a new hue.

---

## 2. Color

> **THEME NOTE.** This is the **light** scheme — off-white / navy / black. It
> replaced the original glow-on-black + electric-yellow look. Only the color,
> gradient, and shadow tokens changed; type, spacing, and components are intact.
> The original dark look is kept as an optional `[data-theme="dark"]` block at
> the bottom of `tokens.css`.

### Primitives
| Token | Value | Notes |
|---|---|---|
| `--color-offwhite` | `#F4F2EC` | paper — page background |
| `--color-offwhite-raised` | `#FCFBF8` | lifted paper — cards/surfaces |
| `--color-white` | `#FFFFFF` | pure white (rare, max-light strokes) |
| `--color-navy-900` | `#0B1A2E` | very dark navy — primary "ink" text |
| `--color-navy-700` | `#1B3A6B` | **the** accent (navy blue) |
| `--color-navy-500` | `#54627A` | navy-gray — muted/body text |
| `--color-navy-200` | `#C9D0DB` | light navy-gray — borders/dividers |
| `--color-navy-100` | `#E7EAF0` | faint navy tint — chip fills |
| `--color-black` | `#000000` | true black — max-contrast emphasis |

### Semantic (use these in UI)
| Token | → | Role | RATIONALE |
|---|---|---|---|
| `--color-bg` | offwhite | app background | warm paper keeps contrast gentle |
| `--color-surface` | offwhite-raised | cards, inputs, chips | a touch lighter than paper = raised |
| `--color-border` | navy-200 | 1px borders/dividers | structure without drawing the eye |
| `--color-text` | navy-900 | headings/strong text | near-black navy ink, not pure black |
| `--color-text-muted` | navy-500 | body copy, captions | body is intentionally quiet |
| `--color-accent` | navy-700 | link-hover, labels | the one hue allowed to carry meaning |
| `--color-accent-hover` | navy-900 | deepened accent | hover/active darkens, never brightens |
| `--color-on-accent` | offwhite | text on navy fills | off-white reads cleanly on navy |

Translucent helpers: `--color-accent-a20…a60` (soft navy depth),
`--color-white-a05` (navy chip fill), `--color-scrim-80` (header fade / card shadow).

Gradients: `--gradient-mono` (navy ramp `#1B3A6B→#54627A`, used for text emphasis,
the primary button fill, particles, the footer hairline) and `--gradient-header`
(off-white→transparent top fade).

> **RESOLVED DRIFT.** The original `.btn-primary` carried off-palette **magenta**
> + **cyan** glows (leftover from a "reference video"). In this re-theme they are
> retired to on-system navy elevation (`--shadow-btn-primary[-hover]`).

> **ACCESSIBILITY NOTE.** Navy ink `--color-text` (#0B1A2E) on off-white is
> ~15:1; muted body `--color-text-muted` (#54627A) on off-white ≈ 4.7:1 — passes
> AA for normal text but is the floor; don't lighten it further. Accent navy
> (#1B3A6B) on off-white ≈ 8:1 (good for links/labels); off-white **on** navy
> ≈ 7:1. Because ink and accent are both dark, signal link hover/active with the
> navy-blue accent **plus** the subtle `--glow-accent-*` depth (or an underline)
> — color alone shifts only slightly.

---

## 3. Typography

Two Google fonts: **VT323** (pixel display) for headings, **Share Tech Mono**
for everything else. `text-transform: uppercase` is global on `<body>`.

| Token | Value | Applied to |
|---|---|---|
| `--font-heading` | `'VT323', monospace` | `h1–h3`, hero/section titles |
| `--font-ui` | `'Share Tech Mono', monospace` | body, nav, buttons, chips |
| `--font-mono` | → `--font-ui` | inline SVG `<text>` (was undefined in source) |

### Type scale (extracted)
| Token | Size | Use |
|---|---|---|
| `--text-hero` | `clamp(4rem,10vw,8.5rem)` | `.hero-title` (tracking 2px) |
| `--text-section` | `clamp(3rem,6vw,5rem)` | `.section-title` |
| `--text-2xl` | `24px` | `.list-item h3` (line-height 1.2) |
| `--text-xl` | `20px` | `.logo`, `.card-title` |
| `--text-lg` | `16px` | newsletter submit arrow |
| `--text-md` | `14px` | nav brand word, `.subsection-title` (tracking 2px) |
| `--text-base` | `13px` | **body / paragraphs / buttons (default)** |
| `--text-sm` | `12px` | `.read-more`, footer caption, `.mini-card` |
| `--text-xs` | `11px` | `.footer-bottom`, meta chips, `.tag-link` |

Line-heights: `--leading-tight 0.9` (headings), `--leading-snug 1.2`
(list h3), `--leading-base 1.5` (body). Tracking: `0.5px` body, `2px` display.
Weights: headings `400` (VT323 is intrinsically chunky), `700` for
`.btn-primary` and `.read-more`.

- **RATIONALE:** the dramatic jump from 13px body to clamp(8.5rem) hero is the
  signature contrast. Keep body small and let display type carry scale.
- **DRIFT:** base is hardcoded `13px` in `body`, `p`, and `button` rather than a
  shared token. **REC:** route all three through `--text-base`.

---

## 4. Spacing & Sizing

Primary rem scale (≈ ×2 ramp):

| Token | px | Typical use |
|---|---|---|
| `--space-xs` | 8 | link-column gaps, nav-links gap |
| `--space-sm` | 16 | heading margins, nav gaps |
| `--space-md` | 32 | section/header padding, card gaps, `<p>` margin |
| `--space-lg` | 64 | card padding, hero-subtitle margin |
| `--space-xl` | 96 | section rhythm, footer top |

- **RATIONALE:** vertical rhythm is driven by `md/lg/xl`; `xs/sm` handle
  intra-component gaps.
- **DRIFT:** ~15 ad-hoc px values (`5,10,12,15,20,24,30,180,200,300,400,800`)
  appear inline. Common ones are tokenized as `--space-2…--space-30`. **REC:**
  migrate inline px to the rem scale where it doesn't break layout.

Layout sizes: `--container-narrow 900px` (reading column & max info-card),
`--container-prose 60ch` (paragraph width), `--header-offset 100px`,
`--size-avatar 32px`, `--size-svg-illu 150px`.

---

## 5. Radius, Border, Shadow

**Radius** (reconstructed — no source token): `--radius-xs 4px` (chip) ·
`--radius-sm 8px` (mini-card) · `--radius-md 16px` (info-card) ·
`--radius-pill-sm 20px` (tag-link) · `--radius-pill 30px` (buttons) ·
`--radius-full 50%` (avatar, particles).
- **RATIONALE:** soft cards (16px) + fully-pill interactive controls (20–30px)
  is the consistent intent; the small chips just round their corners.

**Border:** `--border-1 1px` default; `--border-2 2px` for the accent left-rail
on featured cards, the connector line, and animated SVG paths.

**Shadow / glow** — in light mode the old emitted "glow" becomes soft,
navy-tinted elevation. Token *names* are unchanged so components keep working:
- `--shadow-card-hover` `0 10px 30px rgba(11,26,46,.12)` — card lift on hover.
- `--glow-accent-sm/md/lg` — subtle navy depth (labels, link hover, logo).
- `--glow-inset-accent` — `inset 0 0 0 1px` navy ring on `.btn-secondary:hover`.
- `--shadow-btn-primary` / `-hover` — navy elevation, resting → hover lift.
- **RATIONALE:** on paper, light is *received*, not emitted; prefer soft
  navy-tinted shadows (`box-shadow: 0 Ny Nblur var(--color-accent-aXX)`) over
  glows. Keep elevation shallow — this is an editorial, not neon, surface.

---

## 6. Motion

| Token | Value | Used by |
|---|---|---|
| `--motion-fast` | 0.3s | link color, buttons, newsletter border |
| `--motion-medium` | 0.4s | info-card border + shadow |
| `--motion-slow` | 1s | `.slide-up` reveal |
| `--motion-slower` | 1.5s | `.fade-in` reveal |
| `--motion-draw` | 2s | SVG `stroke-dashoffset` line-draw |
| `--ease-emphasized` | `cubic-bezier(0.16,1,0.3,1)` | scroll reveals |
| `--ease-material` | `cubic-bezier(0.4,0,0.2,1)` | SVG draw |

Patterns:
- **Scroll reveal** (`index.js`): `IntersectionObserver` (threshold 0.1,
  rootMargin `0 0 -100px 0`) adds `.is-visible` once. `.slide-up` rises 40px +
  fades; `.fade-in` fades only. Fires once, then unobserves.
- **Ambient**: `@keyframes float` (6s, particles drift up + rotate),
  `@keyframes pulseGlow` (3s, glow-node breathes).
- **SVG line-draw**: `stroke-dasharray:1000; stroke-dashoffset:1000 → 0` on
  `.is-visible`. Plus SMIL `<animate>`/`<animateMotion>` for data-packet dots.
- **RATIONALE:** motion signals "system is live." Reveal-once avoids fatigue;
  ambient loops stay subtle (low opacity, slow).
- **REC:** wrap ambient loops in `@media (prefers-reduced-motion: reduce)` — the
  source has no reduced-motion guard.

---

## 7. Layout & Grid

- **Page frame:** fixed `.header` (z 100, `backdrop-filter: blur(5px)`,
  off-white→transparent gradient) over a single scrolling `<main>`; `.footer`
  closes with a navy-gradient centered hairline (`::before`).
- **Reading column:** `.container-narrow` = `max-width:900px; margin:0 auto`.
- **Hero/page-header:** full-viewport centered flex column; `page-header` uses
  `180px` top padding to clear the fixed header.
- **Card grid:** `.project-grid` = `repeat(auto-fill, minmax(350px, 1fr))`,
  gap `--space-md`. A secondary inline grid uses `auto-fit, minmax(280px,1fr)`.
  - **DRIFT:** two near-identical grid recipes. **REC:** standardize on
    `auto-fill / minmax(--grid-card-min, 1fr)`.
- **Connector spine:** absolutely-positioned 2px dashed SVG line down the center
  of `.cards-section`, hidden below 768px.
- **Breakpoint:** single `@media (max-width: 768px)` — info-cards stack to a
  centered column, connector hides.
- **RATIONALE:** content is a vertical narrative on a 900px spine; the grid is
  the only 2-D region. Keep new layouts single-column-first.

---

## 8. Component Catalog

Full anatomy/states live in `components.md`; specs summarized here.

| Component | Key tokens | States |
|---|---|---|
| **Header / nav** | fixed, `--z-header`, `--blur-header`, `--gradient-header` | `a.active` → accent + `--glow-accent-sm` |
| **Brand logo** | avatar 32px round, `1px solid --color-accent` border | hover inherits link glow |
| **Button · primary** | `--gradient-mono` fill, `--color-on-accent` text, `--radius-pill`, weight 700, `--shadow-btn-primary` | hover → `--shadow-btn-primary-hover`, inner `<span>` arrow shifts +5px |
| **Button · secondary** | `--color-surface` + `--border-1 --color-border`, `--radius-pill` | hover → accent border + `--glow-inset-accent` |
| **Info card** | `--color-surface`, `1px --color-border`, `--radius-md`, padding `--space-lg` | hover → `border:accent-a30` + `--shadow-card-hover`; `.reverse` flips; `.project-grid` variant = column, left accent rail on featured |
| **Mini card** | `--color-surface`, `--radius-sm`, `--text-sm` | hover → accent border |
| **Meta chip** (`.meta-tags span`) | `--color-white-a05`, `1px --color-border`, `--radius-xs`, `--text-xs` | static |
| **Tag link** (`.tag-link`) | outline pill `--radius-pill-sm`, `--text-xs`, muted | hover → invert (navy-ink bg, off-white text) |
| **Read-more link** | `--color-accent`, weight bold, `--text-sm`, `→` | hover inherits link glow |
| **List item** | `1px dashed --color-border`, padding `--space-md 0` | hover → bottom border accent |
| **Section label** (`// 01 …`) | `--color-accent` + `--glow-accent-sm` | static |
| **Subsection title** | muted, `--text-md`, tracking 2px, bottom rule | static |
| **Newsletter form** | bottom-border input + accent submit | `:focus-within` → accent border |
| **SVG illustration** | `--size-svg-illu`, stroke `--color-text`, `1.5` | `.glow-node` pulses; `.animated-path-segment` draws on reveal |
| **Particles** | 4 absolutely-placed dots, `--gradient-mono`, `float` 6s | ambient loop |

> **DRIFT — undefined vars in markup.** Inline SVGs reference
> `var(--text-secondary)` and `var(--font-mono)`, neither defined in the source
> `:root`. `tokens.css` defines both (→ muted text / `--font-ui`) so SVG art
> renders as intended.

> **DRIFT — orphan CSS.** `.newsletter-form` is fully styled but the index
> footer uses a plain mailto block instead. Component is documented for reuse.

---

## 9. Naming Convention (recap)

- **Primitive:** `--color-<hue>-<step>` (e.g. `--color-navy-700`). Raw value.
  Never used directly in components.
- **Semantic:** `--color-<role>` (e.g. `--color-accent`, `--color-surface`).
  Points at a primitive. **This is what components reference.**
- **Scales:** `--space-*`, `--text-*`, `--radius-*`, `--shadow-*`, `--glow-*`,
  `--motion-*`, `--ease-*`, `--z-*`, `--font-*`.
- **RATIONALE:** swapping a primitive (or adding a light theme) re-skins the
  whole system without touching component CSS.
