# Component Catalog

Every component references **tokens** from `tokens.css` — no hardcoded values.
Each entry: **Anatomy · Variants · States · Do / Don't · Tokens**.

---

## Header / Navigation

**Anatomy.** Fixed full-width bar. Left group = brand (round avatar + lowercase
word `developeruche`) + horizontal `.nav-links`. Right group = `CONTACT`
primary button. Sits above a black→transparent gradient with backdrop blur.

**States.** Active page link (`a.active`) → `--color-accent` + `--glow-accent-sm`.
Any link hover → `--color-accent` + `--glow-accent-md`.

**Do** keep the bar transparent-blurred so hero content shows through.
**Don't** give it a solid fill or a bottom border — it floats.

**Tokens.** `--z-header`, `--blur-header`, `--gradient-header`, `--space-md`
(padding), `--color-accent`, `--glow-accent-sm/md`, `--size-avatar`,
`--radius-full`.

---

## Buttons

Three forms share: `--font-ui`, uppercase, `--text-base`, inline-flex, `gap:8px`,
`transition: all --motion-fast`. An inner `<span>` (usually `→`) slides +5px on
hover.

### Primary — `.btn-primary`
**Anatomy.** Pill with `--gradient-mono` (navy ramp) fill, `--color-on-accent`
(off-white) text, weight 700, padding `--space-12 --space-24`.
**States.** Resting `--shadow-btn-primary` (soft navy); hover lifts to
`--shadow-btn-primary-hover` + inner `<span>` arrow shifts +5px.
> Navy elevation replaced the original off-palette magenta/cyan glows.
**Do** use for the single most important action per view (CONTACT, VIEW PROJECTS).
**Don't** place two primaries side by side.

### Secondary — `.btn-secondary`
**Anatomy.** Pill, `--color-surface` fill, `--border-1 --color-border`,
`--color-text` text, same padding.
**States.** Hover → border `--color-accent` + `--glow-inset-accent` (1px navy ring).
**Do** use for everything alongside a primary (GITHUB, READ PAPER).
**Don't** stack effects — the inset ring is the whole hover signal.

### Bare / icon button — `button`
Transparent, no border, used for the newsletter submit (accent, `--text-lg`).

**Tokens.** `--gradient-mono`, `--color-on-accent`, `--color-surface`,
`--color-border`, `--color-accent`, `--radius-pill`, `--space-12/24`,
`--font-weight-bold`, `--shadow-btn-primary*`, `--glow-inset-accent`,
`--motion-fast`.

---

## Info Card — `.info-card`

**Anatomy.** Horizontal flex row: `.card-content` (label + title + copy + CTA)
beside `.card-art` (SVG illustration). Surface fill, 1px border, 16px radius,
`--space-lg` padding, `max-width:900px`.

**Variants.**
- `.reverse` — flips to `row-reverse` (alternating zig-zag down the page).
- **Grid variant** (inside `.project-grid`) — becomes a vertical column,
  `--space-md` padding, `height:100%`.
- **Featured** — add `border-left: --border-2 solid --color-accent` (left rail).

**States.** Hover → border `--color-accent-a30` + `--shadow-card-hover`
(`--motion-medium`). Mobile (<768px): stacks to centered column.

**Do** alternate `.reverse` for narrative sections; use the grid variant for
catalogs. **Don't** mix the accent left-rail onto non-featured cards.

**Tokens.** `--color-surface`, `--color-border`, `--color-accent-a30`,
`--radius-md`, `--space-lg/md`, `--shadow-card-hover`, `--border-2`,
`--color-accent`, `--motion-medium`, `--container-narrow`.

---

## Mini Card — `.mini-card`

Compact info tile: surface fill, 1px border, `--radius-sm`, `--text-sm`,
centered, `min-width:250px`, flex `1`. Hover → accent border. Use for dense
stat/link rows.

**Tokens.** `--color-surface`, `--color-border`, `--radius-sm`, `--text-sm`,
`--color-accent`.

---

## Chips & Tags

### Meta chip — `.meta-tags span`
Tiny static label. `--color-white-a05` fill, 1px border, `--radius-xs`,
`--text-xs`, muted text, padding `2px 8px`. Rendered in a `gap:10px` flex row.
**Do** use for taxonomy (Rust, RISC-V, HackMD). **Don't** make them clickable —
that's `.tag-link`.

