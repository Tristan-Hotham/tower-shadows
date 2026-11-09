# tower-shadows: working notes

Brief: /home/claude/work/new9/BRIEFS.md (study 8) + shared rules (new8/BRIEFS.md, newdata/BRIEF.md). Format refs: sunless-valleys
(sun code, shared ../ink-map/ engine), church-orientation (OFM tile reading).
Scratch: /home/claude/scratch/tower-shadows (tiles cache ~47 MB, work/ grids and sun arrays). Delete at end.

## Pipeline
- 01_tiles.py: OpenFreeMap z14 tiles (planet version in results.json "tiles") over 8 centres + 1.5 km; 216 tiles.
- 02_grid.py: per centre, 5 m grid in a local transverse Mercator (true north up): H (max render_height), L (parts < 50 m),
  T (parts >= 50 m), G (AWS Terrain Tiles z10, bilinear; /home/claude/newdata/raw_new8/terrain), water, open spaces
  (landcover park/garden/recreation_ground/village_green/common + park layer; named from park/garden POIs), named streets
  (transportation_name, 4 m either side), towers (merged parts >= 50 m). Domain = centre box + 1.2 km buffer.
- shadow.py: shadow sweep along lines parallel to the sun (numba), tested on a block (direction and length match 1/tan(alt)).
- 03_shadows.py: NOAA solar position (Spencer series, Saemundsson refraction) at each centre; 10-minute steps sunrise to
  sunset on 21 Dec, 20 Mar, 21 Jun; three surfaces: terrain, terrain + buildings < 50 m, terrain + all. Hourly bit planes for
  the map (local clock: GMT Dec/Mar, BST Jun) and hours-of-sun palette PNGs (data/shadows/, ~12 MB).
- 04_results.py: results.json, cities/streets/open_spaces/towers CSV + GeoJSON for the page.

## Data facts
- OFM building layer features are MultiPolygons grouped by height (no OSM ids, no names), so counts of features mean nothing;
  completeness reported by footprint AREA: render_height == 5 is OpenMapTiles' default when OSM has neither height nor
  levels (41 to 74% of footprint area by city); ceil(k*3.66) = from building:levels; the rest explicit heights.
- Towers: merged parts >= 50 m with footprint >= 300 m2 (thinner ones = spires/chimneys/masts, counted separately).
- Named only where certain from coordinates: The Shard (310 m, -0.0864 51.5044), 22 Bishopsgate (278 m), One Canada Square
  (235 m, -0.0195 51.5049). Reviewer: please verify these identifications. Canary Wharf 275 m and London 242 m (Vauxhall)
  NOT named (unsure which building).
- Ground for "street level" = cells with no building and no water inside the centre box.

## Caveats
- Default 5 m heights: low buildings under-tall, so shadows from ordinary buildings are underestimated; towers are well tagged.
- Terrain 90 m (smooths Castle Rock etc.), no trees, no bridges/overhangs distinguished (render_min_height ignored), clear sky.
- Hours from 10-minute steps; sun position at the centre of each city.
- Data beyond the brief: AWS terrain tiles z10 already in the container (raw_new8) used for the ground surface.

## Done
- 05 figures (day, length, compare, cities, canary, streets, heights, header), 06 page, 07 paper (8 pp), 08 blog (7 figs) +
  Zenodo, 09 README/LICENSE/post, collage (2700x3900). QA 0 console errors at 1280/390 (MapLibre AbortErrors from fast image
  swaps are filtered in page.js; image updates are serialised).
- Scratch (tiles, grids, sun arrays) deleted at the end: rerun 01..03 (~25 min, network for tiles) before 04/05.

## References to verify
- Littlefair, P., King, S., Howlett, G., Ticleanu, C. and Longfield, A. (2022) Site Layout Planning for Daylight and Sunlight:
  A Guide to Good Practice (BR 209), 3rd edition. BRE.
- Spencer, J. W. (1971) Fourier series representation of the position of the sun. Search 2(5), 172.
- Saemundsson, T. (1986) Astronomical refraction. Sky and Telescope 72, 70.
- Tower identifications by coordinates: The Shard 310 m (named in text); 22 Bishopsgate, One Canada Square, Deansgate Square only
  in notes, not in public copy except "towers at the south end of Deansgate".

## Independent review (2026)
- Reran 01 to 04 from scratch (same tile release 20261101_080013_pt): results.json identical to the builder's.
- Hand checks: noon altitude 21 Dec London 15.09 deg geometric (15.14 with refraction), cot 3.71 / 3.70; Edinburgh 10.64 / 10.72, 5.32 / 5.28.
  Shard 310 m: 1,146 m at noon, 1,649 m at noon - 2 h, 1,642 m at noon + 2 h (texts now say "about 1,650 m"; paper gives both).
- Edinburgh 33% with no sun is NOT the terrain: terrain alone 0.7%, buildings on flat ground 28.8%, both 32.6%. Texts corrected
  (results: zero_ter_pc, zero_flatbld_pc, mean_flatbld_h). Terrain still takes about 1.0 h on average (true).
- Slender parts (<300 m2) are in the "without towers" comparison but not in the counts; keeping them changes tower loss by <0.005 h.
- Storey-derived heights overstate residential towers: Landmark Pinnacle (233 m, 75 storeys) = 275 m; South Quay Plaza 1 (215 m,
  68 storeys) = 249 m; London 242 m at Vauxhall = 66 levels. Caveat added; 5 m default also inflates the towers' share (caveat added).
- Saemundsson title corrected to "Atmospheric refraction" (ADS bibcode 1986S&T....72...70S). Spencer 1971 and BR 209 (2022) verified.
