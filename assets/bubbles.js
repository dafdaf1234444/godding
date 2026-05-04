/* godding — shared bubble-chart module
   Used by /pages/criminals.html (full chart) and /pages/crime.html (inline below the list).
   Each figure is a deceased historical figure widely documented as having caused mass civilian death.
   Numbers are mid-points of mainstream scholarly ranges. The swarm is forbidden from rewriting these.
*/

const FIGURES = [
  { id:'mao',     name:'Mao Zedong',          years:'1893–1976', n:35e6,  range:'~30–45M (Great Leap Forward famine + Cultural Revolution)', summary:'Chairman of the People\'s Republic of China. Excess deaths during the Great Leap Forward famine (1959–61) plus political violence.', src:'mainstream demographic + Frank Dikötter (Mao\'s Great Famine, 2010)', tier:0, links:['stalin','polpot','kim'] },
  { id:'genghis', name:'Genghis Khan',        years:'c. 1162–1227', n:35e6, range:'~30–40M (estimates of Mongol conquest deaths over the 13th c.)', summary:'Mongol conquest of large parts of Asia and Eastern Europe. Death-toll estimates aggregate decades of warfare and famine.', src:'standard histories of the Mongol Empire', tier:3, links:['tamerlane'] },
  { id:'taiping', name:'Hong Xiuquan',        years:'1814–1864', n:20e6,  range:'~20M+ (Taiping Rebellion, 1850–64)', summary:'Self-proclaimed brother of Jesus. Led the Taiping Rebellion in Qing China — one of the deadliest civil wars in history.', src:'Jonathan Spence; standard Qing histories', tier:1, links:[] },
  { id:'hitler',  name:'Adolf Hitler',        years:'1889–1945', n:17e6,  range:'~17M civilian deaths (Holocaust ~6M Jews + ~11M others; WWII total far higher)', summary:'Nazi dictator of Germany. Holocaust + Generalplan Ost + war-crimes against civilians.', src:'Holocaust Encyclopaedia, Yad Vashem, USHMM', tier:0, links:['stalin','tojo'] },
  { id:'tamerlane', name:'Timur (Tamerlane)', years:'1336–1405', n:17e6,  range:'~15–17M (Central Asian conquests)', summary:'Founder of the Timurid Empire. Documented massacres in cities across Persia, India, the Levant.', src:'standard medieval histories', tier:3, links:['genghis'] },
  { id:'leopold', name:'Leopold II of Belgium', years:'1835–1909', n:10e6, range:'~5–10M (Congo Free State, 1885–1908)', summary:'Personal owner of the Congo Free State. Forced-labour rubber regime, mutilation, famine.', src:'Adam Hochschild, King Leopold\'s Ghost (1998)', tier:1, links:[] },
  { id:'stalin',  name:'Joseph Stalin',       years:'1878–1953', n:7e6,   range:'~6–9M (Great Purge, gulag, Holodomor)', summary:'Soviet leader. Forced collectivisation famines, purges, gulag mortality.', src:'Robert Conquest; Wheatcroft & Davies', tier:0, links:['mao','hitler','kim'] },
  { id:'tojo',    name:'Hideki Tōjō',         years:'1884–1948', n:5e6,   range:'~3–10M (Japanese wartime atrocities, 1937–45)', summary:'Imperial Japanese PM. Nanjing, Unit 731, occupied-territory massacres.', src:'standard WWII Pacific histories', tier:0, links:['hitler'] },
  { id:'polpot',  name:'Pol Pot',             years:'1925–1998', n:1.8e6, range:'~1.7–2M (Cambodian genocide, 1975–79)', summary:'Khmer Rouge leader. Killing fields, mass starvation, ~25% of Cambodian population.', src:'Yale Cambodian Genocide Program', tier:0, links:['mao'] },
  { id:'kim',     name:'Kim Il-sung',         years:'1912–1994', n:1.6e6, range:'~1.6M+ (Korean War civilians, post-war repression)', summary:'Founder of the DPRK. Korean War civilian deaths plus decades of repression and famine.', src:'standard DPRK histories', tier:0, links:['mao','stalin'] },
  { id:'suharto', name:'Suharto',             years:'1921–2008', n:9e5,   range:'~500k–1M+ (Indonesian massacres 1965–66; East Timor)', summary:'Indonesian dictator. Anti-communist purge of 1965–66, occupation of East Timor.', src:'Geoffrey Robinson; CIA/State Dept declassifications', tier:0, links:[] },
  { id:'idi',     name:'Idi Amin',            years:'c. 1925–2003', n:3e5, range:'~100k–500k (Ugandan repression, 1971–79)', summary:'Ugandan dictator. Mass political killings during his rule.', src:'standard African political histories', tier:0, links:[] },
];