### Tag link — `.tag-link`
Interactive outline pill: `--radius-pill-sm`, `--text-xs`, muted, padding
`6px 14px`. Hover **inverts**: `--color-text` (navy-ink) bg with
`--color-on-accent` (off-white) text. Use as a card's inline CTA (VIEW PRs).

**Tokens.** `--color-white-a05`, `--color-border`, `--radius-xs`,
`--radius-pill-sm`, `--text-xs`, `--color-text-muted`, `--color-text`.

---

## List Item — `.list-item`

**Anatomy.** Stacked entry: `h3` title (`--text-2xl`, leading 1.2), optional
`.meta-tags`, `<p>` summary, `.read-more` link. Separated by
`1px dashed --color-border`.

**States.** Hover → bottom border `--color-accent` (`--motion-fast`).

**Do** use for blog/publication indexes (many rows). **Don't** box them — the
dashed divider is the only separator.

**Tokens.** `--color-border` (dashed), `--space-md`, `--text-2xl`,
`--leading-snug`, `--color-accent`, `--motion-fast`.

---

## Read-more Link — `.read-more`

Accent-colored, bold, `--text-sm`, trailing `→`. The recurring "go deeper" CTA.
Inherits the global link hover glow.
**Tokens.** `--color-accent`, `--font-weight-bold`, `--text-sm`, `--glow-accent-md`.

---

## Labels & Titles

- **Section label** `.section-label` — `// 01  HIGHLIGHT`. Accent +
  `--glow-accent-sm`, margin-bottom `--space-sm`. Signals a card's index/topic.
- **Subsection title** `.subsection-title` — `// FEATURED PROJECTS`. Muted,
  `--text-md`, tracking 2px, `1px --color-border` bottom rule.
- **Hero title** `.hero-title` — `--text-hero`, tracking 2px, `--font-heading`.
- **Section title** `.section-title` — `--text-section`.
- **Text gradient** `.text-gradient` — clips `--gradient-mono` into glyphs
  (used on one word per title for emphasis).

**Do** prefix labels with `//` to stay on-voice. **Don't** sentence-case —
everything is uppercase.

---

## Newsletter Form — `.newsletter-form`

**Anatomy.** Bottom-border row: transparent text input + accent submit button.
`max-width:300px`.
**States.** `:focus-within` → border `--color-accent`. Placeholder = muted.
> Styled but unused in the shipped footer (orphan). Documented for reuse.
**Tokens.** `--color-border`, `--color-accent`, `--color-text-muted`,
`--motion-fast`.

---

## Footer — `.footer`

**Anatomy.** `.footer-top` (newsletter/mission + link columns) → `.footer-bottom`
(genre + copyright, `--text-xs`). A navy-gradient centered hairline (`::before`,
200px, `--gradient-mono` + accent glow) caps the top edge.
**Tokens.** `--space-xl/md`, `--color-border`, `--gradient-mono`,
`--color-accent`, `--text-xs`, `--color-text-muted`.

---

## Decorative / Motion Components

- **SVG illustration** `.svg-illustration` — 150px, `fill:none`,
  `stroke:--color-text`, width 1.5, round caps/joins.
  - `.glow-node` → `drop-shadow` + `pulseGlow` 3s breathing; strokes go accent.
  - `.animated-path-segment` → `stroke-dasharray:1000` draws to offset 0 when an
    ancestor gets `.is-visible`.
- **Connector line** `.connector-line` — centered 2px dashed vertical spine
  behind a card column; hidden < 768px.
- **Particles** `.particle` — 4 absolutely-placed dots/shards,
  `--gradient-mono`, `float` 6s with staggered delays; one is pure accent with a
  drop-shadow.

**Reveal classes** (paired with `index.js` IntersectionObserver):
- `.slide-up` → translateY(40px)+fade, `--motion-slow` `--ease-emphasized`.
- `.fade-in` → opacity, `--motion-slower` `--ease-out`.
- `.is-visible` → reset to resting (added once, then unobserved).

**Do** add `.slide-up`/`.fade-in` to major blocks for the on-scroll reveal.
**Don't** rely on them for content visibility — guard with
`prefers-reduced-motion` (REC; absent in source).

**Tokens.** `--size-svg-illu`, `--color-text`, `--color-accent`, `--border-2`,
`--gradient-mono`, `--motion-slow/slower/draw`, `--ease-emphasized/out/material`.
