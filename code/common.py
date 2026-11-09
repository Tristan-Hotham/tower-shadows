"""Shared paths, constants and helpers for the tower-shadows study ("Shadows of the giants").

Inputs (read in place, never modified):
  OFM    OpenFreeMap vector tiles (https://tiles.openfreemap.org/planet, OpenMapTiles schema, OpenStreetMap data, ODbL) at
         zoom 14: building (render_height, render_min_height), transportation_name (named streets), landcover and park
         (open spaces), poi (names of parks and squares). Tiles are cached in TILES (outside the repo) and deleted after use.
  DEM    /home/claude/newdata/raw_new8/terrain/tiles/10/{x}/{y}.png: AWS Terrain Tiles, Terrarium encoding
         (height = R*256 + G + B/256 - 32768 m), zoom 10, about 90 m; the lie of the land under each city centre.
Intermediates go to WORK, outside the repo.
"""
import json, gzip, os, re, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEO = os.environ.get("TS_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("TS_FONTS", "/home/claude/ref/fonts")
INK = os.environ.get("TS_INK", "/home/claude/studies/ink-map")
INKFONTS = os.path.join(INK, "fonts", "ttf")
DEM = os.environ.get("TS_DEM", "/home/claude/newdata/raw_new8/terrain/tiles/10")
SCR = os.environ.get("TS_SCRATCH", "/home/claude/scratch/tower-shadows")
TILES = os.path.join(SCR, "tiles")
WORK = os.path.join(SCR, "work")
DATA = os.path.join(ROOT, "data")
IMG = os.path.join(ROOT, "img")
for d in (DATA, IMG, WORK, TILES):
    os.makedirs(d, exist_ok=True)

SLUG = "tower-shadows"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
BYLINE = "Dr Tristan Hotham · Independent researcher · 2026"
UA = {"User-Agent": "tower-shadows-study/1.0 (research; maps.tristanhotham.com)"}
Z = 14
CELL = 5.0                 # metres, grid cell
TOWER_M = 50.0             # a tower: a building part 50 m or more high
BUFFER_M = 1200.0          # buildings are read this far outside each centre, so that their shadows fall in
STEP_MIN = 10              # minutes between sun positions for the hours of sun

# City centres: (key, name, lon0, lon1, lat0, lat1)
CITIES = [
    ("london", "Central London", -0.1750, -0.0550, 51.4750, 51.5270),
    ("canary", "Canary Wharf", -0.0450, 0.0000, 51.4930, 51.5120),
    ("manchester", "Manchester", -2.2620, -2.2180, 53.4680, 53.4920),
    ("birmingham", "Birmingham", -1.9180, -1.8780, 52.4680, 52.4920),
    ("leeds", "Leeds", -1.5700, -1.5250, 53.7880, 53.8060),
    ("liverpool", "Liverpool", -3.0100, -2.9650, 53.3950, 53.4180),
    ("glasgow", "Glasgow", -4.2800, -4.2300, 55.8500, 55.8700),
    ("edinburgh", "Edinburgh", -3.2150, -3.1700, 55.9400, 55.9580),
]
CNAME = {c[0]: c[1] for c in CITIES}
DATES = [("dec", "21 December", 2026, 12, 21), ("mar", "20 March", 2026, 3, 20), ("jun", "21 June", 2026, 6, 21)]
DNAME = {d[0]: d[1] for d in DATES}


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def nonan(v):
    if isinstance(v, float) and (v != v or v in (float("inf"), float("-inf"))):
        return None
    if isinstance(v, list):
        return [nonan(x) for x in v]
    if isinstance(v, dict):
        return {k: nonan(x) for k, x in v.items()}
    if hasattr(v, "item"):
        return nonan(v.item())
    return v


def jsave(obj, path, indent=None):
    obj = dash(nonan(obj))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, allow_nan=False, indent=indent, separators=None if indent else (",", ":"))


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "hm": return hm(v)
    raise ValueError(f)


def hm(hours):
    m = int(round(float(hours) * 60))
    h, mm = divmod(m, 60)
    return f"{h} h {mm:02d} min" if h else f"{mm} min"


# ---------- the sun (NOAA general solar position equations, after Spencer 1971)
def sun_position(lat, lon, year, month, day, hour_utc):
    """apparent solar altitude and azimuth (degrees, azimuth clockwise from true north) at a UTC time"""
    import numpy as np
    import datetime as dt
    doy = dt.date(year, month, day).timetuple().tm_yday
    hour_utc = np.asarray(hour_utc, float)
    g = 2 * np.pi / 365 * (doy - 1 + (hour_utc - 12) / 24)
    eqt = 229.18 * (0.000075 + 0.001868 * np.cos(g) - 0.032077 * np.sin(g) - 0.014615 * np.cos(2 * g) - 0.040849 * np.sin(2 * g))
    decl = (0.006918 - 0.399912 * np.cos(g) + 0.070257 * np.sin(g) - 0.006758 * np.cos(2 * g) + 0.000907 * np.sin(2 * g)
            - 0.002697 * np.cos(3 * g) + 0.00148 * np.sin(3 * g))
    tst = hour_utc * 60 + eqt + 4 * lon
    ha = np.radians(tst / 4 - 180)
    p = np.radians(lat)
    cz = np.sin(p) * np.sin(decl) + np.cos(p) * np.cos(decl) * np.cos(ha)
    zen = np.arccos(np.clip(cz, -1, 1))
    alt = 90 - np.degrees(zen)
    az = np.degrees(np.arctan2(np.sin(ha), np.cos(ha) * np.sin(p) - np.tan(decl) * np.cos(p))) + 180
    # refraction (Saemundsson), small near noon, about half a degree at the horizon
    R = 1.02 / np.tan(np.radians(alt + 10.3 / (alt + 5.11))) / 60
    alt_app = np.where(alt > -1, alt + R, alt)
    return alt_app, az % 360, np.degrees(decl), eqt
