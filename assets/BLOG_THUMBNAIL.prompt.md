# Blog Thumbnail — Image Generation Prompt

A reusable prompt for generating blog-post thumbnails that match the
**developeruche** "light terminal / blueprint" design system. Swap the
`{{BLOG_TITLE}}` placeholder to generate a new thumbnail; keep everything else
fixed so the whole set stays visually consistent.

---

## How to use
1. Copy the **Prompt** block below.
2. Replace `{{BLOG_TITLE}}` with the post title, e.g.
   `Deconstructing the 1.5 GHz zkVM: How ZisK Redefined the Limits of Trace Generation`.
3. Generate at **1600×900 (16:9)**. Save as `assets/blog/<slug>.png` and set the
   matching item's `thumbnail` field in `data/blog.json`.

---

## Prompt

```
A 16:9 technical blueprint-style thumbnail graphic for an engineering blog post.

DESIGN SYSTEM (follow exactly):
- Aesthetic: light "terminal / blueprint" — like an architect's schematic crossed
  with a monospace code editor. Clean, editorial, precise. NOT neon, NOT glossy,
  NOT 3D, NOT photorealistic.
- Background: warm off-white paper, hex #F4F2EC, with a faint navy engineering
  grid (thin 1px lines, hex #1B3A6B at ~12% opacity) and subtle crosshatch and
  dashed construction lines, as if drafted on graph paper.
- Ink / line work: very dark navy, hex #0B1A2E, for primary strokes; medium navy
  #1B3A6B as the single accent color. Navy-gray #54627A for secondary detail.
  Use ONLY this palette — off-white, navy, near-black. No other hues.
- Typography: all-caps pixel/monospace lettering (VT323 / Share Tech Mono vibe).
- Voice marks: include a small "//" comment-style label and a "→" arrow glyph as
  decorative terminal accents.

COMPOSITION:
- Left/center: the post title set in bold all-caps monospace navy ink, wrapped to
  2-4 lines, as the clear focal point:
  "{{BLOG_TITLE}}"
- Above the title, a tiny accent label in navy reading "// DEVELOPERUCHE — BLOG".
- Right/background: an abstract line-art diagram thematically related to the
  title — e.g. nodes and edges, circuit traces, polynomial curves, stacked
  layers, hash trees, or VM/register schematics — drawn as thin navy vector
  strokes with round caps, like a wireframe illustration. Keep it secondary to
  the text and low-contrast so the title stays readable.
- A thin navy accent rule or bracket framing one corner.
- Generous margins; balanced, calm, lots of paper showing through.

CONSTRAINTS:
- Flat 2D vector look. No gradients except a single very subtle navy elevation
  shadow if needed. No photographic textures, no people, no logos, no emojis.
- High contrast between the navy title text and the off-white paper (WCAG AA).
- Spell the title text exactly as given, in all caps.
```

---

## Variant knobs (optional)
- **Diagram motif** — append one line to steer the background art, e.g.
  `Background diagram motif: layered arithmetic circuit with sum-check folds.`
- **Density** — add `minimal, mostly empty paper` for a sparser look, or
  `dense schematic detail` for a busier one.
- **No title text** — if your renderer mangles text, drop the title lines and
  generate a pure blueprint texture, then overlay the title in HTML/CSS instead.

## Tokens reference (source of truth: assets/css/tokens.css)
| Role            | Hex       |
| --------------- | --------- |
| Paper / bg      | `#F4F2EC` |
| Raised paper    | `#FCFBF8` |
| Ink (near-black)| `#0B1A2E` |
| Accent navy     | `#1B3A6B` |
| Muted navy-gray | `#54627A` |
| Borders         | `#C9D0DB` |

Fonts: **VT323** (display) · **Share Tech Mono** (UI/body). Everything uppercase.
