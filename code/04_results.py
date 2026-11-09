"""Step 4: results.json (every number quoted anywhere) and the derived data.
Per city centre: completeness of heights, towers, sun at street level on the three dates (with all buildings, without the
towers, terrain only), the most overshadowed named streets and open spaces, and the noon shadow of every tower.
Output: data/results.json, data/cities.csv, data/streets.csv, data/open_spaces.csv, data/towers.csv,
data/streets.geojson, data/open_spaces.geojson, data/towers.json (page), data/shadow_meta.json (page)
"""
import numpy as np, pandas as pd
from pyproj import Transformer
from shapely.geometry import mapping
from rasterio import features as rfeat
from rasterio.transform import from_origin
from common import *

META = jload(f"{WORK}/sun_meta.json")
LEVELS = {math.ceil(k * 3.66) for k in range(1, 120)}
MIN_TOWER_AREA = 300.0         # m2: thinner parts of 50 m or more are spires, chimneys and masts
MIN_STREET_M, MIN_OPEN_M2 = 150.0, 2000.0
R = {"cities": {}, "dates": {d[0]: d[1] for d in DATES}, "cell_m": CELL, "tower_m": TOWER_M, "step_min": STEP_MIN,
     "min_tower_area": MIN_TOWER_AREA, "tiles": jload(f"{WORK}/tiles_version.json")["version"]}