const TIER_COLORS = ['#d96936', '#c89a3e', '#6b4a8b', '#4a7ba8'];

function renderBubbles(opts) {
  /* opts: { svgEl, detailEl, viewBox:[w,h], scale, packIters, small, gap } */
  const NS = 'http://www.w3.org/2000/svg';
  const W = opts.viewBox ? opts.viewBox[0] : 1100;
  const H = opts.viewBox ? opts.viewBox[1] : 560;
  const SCALE = opts.scale || 0.0010;
  const ITERS = opts.packIters || 900;
  const GAP = opts.gap !== undefined ? opts.gap : 9;   // space between bubbles
  const cx = W / 2, cy = H / 2;
  const small = !!opts.small;

  // Initial spread on a grid-ish layout so packing has space to work
  const N = FIGURES.length;
  const cols = Math.ceil(Math.sqrt(N * (W / H)));
  const data = FIGURES.map((f, i) => {
    const rr = Math.max(small ? 14 : 20, Math.sqrt(f.n * SCALE / Math.PI) * (small ? 6.5 : 8.5));
    const col = i % cols, row = Math.floor(i / cols);
    return {
      ...f,
      r: rr,
      x: (col + 0.5) * (W / cols) + (Math.random() - 0.5) * 16,
      y: (row + 0.6) * (H / Math.ceil(N / cols)) + (Math.random() - 0.5) * 16,
      vx: 0, vy: 0,
    };
  });

  // Robust packing: multiple overlap-resolution passes per iteration so
  // the system actually converges with no remaining intersections.
  for (let it = 0; it < ITERS; it++) {
    // gentle attraction toward center (weaker for bigger bubbles so they stay put)
    const attract = 0.0006;
    for (const a of data) {
      a.vx += (cx - a.x) * attract;
      a.vy += (cy - a.y) * attract;
    }
    // Resolve pairwise overlaps — repeat 4× per iteration for fast convergence
    for (let pass = 0; pass < 4; pass++) {
      for (let i = 0; i < data.length; i++) {
        for (let j = i + 1; j < data.length; j++) {
          const a = data[i], b = data[j];
          let dx = b.x - a.x, dy = b.y - a.y;
          let d = Math.hypot(dx, dy);
          if (d < 0.01){ dx = (Math.random()-0.5); dy = (Math.random()-0.5); d = Math.hypot(dx,dy)+0.01; }
          const overlap = (a.r + b.r + GAP) - d;
          if (overlap > 0) {
            const ux = dx / d, uy = dy / d;
            // larger bubble moves less (mass-weighted)
            const ma = a.r * a.r, mb = b.r * b.r, mt = ma + mb;
            const sa = mb / mt, sb = ma / mt;
            a.x -= ux * overlap * sa; a.y -= uy * overlap * sa;
            b.x += ux * overlap * sb; b.y += uy * overlap * sb;
          }
        }
      }
    }
    // integrate + damping
    for (const a of data) {
      a.x += a.vx; a.y += a.vy;
      a.vx *= 0.78; a.vy *= 0.78;
      a.x = Math.max(a.r + 6, Math.min(W - a.r - 6, a.x));
      a.y = Math.max(a.r + 6, Math.min(H - a.r - 6, a.y));
    }
  }
  // Final hard pass: any residual overlap, hard-resolve
  for (let pass = 0; pass < 12; pass++) {
    let moved = false;
    for (let i = 0; i < data.length; i++) {
      for (let j = i + 1; j < data.length; j++) {
        const a = data[i], b = data[j];
        let dx = b.x - a.x, dy = b.y - a.y;
        let d = Math.hypot(dx, dy);
        if (d < 0.01){ dx = 1; dy = 0; d = 1; }
        const overlap = (a.r + b.r + GAP) - d;
        if (overlap > 0.5) {
          const ux = dx / d, uy = dy / d;
          a.x -= ux * overlap * 0.5; a.y -= uy * overlap * 0.5;
          b.x += ux * overlap * 0.5; b.y += uy * overlap * 0.5;
          moved = true;
        }
      }
    }
    if (!moved) break;
  }
  for (const a of data) {
    a.x = Math.max(a.r + 6, Math.min(W - a.r - 6, a.x));
    a.y = Math.max(a.r + 6, Math.min(H - a.r - 6, a.y));
  }

  const svg = opts.svgEl;
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  while (svg.firstChild) svg.removeChild(svg.firstChild);

  // soft warm wash (background, not zoomed)
  const def = document.createElementNS(NS, 'defs');
  def.innerHTML = '<radialGradient id="bgw" cx="50%" cy="50%" r="60%"><stop offset="0%" stop-color="#fff8ea"/><stop offset="100%" stop-color="#f0e8d4"/></radialGradient>';
  svg.appendChild(def);
  const bg = document.createElementNS(NS, 'rect');
  bg.setAttribute('x', '0'); bg.setAttribute('y', '0');
  bg.setAttribute('width', String(W)); bg.setAttribute('height', String(H));
  bg.setAttribute('fill', 'url(#bgw)');
  svg.appendChild(bg);

  // zoom/pan layer — bubbles draw inside this group
  const zoomLayer = document.createElementNS(NS, 'g');
  zoomLayer.setAttribute('class', 'zoom-layer');
  svg.appendChild(zoomLayer);

  // viewport transform state
  const view = { tx: 0, ty: 0, k: 1 };
  function applyView(){
    zoomLayer.setAttribute('transform', `translate(${view.tx} ${view.ty}) scale(${view.k})`);
  }
  applyView();

  // ── zoom controls ────────────────────────────────────────────────────
  // explicit buttons are clearer than mystery wheel-zoom; wheel only works
  // when the user holds Ctrl/Cmd (so normal page-scroll keeps working).
  function zoomBy(factor, anchorPx, anchorPy){
    const nk = Math.max(0.6, Math.min(10, view.k * factor));
    const px = anchorPx ?? W / 2;
    const py = anchorPy ?? H / 2;
    const wx = (px - view.tx) / view.k;
    const wy = (py - view.ty) / view.k;
    view.k = nk;
    view.tx = px - wx * nk;
    view.ty = py - wy * nk;
    applyView();
  }
  function resetView(){ view.tx = 0; view.ty = 0; view.k = 1; applyView(); }

  // ── on-canvas zoom buttons (foreignObject so they work with HTML buttons) ──
  function mkBtn(x, label, title, onClick){
    const fo = document.createElementNS(NS, 'foreignObject');
    fo.setAttribute('x', x); fo.setAttribute('y', 12);
    fo.setAttribute('width', 36); fo.setAttribute('height', 32);
    const html = document.createElementNS('http://www.w3.org/1999/xhtml', 'button');
    html.textContent = label; html.title = title;
    html.style.cssText = 'width:100%;height:100%;border-radius:8px;border:1px solid #a39179;background:#fff8ea;color:#1f1813;font-family:ui-sans-serif,system-ui,sans-serif;font-size:16px;cursor:pointer;display:flex;align-items:center;justify-content:center;line-height:1;padding:0';
    html.addEventListener('click', e => { e.preventDefault(); e.stopPropagation(); onClick(); });
    html.addEventListener('mousedown', e => e.stopPropagation());
    fo.appendChild(html);
    svg.appendChild(fo);
  }
  mkBtn(W - 130, '+',  'zoom in',     () => zoomBy(1.4));
  mkBtn(W -  92, '−',  'zoom out',    () => zoomBy(1/1.4));
  mkBtn(W -  54, '⊙',  'reset view',  () => resetView());

  // hint
  const hint = document.createElementNS(NS, 'text');
  hint.setAttribute('x', 14); hint.setAttribute('y', 28);
  hint.setAttribute('font-family', 'JetBrains Mono, monospace');
  hint.setAttribute('font-size', '11');
  hint.setAttribute('fill', '#a39179');
  hint.textContent = 'drag = pan · +/− = zoom · ⊙ = reset · ctrl+wheel = zoom';
  svg.appendChild(hint);

  // Ctrl/Cmd + wheel zoom (so plain scroll still scrolls the page)
  svg.addEventListener('wheel', (e) => {
    if (!(e.ctrlKey || e.metaKey)) return;
    e.preventDefault();
    const rect = svg.getBoundingClientRect();
    const px = (e.clientX - rect.left) / rect.width * W;
    const py = (e.clientY - rect.top) / rect.height * H;
    const factor = e.deltaY < 0 ? 1.15 : 1 / 1.15;
    zoomBy(factor, px, py);
  }, { passive: false });

  // Robust drag-pan: starts on any click, except on bubble groups (which
  // need to receive their own click for the detail card). We track if the
  // mouse moved enough to count as a drag, and if so cancel the bubble click.
  let panning = null, moved = 0;
  svg.addEventListener('mousedown', (e) => {
    if (e.button !== 0) return;
    panning = { x: e.clientX, y: e.clientY, tx: view.tx, ty: view.ty };
    moved = 0;
    svg.style.cursor = 'grabbing';
  });
  svg.addEventListener('mousemove', (e) => {
    if (!panning) return;
    const rect = svg.getBoundingClientRect();
    const sx = W / rect.width, sy = H / rect.height;
    const dx = (e.clientX - panning.x), dy = (e.clientY - panning.y);
    moved += Math.abs(dx) + Math.abs(dy);
    view.tx = panning.tx + dx * sx;
    view.ty = panning.ty + dy * sy;
    applyView();
  });
  function endPan(){ panning = null; svg.style.cursor = ''; }
  svg.addEventListener('mouseup', endPan);
  svg.addEventListener('mouseleave', endPan);
  svg.addEventListener('dblclick', resetView);
  // Suppress click events that follow a drag so dragging doesn't open a card
  svg.addEventListener('click', (e) => { if (moved > 4){ e.stopPropagation(); e.preventDefault(); moved = 0; } }, true);

  const detail = opts.detailEl;
  function showDetail(f) {
    if (!detail) return;
    detail.hidden = false;
    detail.querySelector('[data-name]').textContent = f.name;
    detail.querySelector('[data-meta]').textContent = f.years + ' · est. mid-range ' + (f.n / 1e6).toFixed(1) + 'M deaths';
    detail.querySelector('[data-body]').innerHTML = '<strong>range:</strong> ' + f.range + '<br><br>' + f.summary;
    detail.querySelector('[data-source]').textContent = 'sources (representative): ' + f.src;
  }

  // Draw dependency/relation lines FIRST so bubbles overlay them
  const linkLayer = document.createElementNS(NS, 'g');
  linkLayer.setAttribute('class', 'links');
  zoomLayer.appendChild(linkLayer);
  const byId = Object.fromEntries(data.map(d => [d.id, d]));
  const drawn = new Set();
  for (const f of data) {
    if (!Array.isArray(f.links)) continue;
    for (const tid of f.links) {
      const t = byId[tid]; if (!t) continue;
      const k = f.id < tid ? f.id+'__'+tid : tid+'__'+f.id;
      if (drawn.has(k)) continue;
      drawn.add(k);
      // gentle curved line via cubic bezier
      const mx = (f.x + t.x) / 2, my = (f.y + t.y) / 2;
      // perpendicular offset for the curve
      const dx = t.x - f.x, dy = t.y - f.y, len = Math.hypot(dx,dy) || 1;
      const ox = -dy / len * Math.min(28, len * 0.18);
      const oy =  dx / len * Math.min(28, len * 0.18);
      const path = document.createElementNS(NS, 'path');
      path.setAttribute('d', `M ${f.x} ${f.y} Q ${mx+ox} ${my+oy} ${t.x} ${t.y}`);
      path.setAttribute('fill', 'none');
      path.setAttribute('stroke', '#a39179');
      path.setAttribute('stroke-width', '1.1');
      path.setAttribute('stroke-dasharray', '2 4');
      path.setAttribute('opacity', '0.45');
      linkLayer.appendChild(path);
    }
  }

  for (const f of data) {
    const color = TIER_COLORS[f.tier % TIER_COLORS.length];
    const g = document.createElementNS(NS, 'g');
    g.setAttribute('style', 'cursor:pointer');

    const halo = document.createElementNS(NS, 'circle');
    halo.setAttribute('cx', f.x); halo.setAttribute('cy', f.y);
    halo.setAttribute('r', f.r + 8);
    halo.setAttribute('fill', color); halo.setAttribute('opacity', '0.10');

    const c = document.createElementNS(NS, 'circle');
    c.setAttribute('cx', f.x); c.setAttribute('cy', f.y);
    c.setAttribute('r', f.r);
    c.setAttribute('fill', color); c.setAttribute('fill-opacity', '0.25');
    c.setAttribute('stroke', color); c.setAttribute('stroke-width', '1.4');

    // White-cream plate behind the label so text reads cleanly even when
    // the bubble is small or overlapping a dependency line.
    const fontSize = Math.max(11, Math.min(small ? 14 : 17, f.r * 0.32));
    const labelW = Math.min(f.r * 1.85, Math.max(54, f.name.length * fontSize * 0.46));
    const labelH = fontSize + 6;
    const plate = document.createElementNS(NS, 'rect');
    plate.setAttribute('x', f.x - labelW/2);
    plate.setAttribute('y', f.y - labelH/2 - 2);
    plate.setAttribute('width', labelW);
    plate.setAttribute('height', labelH);
    plate.setAttribute('rx', '4');
    plate.setAttribute('fill', '#fff8ea');
    plate.setAttribute('opacity', '0.92');
    plate.setAttribute('stroke', color);
    plate.setAttribute('stroke-opacity', '0.30');
    plate.setAttribute('stroke-width', '0.8');

    const t = document.createElementNS(NS, 'text');
    t.setAttribute('x', f.x); t.setAttribute('y', f.y + 1);
    t.setAttribute('text-anchor', 'middle'); t.setAttribute('dominant-baseline', 'middle');
    t.setAttribute('fill', '#1f1813');
    t.setAttribute('font-family', 'Fraunces, Georgia, serif');
    t.setAttribute('font-style', 'italic');
    t.setAttribute('font-size', String(fontSize));
    t.setAttribute('font-weight', '500');
    t.textContent = f.name;

    const sub = document.createElementNS(NS, 'text');
    sub.setAttribute('x', f.x); sub.setAttribute('y', f.y + labelH/2 + 9);
    sub.setAttribute('text-anchor', 'middle');
    sub.setAttribute('fill', color);
    sub.setAttribute('font-family', 'JetBrains Mono, monospace');
    sub.setAttribute('font-size', String(small ? 10 : 11));
    sub.setAttribute('font-weight', '500');
    sub.textContent = (f.n / 1e6).toFixed(1) + 'M';

    const title = document.createElementNS(NS, 'title');
    title.textContent = f.name + ' — ' + f.range;

    g.appendChild(title); g.appendChild(halo); g.appendChild(c);
    g.appendChild(plate); g.appendChild(t); g.appendChild(sub);
    g.addEventListener('click', () => showDetail(f));
    zoomLayer.appendChild(g);
  }
}

/* ESM-friendly export for any future module use */
if (typeof window !== 'undefined') { window.GoddingBubbles = { FIGURES, renderBubbles }; }
