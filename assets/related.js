/* godding/assets/related.js
   Reads /data/links.json and renders the top-N weighted neighbours of the
   current page into any element with id="related-mount". The weight is
   shown as a small bar and the shared concept buckets are exposed via title.
   Self-mounting: include with `<script src="../assets/related.js" defer></script>`. */
(function () {
  const mount = document.getElementById('related-mount');
  if (!mount) return;
  const here = mount.dataset.page;
  if (!here) return;

  // resolve the relative path to data/links.json from any page depth
  const isPagesDir = location.pathname.includes('/pages/');
  const url = (isPagesDir ? '../' : './') + 'data/links.json';

  fetch(url, { cache: 'no-cache' })
    .then(r => r.ok ? r.json() : null)
    .then(j => {
      if (!j || !j.neighbours || !j.neighbours[here]) {
        mount.innerHTML = '<span class="muted" style="font-size:11.5px">no neighbours yet — run swarm/linker.py</span>';
        return;
      }
      const rows = j.neighbours[here].slice(0, 4);
      const block = document.createElement('div');
      block.className = 'related-block';
      for (const r of rows) {
        const w = Math.max(0.04, Math.min(1, r.w || 0));
        const shared = (r.shared || []).join(', ') || 'low overlap';
        const href = (r.page === 'index') ? '../index.html' : (r.page + '.html');
        const row = document.createElement('div');
        row.className = 'related-row';
        row.title = 'shared: ' + shared + '  ·  weight: ' + w.toFixed(2);
        row.innerHTML =
          '<a href="' + href + '">' + (r.page === 'index' ? 'home' : r.page) + '</a>' +
          '<span class="related-bar"><span style="width:' + (w * 100).toFixed(1) + '%"></span></span>';
        block.appendChild(row);
      }
      mount.replaceChildren(block);
    })
    .catch(() => {
      mount.innerHTML = '<span class="muted" style="font-size:11.5px">links.json not yet generated</span>';
    });
})();
