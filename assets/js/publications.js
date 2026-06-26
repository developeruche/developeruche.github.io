import { mountLayout } from './layout.js';
import {
  fetchJSON, card, createFilterBar, filterItems,
  readTagsFromURL, writeTagsToURL, observeReveals, stateMessage,
} from './data.js';

mountLayout();

const pubCard = (p) => card({ title: p.title, tags: p.tags, body: p.abstract, links: p.links, thumbnail: p.thumbnail, featured: true });

(async function init() {
  const filterHost = document.getElementById('filter-host');
  const grid = document.getElementById('pub-grid');

  let items;
  try {
    stateMessage(grid, 'loading', '// Loading…');
    items = await fetchJSON('data/publications.json');
  } catch (e) {
    stateMessage(grid, 'error', `// Failed to load. ${e.message}`);
    return;
  }

  const bar = createFilterBar(items, apply);
  filterHost.appendChild(bar.mount);
  bar.setSelected(readTagsFromURL());

  function apply(selected) {
    writeTagsToURL(selected);
    const filtered = filterItems(items, selected);
    grid.innerHTML = '';
    if (!filtered.length) { stateMessage(grid, 'empty', '// No publications match these tags.'); }
    filtered.forEach((p) => {
      const c = pubCard(p);
      c.classList.add('slide-up');
      grid.appendChild(c);
    });
    bar.setCount(filtered.length, items.length);
    observeReveals();
  }

  apply(bar.getSelected());
})();
