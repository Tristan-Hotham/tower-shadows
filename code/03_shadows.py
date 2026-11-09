"""Step 3: shadows through the day on 21 December, 20 March and 21 June for each city centre.

Sun positions every STEP_MIN minutes from sunrise to sunset (NOAA solar position at the centre of each city, with
refraction). Three surfaces: terrain only (G), terrain and buildings under 50 m (G + L, the city without its towers), and
terrain and all buildings (G + H). For every cell: minutes of direct sun under each surface. For the map: the shadows on
each whole hour of local clock time (GMT in December and March, BST in June) as bit planes, one bit per hour, for all
buildings and for the share cast by towers alone (in shadow with the towers, in sun without them).
Output: WORK/<city>_<date>_sun.npz; data/shadows/<city>_<date>_all.png and _tow.png (RGB, bit k of R+256G+65536B = hour k
in that date's list), data/shadows/<city>_<date>_hours.png (hours of direct sun, palette); WORK/sun_meta.json
"""
import sys, time
import numpy as np, pandas as pd
from PIL import Image
from pyproj import Transformer
from common import *
from shadow import shade

OUT = os.path.join(DATA, "shadows"); os.makedirs(OUT, exist_ok=True)
HOURS_PAL = ["#1F1838", "#3B2F63", "#5B4A8B", "#7E6CA8", "#A99BC0", "#D9C9A3", "#EBCB7A", "#F0B23A", "#E39A2C"]
meta = {}
t0 = time.time()
for key, cname, lo0, lo1, la0, la1 in CITIES:
    g = np.load(f"{WORK}/{key}_grid.npz")
    H, L, G, Wm = g["H"], g["L"], g["G"], g["W"]
    r0, r1, c0, c1 = g["box"]
    latc, lonc = g["crs"]
    dx0, dx1, dy0, dy1 = g["dom"]
    crs = f"+proj=tmerc +lat_0={latc} +lon_0={lonc} +k=1 +x_0=0 +y_0=0 +ellps=WGS84 +units=m +no_defs"
    inv = Transformer.from_crs(crs, 4326, always_xy=True).transform
    bx0, bx1 = dx0 + c0 * CELL, dx0 + c1 * CELL
    by1, by0 = dy1 - r0 * CELL, dy1 - r1 * CELL
    corners = [list(inv(bx0, by1)), list(inv(bx1, by1)), list(inv(bx1, by0)), list(inv(bx0, by0))]   # NW, NE, SE, SW
    surf = {"ter": G.astype(np.float32), "low": (G + L).astype(np.float32), "all": (G + H).astype(np.float32)}
    meta[key] = {"name": cname, "corners": corners, "shape": [int(r1 - r0), int(c1 - c0)], "lat": float(latc), "lon": float(lonc), "dates": {}}
    for dkey, dname, Y, M, D in DATES:
        tz = 1 if dkey == "jun" else 0
        tt = np.arange(0, 24 * 60, STEP_MIN) / 60.0
        alt, az, decl, eqt = sun_position(latc, lonc, Y, M, D, tt + STEP_MIN / 120.0)    # centre of each step
        day = alt > 0
        sun = {k: np.zeros((r1 - r0, c1 - c0), np.uint16) for k in surf}
        for a, z in zip(alt[day], az[day]):
            for k, S in surf.items():
                sh = shade(S, float(a), float(z), CELL)[r0:r1, c0:c1]
                sun[k] += (~sh).astype(np.uint16) * STEP_MIN
        # whole hours of local clock time with the sun up, for the map
        hrs = []
        for hh in range(0, 24):
            a, z, _, _ = sun_position(latc, lonc, Y, M, D, hh - tz)
            if float(a) > 0.5:
                hrs.append((hh, float(a), float(z)))
        ball = np.zeros((r1 - r0, c1 - c0), np.uint32); btow = np.zeros_like(ball)
        for k, (hh, a, z) in enumerate(hrs):
            sa = shade(surf["all"], a, z, CELL)[r0:r1, c0:c1]
            sl = shade(surf["low"], a, z, CELL)[r0:r1, c0:c1]
            ball |= (sa.astype(np.uint32) << k)
            btow |= ((sa & ~sl).astype(np.uint32) << k)
        for nm, b in (("all", ball), ("tow", btow)):
            rgb = np.stack([b & 255, (b >> 8) & 255, (b >> 16) & 255], -1).astype(np.uint8)
            Image.fromarray(rgb, "RGB").save(f"{OUT}/{key}_{dkey}_all.png" if nm == "all" else f"{OUT}/{key}_{dkey}_tow.png", optimize=True)
        # hours of direct sun (palette PNG; buildings transparent)
        hours = sun["all"] / 60.0
        flat = day.sum() * STEP_MIN / 60.0
        bins = np.minimum((hours / max(flat, 1e-6) * 8).astype(int), 8)
        idx = (bins + 1).astype(np.uint8)
        bld = H[r0:r1, c0:c1] > 0
        idx[bld] = 0
        im = Image.fromarray(idx, "P")
        pal = [0, 0, 0]
        for c in HOURS_PAL:
            pal += [int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)]
        im.putpalette(pal + [0] * (768 - len(pal)))
        im.info["transparency"] = 0
        im.save(f"{OUT}/{key}_{dkey}_hours.png", optimize=True, transparency=0)
        # sunrise and sunset (apparent upper limb ignored: centre of the disc)
        fine = np.arange(0, 24 * 60) / 60.0
        af, azf, _, _ = sun_position(latc, lonc, Y, M, D, fine)
        up = np.where(af > 0)[0]
        noon_i = int(np.argmax(af))
        np.savez_compressed(f"{WORK}/{key}_{dkey}_sun.npz", **sun)
        meta[key]["dates"][dkey] = {"hours": [h[0] for h in hrs], "alt": [round(h[1], 2) for h in hrs], "az": [round(h[2], 2) for h in hrs],
                                    "flat_h": round(float(flat), 3), "sunrise_utc": float(fine[up[0]]), "sunset_utc": float(fine[up[-1]]),
                                    "noon_utc": float(fine[noon_i]), "noon_alt": float(af[noon_i]), "noon_az": float(azf[noon_i]),
                                    "tz": tz, "n_steps": int(day.sum()), "decl": float(np.atleast_1d(decl)[0])}
        print(key, dkey, len(hrs), "hours", f"{time.time() - t0:.0f}s", file=sys.stderr)
jsave(meta, f"{WORK}/sun_meta.json", indent=1)
