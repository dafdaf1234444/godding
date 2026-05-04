/* godding — shared bubble-chart module
   Used by /pages/criminals.html (full chart) and /pages/crime.html (inline below the list).
   Each figure is a deceased historical figure widely documented as having caused mass civilian death.
   Numbers are mid-points of mainstream scholarly ranges. The swarm is forbidden from rewriting these.
*/

const FIGURES = [
  { id:'mao',     name:'Mao Zedong',          years:'1893–1976', n:35e6,  lo:30e6, hi:45e6, century:'20c', region:'Asia',   range:'~30–45M (Great Leap Forward famine + Cultural Revolution)', summary:'Chairman of the People\'s Republic of China. Excess deaths during the Great Leap Forward famine (1959–61) plus political violence.', src:'mainstream demographic + Frank Dikötter (Mao\'s Great Famine, 2010)', tier:0, links:['stalin','polpot','kim'] },
  { id:'genghis', name:'Genghis Khan',        years:'c. 1162–1227', n:35e6, lo:30e6, hi:40e6, century:'13c', region:'Asia',  range:'~30–40M (estimates of Mongol conquest deaths over the 13th c.)', summary:'Mongol conquest of large parts of Asia and Eastern Europe. Death-toll estimates aggregate decades of warfare and famine.', src:'standard histories of the Mongol Empire', tier:3, links:['tamerlane'] },
  { id:'taiping', name:'Hong Xiuquan',        years:'1814–1864', n:20e6, lo:20e6, hi:30e6, century:'19c', region:'Asia',  range:'~20–30M (Taiping Rebellion, 1850–64)', summary:'Self-proclaimed brother of Jesus. Led the Taiping Rebellion in Qing China — one of the deadliest civil wars in history.', src:'Jonathan Spence; standard Qing histories', tier:1, links:[] },
  { id:'hitler',  name:'Adolf Hitler',        years:'1889–1945', n:17e6, lo:11e6, hi:20e6, century:'20c', region:'Europe',range:'~11–20M civilian deaths (Holocaust ~6M Jews + ~5–11M others; WWII total far higher)', summary:'Nazi dictator of Germany. Holocaust + Generalplan Ost + war-crimes against civilians.', src:'Holocaust Encyclopaedia, Yad Vashem, USHMM', tier:0, links:['stalin','tojo'] },
  { id:'tamerlane', name:'Timur (Tamerlane)', years:'1336–1405', n:17e6, lo:15e6, hi:17e6, century:'14c', region:'Asia',  range:'~15–17M (Central Asian conquests)', summary:'Founder of the Timurid Empire. Documented massacres in cities across Persia, India, the Levant.', src:'standard medieval histories', tier:3, links:['genghis'] },
  { id:'leopold', name:'Leopold II of Belgium', years:'1835–1909', n:10e6, lo:5e6, hi:15e6, century:'19c', region:'Africa',range:'~5–15M (Congo Free State, 1885–1908)', summary:'Personal owner of the Congo Free State. Forced-labour rubber regime, mutilation, famine.', src:'Adam Hochschild, King Leopold\'s Ghost (1998)', tier:1, links:[] },
  { id:'stalin',  name:'Joseph Stalin',       years:'1878–1953', n:7e6, lo:6e6, hi:9e6, century:'20c', region:'Europe',range:'~6–9M (Great Purge, gulag, Holodomor)', summary:'Soviet leader. Forced collectivisation famines, purges, gulag mortality.', src:'Robert Conquest; Wheatcroft & Davies', tier:0, links:['mao','hitler','kim'] },
  { id:'tojo',    name:'Hideki Tōjō',         years:'1884–1948', n:5e6, lo:3e6, hi:10e6, century:'20c', region:'Asia',  range:'~3–10M (Japanese wartime atrocities, 1937–45)', summary:'Imperial Japanese PM. Nanjing, Unit 731, occupied-territory massacres.', src:'standard WWII Pacific histories', tier:0, links:['hitler'] },
  { id:'polpot',  name:'Pol Pot',             years:'1925–1998', n:1.8e6, lo:1.7e6, hi:2e6, century:'20c', region:'Asia',range:'~1.7–2M (Cambodian genocide, 1975–79)', summary:'Khmer Rouge leader. Killing fields, mass starvation, ~25% of Cambodian population.', src:'Yale Cambodian Genocide Program', tier:0, links:['mao'] },
  { id:'kim',     name:'Kim Il-sung',         years:'1912–1994', n:1.6e6, lo:1.5e6, hi:3e6, century:'20c', region:'Asia',range:'~1.5–3M (Korean War civilians, post-war repression)', summary:'Founder of the DPRK. Korean War civilian deaths plus decades of repression and famine.', src:'standard DPRK histories', tier:0, links:['mao','stalin'] },
  { id:'suharto', name:'Suharto',             years:'1921–2008', n:9e5, lo:5e5, hi:1.2e6, century:'20c', region:'Asia',range:'~500k–1.2M (Indonesian massacres 1965–66; East Timor)', summary:'Indonesian dictator. Anti-communist purge of 1965–66, occupation of East Timor.', src:'Geoffrey Robinson; CIA/State Dept declassifications', tier:0, links:[] },
  { id:'idi',     name:'Idi Amin',            years:'c. 1925–2003', n:3e5, lo:1e5, hi:5e5, century:'20c', region:'Africa',range:'~100k–500k (Ugandan repression, 1971–79)', summary:'Ugandan dictator. Mass political killings during his rule.', src:'standard African political histories', tier:0, links:[] },
];

