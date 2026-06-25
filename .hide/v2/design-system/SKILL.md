---
name: developeruche-design-system
description: Light terminal/blueprint design system (tokens, components, colors, typography, spacing, radius, shadows, motion) for the Developer Uche brand — off-white, navy blue, black. Load when building UI, styling pages, or theming React/Tailwind/CSS in this aesthetic.
---

# Developer Uche Design System

A portable, token-driven design system extracted from the Developer Uche v2
portfolio and re-themed to a **light** palette. Aesthetic: **light terminal /
blueprint** — off-white paper (`#F4F2EC`), VT323 + Share Tech Mono pixel fonts,
all-uppercase text, a single very-dark-navy-blue (`#1B3A6B`) accent, navy ink
(`#0B1A2E`), and soft navy elevation instead of neon glow.

## When to use
Use whenever you build or restyle UI for this brand — pages, components, color,
typography, spacing, radius, shadow, or motion decisions. Reference the tokens
and component specs instead of inventing values.

## How to use
1. **Tokens** — copy `tokens.css` into the project and import it (e.g. into
   `globals.css`). Reference semantic CSS variables (`--color-accent`,
   `--color-surface`, `--space-md`, `--radius-pill`, `--text-base`,
   `--motion-fast`…). Never hardcode hex/px when a token exists.
2. **Specs** — read `DESIGN.md` for the full system (brand voice, color tokens,
   type/spacing scales, layout & grid rules, component catalog) with a one-line
   RATIONALE per decision so you stay on-system in uncovered cases.
3. **Components** — read `components.md` for per-component anatomy, variants,
   states, do/don't, and which tokens each one uses.
4. **Visual truth** — open `design-system.html` in a browser to see the live
   palette, type scale, spacing, and every component/state rendered from
   `tokens.css`.

## Core rules
- **One hue (navy) + paper.** Off-white / navy / black only. When in doubt,
  deepen the navy or add weight — don't introduce a new hue.
- **Everything uppercase**, mono fonts; headings = VT323, UI/body = Share Tech Mono.
- **Body is small (13px) and muted navy-gray (#54627A);** display type carries scale.
- **Soft navy elevation, not glow.** Prefer shallow `box-shadow` tinted with
  `var(--color-accent-aXX)`; keep it editorial, not neon.
- **Voice:** prefix labels with `//`, use `→` for "go deeper" CTAs.
- **Hover signal:** ink and accent are both dark — use the navy accent **plus**
  `--glow-accent-*` depth (or an underline), since color alone shifts little.

## Notes
- The original off-palette magenta/cyan button glows were **retired** to
  on-system navy elevation (`--shadow-btn-primary[-hover]`).
- Source left `--text-secondary` / `--font-mono` undefined; `tokens.css` defines
  them. Always use the tokenized versions.
- This is the **light** scheme; the original glow-on-black look is available as
  an optional `[data-theme="dark"]` block at the bottom of `tokens.css`.

## Files
- `tokens.css` — all design tokens (`:root` custom properties).
- `DESIGN.md` — primary spec + rationale.
- `components.md` — component catalog.
- `design-system.html` — live visual reference.
- `README.md` — install/usage for Claude Design, projects, and skills.
