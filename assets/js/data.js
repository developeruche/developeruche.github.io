/* ============================================================================
   data.js — shared fetch, normalization, filtering, and rendering helpers.
   Used by every page. Vanilla ES modules, no build step.
   ========================================================================== */

/* Filter combine mode. 'OR' = item shown if it matches ANY selected tag
   (default — avoids empty states). Alternative: 'AND' = item must match ALL
   selected tags. Flip this single constant to change site-wide behavior. */
export const FILTER_MODE = 'OR';

/* ── Fetch ─────────────────────────────────────────────────────────────── */

// Resolve data paths relative to the site root so it works on GitHub Pages
// whether served from a user page (/) or a sub-path.
export async function fetchJSON(path) {
  const res = await fetch(path, { cache: 'no-cache' });
  if (!res.ok) throw new Error(`Failed to load ${path} (${res.status})`);
  return res.json();
}

/* ── Tags: case-insensitive match, Title Case display ──────────────────── */

// Match key — lowercase, trimmed.
export function tagKey(tag) {
  return String(tag || '').trim().toLowerCase();
}

// Display form — Title Case, preserving common acronyms in upper case.
const ACRONYMS = new Set([
  'evm', 'zk', 'zkvm', 'pq', 'risc-v', 'riscv', 'kzg', 'mle', 'iop',
  'snarks', 'sdk', 'api', 'dex', 'erc-2771', 'meta-tx', 'r1cs', 'qap',
  'eof', 'wasm'
]);
export function tagDisplay(tag) {
  const key = tagKey(tag);
  return key
    .split(/\s+/)
    .map((word) => {
      if (ACRONYMS.has(word)) return word.toUpperCase();
      // hyphenated words: title-case each part unless acronym
      return word
        .split('-')
        .map((p) => (ACRONYMS.has(p) ? p.toUpperCase() : p.charAt(0).toUpperCase() + p.slice(1)))
        .join('-');
    })
    .join(' ');
}

// Deduped, sorted display tags from a dataset (case-insensitive).
export function deriveTags(items) {
  const map = new Map(); // key -> display
  items.forEach((item) => {
    (item.tags || []).forEach((t) => {
      const key = tagKey(t);
      if (key && !map.has(key)) map.set(key, tagDisplay(t));
    });
  });
  return [...map.entries()]
    .sort((a, b) => a[1].localeCompare(b[1]))
    .map(([key, display]) => ({ key, display }));
}

/* ── Filtering ─────────────────────────────────────────────────────────── */

// selectedKeys: array of lowercase tag keys. Empty = show all.
export function filterItems(items, selectedKeys) {
  if (!selectedKeys || selectedKeys.length === 0) return items;
  const sel = new Set(selectedKeys);
  return items.filter((item) => {
    const keys = (item.tags || []).map(tagKey);
    if (FILTER_MODE === 'AND') return [...sel].every((k) => keys.includes(k));
    return keys.some((k) => sel.has(k)); // OR (default)
  });
}

// Highlights — first N items flagged highlight === true.
// TODO: curate highlights (currently every item is highlight:true, so this
// returns the first N until the data is curated). Do not hardcode the N items.
export function highlights(items, n = 4) {
  return items.filter((i) => i.highlight === true).slice(0, n);
}

/* ── URL query-string sync (?tags=rust,evm) ────────────────────────────── */

export function readTagsFromURL() {
  const params = new URLSearchParams(location.search);
  const raw = params.get('tags');
  if (!raw) return [];
  return raw.split(',').map(tagKey).filter(Boolean);
}

export function writeTagsToURL(selectedKeys) {
  const params = new URLSearchParams(location.search);
  if (selectedKeys.length) params.set('tags', selectedKeys.join(','));
  else params.delete('tags');
  const qs = params.toString();
  history.replaceState(null, '', qs ? `?${qs}${location.hash}` : location.pathname + location.hash);
}

/* ── DOM helpers ───────────────────────────────────────────────────────── */

export function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null) continue;
    if (k === 'class') node.className = v;
    else if (k === 'html') node.innerHTML = v;
    else if (k === 'text') node.textContent = v;
    else if (k.startsWith('on') && typeof v === 'function') node.addEventListener(k.slice(2), v);
    else node.setAttribute(k, v);
  }
  (Array.isArray(children) ? children : [children]).forEach((c) => {
    if (c == null) return;
    node.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
  });
  return node;
}

/* ── Card image slot: skeleton wireframe when thumbnail is null ─────────── */

