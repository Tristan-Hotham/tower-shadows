**Title:** [OC] On the shortest day the Shard casts a shadow 1,146 m long at noon. I traced the winter sun through eight UK city centres to see who loses it to towers

**Body:**

Building heights from OpenStreetMap on a 5 m grid, the sun every 10 minutes on 21 December, the equinox and 21 June, each city as built, without its towers (50 m+) and without any buildings.

- On 21 December a shadow at noon is 3.7 times the height in London, 5.3 in Edinburgh.
- The ordinary dense city takes most of the winter sun: central London's open ground gets 2.8 h of a 7.7 h day; removing the towers would give back only 0.18 h.
- Canary Wharf is the exception: towers take 0.76 h from the average square metre, and 26% of open ground loses an hour or more.
- Darkest centre: Edinburgh (33% of open ground with no direct sun), with almost no towers: ordinary buildings under a sun only 10.7 degrees up at noon (the hills alone would leave under 1% in shade all day).
- Caveat: 41 to 74% of building footprint has no height in OSM and is drawn 5 m tall, so real streets are darker and the towers' share is if anything a little high.

Interactive map (time slider, three dates, tap a tower for its shadow length): https://maps.tristanhotham.com/tower-shadows/

**Source comment:**

Data: OpenStreetMap contributors (ODbL) via OpenFreeMap vector tiles; AWS Terrain Tiles. Tools: Python (numpy, numba, shapely, rasterio, matplotlib), MapLibre. Sun: NOAA solar equations. Paper and code: https://github.com/Tristan-Hotham/tower-shadows