/* CURRENT (2020s) figures — issue-level only, no living people named.
   Each entry tracks a publicly documented humanitarian-toll situation; the actor
   is described by role (regime, militia, junta) rather than by personal name to
   avoid defamation. Numbers are mid-points of mainstream estimates with sources. */
const CURRENT_FIGURES = [
  { id:'cur-ukraine', name:'invasion of Ukraine',         years:'2022– ',  n:5e5, lo:2.5e5, hi:8e5, century:'21c', region:'Europe',range:'~250k–800k civilian + military deaths cumulative (open-source estimates)', summary:'Mass-scale interstate war in Europe; documented strikes on civilian infrastructure, deportations, and mass-grave findings in occupied areas.', src:'UN OHCHR; Mediazona/BBC tally; ICRC reports', tier:0, links:[] },
  { id:'cur-yemen',   name:'Yemen war + blockade',        years:'2014– ',  n:3.7e5, lo:3.5e5, hi:5e5, century:'21c', region:'Asia',range:'~370k+ direct + indirect (UNDP, 2021 baseline; growing)', summary:'Coalition + Houthi conflict with naval blockade and famine-level food insecurity.', src:'UNDP "Assessing the Impact of War in Yemen" (2021); ACLED', tier:1, links:[] },
  { id:'cur-tigray',  name:'Tigray war',                  years:'2020–2022', n:6e5, lo:3e5, hi:8e5, century:'21c', region:'Africa',range:'~300k–800k excess deaths', summary:'Ethiopian federal + Eritrean forces vs. TPLF; widespread civilian massacres and famine documented.', src:'Ghent University estimate; Amnesty + HRW reports', tier:0, links:[] },
  { id:'cur-syria',   name:'Syrian war (post-2020 phase)',years:'2011– ',  n:5.8e5, lo:5e5, hi:6.5e5, century:'21c', region:'Asia',range:'~580k+ cumulative; tens of thousands of "disappearances"', summary:'Long civil war with documented sieges, chemical-weapon use, and detention-system abuses.', src:'SNHR; UN COI; OPCW', tier:0, links:[] },
  { id:'cur-myanmar', name:'Myanmar coup + war',          years:'2021– ',  n:5e4, lo:4e4, hi:8e4, century:'21c', region:'Asia',range:'~50k+ killed; over 3M displaced', summary:'Military junta vs. resistance forces; documented airstrikes on civilians and village burnings.', src:'AAPP Burma; UN OCHA; ACLED', tier:1, links:[] },
  { id:'cur-sudan',   name:'Sudan war (RSF vs SAF)',      years:'2023– ',  n:1.5e5, lo:1.5e5, hi:1.5e5, century:'21c', region:'Africa',range:'~150k killed (UN/Yale est.); largest displacement crisis on record', summary:'Two militaries fighting over the capital with widespread ethnic-targeted killings in Darfur.', src:'Yale Humanitarian Lab; UN OCHA; HRW', tier:0, links:[] },
  { id:'cur-gaza',    name:'Israel–Gaza war',                  years:'2023– ', n:5e4, lo:4e4, hi:1.86e5, century:'21c', region:'Asia',range:'~40k–186k Gazan deaths (low: Gaza MoH direct; high: Lancet excess-mortality est.); ~1,200 Israeli on Oct 7', summary:'High civilian-casualty urban war following Hamas-led attack; documented strikes on hospitals, journalists, aid workers.', src:'Lancet correspondence 2024; UN OCHA; HRW; Gaza MoH; IDF briefings', tier:0, links:[] },
  { id:'cur-dprk',    name:'DPRK political-prison system',years:'1990s– ',  n:1.5e5, lo:1e5, hi:2e5, century:'21c', region:'Asia',range:'~100k–200k currently in camps; tens of thousands deaths/decade', summary:'Long-running gulag-style camp system documented by escapee testimony and satellite imagery.', src:'UN COI on DPRK (2014); Committee for Human Rights in North Korea', tier:1, links:[] },
  { id:'cur-uyghur',  name:'Xinjiang internment',         years:'2017– ',  n:1e6, lo:1e6, hi:1.8e6, century:'21c', region:'Asia',range:'~1M+ detained; deaths uncertain, mass forced-labour and family separation', summary:'Documented internment of Uyghur and other Turkic Muslims; coercive birth-control measures.', src:'UN OHCHR (2022) "Xinjiang assessment"; Australian Strategic Policy Institute', tier:1, links:[] },
  { id:'cur-mexico',  name:'Mexico cartel violence',      years:'2006– ',  n:4e5, lo:4e5, hi:5e5, century:'21c', region:'Americas',range:'~400k+ homicides since 2006; ~110k missing', summary:'Cartel-driven mass-homicide pattern with documented massacres and disappearances.', src:'Mexican government statistics; CNDH; HRW', tier:2, links:[] },
];