export function imageSlot(thumbnail, alt) {
  if (thumbnail) {
    return el('div', { class: 'card-media' }, [
      el('img', { src: thumbnail, alt: alt || '', loading: 'lazy', class: 'card-img' }),
    ]);
  }
  // Blueprint skeleton: bordered box, crosshatch, shimmer (gated by reduced-motion in CSS).
  return el('div', { class: 'card-media card-media--skeleton', role: 'img', 'aria-label': 'Placeholder image' }, [
    el('div', { class: 'skeleton-shimmer' }),
    el('div', {
      class: 'skeleton-blueprint',
      'aria-hidden': 'true',
      html: `<svg viewBox="0 0 100 60" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
        <rect x="1" y="1" width="98" height="58" fill="none" stroke="var(--color-accent-a20)" stroke-width="0.5" stroke-dasharray="2 2"/>
        <line x1="1" y1="1" x2="99" y2="59" stroke="var(--color-accent-a20)" stroke-width="0.5"/>
        <line x1="99" y1="1" x2="1" y2="59" stroke="var(--color-accent-a20)" stroke-width="0.5"/>
        <circle cx="50" cy="30" r="8" fill="none" stroke="var(--color-accent-a30)" stroke-width="0.5"/>
      </svg>`,
    }),
  ]);
}

/* ── Tag chips (display) for a card ────────────────────────────────────── */

export function metaTags(tags) {
  if (!tags || !tags.length) return null;
  return el('div', { class: 'meta-tags' },
    tags.map((t) => el('span', { text: tagDisplay(t) })));
}

/* ── Link buttons row ──────────────────────────────────────────────────── */

export function linkRow(links) {
  if (!links || !links.length) return null;
  return el('div', { class: 'card-links' },
    links.map((l) =>
      el('a', {
        class: 'btn-secondary btn-sm',
        href: l.url,
        target: '_blank',
        rel: 'noopener noreferrer',
      }, [l.label, el('span', { 'aria-hidden': 'true', text: ' →' })])
    ));
}

/* ── Universal card ────────────────────────────────────────────────────── */
// opts: { title, tags, body, links, href, featured }
export function card(opts) {
  const body = el('div', { class: 'card-body' }, [
    el('h3', { class: 'card-title', text: opts.title }),
    metaTags(opts.tags),
    opts.body ? el('p', { class: 'card-copy', text: opts.body }) : null,
    linkRow(opts.links),
  ]);

  const cls = 'info-card card' + (opts.featured ? ' card--featured' : '');

  if (opts.href) {
    // Whole-card link variant (e.g. blog → external). Keep inner link buttons usable.
    return el('article', { class: cls }, [
      el('a', {
        class: 'card-media-link',
        href: opts.href,
        target: '_blank',
        rel: 'noopener noreferrer',
        'aria-label': opts.title,
      }, [imageSlot(opts.thumbnail, opts.title)]),
      body,
    ]);
  }

  return el('article', { class: cls }, [
    imageSlot(opts.thumbnail, opts.title),
    body,
  ]);
}

/* ── Scroll reveal (IntersectionObserver, reveal-once) ─────────────────── */

export function observeReveals(root = document) {
  const els = root.querySelectorAll('.slide-up, .fade-in');
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduce || !('IntersectionObserver' in window)) {
    els.forEach((e) => e.classList.add('is-visible'));
    return;
  }
  const io = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        io.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
  els.forEach((e) => io.observe(e));
}

/* ── State helpers for fetch (loading / error / empty) ─────────────────── */

export function stateMessage(container, kind, msg) {
  container.innerHTML = '';
  container.appendChild(el('div', { class: `state state--${kind}`, text: msg }));
}

/* ── Filter bar ────────────────────────────────────────────────────────
   Builds a horizontal, keyboard-operable chip bar. `All` clears selection.
   onChange(selectedKeys) fires on every toggle.
   Returns { mount, setCount, getSelected, setSelected }. */
export function createFilterBar(items, onChange) {
  const tags = deriveTags(items);
  let selected = new Set();

  const bar = el('div', { class: 'filter-bar', role: 'group', 'aria-label': 'Filter by tag' });
  const chips = el('div', { class: 'filter-chips' });
  const count = el('span', { class: 'filter-count', 'aria-live': 'polite' });

  function makeChip(label, key) {
    const isAll = key == null;
    const pressed = isAll ? selected.size === 0 : selected.has(key);
    return el('button', {
      type: 'button',
      class: 'tag-link filter-chip' + (pressed ? ' is-active' : ''),
      'aria-pressed': String(pressed),
      'data-key': key || '',
      onclick: () => {
        if (isAll) selected.clear();
        else if (selected.has(key)) selected.delete(key);
        else selected.add(key);
        render();
        onChange([...selected]);
      },
    }, label);
  }

  function render() {
    chips.innerHTML = '';
    chips.appendChild(makeChip('All', null));
    tags.forEach(({ key, display }) => chips.appendChild(makeChip(display, key)));
  }

  bar.appendChild(chips);
  bar.appendChild(count);
  render();

  return {
    mount: bar,
    setCount: (n, total) => { count.textContent = `// ${n}/${total}`; },
    getSelected: () => [...selected],
    setSelected: (keys) => { selected = new Set(keys); render(); },
  };
}