ST_ALL, OP_ALL, TW_ALL, CI = [], [], [], []
tw_json = []
for key, cname, *_ in CITIES:
    g = np.load(f"{WORK}/{key}_grid.npz"); v = pd.read_pickle(f"{WORK}/{key}_vec.pkl")
    r0, r1, c0, c1 = g["box"]; dx0, dx1, dy0, dy1 = g["dom"]
    H = g["H"][r0:r1, c0:c1]; Wm = g["W"][r0:r1, c0:c1]; Sm = g["S"][r0:r1, c0:c1]
    inv = Transformer.from_crs(v["crs"], 4326, always_xy=True).transform
    bx0, bx1, by0, by1 = v["box"]
    ground = (H == 0) & (Wm == 0)
    m = META[key]
    sun = {d: dict(np.load(f"{WORK}/{key}_{d}_sun.npz")) for d, *_ in DATES}
    # --- heights
    B = v["B"]; B = B[B.cx.between(bx0, bx1) & B.cy.between(by0, by1)]
    a = B.area.sum()
    comp = {"footprint_km2": round(a / 1e6, 2), "default_pc": round(100 * B[B.h == 5].area.sum() / a, 1),
            "levels_pc": round(100 * B[(B.h != 5) & B.h.isin(LEVELS)].area.sum() / a, 1),
            "other_pc": round(100 * B[(B.h != 5) & ~B.h.isin(LEVELS)].area.sum() / a, 1),
            "built_pc": round(100 * (H > 0).mean(), 1), "box_km2": round((bx1 - bx0) * (by1 - by0) / 1e6, 1)}
    # --- towers
    T = v["TW"]; T = T[T.in_box].copy()
    slender = int((T.area < MIN_TOWER_AREA).sum())
    T = T[T.area >= MIN_TOWER_AREA].sort_values("h", ascending=False)
    dec = m["dates"]["dec"]
    k_noon = 1 / math.tan(math.radians(dec["noon_alt"]))
    for d in ("dec", "mar", "jun"):
        T[f"noon_{d}_m"] = T.h / math.tan(math.radians(m["dates"][d]["noon_alt"]))
    # the low sun two hours either side of noon in December
    # two hours before and after noon (the morning and afternoon values differ by under 0.5%)
    a2, _, _, _ = sun_position(m["lat"], m["lon"], 2026, 12, 21, dec["noon_utc"] - 2)
    a2b, _, _, _ = sun_position(m["lat"], m["lon"], 2026, 12, 21, dec["noon_utc"] + 2)
    T["dec_2h_am_m"] = T.h / math.tan(math.radians(float(a2)))
    T["dec_2h_pm_m"] = T.h / math.tan(math.radians(float(a2b)))
    T["dec_2h_m"] = (T.dec_2h_am_m + T.dec_2h_pm_m) / 2
    T["city"] = key
    TW_ALL.append(T.drop(columns=["geom"]))
    for t in T.itertuples():
        tw_json.append([key, round(t.lon, 5), round(t.lat, 5), round(t.h), round(t.area), round(t.noon_dec_m), round(t.noon_mar_m), round(t.noon_jun_m)])
    # --- sun at street level (open ground: not building, not water)
    city = {"name": cname, "heights": comp, "towers50": int(len(T)), "towers100": int((T.h >= 100).sum()), "towers150": int((T.h >= 150).sum()),
            "slender50": slender, "tallest_m": float(T.h.iloc[0]) if len(T) else 0.0,
            "tallest": [{"h": float(t.h), "lon": round(t.lon, 4), "lat": round(t.lat, 4), "noon_dec_m": round(t.noon_dec_m), "dec_2h_m": round(t.dec_2h_m), "dec_2h_am_m": round(t.dec_2h_am_m), "dec_2h_pm_m": round(t.dec_2h_pm_m)} for t in T.head(5).itertuples()],
            "noon_ratio_dec": round(k_noon, 2), "noon_alt": {d: round(m["dates"][d]["noon_alt"], 1) for d in ("dec", "mar", "jun")}, "dates": {}}
    for d, dname, *_ in DATES:
        s = sun[d]; flat = m["dates"][d]["flat_h"]
        al, lo, te = s["all"][ground] / 60, s["low"][ground] / 60, s["ter"][ground] / 60
        city["dates"][d] = {"flat_h": round(flat, 2), "mean_all_h": round(al.mean(), 2), "mean_low_h": round(lo.mean(), 2), "mean_ter_h": round(te.mean(), 2),
                            "lost_bld_h": round((te - al).mean(), 2), "lost_tow_h": round((lo - al).mean(), 2),
                            "zero_pc": round(100 * (al == 0).mean(), 1), "zero_low_pc": round(100 * (lo == 0).mean(), 1),
                            "zero_ter_pc": round(100 * (te == 0).mean(), 1),
                            "lt1_pc": round(100 * (al < 1).mean(), 1), "tow_lost1h_pc": round(100 * ((lo - al) >= 1).mean(), 1),
                            "tow_any_pc": round(100 * ((lo - al) > 0).mean(), 1),
                            "half_lost_pc": round(100 * (al < 0.5 * te).mean(), 1),
                            "sunrise_utc": m["dates"][d]["sunrise_utc"], "sunset_utc": m["dates"][d]["sunset_utc"]}
    from shadow import shade
    Hf = g["H"].astype(np.float32); tt = np.arange(0, 24 * 60, STEP_MIN) / 60.0
    altd, azd, _, _ = sun_position(m["lat"], m["lon"], 2026, 12, 21, tt + STEP_MIN / 120.0)
    sflat = np.zeros(H.shape, np.uint16)
    for a_, z_ in zip(altd[altd > 0], azd[altd > 0]):
        sflat += (~shade(Hf, float(a_), float(z_), CELL)[r0:r1, c0:c1]).astype(np.uint16) * STEP_MIN
    city["dates"]["dec"]["zero_flatbld_pc"] = round(100 * (sflat[ground] == 0).mean(), 1)
    city["dates"]["dec"]["mean_flatbld_h"] = round(float((sflat[ground] / 60).mean()), 2)
    R["cities"][key] = city
    CI.append({"city": key, "name": cname, **{f"{d}_{k}": v2 for d in city["dates"] for k, v2 in city["dates"][d].items()},
               "towers50": city["towers50"], "towers100": city["towers100"], "tallest_m": city["tallest_m"], **{f"h_{k}": v2 for k, v2 in comp.items()}})
    # --- streets
    STv = v["ST"].reset_index(drop=True)
    ids = Sm[ground]
    rows = []
    for d in ("dec", "mar", "jun"):
        s = sun[d]
        for k in ("all", "low", "ter"):
            vals = s[k][ground].astype(float)
            sums = np.bincount(ids, weights=vals, minlength=len(STv) + 1)
            cnt = np.bincount(ids, minlength=len(STv) + 1)
            STv[f"{d}_{k}"] = (sums[1:] / np.maximum(cnt[1:], 1) / 60)
            STv["cells"] = cnt[1:]
    from shapely.geometry import box as sbox
    bb = sbox(bx0, by0, bx1, by1)
    STv["len_in"] = [geom.intersection(bb).length for geom in STv.geom]
    STv = STv[(STv.cls != "path") & (STv.len_in >= MIN_STREET_M) & (STv.cells >= 20)].copy()
    # one row per name: keep the longest class of a name
    STv = STv.sort_values("len_in", ascending=False).drop_duplicates("name")
    STv["city"] = key
    STv["dec_lost_tow"] = STv.dec_low - STv.dec_all; STv["dec_lost_bld"] = STv.dec_ter - STv.dec_all
    ST_ALL.append(STv)
    # --- open spaces
    OP = v["OP"]
    if len(OP):
        OP = OP[OP.geom.apply(lambda q: q.intersects(bb))].reset_index(drop=True)
        tr = from_origin(bx0, by1, CELL, CELL)
        Pm = rfeat.rasterize(((q, i + 1) for i, q in enumerate(OP.geom)), out_shape=H.shape, transform=tr, fill=0, dtype="int32") if len(OP) else np.zeros(H.shape, "int32")
        pid = Pm[ground]
        for d in ("dec", "mar", "jun"):
            for k in ("all", "low", "ter"):
                vals = sun[d][k][ground].astype(float)
                sums = np.bincount(pid, weights=vals, minlength=len(OP) + 1); cnt = np.bincount(pid, minlength=len(OP) + 1)
                OP[f"{d}_{k}"] = sums[1:] / np.maximum(cnt[1:], 1) / 60
                OP["cells"] = cnt[1:]
        OP["area_in"] = OP.cells * CELL * CELL
        OP = OP[(OP.area_in >= MIN_OPEN_M2)].copy()
        OP["city"] = key
        OP["dec_lost_tow"] = OP.dec_low - OP.dec_all; OP["dec_lost_bld"] = OP.dec_ter - OP.dec_all
        OP_ALL.append(OP)
    R["cities"][key]["streets"] = int(len(STv)); R["cities"][key]["open_spaces"] = int(len(OP))

