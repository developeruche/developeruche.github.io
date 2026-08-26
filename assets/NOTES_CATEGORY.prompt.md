# Notes Category Art — Image Generation Prompts

Three prompts, one per notes category, derived from
[`BLOG_THUMBNAIL.prompt.md`](BLOG_THUMBNAIL.prompt.md). Same design system, so
the notes index sits alongside the blog set without looking like a different
site. Only the accent label and the diagram motif differ.

Generate at **1600×900 (16:9)** and save to the path given under each prompt.

> **Recommended: generate the textless variant.** Each prompt ends with an
> optional `NO TEXT` clause. Because these are category cards whose titles I
> render in HTML, dropping the baked-in lettering is better: the type comes out
> in the real VT323/Share Tech Mono, it stays selectable and accessible, it
> survives a category rename, and there is no risk of the generator misspelling
> it. Use the with-text version only if you want the art to stand alone.

---

## 1. Blockchain

Save as `assets/notes/blockchain.png`

```
A 16:9 technical blueprint-style category card for an engineering notes index.

DESIGN SYSTEM (follow exactly):
- Aesthetic: light "terminal / blueprint" — an architect's schematic crossed with
  a monospace code editor. Clean, editorial, precise. NOT neon, NOT glossy,
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
- Left/center: the category name set in bold all-caps monospace navy ink, on one
  line, as the clear focal point:
  "BLOCKCHAIN"
- Above it, a tiny accent label in navy reading "// DEVELOPERUCHE — NOTES".
- Right/background: an abstract line-art diagram of a chain of block headers —
  rectangular blocks linked left to right by hash arrows, each block opening into
  a small Merkle tree of hashed leaves, with one branch drawn as a nested
  Patricia-trie path. Thin navy vector strokes with round caps, wireframe style.
  Keep it secondary and low-contrast so the title stays readable.
- A thin navy accent rule or bracket framing one corner.
- Generous margins; balanced, calm, lots of paper showing through.

CONSTRAINTS:
- Flat 2D vector look. No gradients except a single very subtle navy elevation
  shadow if needed. No photographic textures, no people, no logos, no emojis.
- High contrast between the navy title text and the off-white paper (WCAG AA).
- Spell the title text exactly as given, in all caps.

NO TEXT VARIANT (recommended): omit the title and the "//" label entirely and
render only the blueprint texture and the chain/Merkle diagram, composed so the
left third stays mostly empty paper for a title to be overlaid in HTML.
```

---

## 2. Cryptography & ZKP

Save as `assets/notes/cryptography-zkp.png`

```
A 16:9 technical blueprint-style category card for an engineering notes index.

DESIGN SYSTEM (follow exactly):
- Aesthetic: light "terminal / blueprint" — an architect's schematic crossed with
  a monospace code editor. Clean, editorial, precise. NOT neon, NOT glossy,
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
- Left/center: the category name set in bold all-caps monospace navy ink, wrapped
  to two lines, as the clear focal point:
  "CRYPTOGRAPHY & ZKP"
- Above it, a tiny accent label in navy reading "// DEVELOPERUCHE — NOTES".
- Right/background: an abstract line-art diagram of a layered arithmetic circuit —
  addition and multiplication gates wired in fan-in-2 layers, folding upward into
  a single output wire, with a smooth polynomial curve plotted across a lattice of
  evaluation points beneath it and a small bracketed commitment box at the apex.
  Thin navy vector strokes with round caps, wireframe style. Keep it secondary and
  low-contrast so the title stays readable.
- A thin navy accent rule or bracket framing one corner.
- Generous margins; balanced, calm, lots of paper showing through.

CONSTRAINTS:
- Flat 2D vector look. No gradients except a single very subtle navy elevation
  shadow if needed. No photographic textures, no people, no logos, no emojis.
- High contrast between the navy title text and the off-white paper (WCAG AA).
- Spell the title text exactly as given, in all caps.

NO TEXT VARIANT (recommended): omit the title and the "//" label entirely and
render only the blueprint texture and the circuit/polynomial diagram, composed so
the left third stays mostly empty paper for a title to be overlaid in HTML.
```

---

## 3. Artificial Intelligence

Save as `assets/notes/artificial-intelligence.png`

```
A 16:9 technical blueprint-style category card for an engineering notes index.

DESIGN SYSTEM (follow exactly):
- Aesthetic: light "terminal / blueprint" — an architect's schematic crossed with
  a monospace code editor. Clean, editorial, precise. NOT neon, NOT glossy,
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
- Left/center: the category name set in bold all-caps monospace navy ink, wrapped
  to two lines, as the clear focal point:
  "ARTIFICIAL INTELLIGENCE"
- Above it, a tiny accent label in navy reading "// DEVELOPERUCHE — NOTES".
- Right/background: an abstract line-art diagram of a transformer block — a token
  sequence entering as small squares along the bottom, fanning into an attention
  head drawn as a matrix of connection lines between two rows of nodes, then a
  stacked matrix-multiply grid rendered as a tiled rectangle with a few cells
  outlined to suggest quantization buckets. Thin navy vector strokes with round
  caps, wireframe style. Keep it secondary and low-contrast so the title stays
  readable.
- A thin navy accent rule or bracket framing one corner.
- Generous margins; balanced, calm, lots of paper showing through.

CONSTRAINTS:
- Flat 2D vector look. No gradients except a single very subtle navy elevation
  shadow if needed. No photographic textures, no people, no logos, no emojis.
- High contrast between the navy title text and the off-white paper (WCAG AA).
- Spell the title text exactly as given, in all caps.

NO TEXT VARIANT (recommended): omit the title and the "//" label entirely and
render only the blueprint texture and the transformer/attention diagram, composed
so the left third stays mostly empty paper for a title to be overlaid in HTML.
```

---

## Tokens reference (source of truth: `assets/css/tokens.css`)

| Role             | Hex       |
| ---------------- | --------- |
| Paper / bg       | `#F4F2EC` |
| Raised paper     | `#FCFBF8` |
| Ink (near-black) | `#0B1A2E` |
| Accent navy      | `#1B3A6B` |
| Muted navy-gray  | `#54627A` |
| Borders          | `#C9D0DB` |

Fonts: **VT323** (display) · **Share Tech Mono** (UI/body). Everything uppercase.
