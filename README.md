# Shadows of the giants

Winter sun at street level and the shadows of tall buildings in eight UK city centres (central London, Canary Wharf, Manchester, Birmingham, Leeds, Liverpool, Glasgow, Edinburgh). Building heights from OpenStreetMap (OpenFreeMap vector tiles, release 20261101_080013_pt) on a 5 m grid with the terrain beneath; the sun traced every 10 minutes on 21 December, 20 March and 21 June; each centre as built, without its towers (building parts of 50 m or more) and without any buildings.

Interactive page: https://maps.tristanhotham.com/tower-shadows/
Paper: https://doi.org/10.5281/zenodo.24075303
Blog post: https://blog.tristanhotham.com/2026/10/31/tower-shadows/
Code and data: https://github.com/Tristan-Hotham/tower-shadows

## Headline results

- At noon on 21 December a shadow is 3.7 times the height in London and 5.3 times in Edinburgh. A 300 m tower in London: 1,110 m. The Shard (310 m in OpenStreetMap): 1,146 m at noon on 21 December, about 1,650 m two hours either side, 395 m at the equinox, 165 m at midsummer.
- Ordinary buildings take most of the winter sun; towers take most at Canary Wharf (0.76 h from the average square metre of open ground; 26% loses an hour or more) and Manchester (0.48 h).
- Edinburgh, with 1 tower, is darkest: 33% of open ground has no direct sun on 21 December. The cause is ordinary buildings under a very low sun (10.7 degrees at noon): terrain alone leaves 0.7% without sun, the buildings alone on flat ground 29%.
- 209 of 3,469 named streets lose an hour or more to towers on 21 December; the largest losses are at Canary Wharf (South Colonnade) and in central London beside Battersea Power Station (Circus Road South).
- Heights are incomplete: 41% to 74% of building footprint has neither a height nor a storey count and is drawn 5 m high. That makes ordinary buildings too short and, if anything, inflates the towers' share; heights from storeys (3.66 m each) also overstate some residential towers (Landmark Pinnacle, 233 m, appears as 275 m).

| Centre | Towers | Footprint at 5 m default | Flat-horizon day (h) | Sun on open ground, 21 Dec (h) | No direct sun | Taken by towers (h) |
|---|---|---|---|---|---|---|
| Central London | 316 | 47% | 7.67 | 2.84 | 21.9% | 0.18 |
| Canary Wharf | 107 | 41% | 7.67 | 2.60 | 20.0% | 0.76 |
| Manchester | 103 | 47% | 7.50 | 2.60 | 19.2% | 0.48 |
| Birmingham | 63 | 62% | 7.50 | 2.91 | 19.0% | 0.28 |
| Leeds | 43 | 62% | 7.33 | 3.44 | 12.8% | 0.32 |
| Liverpool | 28 | 74% | 7.33 | 3.23 | 13.8% | 0.27 |
| Glasgow | 19 | 64% | 6.83 | 2.97 | 20.0% | 0.13 |
| Edinburgh | 1 | 53% | 7.00 | 2.11 | 32.6% | 0.01 |

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
- Towers: merged parts of 50 m or more with footprint at least 300 m2. Streets: named roads, cells within 4 m. Open ground: no building, no water.
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

Hotham, T. (2026) Shadows of the giants: winter sun at street level in eight UK city centres. Zenodo. 10.5281/zenodo.24075303

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
