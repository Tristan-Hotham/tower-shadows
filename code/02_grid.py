"""Step 2: for each city centre, a 5 m grid in a local transverse Mercator projection (true north up) holding
  H   building height (m) from OpenMapTiles render_height (the tallest part over each cell)
  L   the same for parts under 50 m only (the city without its towers)
  T   the same for tower parts only (render_height >= 50 m)
  G   ground height (m) from the AWS Terrain Tiles (zoom 10, bilinear)
  W   water; P open space (parks, gardens, squares, recreation grounds); S named streets (4 m either side of the line)
over the centre plus a buffer of BUFFER_M, so that buildings outside the centre can cast shadows into it.
Also: every building part (for the completeness of heights), towers as merged footprints, streets and open spaces as vectors.
Output: WORK/<city>_grid.npz, WORK/<city>_vec.pkl
"""
import sys, glob
import shapely
import numpy as np, pandas as pd
import mapbox_vector_tile as mvt
from PIL import Image
from pyproj import Transformer
from shapely.geometry import shape, Polygon, MultiPolygon, LineString, box, Point
from shapely.ops import transform as stransform, unary_union
from shapely.strtree import STRtree
from rasterio import features as rfeat
from rasterio.transform import from_origin
from common import *

n = 2 ** Z
OPEN = {"park", "garden", "recreation_ground", "village_green", "common", "playground", "grass"}   # landcover subclasses
OPEN_KEEP = {"park", "garden", "recreation_ground", "village_green", "common"}
ROADS = {"motorway", "trunk", "primary", "secondary", "tertiary", "minor", "service", "path"}


def txy(lon, lat):
    return (lon + 180) / 360 * n, (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n


def tile_ll(x, y, px, py, ext=4096):
    X = x + px / ext; Y = y + py / ext
    lon = X / n * 360 - 180
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * Y / n))))
    return lon, lat


