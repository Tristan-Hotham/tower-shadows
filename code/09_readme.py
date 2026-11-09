"""Step 9: README.md, LICENSE and reddit/post.md from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json")
C = R["cities"]
rows = "\n".join(f"| {C[k]['name']} | {C[k]['towers50']} | {C[k]['heights']['default_pc']:.0f}% | {C[k]['dates']['dec']['flat_h']:.2f} | {C[k]['dates']['dec']['mean_all_h']:.2f} | {C[k]['dates']['dec']['zero_pc']:.1f}% | {C[k]['dates']['dec']['lost_tow_h']:.2f} |" for k, *_ in CITIES)
sh = R["shard"]
readme = f"""# Shadows of the giants

Winter sun at street level and the shadows of tall buildings in eight UK city centres (central London, Canary Wharf, Manchester, Birmingham, Leeds, Liverpool, Glasgow, Edinburgh). Building heights from OpenStreetMap (OpenFreeMap vector tiles, release {R['tiles']}) on a 5 m grid with the terrain beneath; the sun traced every {R['step_min']} minutes on 21 December, 20 March and 21 June; each centre as built, without its towers (building parts of 50 m or more) and without any buildings.

Interactive page: https://maps.tristanhotham.com/tower-shadows/
Paper: {{https://doi.org/10.5281/zenodo.24075303}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/tower-shadows/}}
Code and data: https://github.com/Tristan-Hotham/tower-shadows

## Headline results

- At noon on 21 December a shadow is {R['london_noon_ratio']:.1f} times the height in London and {R['edinburgh_noon_ratio']:.1f} times in Edinburgh. A 300 m tower in London: {R['hypo300']['london_dec_m']:,} m. The Shard ({sh['h']:.0f} m in OpenStreetMap): {sh['noon_dec_m']:,} m at noon on 21 December, about {sh['dec_2h_r10']:,} m two hours either side, {sh['noon_mar_m']} m at the equinox, {sh['noon_jun_m']} m at midsummer.
- Ordinary buildings take most of the winter sun; towers take most at Canary Wharf ({C['canary']['dates']['dec']['lost_tow_h']:.2f} h from the average square metre of open ground; {C['canary']['dates']['dec']['tow_lost1h_pc']:.0f}% loses an hour or more) and Manchester ({C['manchester']['dates']['dec']['lost_tow_h']:.2f} h).
- Edinburgh, with {C['edinburgh']['towers50']} tower, is darkest: {C['edinburgh']['dates']['dec']['zero_pc']:.0f}% of open ground has no direct sun on 21 December. The cause is ordinary buildings under a very low sun ({C['edinburgh']['noon_alt']['dec']:.1f} degrees at noon): terrain alone leaves {C['edinburgh']['dates']['dec']['zero_ter_pc']:.1f}% without sun, the buildings alone on flat ground {C['edinburgh']['dates']['dec']['zero_flatbld_pc']:.0f}%.
- {R['streets_tow_1h']} of {R['n_streets']:,} named streets lose an hour or more to towers on 21 December; the largest losses are at Canary Wharf ({R['streets_tow'][0]['name']}) and in central London beside Battersea Power Station ({R['streets_tow'][1]['name']}).
- Heights are incomplete: {C['canary']['heights']['default_pc']:.0f}% to {C['liverpool']['heights']['default_pc']:.0f}% of building footprint has neither a height nor a storey count and is drawn 5 m high. That makes ordinary buildings too short and, if anything, inflates the towers' share; heights from storeys (3.66 m each) also overstate some residential towers (Landmark Pinnacle, 233 m, appears as 275 m).

| Centre | Towers | Footprint at 5 m default | Flat-horizon day (h) | Sun on open ground, 21 Dec (h) | No direct sun | Taken by towers (h) |
|---|---|---|---|---|---|---|
{rows}

## Files

| File | What it is |
|---|---|
| `index.html`, `js/page.js` | The interactive page: The Inked World base map (shared engine from ../ink-map/), hour-by-hour shadows decoded in the browser, date and city pickers, towers, streets and open spaces with popups. |
| `header.png` | Social card, 1200 x 630. |
| `data/shadows/<city>_<date>_all.png`, `_tow.png` | Shadow bit planes: bit k of R + 256 G + 65536 B is 1 when the cell is in shadow at the k-th whole hour listed in `data/shadow_meta.json` (all buildings; towers only). |
| `data/shadows/<city>_<date>_hours.png` | Hours of direct sun over the day, in ninths of the flat-horizon day (palette index 1 to 9; 0 = building). |
| `data/cities.csv`, `data/streets.csv`, `data/open_spaces.csv`, `data/towers.csv` | Results by centre, named street, open space and tower. |
| `data/streets.geojson`, `data/open_spaces.geojson`, `data/towers.json`, `data/shadow_meta.json` | Page data. |
| `data/results.json` | Every number quoted anywhere. |
| `code/` | Scripts in order, `shadow.py` (the shadow sweep), templates, `qa.js`. |
| `release/` | Paper, blog post and figures, Zenodo files. |
| `reddit/` | Collage and post text. |

## Method in brief

- Grid: 5 m cells in a transverse Mercator projection centred on each box (grid north = true north), 1.2 km margin; surface = terrain (AWS Terrain Tiles z10, bilinear) + building render_height (the tallest part over each cell).
- Sun: NOAA general solar position equations (Spencer 1971 series), Saemundsson refraction, every 10 minutes from sunrise to sunset at the box centre.
- Shadows: sweep along lines parallel to the sun's azimuth, shadow line falling by step x tan(altitude); three surfaces (terrain; terrain + parts under 50 m; terrain + all).
- Towers: merged parts of 50 m or more with footprint at least {R['min_tower_area']:.0f} m2. Streets: named roads, cells within 4 m. Open ground: no building, no water.
- Caveats: default 5 m heights make ordinary buildings too short; 90 m terrain; no trees, cloud or awnings; raised parts treated as solid.

## How to rerun

Needs Python 3 with numpy, numba, pandas, shapely 2, pyproj, rasterio, scipy, mapbox-vector-tile, matplotlib, Pillow; xelatex; node with Playwright for `code/qa.js`. Tiles and intermediates go to a scratch folder (`code/common.py`).

```
python3 code/01_tiles.py       # OpenFreeMap zoom-14 tiles (network)
python3 code/02_grid.py        # 5 m grids and vectors per centre
python3 code/03_shadows.py     # sun and shadows (about 10 minutes)
python3 code/04_results.py     # results.json and data files
python3 code/05_figures.py     # figures and header
python3 code/06_build_site.py  # index.html
python3 code/07_paper.py       # paper PDF (set DOI=10.5281/zenodo.N to fill the DOI)
python3 reddit/collage.py      # collage
python3 code/09_readme.py      # README, LICENSE, Reddit post
python3 code/08_release.py     # blog post, Zenodo files
```

## Sources and licences

- OpenStreetMap contributors (https://www.openstreetmap.org/copyright), ODbL, via OpenFreeMap (https://openfreemap.org/) vector tiles (OpenMapTiles schema). Derived data from it (shadows, streets, open spaces, towers) are under the ODbL.
- AWS Terrain Tiles (https://registry.opendata.aws/terrain-tiles/).
- Base map on the page: The Inked World (https://maps.tristanhotham.com/ink-map/). Fonts: MedievalSharp, IM Fell (SIL OFL).
- Text and figures CC BY 4.0; code MIT.

## Citation

Hotham, T. (2026) Shadows of the giants: winter sun at street level in eight UK city centres. Zenodo. {{10.5281/zenodo.24075303}}

{AI}
"""
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)
lic = open("/home/claude/studies/renamed-world/LICENSE", encoding="utf-8").read().replace(
    "Derived data (data/): CC0 1.0, like its source, Wikidata.", "Derived data (data/): Open Database Licence (ODbL) 1.0, as derived from OpenStreetMap (c) OpenStreetMap contributors.")
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)
cw = C["canary"]["dates"]["dec"]
post = f"""**Title:** [OC] On the shortest day the Shard casts a shadow {sh['noon_dec_m']:,} m long at noon. I traced the winter sun through eight UK city centres to see who loses it to towers

**Body:**

Building heights from OpenStreetMap on a 5 m grid, the sun every 10 minutes on 21 December, the equinox and 21 June, each city as built, without its towers (50 m+) and without any buildings.

- On 21 December a shadow at noon is {R['london_noon_ratio']:.1f} times the height in London, {R['edinburgh_noon_ratio']:.1f} in Edinburgh.
- The ordinary dense city takes most of the winter sun: central London's open ground gets {C['london']['dates']['dec']['mean_all_h']:.1f} h of a {C['london']['dates']['dec']['flat_h']:.1f} h day; removing the towers would give back only {C['london']['dates']['dec']['lost_tow_h']:.2f} h.
- Canary Wharf is the exception: towers take {cw['lost_tow_h']:.2f} h from the average square metre, and {cw['tow_lost1h_pc']:.0f}% of open ground loses an hour or more.
- Darkest centre: Edinburgh ({C['edinburgh']['dates']['dec']['zero_pc']:.0f}% of open ground with no direct sun), with almost no towers: ordinary buildings under a sun only {C['edinburgh']['noon_alt']['dec']:.1f} degrees up at noon (the hills alone would leave under 1% in shade all day).
- Caveat: {C['canary']['heights']['default_pc']:.0f} to {C['liverpool']['heights']['default_pc']:.0f}% of building footprint has no height in OSM and is drawn 5 m tall, so real streets are darker and the towers' share is if anything a little high.

Interactive map (time slider, three dates, tap a tower for its shadow length): https://maps.tristanhotham.com/tower-shadows/

**Source comment:**

Data: OpenStreetMap contributors (ODbL) via OpenFreeMap vector tiles; AWS Terrain Tiles. Tools: Python (numpy, numba, shapely, rasterio, matplotlib), MapLibre. Sun: NOAA solar equations. Paper and code: https://github.com/Tristan-Hotham/tower-shadows
"""
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
for t in (readme, post):
    for bad in ("—", "–", "DSIT", "DCMS"):
        assert bad not in t, bad
print("readme", len(readme.split()), "words")
