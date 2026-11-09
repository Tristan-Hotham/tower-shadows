/* Shadows of the giants: building shadows hour by hour in eight UK city centres, decoded in the browser from bit-plane
 * PNGs (bit k of R + 256 G + 65536 B = in shadow at the k-th whole hour), on The Inked World base map.
 * Dr Tristan Hotham, Independent researcher, 2026. MIT licence. */
(function () {
  'use strict';
  const qs = new URLSearchParams(location.search);
  const BASE = window.INKBASE, V = '?v=20261108';
  const ENGINE = ['js/curated.js', 'js/ink-palette.js', 'js/ink-icons.js', 'js/ink-houses.js', 'js/ink-map.js', 'js/ink-extras.js'];
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const norm = s => String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const small = matchMedia('(max-width:800px)').matches;
  const DN = { dec: '21 December', mar: '20 March', jun: '21 June' };
  const HC = ['#1F1838', '#3B2F63', '#5B4A8B', '#7E6CA8', '#A99BC0', '#D9C9A3', '#EBCB7A', '#F0B23A', '#E39A2C'];
  let map = null, M = null, TW = null, city = qs.get('city') || 'london', day = qs.get('date') || 'dec', hi = null;
  const cache = {};
  document.getElementById('theme').addEventListener('click', () => { const r = document.documentElement, d = r.dataset.theme ? r.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches; r.dataset.theme = d ? 'light' : 'dark'; });
  const ct = document.getElementById('cartouche'); const fold = f => ct.classList.toggle('folded', f);
  if (small) fold(true);
  document.getElementById('ctToggle').addEventListener('click', () => fold(!ct.classList.contains('folded')));
  document.getElementById('ctFold').addEventListener('click', () => fold(true));
  function loadScripts(list) { return list.reduce((p, src) => p.then(() => new Promise((res, rej) => { const el = document.createElement('script'); el.src = BASE + src + V; el.onload = res; el.onerror = () => rej(new Error('script ' + src)); document.head.appendChild(el); })), Promise.resolve()); }
  const hhmm = h => { const m = Math.round(h * 60); return String(Math.floor(m / 60) % 24).padStart(2, '0') + ':' + String(m % 60).padStart(2, '0'); };

  function planes(c, d) {                       // decoded bit planes for all and towers-only
    const k = c + '_' + d;
    if (!cache[k]) cache[k] = Promise.all(['all', 'tow'].map(n => new Promise((res, rej) => {
      const im = new Image(); im.onload = () => { const cv = document.createElement('canvas'); cv.width = im.width; cv.height = im.height; const g = cv.getContext('2d'); g.drawImage(im, 0, 0);
        const px = g.getImageData(0, 0, im.width, im.height).data, out = new Uint32Array(im.width * im.height);
        for (let i = 0, j = 0; i < out.length; i++, j += 4) out[i] = px[j] | (px[j + 1] << 8) | (px[j + 2] << 16);
        res({ w: im.width, h: im.height, b: out }); };
      im.onerror = () => rej(new Error('shadow image ' + k)); im.src = `data/shadows/${c}_${d}_${n}.png`;
    })));
    return cache[k];
  }
  const Q = {};
  function setImg(id, url, coords) {               // one image update at a time per source (MapLibre aborts overlapping loads)
    const q = Q[id] || (Q[id] = { busy: false, next: null, last: null });
    const key = url + JSON.stringify(coords); if (key === q.last) return; q.last = key; q.next = { url, coords };
    const flush = () => {
      if (q.busy || !q.next) return; q.busy = true; const p = q.next; q.next = null;
      const done = e => { if (e.sourceId === id) { map.off('sourcedata', done); clearTimeout(t); q.busy = false; flush(); } };
      const t = setTimeout(() => { map.off('sourcedata', done); q.busy = false; flush(); }, 4000);
      map.on('sourcedata', done);
      map.getSource(id).updateImage({ url: p.url, coordinates: p.coords });
    };
    flush();
  }
  function guard(id, url, coords) {              // a source's first image is loading: queue updates until it is in
    Q[id] = { busy: true, next: null, last: url + JSON.stringify(coords) };
    const first = e => { if (e.sourceId === id) { map.off('sourcedata', first); Q[id].busy = false; const n = Q[id].next; if (n) { Q[id].next = null; Q[id].last = null; setImg(id, n.url, n.coords); } } };
    map.on('sourcedata', first);
  }
  const cv = document.createElement('canvas');
  function render() {
    const md = M[city].dates[day], k = hi, showT = document.getElementById('lyTw').checked;
    document.getElementById('hr').textContent = hhmm(md.hours[k]) + (md.tz ? ' BST' : ' GMT');
    document.getElementById('alt').textContent = 'sun ' + md.alt[k].toFixed(0) + '° up';
    const sr = md.sunrise_utc + md.tz, ss = md.sunset_utc + md.tz;
    document.getElementById('sunTxt').textContent = `${M[city].name}, ${DN[day]}: sunrise ${hhmm(sr)}, sunset ${hhmm(ss)}${md.tz ? ' BST' : ' GMT'}`;
    return planes(city, day).then(([A, T]) => {
      cv.width = A.w; cv.height = A.h; const g = cv.getContext('2d'); const img = g.createImageData(A.w, A.h); const p = img.data;
      for (let i = 0, j = 0; i < A.b.length; i++, j += 4) {
        if ((A.b[i] >>> k) & 1) { if (showT && ((T.b[i] >>> k) & 1)) { p[j] = 163; p[j + 1] = 38; p[j + 2] = 27; p[j + 3] = 175; } else { p[j] = 31; p[j + 1] = 24; p[j + 2] = 56; p[j + 3] = 140; } }
      }
      g.putImageData(img, 0, 0);
      setImg('sh', cv.toDataURL(), M[city].corners);
      drawTowerShadows();
    });
  }
  function drawTowerShadows() {
    const md = M[city].dates[day], a = md.alt[hi], az = md.az[hi];
    const f = TW.filter(t => t[0] === city && t[3] >= 100).map(t => { const L = t[3] / Math.tan(a * Math.PI / 180), r = (az + 180) * Math.PI / 180, k = Math.cos(t[2] * Math.PI / 180);
      return { type: 'Feature', properties: { L: Math.round(L) }, geometry: { type: 'LineString', coordinates: [[t[1], t[2]], [t[1] + Math.sin(r) * L / (111195 * k), t[2] + Math.cos(r) * L / 111195]] } }; });
    map.getSource('tl').setData({ type: 'FeatureCollection', features: f });
  }
  function setHours() {
    const s = document.getElementById('hrs'), md = M[city].dates[day];
    s.max = md.hours.length - 1;
    if (hi === null || hi >= md.hours.length) { const noon = md.hours.findIndex(h => h === (day === 'jun' ? 13 : 12)); hi = noon >= 0 ? noon : Math.floor(md.hours.length / 2); }
    s.value = hi;
  }
  function setCity(c, fly) {
    city = c; document.getElementById('city').value = c; setHours();
    setImg('hr', `data/shadows/${c}_${day}_hours.png`, M[c].corners);
    if (fly) { const cs = M[c].corners; map.fitBounds([[cs[0][0], cs[2][1]], [cs[1][0], cs[0][1]]], { padding: small ? 10 : 60, duration: 1200 }); }
    render();
  }
  function setDay(d, quiet) {
    day = d; document.querySelectorAll('.chip[data-d]').forEach(b => b.setAttribute('aria-pressed', b.dataset.d === d));
    setHours(); if (!quiet) setImg('hr', `data/shadows/${city}_${day}_hours.png`, M[city].corners);
    map.setPaintProperty('st', 'line-color', ramp(day)); map.setPaintProperty('op', 'fill-color', ramp(day));
    if (!quiet) render();
  }
  function ramp(d) {
    const key = { dec: 'd', mar: 'm', jun: 'j' }[d], flat = { dec: 7.7, mar: 12.2, jun: 16.6 }[d];
    const e = ['interpolate', ['linear'], ['/', ['get', key], flat]]; HC.forEach((c, i) => e.push(i / 8, c)); return e;
  }
  function popupTower(t, ll) {
    const lens = ['dec', 'mar', 'jun'].map((d, i) => `<tr><td>${DN[d]}, noon</td><td>${t[5 + i].toLocaleString('en-GB')} m</td></tr>`).join('');
    const md = M[city].dates[day], L = t[3] / Math.tan(md.alt[hi] * Math.PI / 180);
    new maplibregl.Popup({ maxWidth: '300px' }).setLngLat(ll).setHTML(`<b class="t">A ${t[3]} m tower</b><div class="nt">${esc(M[t[0]].name)} · footprint ${t[4].toLocaleString('en-GB')} m²</div>
      <table>${lens}<tr><td>${DN[day]}, ${hhmm(md.hours[hi])}</td><td><b>${Math.round(L).toLocaleString('en-GB')} m</b></td></tr></table>
      <div class="nt">Shadow length on flat ground. Height: OpenStreetMap (render_height) via OpenFreeMap.</div>`).addTo(map);
  }
  function popupSt(p, ll, kind) {
    const rows = `<tr><td>21 December</td><td>${(+p.d).toFixed(1)} h (${(+p.dl).toFixed(1)} h without towers, ${(+p.dt).toFixed(1)} h without buildings)</td></tr><tr><td>20 March</td><td>${(+p.m).toFixed(1)} h</td></tr><tr><td>21 June</td><td>${(+p.j).toFixed(1)} h</td></tr>`;
    new maplibregl.Popup({ maxWidth: '320px' }).setLngLat(ll).setHTML(`<b class="t">${esc(p.n || (kind === 'op' ? 'Open space' : 'Street'))}</b><div class="nt">${esc(M[p.c].name)}${p.a ? ' · ' + (+p.a).toLocaleString('en-GB') + ' m²' : ''}</div>
      <div>Average hours of direct sun at ground level:</div><table>${rows}</table><div class="nt">Buildings from OpenStreetMap heights; no trees or cloud.</div>`).addTo(map);
  }
  function setupLayers() {
    const before = (map.getStyle().layers.find(l => l.metadata && ['names'].includes(l.metadata.group)) || {}).id;
    const c0 = M[city].corners;
    map.addSource('hr', { type: 'image', url: `data/shadows/${city}_${day}_hours.png`, coordinates: c0 });
    guard('hr', `data/shadows/${city}_${day}_hours.png`, c0);
    map.addLayer({ id: 'hr', type: 'raster', source: 'hr', layout: { visibility: 'none' }, paint: { 'raster-opacity': 0.8, 'raster-resampling': 'nearest', 'raster-fade-duration': 0 } }, before);
    map.addSource('sh', { type: 'image', url: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==', coordinates: c0 });
    guard('sh', 'init', c0);
    map.addLayer({ id: 'sh', type: 'raster', source: 'sh', paint: { 'raster-opacity': 0.95, 'raster-resampling': 'nearest', 'raster-fade-duration': 0 } }, before);
    try { map.addLayer({ id: 'bld', type: 'fill', source: 'ofm', 'source-layer': 'building', minzoom: 13, paint: { 'fill-color': '#E6D6B0', 'fill-outline-color': '#7A6446', 'fill-opacity': 0.95 } }, before); } catch (e) { }
    map.addSource('op', { type: 'geojson', data: 'data/open_spaces.geojson', attribution: 'Buildings, streets, parks: <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> (ODbL)' });
    map.addLayer({ id: 'op', type: 'fill', source: 'op', paint: { 'fill-color': ramp(day), 'fill-opacity': 0.0, 'fill-outline-color': '#2F6E5A' } }, before);
    map.addLayer({ id: 'opl', type: 'line', source: 'op', paint: { 'line-color': '#2F6E5A', 'line-width': 1.6, 'line-dasharray': [2, 1.5] } }, before);
    map.addSource('st', { type: 'geojson', data: 'data/streets.geojson' });
    map.addLayer({ id: 'st', type: 'line', source: 'st', minzoom: 13, layout: { 'line-cap': 'round' }, paint: { 'line-color': ramp(day), 'line-width': ['interpolate', ['linear'], ['zoom'], 13, 1.5, 17, 5], 'line-opacity': 0.9 } }, before);
    map.addSource('tl', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
    map.addLayer({ id: 'tl', type: 'line', source: 'tl', paint: { 'line-color': '#A3261B', 'line-width': 1.4, 'line-dasharray': [3, 2], 'line-opacity': 0.85 } });
    const tf = TW.map((t, i) => ({ type: 'Feature', properties: { i, h: t[3] }, geometry: { type: 'Point', coordinates: [t[1], t[2]] } }));
    map.addSource('tw', { type: 'geojson', data: { type: 'FeatureCollection', features: tf } });
    map.addLayer({ id: 'tw', type: 'circle', source: 'tw', paint: { 'circle-color': '#A3261B', 'circle-stroke-color': '#FBF5E4', 'circle-stroke-width': 1.2, 'circle-radius': ['interpolate', ['linear'], ['get', 'h'], 50, 3, 150, 6, 310, 10] } });
    map.addLayer({ id: 'twl', type: 'symbol', source: 'tw', minzoom: 14, filter: ['>=', ['get', 'h'], 100], layout: { 'text-field': ['concat', ['to-string', ['get', 'h']], ' m'], 'text-font': ['Ink Italic'], 'text-size': 12, 'text-offset': [0, 1.1], 'text-anchor': 'top' }, paint: { 'text-color': '#A3261B', 'text-halo-color': 'rgba(251,245,228,.95)', 'text-halo-width': 1.5 } });
    map.on('click', e => {
      const t = map.queryRenderedFeatures(e.point, { layers: ['tw'] })[0];
      if (t) { const r = TW[t.properties.i]; city = r[0]; popupTower(r, e.lngLat); return; }
      const s = map.queryRenderedFeatures([[e.point.x - 4, e.point.y - 4], [e.point.x + 4, e.point.y + 4]], { layers: ['st'] })[0];
      if (s) { popupSt(s.properties, e.lngLat, 'st'); return; }
      const o = map.queryRenderedFeatures(e.point, { layers: ['op'] })[0];
      if (o) popupSt(o.properties, e.lngLat, 'op');
    });
    ['tw', 'st', 'op'].forEach(l => { map.on('mouseenter', l, () => map.getCanvas().style.cursor = 'pointer'); map.on('mouseleave', l, () => map.getCanvas().style.cursor = ''); });
    const lp = document.getElementById('lp'), btn = document.getElementById('lyrBtn');
    btn.addEventListener('click', e => { e.stopPropagation(); const o = lp.classList.toggle('open'); btn.setAttribute('aria-expanded', o); });
    document.addEventListener('click', e => { if (!lp.contains(e.target) && e.target !== btn) { lp.classList.remove('open'); btn.setAttribute('aria-expanded', false); } });
    const vis = (id, v) => { if (map.getLayer(id)) map.setLayoutProperty(id, 'visibility', v ? 'visible' : 'none'); };
    document.getElementById('lySh').addEventListener('change', e => vis('sh', e.target.checked));
    document.getElementById('lyTw').addEventListener('change', () => render());
    document.getElementById('lyHr').addEventListener('change', e => vis('hr', e.target.checked));
    document.getElementById('lySt').addEventListener('change', e => vis('st', e.target.checked));
    document.getElementById('lyOp').addEventListener('change', e => { vis('op', e.target.checked); vis('opl', e.target.checked); });
    document.getElementById('lyT').addEventListener('change', e => { vis('tw', e.target.checked); vis('twl', e.target.checked); vis('tl', e.target.checked); });
    const boxes = [...lp.querySelectorAll('input[data-g]')], modern = document.getElementById('modern');
    const base = () => { const m = modern.checked; boxes.forEach(b => { try { InkMap.setGroup(map, b.dataset.g, b.checked && !(m && b.dataset.g === 'tint')); } catch (e) { } });
      try { InkMap.setGroup(map, 'paper', !m); InkMap.setGroup(map, 'modern', m); InkMap.setGroup(map, 'coast', !m); } catch (e) { } };
    boxes.forEach(b => b.addEventListener('change', base)); modern.addEventListener('change', base); base();
    const sel = document.getElementById('city');
    Object.keys(M).forEach(k => { const o = document.createElement('option'); o.value = k; o.textContent = M[k].name; sel.appendChild(o); });
    sel.addEventListener('change', () => setCity(sel.value, true));
    document.querySelectorAll('.chip[data-d]').forEach(b => b.addEventListener('click', () => setDay(b.dataset.d)));
    const s = document.getElementById('hrs'); s.addEventListener('input', () => { hi = +s.value; render(); });
    let timer = null; const play = document.getElementById('play');
    play.addEventListener('click', () => { if (timer) { clearInterval(timer); timer = null; play.textContent = '▶'; return; } play.textContent = '❚❚';
      timer = setInterval(() => { hi = (hi + 1) % M[city].dates[day].hours.length; s.value = hi; render(); }, 1100); });
  }
  function setupSearch() {
    const q = document.getElementById('q'), sug = document.getElementById('sug'); let idx = [], items = [], k = -1;
    Object.keys(M).forEach(c => idx.push({ n: M[c].name, s: 'city centre', city: c }));
    Promise.all([fetch('data/streets.geojson').then(r => r.json()), fetch('data/open_spaces.geojson').then(r => r.json())]).then(([a, b]) => {
      a.features.forEach(f => { const c = f.geometry.coordinates; const p = f.geometry.type === 'LineString' ? c[Math.floor(c.length / 2)] : c[0][Math.floor(c[0].length / 2)]; idx.push({ n: f.properties.n, s: M[f.properties.c].name + ' · ' + (+f.properties.d).toFixed(1) + ' h on 21 Dec', ll: p, city: f.properties.c, f: f.properties, kind: 'st' }); });
      b.features.forEach(f => { if (!f.properties.n) return; const c = f.geometry.type === 'Polygon' ? f.geometry.coordinates[0][0] : f.geometry.coordinates[0][0][0]; idx.push({ n: f.properties.n, s: M[f.properties.c].name + ' · open space', ll: c, city: f.properties.c, f: f.properties, kind: 'op' }); });
    });
    const show = () => { const v = norm(q.value.trim()); sug.innerHTML = ''; k = -1; if (v.length < 2) { sug.style.display = 'none'; return; }
      items = idx.filter(x => norm(x.n).startsWith(v)).concat(idx.filter(x => !norm(x.n).startsWith(v) && v.length > 3 && norm(x.n).includes(v))).slice(0, 12);
      items.forEach((it, j) => { const li = document.createElement('li'); li.setAttribute('role', 'option'); li.innerHTML = `${esc(it.n)} <span>${esc(it.s)}</span>`; li.addEventListener('mousedown', e => { e.preventDefault(); pick(j); }); sug.appendChild(li); });
      sug.style.display = items.length ? 'block' : 'none'; };
    const pick = j => { const it = items[j]; if (!it) return; q.value = it.n; sug.style.display = 'none'; fold(true);
      if (it.city !== city) setCity(it.city, !it.ll);
      if (it.ll) { map.flyTo({ center: it.ll, zoom: 16, duration: 1400 }); map.once('moveend', () => popupSt(it.f, it.ll, it.kind)); } };
    q.addEventListener('input', show);
    q.addEventListener('keydown', e => { const lis = [...sug.children];
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); k = Math.max(0, Math.min(lis.length - 1, k + (e.key === 'ArrowDown' ? 1 : -1))); lis.forEach((l, i) => l.setAttribute('aria-selected', i === k)); }
      else if (e.key === 'Enter') { e.preventDefault(); if (!items.length) show(); pick(k < 0 ? 0 : k); } else if (e.key === 'Escape') sug.style.display = 'none'; });
    q.addEventListener('blur', () => setTimeout(() => sug.style.display = 'none', 150));
  }
  Promise.all([fetch('data/shadow_meta.json').then(r => r.json()), fetch('data/towers.json').then(r => r.json())]).then(([m, t]) => {
    M = m; TW = t.towers; if (!M[city]) city = 'london'; if (!DN[day]) day = 'dec';
    const opts = { base: BASE, winter: false };
    if (qs.get('tj')) opts.tilejson = qs.get('tj');
    if (qs.get('dem')) opts.dem = qs.get('dem');
    if (qs.get('demmax')) opts.demMax = +qs.get('demmax');
    const at = (qs.get('at') || '').split(',').map(Number);
    const cs = M[city].corners;
    opts.mapOptions = at.length === 3 && at.every(isFinite) ? { center: [at[1], at[0]], zoom: at[2] } : { bounds: [[cs[0][0], cs[2][1]], [cs[1][0], cs[0][1]]], fitBoundsOptions: { padding: small ? 4 : 40 } };
    return loadScripts(ENGINE).then(() => InkMap.create('map', opts));
  }).then(mm => {
    map = mm; window.__map = mm;
    mm.on('error', e => { const er = e && e.error; if (er && (er.name === 'AbortError' || /abort/i.test(er.message || ''))) return; console.error(er || e); });   // aborted loads are expected when the hour or city changes fast
    const n = document.getElementById('nojs'); if (n) n.remove();
    mm.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right');
    const foldAt = () => document.querySelectorAll('.maplibregl-ctrl-attrib.maplibregl-compact').forEach(at => { at.classList.remove('maplibregl-compact-show'); at.removeAttribute('open'); });
    mm.once('idle', foldAt); setTimeout(foldAt, 1500);
    try { ['heritage', 'flight', 'animals', 'farms', 'towns', 'mountains', 'forests'].forEach(g => InkMap.setGroup(mm, g, false)); } catch (e) { }
    setupLayers(); setupSearch();
    if (qs.get('hour')) { const md = M[city].dates[day]; const i = md.hours.indexOf(+qs.get('hour')); if (i >= 0) hi = i; }
    setDay(day, true); setCity(city, false);
    document.getElementById('mapWrap').addEventListener('pointerdown', e => { if (e.target.closest && e.target.closest('.cartouche,.ov,.lp,.tl,.keys,.mfs-btn,.maplibregl-ctrl')) return; fold(true); }, { capture: true, passive: true, once: true });
  }).catch(e => { console.error(e); const n = document.getElementById('nojs'); if (n) n.textContent = 'The map could not load: ' + e.message; });
})();
