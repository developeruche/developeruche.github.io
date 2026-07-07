# Developer Uche — Design System

A complete, portable design system **reverse-engineered from the actual v2
portfolio code** (`../index.html`, `../projects.html`, `../blog.html`,
`../publications.html`, `../styles.css`, `../index.js`), then **re-themed to a
light palette**. Every structural value traces to that source; recommendations
that fix source inconsistencies are labelled **REC** and kept separate.

**Aesthetic in one line:** light terminal / blueprint — off-white paper
(`#F4F2EC`), VT323 + Share Tech Mono pixel fonts, all-uppercase, a single very
dark navy-blue accent (`#1B3A6B`) with navy ink (`#0B1A2E`), soft navy elevation.

## File map
| File | What it is |
|---|---|
| `DESIGN.md` | Primary artifact. Brand/voice, color (primitive+semantic), type & spacing scales, radius/shadow/motion, layout & grid, component catalog — each major decision has a RATIONALE. Built for Claude Design ingestion. |
| `tokens.css` | All tokens as `:root` CSS custom properties, grouped by category. Drop-in for `globals.css`. Light-mode default (off-white/navy/black) + a commented optional `[data-theme="dark"]` block. |
| `components.md` | Per-component anatomy, variants, states, do/don't, and token references. |
| `design-system.html` | Self-contained live reference page — renders palette, type, spacing, radius, and every component/state from `tokens.css`. Visual source of truth. |
| `SKILL.md` | Claude Skill wrapper so the system auto-loads in Claude Code / Claude.ai. |
| `README.md` | This file. |

## Usage

### (a) Import `DESIGN.md` into Claude Design
1. Open Claude Design → create/open a project.
2. Add `DESIGN.md` as design-system context (paste its contents or upload the
   file). It is self-contained — colors, type, spacing, components, and rationale
   are all inline.
3. Optionally also attach `tokens.css` and `components.md` so the agent can cite
   exact token names. Ask Claude to "build X using the Developer Uche design
   system" and it will reference the semantic tokens.

### (b) Drop `tokens.css` into a new project
1. Copy `tokens.css` into your styles dir (e.g. `app/globals.css` or import it
   from there: `@import "./tokens.css";`).
2. Load the two fonts (already used by the source):
   ```html
   <link rel="preconnect" href="https://fonts.googleapis.com">
   <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
   <link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=VT323&display=swap" rel="stylesheet">
   ```
3. Reference **semantic** tokens in your components:
   ```css
   .button { background: var(--gradient-mono); color: var(--color-on-accent);
             border-radius: var(--radius-pill); padding: var(--space-12) var(--space-24); }
   ```
   - **Tailwind:** map tokens in `theme.extend` (e.g.
     `colors: { accent: 'var(--color-accent)', surface: 'var(--color-surface)' }`,
     `borderRadius: { pill: 'var(--radius-pill)' }`).
   - **React (CSS-in-JS / inline):** use `var(--token)` strings directly.
4. Dark theme (optional): light is the default. Uncomment the
   `[data-theme="dark"]` block at the bottom of `tokens.css` and set
   `data-theme="dark"` on `<html>` to switch to the original glow-on-navy look.

### (c) Install `SKILL.md` as a skill
- **Claude Code (project):** copy this folder to
  `.claude/skills/developeruche-design-system/` in your repo (it must contain
  `SKILL.md` plus the reference files). It auto-loads when relevant.
- **Claude Code (personal):** copy to
  `~/.claude/skills/developeruche-design-system/`.
- **Claude.ai:** upload `SKILL.md` (with the companion files) via the Skills UI.
- The `description` front-matter is keyword-rich (tokens, components, colors,
  typography, spacing) so it triggers on UI/styling tasks.

## Theme change vs. the original source
This bundle ships the **light** scheme (off-white / navy / black). The original
site was glow-on-black with an electric-yellow accent. Only **color, gradient,
and shadow** tokens moved — typography, spacing, radius, layout, and every
component are unchanged. The dark look is preserved as the optional
`[data-theme="dark"]` block in `tokens.css`.

## Drift found in the source (summary)
- **Off-palette button glows** — the original `.btn-primary` used magenta/cyan
  shadows (leftover from a reference video); **retired** to on-system navy
  elevation in this re-theme.
- **Undefined vars in markup** — inline SVGs reference `--text-secondary` and
  `--font-mono`, never defined in source; `tokens.css` defines both.
- **Hardcoded base size** — `13px` repeated instead of a token (now `--text-base`).
- **Two grid recipes** — `auto-fill minmax(350px)` vs `auto-fit minmax(280px)`.
- **Ad-hoc spacing** — ~15 inline px values bypass the rem scale.
- **No radius token / no reduced-motion guard** in source.

See `DESIGN.md` and `components.md` for the labelled details and recommended fixes.