const TIER_COLORS = ['#d96936', '#c89a3e', '#6b4a8b', '#4a7ba8'];
/* current bubbles use a different palette so the user can tell at a glance */
const TIER_COLORS_CURRENT = ['#5d8c4a', '#4a7ba8', '#a39179', '#c4576b'];

function renderBubbles(opts) {
  /* opts: { svgEl, detailEl, viewBox:[w,h], scale, packIters, small, gap, mode } */
  const NS = 'http://www.w3.org/2000/svg';
  const W = opts.viewBox ? opts.viewBox[0] : 1100;
  const H = opts.viewBox ? opts.viewBox[1] : 560;
  const SCALE = opts.scale || 0.0008;       // smaller area per death so bubbles fit
  const ITERS = opts.packIters || 2200;     // more packing iterations
  const GAP = opts.gap !== undefined ? opts.gap : 14; // bigger gap between bubbles
  const cx = W / 2, cy = H / 2;
  const small = !!opts.small;

  // pick which dataset to draw based on mode + century/region filters
  const mode = opts.mode || 'historical';
  const centuryF = opts.century || 'all';
  const regionF  = opts.region  || 'all';
  const sourceArrays = (mode === 'current')
    ? [{ arr: CURRENT_FIGURES, kind: 'current' }]
    : (mode === 'both')
      ? [{ arr: FIGURES, kind: 'historical' }, { arr: CURRENT_FIGURES, kind: 'current' }]
      : [{ arr: FIGURES, kind: 'historical' }];
  let FLAT = sourceArrays.flatMap(s => s.arr.map(f => ({ ...f, _kind: s.kind })));
  if (centuryF !== 'all') FLAT = FLAT.filter(f => f.century === centuryF);
  if (regionF  !== 'all') FLAT = FLAT.filter(f => f.region  === regionF);

  // Initial spread on a grid-ish layout so packing has space to work
  const N = FLAT.length;
  if (N === 0){
    // empty set — show a neutral message
    const svg = opts.svgEl;
    svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    const t = document.createElementNS(NS, 'text');
    t.setAttribute('x', W/2); t.setAttribute('y', H/2);
    t.setAttribute('text-anchor', 'middle');
    t.setAttribute('font-family', 'Fraunces, Georgia, serif');
    t.setAttribute('font-style', 'italic');
    t.setAttribute('font-size', '20'); t.setAttribute('fill', '#6f5f53');
    t.textContent = 'no figures match these filters';
    svg.appendChild(t);
    return;
  }
  const cols = Math.ceil(Math.sqrt(N * (W / H)));
  const data = FLAT.map((f, i) => {
    // tighter cap on max bubble radius so the biggest bubbles don't smother neighbours
    const rawR = Math.sqrt(f.n * SCALE / Math.PI) * (small ? 5.6 : 7.2);
    const maxR = small ? Math.min(W, H) * 0.18 : Math.min(W, H) * 0.16;
    const rr = Math.min(maxR, Math.max(small ? 14 : 22, rawR));
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
    const palette = (f._kind === 'current') ? TIER_COLORS_CURRENT : TIER_COLORS;
    const color = palette[f.tier % palette.length];
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
/* ──────────────────────────────────────────────────────────────────────
   renderBars — clearer "best-resources" view of the same data.
   Horizontal bar chart, log-scaled x-axis, sorted by midpoint death toll,
   with low/high range "whiskers". Filterable by century and region.
   opts: { svgEl, detailEl, viewBox:[w,h], mode, century, region }
   ─────────────────────────────────────────────────────────────────────── */
function renderBars(opts) {
  const NS = 'http://www.w3.org/2000/svg';
  const W = (opts.viewBox && opts.viewBox[0]) || 1100;
  const mode = opts.mode || 'historical';
  const century = opts.century || 'all';
  const region  = opts.region  || 'all';

  const sourceArrays = (mode === 'current')
    ? [{ arr: CURRENT_FIGURES, kind: 'current' }]
    : (mode === 'both')
      ? [{ arr: FIGURES, kind: 'historical' }, { arr: CURRENT_FIGURES, kind: 'current' }]
      : [{ arr: FIGURES, kind: 'historical' }];
  let DATA = sourceArrays.flatMap(s => s.arr.map(f => ({ ...f, _kind: s.kind })));
  if (century !== 'all') DATA = DATA.filter(f => f.century === century);
  if (region  !== 'all') DATA = DATA.filter(f => f.region  === region);
  DATA.sort((a, b) => b.n - a.n);

  const rowH = 34;
  const padTop = 64;
  const padBot = 48;
  const padL = 240;     // widened left label gutter
  const padR = 120;
  const H = padTop + padBot + Math.max(1, DATA.length) * rowH;

  const svg = opts.svgEl;
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  while (svg.firstChild) svg.removeChild(svg.firstChild);

  // background
  const bg = document.createElementNS(NS, 'rect');
  bg.setAttribute('x', '0'); bg.setAttribute('y', '0');
  bg.setAttribute('width', String(W)); bg.setAttribute('height', String(H));
  bg.setAttribute('fill', '#fcf8ee');
  svg.appendChild(bg);

  if (DATA.length === 0) {
    const t = document.createElementNS(NS, 'text');
    t.setAttribute('x', W/2); t.setAttribute('y', H/2);
    t.setAttribute('text-anchor', 'middle');
    t.setAttribute('font-family', 'Fraunces, Georgia, serif');
    t.setAttribute('font-style', 'italic');
    t.setAttribute('font-size', '18');
    t.setAttribute('fill', '#6f5f53');
    t.textContent = 'no entries match these filters';
    svg.appendChild(t);
    return;
  }

  // log scale: 1e4 → 5e7
  const xMin = 1e4, xMax = 5e7;
  const x0 = padL, x1 = W - padR;
  const xScale = v => x0 + (Math.log10(Math.max(xMin, v)) - Math.log10(xMin)) /
                              (Math.log10(xMax) - Math.log10(xMin)) * (x1 - x0);

  // gridlines + axis ticks at 10k, 100k, 1M, 10M, 50M
  const ticks = [1e4, 1e5, 1e6, 1e7, 5e7];
  const fmt = v => v >= 1e6 ? (v/1e6).toFixed(v >= 1e7 ? 0 : 1).replace(/\.0$/, '') + 'M'
                : v >= 1e3 ? (v/1e3).toFixed(0) + 'k' : String(v);
  for (const t of ticks) {
    const xx = xScale(t);
    const ln = document.createElementNS(NS, 'line');
    ln.setAttribute('x1', xx); ln.setAttribute('x2', xx);
    ln.setAttribute('y1', padTop - 8); ln.setAttribute('y2', H - padBot + 4);
    ln.setAttribute('stroke', 'rgba(31,24,19,.10)');
    ln.setAttribute('stroke-dasharray', '2 4');
    svg.appendChild(ln);
    const lbl = document.createElementNS(NS, 'text');
    lbl.setAttribute('x', xx); lbl.setAttribute('y', padTop - 16);
    lbl.setAttribute('text-anchor', 'middle');
    lbl.setAttribute('font-family', 'JetBrains Mono, monospace');
    lbl.setAttribute('font-size', '11');
    lbl.setAttribute('fill', '#a39179');
    lbl.textContent = fmt(t);
    svg.appendChild(lbl);
  }

  // x-axis caption
  const xcap = document.createElementNS(NS, 'text');
  xcap.setAttribute('x', (x0 + x1) / 2);
  xcap.setAttribute('y', H - 14);
  xcap.setAttribute('text-anchor', 'middle');
  xcap.setAttribute('font-family', 'JetBrains Mono, monospace');
  xcap.setAttribute('font-size', '11');
  xcap.setAttribute('fill', '#6f5f53');
  xcap.textContent = 'estimated deaths attributed to regime / conflict (log scale)';
  svg.appendChild(xcap);

  const palette = {
    historical: { '13c':'#6b4a8b','14c':'#6b4a8b','19c':'#c89a3e','20c':'#d96936' },
    current:    { '21c':'#5d8c4a' }
  };

  for (let i = 0; i < DATA.length; i++) {
    const f = DATA[i];
    const yMid = padTop + i * rowH + rowH/2;
    const col = (f._kind === 'current')
      ? palette.current[f.century] || '#5d8c4a'
      : palette.historical[f.century] || '#d96936';

    // row label (name + years) — truncate any name that still won't fit
    const lbl = document.createElementNS(NS, 'text');
    lbl.setAttribute('x', padL - 12);
    lbl.setAttribute('y', yMid + 4);
    lbl.setAttribute('text-anchor', 'end');
    lbl.setAttribute('font-family', 'Fraunces, Georgia, serif');
    lbl.setAttribute('font-size', '14');
    lbl.setAttribute('fill', '#1f1813');
    const nm = f.name.length > 28 ? f.name.slice(0, 26) + '…' : f.name;
    lbl.textContent = nm;
    svg.appendChild(lbl);

    const yrs = document.createElementNS(NS, 'text');
    yrs.setAttribute('x', padL - 12);
    yrs.setAttribute('y', yMid + 18);
    yrs.setAttribute('text-anchor', 'end');
    yrs.setAttribute('font-family', 'JetBrains Mono, monospace');
    yrs.setAttribute('font-size', '10');
    yrs.setAttribute('fill', '#a39179');
    yrs.textContent = f.years + ' · ' + f.region;
    svg.appendChild(yrs);

    // range whisker (low → high)
    const lo = f.lo || f.n, hi = f.hi || f.n;
    const xl = xScale(lo), xh = xScale(hi);
    const whisker = document.createElementNS(NS, 'line');
    whisker.setAttribute('x1', xl); whisker.setAttribute('x2', xh);
    whisker.setAttribute('y1', yMid); whisker.setAttribute('y2', yMid);
    whisker.setAttribute('stroke', col);
    whisker.setAttribute('stroke-opacity', '0.32');
    whisker.setAttribute('stroke-width', '8');
    whisker.setAttribute('stroke-linecap', 'round');
    svg.appendChild(whisker);

    // midpoint marker
    const xm = xScale(f.n);
    const dot = document.createElementNS(NS, 'circle');
    dot.setAttribute('cx', xm); dot.setAttribute('cy', yMid);
    dot.setAttribute('r', 6);
    dot.setAttribute('fill', col);
    dot.setAttribute('stroke', '#1f1813');
    dot.setAttribute('stroke-width', '0.8');
    svg.appendChild(dot);

    // right-side label
    const num = document.createElementNS(NS, 'text');
    num.setAttribute('x', x1 + 10);
    num.setAttribute('y', yMid + 4);
    num.setAttribute('text-anchor', 'start');
    num.setAttribute('font-family', 'JetBrains Mono, monospace');
    num.setAttribute('font-size', '12');
    num.setAttribute('fill', '#3a302a');
    num.textContent = fmt(f.n);
    svg.appendChild(num);

    // hit area for click
    const hit = document.createElementNS(NS, 'rect');
    hit.setAttribute('x', '0');
    hit.setAttribute('y', yMid - rowH/2);
    hit.setAttribute('width', String(W));
    hit.setAttribute('height', String(rowH));
    hit.setAttribute('fill', 'transparent');
    hit.style.cursor = 'pointer';
    hit.addEventListener('mouseenter', () => hit.setAttribute('fill', 'rgba(217,105,54,0.05)'));
    hit.addEventListener('mouseleave', () => hit.setAttribute('fill', 'transparent'));
    hit.addEventListener('click', () => {
      const detail = opts.detailEl; if (!detail) return;
      detail.hidden = false;
      detail.querySelector('[data-name]').textContent = f.name;
      detail.querySelector('[data-meta]').textContent = f.years + ' · ' + f.region + ' · est. mid-range ' + (f.n / 1e6).toFixed(2) + 'M deaths';
      detail.querySelector('[data-body]').innerHTML = '<strong>range:</strong> ' + f.range + '<br><br>' + f.summary;
      detail.querySelector('[data-source]').textContent = 'sources (representative): ' + f.src;
    });
    svg.appendChild(hit);
  }
}

if (typeof window !== 'undefined') {
  window.GoddingBubbles = { FIGURES, CURRENT_FIGURES, renderBubbles, renderBars };
}
