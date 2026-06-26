import { mountLayout } from './layout.js';
import { fetchJSON, highlights, card, el, observeReveals, stateMessage } from './data.js';

mountLayout();

// Render a highlight section grid into a host element.
async function renderHighlights(host, path, opts = {}) {
  const { filter, hrefField, cardFn } = opts;
  try {
    stateMessage(host, 'loading', '// Loading…');
    let items = await fetchJSON(path);
    if (filter) items = items.filter(filter);
    const picks = highlights(items, 4);
    host.innerHTML = '';
    if (!picks.length) { stateMessage(host, 'empty', '// Nothing here yet.'); return; }
    picks.forEach((item) => host.appendChild(cardFn(item)));
  } catch (e) {
    stateMessage(host, 'error', `// Failed to load. ${e.message}`);
  }
}

// Card builders per dataset
const pubCard = (p) => card({ title: p.title, tags: p.tags, body: p.abstract, links: p.links, thumbnail: p.thumbnail, featured: true });
const blogCard = (b) => card({ title: b.title, tags: b.tags, href: b.link, thumbnail: b.thumbnail });
const projCard = (p) => card({ title: p.name, tags: p.tags, body: p.description, links: p.links, thumbnail: p.thumbnail });

// Companies strip
async function renderCompanies(host) {
  try {
    const companies = await fetchJSON('data/companies.json');
    host.innerHTML = '';
    companies.forEach((c) => {
      const slot = el('div', { class: 'company-logo' });
      if (c.logo) slot.appendChild(el('img', { src: c.logo, alt: c.name || 'Company logo', loading: 'lazy' }));
      else slot.appendChild(el('div', { class: 'card-media--skeleton skeleton-shimmer' }));
      host.appendChild(slot);
    });
  } catch { /* non-critical strip */ }
}

renderHighlights(document.getElementById('pub-grid'), 'data/publications.json', { cardFn: pubCard });
renderHighlights(document.getElementById('blog-grid'), 'data/blog.json', { cardFn: blogCard });
renderHighlights(document.getElementById('os-grid'), 'data/os-n-projects.json', { filter: (p) => p.type === 'contribution', cardFn: projCard });
renderHighlights(document.getElementById('proj-grid'), 'data/os-n-projects.json', { filter: (p) => p.type === 'personal', cardFn: projCard });
renderCompanies(document.getElementById('companies-row'));

observeReveals();