def dem_sampler():
    cache = {}
    def tile(x, y):
        if (x, y) not in cache:
            f = f"{DEM}/{x}/{y}.png"
            a = np.asarray(Image.open(f).convert("RGB"), float)
            cache[(x, y)] = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
        return cache[(x, y)]
    def h(lon, lat):
        N = 256 * 2 ** 10
        X = (np.asarray(lon) + 180) / 360 * N
        lr = np.radians(np.asarray(lat))
        Y = (1 - np.log(np.tan(lr) + 1 / np.cos(lr)) / np.pi) / 2 * N
        X -= 0.5; Y -= 0.5
        x0, y0 = np.floor(X).astype(int), np.floor(Y).astype(int)
        fx, fy = X - x0, Y - y0
        out = np.zeros(X.shape)
        def v(xx, yy):
            r = np.zeros(xx.shape)
            for (tx, ty) in set(zip((xx // 256).ravel().tolist(), (yy // 256).ravel().tolist())):
                m = (xx // 256 == tx) & (yy // 256 == ty)
                r[m] = tile(tx, ty)[yy[m] % 256, xx[m] % 256]
            return r
        out = (v(x0, y0) * (1 - fx) * (1 - fy) + v(x0 + 1, y0) * fx * (1 - fy) + v(x0, y0 + 1) * (1 - fx) * fy + v(x0 + 1, y0 + 1) * fx * fy)
        return out
    return h


DEMH = dem_sampler()
summary = jload(f"{WORK}/grid_summary.json") if os.path.exists(f"{WORK}/grid_summary.json") else {}
for key, cname, lo0, lo1, la0, la1 in CITIES:
    if os.path.exists(f"{WORK}/{key}_grid.npz") and key in summary and not os.environ.get("TS_REDO"):
        continue
    lonc, latc = (lo0 + lo1) / 2, (la0 + la1) / 2
    crs = f"+proj=tmerc +lat_0={latc} +lon_0={lonc} +k=1 +x_0=0 +y_0=0 +ellps=WGS84 +units=m +no_defs"
    fwd = Transformer.from_crs(4326, crs, always_xy=True).transform
    inv = Transformer.from_crs(crs, 4326, always_xy=True).transform
    # the centre box in metres (its corners projected) and the domain with the buffer
    cx, cy = fwd(np.array([lo0, lo1, lo0, lo1]), np.array([la0, la0, la1, la1]))
    bx0, bx1, by0, by1 = math.floor(min(cx) / CELL) * CELL, math.ceil(max(cx) / CELL) * CELL, math.floor(min(cy) / CELL) * CELL, math.ceil(max(cy) / CELL) * CELL
    dx0, dx1, dy0, dy1 = bx0 - BUFFER_M, bx1 + BUFFER_M, by0 - BUFFER_M, by1 + BUFFER_M
    W_, H_ = int(round((dx1 - dx0) / CELL)), int(round((dy1 - dy0) / CELL))
    tr = from_origin(dx0, dy1, CELL, CELL)
    dom = box(dx0, dy0, dx1, dy1)
    # tiles
    dlat = (BUFFER_M + 300) / 111195; dlon = dlat / math.cos(math.radians(latc))
    tx0, ty1 = txy(lo0 - dlon, la0 - dlat); tx1, ty0 = txy(lo1 + dlon, la1 + dlat)
    blds, streets, opens, parks_named, water = [], [], [], [], []
    for x in range(int(tx0), int(tx1) + 1):
        for y in range(int(ty0), int(ty1) + 1):
            d = mvt.decode(open(f"{TILES}/{x}_{y}.pbf", "rb").read(), default_options={"y_coord_down": True})
            tb = box(*[c for c in fwd(*tile_ll(x, y, 0, 4096))] + [c for c in fwd(*tile_ll(x, y, 4096, 0))])  # tile extent in metres
            def proj(g, x=x, y=y):
                def f(a):
                    X = x + a[:, 0] / 4096; Y = y + a[:, 1] / 4096
                    lon = X / n * 360 - 180
                    lat = np.degrees(np.arctan(np.sinh(np.pi * (1 - 2 * Y / n))))
                    ex, ny = fwd(lon, lat)
                    return np.c_[ex, ny]
                return shapely.transform(g, f)
            for L, sink in (("building", blds), ("transportation_name", streets), ("landcover", opens), ("park", opens), ("water", water), ("poi", parks_named)):
                lay = d.get(L)
                if not lay:
                    continue
                for ft in lay["features"]:
                    p = ft["properties"]
                    if L == "landcover" and p.get("subclass") not in OPEN_KEEP:
                        continue
                    if L == "park" and p.get("class") not in ("park",):
                        continue
                    if L == "poi" and not (p.get("class") in ("park", "garden") and p.get("name")):
                        continue
                    if L == "transportation_name" and not (p.get("name") and p.get("class") in ROADS):
                        continue
                    try:
                        g = proj(shape(ft["geometry"]))
                    except Exception:
                        continue
                    if not g.is_valid:
                        g = g.buffer(0)
                    g = g.intersection(tb)            # tiles carry a buffer; keep each tile's own share
                    if g.is_empty or not g.intersects(dom):
                        continue
                    sink.append((g, p, (x, y)))
    # ------------- building heights
    B = pd.DataFrame([dict(h=float(p.get("render_height", 0) or 0), h0=float(p.get("render_min_height", 0) or 0), area=g.area, geom=g, tile=t)
                      for g, p, t in blds if g.geom_type in ("Polygon", "MultiPolygon")])
    B = B[B.h > 0].sort_values("h")
    H = rfeat.rasterize(((g, h) for g, h in zip(B.geom, B.h)), out_shape=(H_, W_), transform=tr, fill=0, dtype="float32")
    Bl = B[B.h < TOWER_M]
    L = rfeat.rasterize(((g, h) for g, h in zip(Bl.geom, Bl.h)), out_shape=(H_, W_), transform=tr, fill=0, dtype="float32")
    Bt = B[B.h >= TOWER_M]
    T = rfeat.rasterize(((g, h) for g, h in zip(Bt.geom, Bt.h)), out_shape=(H_, W_), transform=tr, fill=0, dtype="float32") if len(Bt) else np.zeros((H_, W_), "float32")
    # ------------- ground
    xs = dx0 + (np.arange(0, W_, 8) + 0.5) * CELL; ys = dy1 - (np.arange(0, H_, 8) + 0.5) * CELL
    XX, YY = np.meshgrid(xs, ys)
    lon, lat = inv(XX, YY)
    g8 = DEMH(lon, lat)
    from scipy.ndimage import zoom
    G = zoom(g8, (H_ / g8.shape[0], W_ / g8.shape[1]), order=1).astype("float32")[:H_, :W_]
    # ------------- masks
    wat = [g for g, p, t in water if g.geom_type in ("Polygon", "MultiPolygon")]
    Wm = rfeat.rasterize(((g, 1) for g in wat), out_shape=(H_, W_), transform=tr, fill=0, dtype="uint8") if wat else np.zeros((H_, W_), "uint8")
    # open spaces: merge pieces split by tiles, name them from park and garden points inside
    og = unary_union([g for g, p, t in opens if g.geom_type in ("Polygon", "MultiPolygon")]) if opens else None
    OP = []
    if og is not None and not og.is_empty:
        for k, pg in enumerate(og.geoms if hasattr(og, "geoms") else [og]):
            if pg.area < 400:
                continue
            OP.append(dict(oid=k, geom=pg, area=pg.area, name=None))
    nm_pts = [(g.centroid if g.geom_type != "Point" else g, p["name"], p.get("class")) for g, p, t in parks_named]
    if OP and nm_pts:
        tree = STRtree([o["geom"] for o in OP])
        for pt, nm, cl in nm_pts:
            for i in tree.query(pt, predicate="within"):
                o = OP[int(i)]
                if o["name"] is None or (cl == "park" and o.get("ncl") != "park"):
                    o["name"], o["ncl"] = nm, cl
    Pm = rfeat.rasterize(((o["geom"], 1) for o in OP), out_shape=(H_, W_), transform=tr, fill=0, dtype="uint8") if OP else np.zeros((H_, W_), "uint8")
    # streets: merge the pieces of each name; 4 m either side
    SD = {}
    for g, p, t in streets:
        if g.geom_type not in ("LineString", "MultiLineString"):
            continue
        SD.setdefault((p["name"], p.get("class")), []).append(g)
    ST = []
    for (nm, cl), gs in SD.items():
        u = unary_union(gs)
        ST.append(dict(name=nm, cls=cl, geom=u, length=u.length))
    ST = pd.DataFrame(ST)
    Sm = np.zeros((H_, W_), "int32")
    for i, r in enumerate(ST.itertuples(), 1):
        if r.cls == "path":
            continue
        m = rfeat.rasterize([(r.geom.buffer(4.0), i)], out_shape=(H_, W_), transform=tr, fill=0, dtype="int32")
        Sm = np.where((m > 0) & (Sm == 0), m, Sm)
    # towers: merge touching tower parts into one footprint
    TW = []
    if len(Bt):
        u = unary_union([g.buffer(0.5) for g in Bt.geom])
        tree = STRtree(list(Bt.geom))
        for pg in (u.geoms if hasattr(u, "geoms") else [u]):
            idx = tree.query(pg, predicate="intersects")
            hs = Bt.iloc[idx].h.values
            c = pg.centroid
            TW.append(dict(geom=pg.buffer(-0.5), h=float(hs.max()), area=pg.area, x=c.x, y=c.y, n_parts=len(idx)))
    TW = pd.DataFrame(TW)
    if len(TW):
        TW["lon"], TW["lat"] = inv(TW.x.values, TW.y.values)
        TW["ground"] = DEMH(TW.lon.values, TW.lat.values)
        TW["in_box"] = (TW.x >= bx0) & (TW.x <= bx1) & (TW.y >= by0) & (TW.y <= by1)
    # inside-box slice
    c0, c1 = int(round((bx0 - dx0) / CELL)), int(round((bx1 - dx0) / CELL))
    r0, r1 = int(round((dy1 - by1) / CELL)), int(round((dy1 - by0) / CELL))
    np.savez_compressed(f"{WORK}/{key}_grid.npz", H=H, L=L, T=T, G=G, W=Wm, P=Pm, S=Sm, box=np.array([r0, r1, c0, c1]),
                        dom=np.array([dx0, dx1, dy0, dy1]), crs=np.array([latc, lonc]))
    pd.to_pickle(dict(B=B.drop(columns=["geom"]).assign(cx=[g.centroid.x for g in B.geom], cy=[g.centroid.y for g in B.geom]),
                      TW=TW, OP=pd.DataFrame(OP), ST=ST, crs=crs, box=(bx0, bx1, by0, by1)), f"{WORK}/{key}_vec.pkl")
    inb = (B.geom.apply(lambda g: g.centroid.x) .between(bx0, bx1)) & (B.geom.apply(lambda g: g.centroid.y).between(by0, by1))
    summary[key] = dict(parts=int(inb.sum()), towers=int(TW.in_box.sum()) if len(TW) else 0, grid=[H_, W_], open=len(OP), streets=len(ST))
    print(key, summary[key], "max h", B.h.max(), file=sys.stderr)
    jsave(summary, f"{WORK}/grid_summary.json", indent=1)