import shapely
ST = pd.concat(ST_ALL, ignore_index=True); OPa = pd.concat(OP_ALL, ignore_index=True); TW = pd.concat(TW_ALL, ignore_index=True)
# ---------------- city-wide comparisons
order = sorted(R["cities"], key=lambda k: -R["cities"][k]["dates"]["dec"]["lost_tow_h"])
R["order_tower_loss"] = order
R["n_towers"] = int(len(TW)); R["n_towers100"] = int((TW.h >= 100).sum())
R["n_streets"] = int(len(ST)); R["n_open"] = int(len(OPa))
lon = R["cities"]["london"]
R["london_noon_ratio"] = lon["noon_ratio_dec"]
# without refraction (geometric altitude 90 - latitude + declination)
R["london_noon_ratio_geom"] = round(1 / math.tan(math.radians(90 - META["london"]["lat"] + META["london"]["dates"]["dec"]["decl"])), 2)
R["edinburgh_noon_ratio_geom"] = round(1 / math.tan(math.radians(90 - META["edinburgh"]["lat"] + META["edinburgh"]["dates"]["dec"]["decl"])), 2)
R["edinburgh_noon_ratio"] = R["cities"]["edinburgh"]["noon_ratio_dec"]
R["shard"] = lon["tallest"][0]
R["shard"]["dec_2h_r10"] = int(math.floor(float(TW[TW.city == "london"].sort_values("h").dec_2h_m.iloc[-1]) / 10 + 0.5) * 10)
R["shard"]["noon_dec_km"] = round(R["shard"]["noon_dec_m"] / 1000, 2); R["shard"]["dec_2h_km"] = round(R["shard"]["dec_2h_m"] / 1000, 2)
R["shard"]["noon_jun_m"] = round(R["shard"]["h"] / math.tan(math.radians(lon["noon_alt"]["jun"])))
R["shard"]["noon_mar_m"] = round(R["shard"]["h"] / math.tan(math.radians(lon["noon_alt"]["mar"])))
R["hypo300"] = {"london_dec_m": round(300 * lon["noon_ratio_dec"]), "ratio": lon["noon_ratio_dec"]}
# the most overshadowed streets and squares (21 December): least sun, and most lost to towers
STs = ST.copy()
STs["name_city"] = STs.name + ", " + STs.city.map(CNAME)
cols = ["name", "city", "cls", "len_in", "dec_all", "dec_low", "dec_ter", "dec_lost_tow", "dec_lost_bld", "mar_all", "mar_low", "jun_all", "jun_low"]
R["streets_least"] = [{k: (round(float(r[k]), 2) if isinstance(r[k], (float, np.floating)) else r[k]) for k in cols}
                      for _, r in STs[STs.len_in >= 250].sort_values("dec_all").head(12).iterrows()]
