import { mountLayout } from './layout.js';
import {
  fetchJSON, card, createFilterBar, filterItems,
  readTagsFromURL, writeTagsToURL, observeReveals, stateMessage,
} from './data.js';

mountLayout();

const projCard = (p) => card({ title: p.name, tags: p.tags, body: p.description, links: p.links, thumbnail: p.thumbnail });

(async function init() {
  const filterHost = document.getElementById('filter-host');
  const osGrid = document.getElementById('os-grid');
  const personalGrid = document.getElementById('personal-grid');
  const osSection = document.getElementById('os-section');
  const personalSection = document.getElementById('personal-section');

  let items;
  try {
    stateMessage(osGrid, 'loading', '// Loading…');
    items = await fetchJSON('data/os-n-projects.json');
  } catch (e) {
    stateMessage(osGrid, 'error', `// Failed to load. ${e.message}`);
    return;
  }

  const bar = createFilterBar(items, apply);
  filterHost.appendChild(bar.mount);
  bar.setSelected(readTagsFromURL());

  function apply(selected) {
    writeTagsToURL(selected);
    const filtered = filterItems(items, selected);
    const os = filtered.filter((p) => p.type === 'contribution');
    const personal = filtered.filter((p) => p.type === 'personal');

    renderGrid(osGrid, os, projCard);
    renderGrid(personalGrid, personal, projCard);
    osSection.hidden = os.length === 0;
    personalSection.hidden = personal.length === 0;

    bar.setCount(filtered.length, items.length);
    if (!filtered.length) stateMessage(osGrid, 'empty', '// No projects match these tags.');
    observeReveals();
  }

  apply(bar.getSelected());
})();

function renderGrid(host, list, cardFn) {
  host.innerHTML = '';
  list.forEach((item) => {
    const c = cardFn(item);
    c.classList.add('slide-up');
    host.appendChild(c);
  });
}
