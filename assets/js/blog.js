import { mountLayout } from './layout.js';
import {
  fetchJSON, card, createFilterBar, filterItems, BLOG_CATEGORIES,
  readTagsFromURL, writeTagsToURL, observeReveals, stateMessage,
} from './data.js';

mountLayout();

const blogCard = (b) => card({ title: b.title, tags: b.tags, href: b.link, thumbnail: b.thumbnail });

(async function init() {
  const filterHost = document.getElementById('filter-host');
  const grid = document.getElementById('blog-grid');

  let items;
  try {
    stateMessage(grid, 'loading', '// Loading…');
    items = await fetchJSON('data/blog.json');
  } catch (e) {
    stateMessage(grid, 'error', `// Failed to load. ${e.message}`);
    return;
  }

  const bar = createFilterBar(items, apply, BLOG_CATEGORIES);
  filterHost.appendChild(bar.mount);
  bar.setSelected(readTagsFromURL());

  function apply(selected) {
    writeTagsToURL(selected);
    const filtered = filterItems(items, selected, bar.categories);
    grid.innerHTML = '';
    if (!filtered.length) { stateMessage(grid, 'empty', '// No posts match these tags.'); }
    filtered.forEach((b) => {
      const c = blogCard(b);
      c.classList.add('slide-up');
      grid.appendChild(c);
    });
    bar.setCount(filtered.length, items.length);
    observeReveals();
  }

  apply(bar.getSelected());
})();