R["streets_tow"] = [{k: (round(float(r[k]), 2) if isinstance(r[k], (float, np.floating)) else r[k]) for k in cols}
                    for _, r in STs.sort_values("dec_lost_tow", ascending=False).head(12).iterrows()]
named = OPa[OPa.name.notna()].copy()
ocols = ["name", "city", "area_in", "dec_all", "dec_low", "dec_ter", "dec_lost_tow", "dec_lost_bld", "mar_all", "jun_all"]
R["open_least"] = [{k: (round(float(r[k]), 2) if isinstance(r[k], (float, np.floating)) else r[k]) for k in ocols}
                   for _, r in named.sort_values("dec_all").head(12).iterrows()]
R["open_tow"] = [{k: (round(float(r[k]), 2) if isinstance(r[k], (float, np.floating)) else r[k]) for k in ocols}
                 for _, r in named.sort_values("dec_lost_tow", ascending=False).head(12).iterrows()]
R["towers_longest"] = [{"city": t.city, "h": float(t.h), "lon": round(t.lon, 4), "lat": round(t.lat, 4), "noon_dec_m": round(t.noon_dec_m), "dec_2h_m": round(t.dec_2h_m)}
                       for t in TW.sort_values("noon_dec_m", ascending=False).head(10).itertuples()]
means = {k: R["cities"][k]["dates"]["dec"]["mean_all_h"] for k in R["cities"]}
R["min_mean_h"], R["max_mean_h"] = min(means.values()), max(means.values())
fl = [R["cities"][k]["dates"]["dec"]["flat_h"] for k in R["cities"]]
R["min_flat_h"], R["max_flat_h"] = min(fl), max(fl)
R["streets_zero_dec"] = int((ST.dec_all < 0.05).sum()); R["streets_lt1_dec"] = int((ST.dec_all < 1).sum())
R["streets_tow_1h"] = int((ST.dec_lost_tow >= 1).sum())
# ---------------- files
pd.DataFrame(CI).to_csv(f"{DATA}/cities.csv", index=False)
fl = lambda df, cs: df[cs].round(3)
ST[["city", "name", "cls", "len_in", "dec_all", "dec_low", "dec_ter", "mar_all", "mar_low", "mar_ter", "jun_all", "jun_low", "jun_ter"]].round(3).to_csv(f"{DATA}/streets.csv", index=False)
OPa[["city", "name", "area_in", "dec_all", "dec_low", "dec_ter", "mar_all", "mar_low", "mar_ter", "jun_all", "jun_low", "jun_ter"]].round(3).to_csv(f"{DATA}/open_spaces.csv", index=False)
TW[["city", "h", "area", "lon", "lat", "ground", "n_parts", "noon_dec_m", "noon_mar_m", "noon_jun_m", "dec_2h_m", "dec_2h_am_m", "dec_2h_pm_m"]].round(3).to_csv(f"{DATA}/towers.csv", index=False)
# GeoJSON for the page (lon/lat, simplified)
crs_of = {k: pd.read_pickle(f"{WORK}/{k}_vec.pkl")["crs"] for k, *_ in CITIES}


