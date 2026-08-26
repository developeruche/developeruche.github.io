/* ============================================================================
   notes.js — drives both /notes (the three category cards) and each
   /notes/<category>/ listing. Which one it renders is decided by
   <body data-category="...">: absent means the index.
   ========================================================================== */
import { mountLayout } from './layout.js';
import {
  fetchJSON, card, el, NOTE_SECTIONS, createFilterBar, filterItems,
  readTagsFromURL, writeTagsToURL, observeReveals, stateMessage,
} from './data.js';

mountLayout();

const section = document.body.dataset.category || '';
const noteCount = (notes, key) => notes.filter((n) => n.category === key).length;

// A note links out to wherever it lives: an internal page under
// /notes/<category>/<slug>/, or external write-ups and repositories.
const noteCard = (n) => card({
  title: n.title,
  tags: n.tags,
  body: n.excerpt,
  links: n.links && n.links.length ? n.links : (n.link ? [{ label: 'READ NOTE', url: n.link }] : null),
  featured: true,
  noMedia: true,
});

export { noteCard };

/* ── /notes ─────────────────────────────────────────────────────────────── */
function renderIndex(host, notes) {
  NOTE_SECTIONS.forEach((s) => {
    const n = noteCount(notes, s.key);
    const card = el('a', { class: 'note-cat slide-up', href: `/notes/${s.key}/` }, [
      // The artwork carries the category name in its own lettering; the
      // heading exists for screen readers and search, not for sighted repeat.
      el('h2', { class: 'sr-only', text: s.display }),
      el('img', {
        src: s.image,
        alt: `${s.display} — notes`,
        width: '1600',
        height: '900',
        loading: 'lazy',
        decoding: 'async',
      }),
      el('div', { class: 'note-cat-body' }, [
        el('p', { class: 'note-cat-blurb', text: s.blurb }),
        el('span', { class: 'note-cat-meta' }, [
          n === 1 ? '1 note' : `${n} notes`,
          el('span', { 'aria-hidden': 'true', text: '→' }),
        ]),
      ]),
    ]);
    host.appendChild(card);
  });
  observeReveals();
}

/* ── /notes/<category>/ ─────────────────────────────────────────────────── */
function renderCategory(filterHost, grid, notes) {
  const items = notes.filter((n) => n.category === section);

  if (!items.length) {
    stateMessage(grid, 'empty', '// No notes here yet. Check back soon.');
    return;
  }

  const bar = createFilterBar(items, apply);
  filterHost.appendChild(bar.mount);
  bar.setSelected(readTagsFromURL());

  function apply(selected) {
    writeTagsToURL(selected);
    const filtered = filterItems(items, selected, bar.categories);
    grid.innerHTML = '';
    if (!filtered.length) stateMessage(grid, 'empty', '// No notes match these tags.');
    filtered.forEach((n) => {
      // card() rather than listItem(): a note can cite several resources
      // (write-up, source, spec), and listItem carries a single href.
      const row = noteCard(n);
      row.classList.add('slide-up');
      grid.appendChild(row);
    });
    bar.setCount(filtered.length, items.length);
    observeReveals();
  }

  apply(bar.getSelected());
}

(async function init() {
  const grid = document.getElementById('notes-grid');
  const filterHost = document.getElementById('filter-host');

  let notes;
  try {
    if (grid) stateMessage(grid, 'loading', '// Loading…');
    notes = await fetchJSON('/data/notes.json');
  } catch (e) {
    if (grid) stateMessage(grid, 'error', `// Failed to load. ${e.message}`);
    return;
  }

  if (section) {
    renderCategory(filterHost, grid, notes);
  } else {
    grid.innerHTML = '';
    renderIndex(grid, notes);
  }
})();
