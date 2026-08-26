/* ============================================================================
   layout.js — shared header + footer, injected on every page.
   Set <body data-page="home|projects|blog|publications"> for aria-current.
   ========================================================================== */

const EMAIL = 'developeruche@gmail.com';
const SOCIALS = {
  github: 'https://github.com/developeruche',
  x: 'https://x.com/developeruche',
  linkedin: 'https://www.linkedin.com/in/developeruche',
};

// Root-absolute hrefs so the shared header/footer work at any URL depth
// (e.g. blog posts served from /blog/<slug>/), not just root-level pages.
const NAV = [
  { key: 'home', label: 'Home', href: '/' },
  { key: 'projects', label: 'Projects', href: '/projects' },
  { key: 'blog', label: 'Blogs', href: '/blog' },
  { key: 'publications', label: 'Publications', href: '/publications' },
  { key: 'notes', label: 'Notes', href: '/notes' },
];

function renderHeader(active) {
  const links = NAV.map((n) => {
    const cur = n.key === active ? ' aria-current="page"' : '';
    return `<a href="${n.href}"${cur}>${n.label}</a>`;
  }).join('');

  return `
  <a class="skip-link" href="#main">Skip to content</a>
  <header class="site-header">
    <nav class="nav" aria-label="Primary">
      <a class="nav-brand" href="/" aria-label="Developer Uche — home">
        <img src="/assets/main/logo.png" alt="" width="32" height="32" />
        <span class="logo-word">developeruche</span>
      </a>
      <nav class="nav-links" id="nav-links" aria-label="Sections">${links}</nav>
      <div class="nav-right">
        <a class="btn-primary" href="mailto:${EMAIL}">Contact <span aria-hidden="true">→</span></a>
        <button class="nav-toggle" type="button" aria-label="Toggle menu" aria-expanded="false" aria-controls="nav-links">≡</button>
      </div>
    </nav>
  </header>`;
}

function renderFooter() {
  return `
  <footer class="site-footer">
    <div class="container">
      <div class="footer-top">
        <p class="footer-mission">Blockchain engineer &amp; researcher building high-performance, secure infrastructure across the EVM, ZK, and zkVM stack.</p>
        <div class="footer-cols">
          <div class="footer-col">
            <h4>// Contact</h4>
            <a href="mailto:${EMAIL}">${EMAIL}</a>
          </div>
          <div class="footer-col">
            <h4>// Socials</h4>
            <a href="${SOCIALS.github}" target="_blank" rel="noopener noreferrer">GitHub →</a>
            <a href="${SOCIALS.x}" target="_blank" rel="noopener noreferrer">X →</a>
            <a href="${SOCIALS.linkedin}" target="_blank" rel="noopener noreferrer">LinkedIn →</a>
          </div>
          <div class="footer-col">
            <h4>// Pages</h4>
            ${NAV.map((n) => `<a href="${n.href}">${n.label} →</a>`).join('')}
          </div>
          <div class="footer-col">
            <h4>// Resources</h4>
            <a href="/python-cheatsheet">Python Cheat Sheet →</a>
            <a href="/cv/">CV / Résumé →</a>
          </div>
        </div>
      </div>
      <div class="footer-bottom">
        <span>// Blockchain Engineer &amp; Researcher</span>
        <span>© ${new Date().getFullYear()} Developer Uche</span>
      </div>
    </div>
  </footer>`;
}

export function mountLayout() {
  const active = document.body.dataset.page || '';
  const headerHost = document.getElementById('site-header');
  const footerHost = document.getElementById('site-footer');
  if (headerHost) headerHost.innerHTML = renderHeader(active);
  if (footerHost) footerHost.innerHTML = renderFooter();

  // Mobile menu toggle
  const toggle = document.querySelector('.nav-toggle');
  const links = document.getElementById('nav-links');
  if (toggle && links) {
    toggle.addEventListener('click', () => {
      const open = links.classList.toggle('open');
      toggle.setAttribute('aria-expanded', String(open));
    });
  }
}

export { EMAIL, SOCIALS };
