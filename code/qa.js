// QA: serve the studies folder (so ../ink-map/ resolves as on the live site), open index.html at desktop and phone widths,
// log console errors and save screenshots to qa/. Usage: node code/qa.js [maplibre dist dir]
// External: OpenFreeMap tiles live; elevation tiles from the local zoom-10 Terrarium tiles; Google Fonts skipped.
const fs = require('fs'), path = require('path'), http = require('http');
const { chromium } = require(process.env.PW || 'playwright');
const ROOT = path.resolve(__dirname, '..'), STUDIES = path.dirname(ROOT), ML = process.argv[2] || '/tmp/ml/node_modules/maplibre-gl/dist';
const DEMDIR = process.env.DEMDIR || '/home/claude/newdata/raw_new8/terrain/tiles';
const TYPES = { '.html': 'text/html', '.js': 'application/javascript', '.json': 'application/json', '.png': 'image/png', '.webp': 'image/webp', '.pbf': 'application/x-protobuf', '.geojson': 'application/json', '.css': 'text/css', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml', '.woff2': 'font/woff2' };
const srv = http.createServer((q, s) => {
  let u = decodeURIComponent(q.url.split('?')[0]);
  const f = u.startsWith('/dem/') ? path.join(DEMDIR, u.slice(5)) : path.join(STUDIES, u);
  fs.readFile(f, (e, b) => { if (e && u.startsWith('/dem/')) { e = null; b = FLAT; } if (e) { s.writeHead(404); s.end(); return; } s.writeHead(200, { 'content-type': TYPES[path.extname(f)] || 'application/octet-stream' }); s.end(b); });
}).listen(8793);
const FLAT = fs.readFileSync(path.join(__dirname, 'qa_flat.png'));   // a sea-level Terrarium tile where no local tile exists
const PAGE = 'http://localhost:8793/tower-shadows/index.html';
const DEM = 'http://localhost:8793/dem/{z}/{x}/{y}.png';
(async () => {
  const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const shots = [
    { out: 'qa/desktop.png', w: 1280, h: 800 },
    { out: 'qa/desktop_canary.png', w: 1280, h: 800, q: 'city=canary&hour=10' },
    { out: 'qa/desktop_city_zoom.png', w: 1280, h: 800, q: 'at=51.512,-0.083,16&hour=12' },
    { out: 'qa/desktop_june_layers.png', w: 1280, h: 800, q: 'city=manchester&date=jun', eval: "document.getElementById('lyrBtn').click()" },
    { out: 'qa/phone.png', w: 390, h: 800, dpr: 2 },
    { out: 'qa/phone_edinburgh.png', w: 390, h: 800, dpr: 2, q: 'city=edinburgh&hour=12' },
    { out: 'qa/phone_full.png', w: 390, h: 800, dpr: 1, full: true },
    { out: 'qa/desktop_full.png', w: 1280, h: 800, full: true },
  ];
  const errors = [], info = {};
  for (const s of shots) {
    const ctx = await browser.newContext({ viewport: { width: s.w, height: s.h }, deviceScaleFactor: s.dpr || 1 });
    const page = await ctx.newPage();
    await page.route(/cdn\.jsdelivr\.net\/npm\/maplibre-gl@4\.7\.1\/dist\/(.*)/, r => { const f = path.join(ML, r.request().url().split('/dist/')[1]); r.fulfill({ body: fs.readFileSync(f), contentType: f.endsWith('.css') ? 'text/css' : 'application/javascript' }); });
    await page.route(/fonts\.(googleapis|gstatic)\.com|maps\.tristanhotham\.com\/assets/, r => r.abort());
    page.on('console', m => { if (m.type() === 'error' && !/Failed to load resource/.test(m.text())) errors.push(`[${s.out}] ${m.text().slice(0, 300)}`); });
    page.on('pageerror', e => errors.push(`[${s.out}] pageerror ${e.message}`));
    page.on('requestfailed', q => { if (!/fonts\.g|site-nav/.test(q.url())) errors.push(`[${s.out}] failed ${q.url().slice(0, 140)}`); });
    await page.goto(`${PAGE}?dem=${encodeURIComponent(DEM)}&demmax=10${s.q ? '&' + s.q : ''}`, { waitUntil: 'load' });
    await page.waitForFunction(() => window.__map && window.__map.getLayer('sh'), null, { timeout: 120000 });
    await page.evaluate(() => new Promise(res => { const m = window.__map; m.once('idle', () => setTimeout(res, 1500)); setTimeout(res, 45000); }));
    if (s.eval) { await page.evaluate(s.eval); await page.waitForTimeout(1500); }
    await page.waitForTimeout(1500);
    info[s.out] = await page.evaluate(() => ({ scrollW: document.documentElement.scrollWidth, w: innerWidth, fsBtns: document.querySelectorAll('.mfs-btn').length,
      tw: window.__map.queryRenderedFeatures({ layers: ['tw'] }).length, hr: document.getElementById('hr').innerText, sun: document.getElementById('sunTxt').innerText }));
    await page.screenshot({ path: path.join(ROOT, s.out), fullPage: !!s.full, timeout: 120000 });
    console.log('ok', s.out, JSON.stringify(info[s.out]));
    await ctx.close();
  }
  await browser.close(); srv.close();
  console.log('ERRORS:', errors.length); errors.forEach(e => console.log(e));
  process.exit(0);
})();