def to_ll(geom, key, tol=2.0):
    inv = Transformer.from_crs(crs_of[key], 4326, always_xy=True).transform
    g = geom.simplify(tol)
    return shapely.transform(g, lambda a: np.c_[inv(a[:, 0], a[:, 1])])


def rnd(o):
    if isinstance(o, float): return round(o, 5)
    if isinstance(o, (list, tuple)): return [rnd(x) for x in o]
    if isinstance(o, dict): return {k: rnd(x) for k, x in o.items()}
    return o


fs = [{"type": "Feature", "properties": {"n": r.name, "c": r.city, "d": round(r.dec_all, 2), "dl": round(r.dec_low, 2), "dt": round(r.dec_ter, 2),
                                         "m": round(r.mar_all, 2), "j": round(r.jun_all, 2)}, "geometry": rnd(mapping(to_ll(r.geom, r.city)))} for r in ST.itertuples()]
jsave({"type": "FeatureCollection", "features": fs}, f"{DATA}/streets.geojson")
fs = [{"type": "Feature", "properties": {"n": r.name if isinstance(r.name, str) else "", "c": r.city, "a": round(r.area_in), "d": round(r.dec_all, 2), "dl": round(r.dec_low, 2),
                                         "dt": round(r.dec_ter, 2), "m": round(r.mar_all, 2), "j": round(r.jun_all, 2)}, "geometry": rnd(mapping(to_ll(r.geom, r.city, 3.0)))} for r in OPa.itertuples()]
jsave({"type": "FeatureCollection", "features": fs}, f"{DATA}/open_spaces.geojson")
jsave({"towers": tw_json}, f"{DATA}/towers.json")
jsave({k: {"name": META[k]["name"], "corners": META[k]["corners"], "shape": META[k]["shape"], "lat": META[k]["lat"], "lon": META[k]["lon"],
           "dates": {d: {kk: META[k]["dates"][d][kk] for kk in ("hours", "alt", "az", "flat_h", "sunrise_utc", "sunset_utc", "noon_alt", "tz")} for d in META[k]["dates"]}}
       for k in META}, f"{DATA}/shadow_meta.json")
e = R["cities"]["edinburgh"]["dates"]["dec"]
assert e["zero_ter_pc"] < 1 and e["zero_flatbld_pc"] > 25, e      # Edinburgh's sunless ground is the buildings', not the land's
assert abs(R["shard"]["dec_2h_am_m"] - R["shard"]["dec_2h_pm_m"]) < 15
jsave(R, f"{DATA}/results.json", indent=1)
for k in R["cities"]:
    c = R["cities"][k]; d = c["dates"]["dec"]
    print(f"{k:11s} tow {c['towers50']:3d} hdef {c['heights']['default_pc']:5.1f}% Dec mean {d['mean_all_h']:.2f}/{d['mean_low_h']:.2f}/{d['mean_ter_h']:.2f} flat {d['flat_h']:.2f} zero {d['zero_pc']}% towlost {d['lost_tow_h']} tow1h {d['tow_lost1h_pc']}% streets {c['streets']} open {c['open_spaces']}")
print("shard", R["shard"], "ratio", R["london_noon_ratio"])
for s in R["streets_least"][:8]: print("least", s["name"], s["city"], s["dec_all"], s["dec_ter"], round(s["len_in"]))
for s in R["streets_tow"][:8]: print("tow", s["name"], s["city"], s["dec_lost_tow"], s["dec_all"])
for s in R["open_least"][:6]: print("open least", s["name"], s["city"], s["dec_all"], s["area_in"])
for s in R["open_tow"][:6]: print("open tow", s["name"], s["city"], s["dec_lost_tow"], s["dec_all"])
for k in ("streets.geojson", "open_spaces.geojson", "towers.json"):
    print(k, os.path.getsize(f"{DATA}/{k}") // 1024, "KB")
