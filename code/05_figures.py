"""Step 5: figures for the page (img/*.jpg), the blog (release/blog/b_*.png), the paper (release/paper/f_*.png), and header.png."""
import numpy as np, pandas as pd
from PIL import Image
import matplotlib.patheffects as pe
from matplotlib.colors import LinearSegmentedColormap, ListedColormap
from figstyle import *

R = jload(f"{DATA}/results.json")
META = jload(f"{WORK}/sun_meta.json")
BLOG, PAPERD = f"{ROOT}/release/blog", f"{ROOT}/release/paper"
for d in (BLOG, PAPERD):
    os.makedirs(d, exist_ok=True)
HALO = [pe.withStroke(linewidth=3, foreground=PAPER)]
HCM = LinearSegmentedColormap.from_list("h", ["#1F1838", "#3B2F63", "#5B4A8B", "#7E6CA8", "#A99BC0", "#D9C9A3", "#EBCB7A", "#F0B23A", "#E39A2C"])
BLD, WAT = np.array([0.80, 0.74, 0.62]), np.array([0.62, 0.74, 0.82])
SHC, TWC = np.array([0.12, 0.09, 0.22]), np.array([0.62, 0.15, 0.11])


def out(fig, name, page=True, blog=True, paper=True, dpi=200):
    fig.savefig(f"{WORK}/{name}.png", dpi=dpi, facecolor=fig.get_facecolor())
    plt.close(fig)
    im = Image.open(f"{WORK}/{name}.png").convert("RGB")
    if page:
        w = min(1600, im.size[0]); im.resize((w, round(im.size[1] * w / im.size[0])), Image.LANCZOS).save(f"{IMG}/{name}.jpg", quality=84, optimize=True)
    if blog:
        w = 1800; im.resize((w, round(im.size[1] * w / im.size[0])), Image.LANCZOS).save(f"{BLOG}/b_{name}.png", optimize=True)
    if paper:
        w = min(2000, im.size[0]); im.resize((w, round(im.size[1] * w / im.size[0])), Image.LANCZOS).save(f"{PAPERD}/f_{name}.png", optimize=True)
    os.remove(f"{WORK}/{name}.png")


def city(key):
    g = np.load(f"{WORK}/{key}_grid.npz"); r0, r1, c0, c1 = g["box"]
    return g["H"][r0:r1, c0:c1], g["W"][r0:r1, c0:c1], {d: dict(np.load(f"{WORK}/{key}_{d}_sun.npz")) for d in ("dec", "mar", "jun")}


def hours_rgb(key, d="dec", which="all", vmax=8.0):
    H, W, S = city(key)
    h = S[d][which] / 60
    rgb = HCM(np.clip(h / vmax, 0, 1))[..., :3]
    rgb[H > 0] = BLD; rgb[W > 0] = WAT
    return rgb


def bits(key, d, kind):
    a = np.asarray(Image.open(f"{DATA}/shadows/{key}_{d}_{kind}.png").convert("RGB")).astype(np.uint32)
    return a[..., 0] | (a[..., 1] << 8) | (a[..., 2] << 16)


def hkey(ax, x, y, w=0.3, vmax=8, label="Hours of direct sun at street level, 21 December", fs=10.5, transform=None):
    tr = transform
    n = 64
    for i in range(n):
        ax.add_patch(plt.Rectangle((x + w * i / n, y), w / n * 1.02, 0.018, color=HCM(i / (n - 1)), transform=tr, lw=0, clip_on=False))
    ax.text(x, y + 0.03, label, fontproperties=FELLSC, fontsize=fs + 1, color=RED, transform=tr, va="bottom")
    for v in range(0, vmax + 1, 2):
        ax.text(x + w * v / vmax, y - 0.008, f"{v} h", fontproperties=FELL, fontsize=fs, color=INKC, transform=tr, ha="center", va="top")


# ---------- 1. eight city centres, hours of sun on 21 December
keys = [c[0] for c in CITIES]
fig = plt.figure(figsize=(14, 11.2)); parchment(fig)
fig.text(0.04, 0.965, "Eight city centres on the shortest day", fontproperties=FELL, fontsize=24, color=INKC, va="center")
fig.text(0.04, 0.937, "Hours of direct sun at street level on 21 December, from building heights in OpenStreetMap and the lie of the land; buildings in buff, water in blue",
         fontproperties=FELL, fontsize=12.5, color=MUT, va="center")
for i, k in enumerate(keys):
    ax = fig.add_axes([0.03 + (i % 4) * 0.243, 0.50 - (i // 4) * 0.415, 0.225, 0.37])
    rgb = hours_rgb(k)
    h, w = rgb.shape[:2]
    # crop to a square around the centre so the panels compare like with like (3 km)
    s = min(h, w, 600)
    r0 = (h - s) // 2; c0 = (w - s) // 2
    ax.imshow(rgb[r0:r0 + s, c0:c0 + s], interpolation="nearest")
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values(): sp.set_color(INKC); sp.set_linewidth(0.8)
    c = R["cities"][k]; d = c["dates"]["dec"]
    ax.set_title(CNAME[k], fontproperties=HAND, fontsize=17, color=RED, loc="left", pad=22)
    ax.text(0, 1.012, f"{d['mean_all_h']:.1f} h of {d['flat_h']:.1f} h; {d['zero_pc']:.0f}% none", transform=ax.transAxes, fontproperties=FELL, fontsize=11, color=INKC, va="bottom")
hkey(fig.axes[0], 0.04, 0.035, w=0.35, transform=fig.transFigure)
fig.text(0.50, 0.04, "Each panel 3 km across, north up. Figures: mean hours of direct sun on open ground (of a full day with a flat horizon) and share with none.",
         fontproperties=FELL, fontsize=10.5, color=MUT, va="center")
out(fig, "cities")

# ---------- 2. Canary Wharf with and without its towers
fig = plt.figure(figsize=(14, 7.6)); parchment(fig)
fig.text(0.04, 0.95, "Canary Wharf on 21 December, with and without its towers", fontproperties=FELL, fontsize=24, color=INKC, va="center")
cw = R["cities"]["canary"]["dates"]["dec"]
fig.text(0.04, 0.905, f"Towers of 50 m or more take {cw['lost_tow_h']:.2f} hours of sun from the average square metre of open ground; {cw['tow_lost1h_pc']:.0f}% loses an hour or more",
         fontproperties=FELL, fontsize=12.5, color=MUT, va="center")
for i, (which, lab) in enumerate((("all", "As built"), ("low", "Towers of 50 m or more removed"))):
    ax = fig.add_axes([0.04 + i * 0.47, 0.13, 0.44, 0.70])
    rgb = hours_rgb("canary", "dec", which)
    if which == "low":
        H, W, S = city("canary")
        g = np.load(f"{WORK}/canary_grid.npz"); r0, r1, c0, c1 = g["box"]; T = g["T"][r0:r1, c0:c1]
        rgb[T > 0] = HCM(np.clip((S["dec"]["low"] / 60)[T > 0] / 8, 0, 1))[..., :3]
    ax.imshow(rgb, interpolation="nearest"); ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values(): sp.set_color(INKC)
    ax.set_title(lab, fontproperties=HAND, fontsize=18, color=RED, loc="left")
hkey(fig.axes[0], 0.04, 0.045, w=0.35, transform=fig.transFigure)
out(fig, "canary")

# ---------- 3. a day of shadows in the City of London (21 December)
m = META["london"]; ds = m["dates"]["dec"]
B, T = bits("london", "dec", "all"), bits("london", "dec", "tow")
H, W, S = city("london")
h, w = H.shape
# window around the City and the Shard: lon -0.105..-0.070, lat 51.500..51.520
from pyproj import Transformer
g = np.load(f"{WORK}/london_grid.npz"); dx0, dx1, dy0, dy1 = g["dom"]; r0, r1, c0, c1 = g["box"]
fwd = Transformer.from_crs(4326, f"+proj=tmerc +lat_0={m['lat']} +lon_0={m['lon']} +k=1 +x_0=0 +y_0=0 +ellps=WGS84 +units=m +no_defs", always_xy=True).transform
(x0, x1), (y0, y1) = zip(*[fwd(-0.104, 51.499), fwd(-0.071, 51.519)])
cc0, cc1 = int((x0 - dx0) / CELL) - c0, int((x1 - dx0) / CELL) - c0
rr0, rr1 = int((dy1 - y1) / CELL) - r0, int((dy1 - y0) / CELL) - r0
hrs = ds["hours"]
fig = plt.figure(figsize=(14, 9.6)); parchment(fig)
fig.text(0.04, 0.96, "A day of shadows in the City of London, 21 December", fontproperties=FELL, fontsize=24, color=INKC, va="center")
fig.text(0.04, 0.925, "Shadow at each hour (GMT): dark where any building shades the ground, red where only towers of 50 m or more do. The Thames and the Shard at bottom right.",
         fontproperties=FELL, fontsize=12.5, color=MUT, va="center")
n = len(hrs)
cols = 4
for i, hh in enumerate(hrs):
    k = i
    ax = fig.add_axes([0.03 + (i % cols) * 0.24, 0.48 - (i // cols) * 0.42, 0.225, 0.40])
    base = np.ones((h, w, 3)) * np.array([0.965, 0.93, 0.85])
    sh = ((B >> k) & 1).astype(bool); tw = ((T >> k) & 1).astype(bool)
    base[sh] = base[sh] * 0.25 + SHC * 0.75
    base[tw] = base[tw] * 0.2 + TWC * 0.8
    base[H > 0] = BLD; base[W > 0] = WAT
    ax.imshow(base[rr0:rr1, cc0:cc1], interpolation="nearest"); ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values(): sp.set_color(INKC)
    ax.set_title(f"{hh:02d}:00", fontproperties=HAND, fontsize=17, color=RED, loc="left", pad=4)
    ax.text(1, 1.01, f"sun {ds['alt'][i]:.0f}° up", transform=ax.transAxes, fontproperties=FELL, fontsize=11, color=INKC, ha="right", va="bottom")
if n < 8:
    ax = fig.add_axes([0.03 + (n % cols) * 0.24, 0.48 - (n // cols) * 0.42, 0.225, 0.40]); ax.axis("off")
    _pb = np.array([0.965, 0.93, 0.85])
    for j, (c, t) in enumerate(((_pb * 0.25 + np.asarray(SHC) * 0.75, "In shadow"), (_pb * 0.2 + np.asarray(TWC) * 0.8, "In shadow only because\nof towers of 50 m or more"), (_pb, "Open ground in sun"), (BLD, "Building"), (WAT, "Water"))):
        ax.add_patch(plt.Rectangle((0.05, 0.84 - j * 0.14), 0.12, 0.08, fc=c, ec=INKC, lw=0.5, transform=ax.transAxes))
        ax.text(0.22, 0.88 - j * 0.14, t, fontproperties=FELL, fontsize=12.5, color=INKC, va="center", transform=ax.transAxes)
    hm_ = lambda x: f"{int(x):02d}:{round((x % 1) * 60):02d}"
    ax.text(0.05, 0.08, f"About 2.3 km by 2.2 km, north up. Centre of the\nsun's disc rises {hm_(ds['sunrise_utc'])}, sets {hm_(ds['sunset_utc'])} GMT.", fontproperties=FELL, fontsize=11, color=MUT, transform=ax.transAxes)
out(fig, "day")
srise, sset = ds["sunrise_utc"], ds["sunset_utc"]
assert 8 < srise < 8.2 and 15.75 < sset < 15.95, (srise, sset)

# ---------- 4. how long a shadow: multiples of height through the year
import datetime as dt
fig = plt.figure(figsize=(13, 6.8)); parchment(fig)
ax = fig.add_axes([0.08, 0.13, 0.60, 0.70])
days = [dt.date(2026, 1, 1) + dt.timedelta(days=i) for i in range(0, 365, 2)]
for key, col, lab in (("london", RED, "London (51.5° N)"), ("edinburgh", "#3D6E9E", "Edinburgh (55.9° N)")):
    mm = META[key]; ys = []
    for dd in days:
        hrs_ = np.arange(10, 14.01, 1 / 30)
        a, _, _, _ = sun_position(mm["lat"], mm["lon"], 2026, dd.month, dd.day, hrs_)
        ys.append(1 / math.tan(math.radians(float(np.max(a)))))
    ax.plot(range(0, 365, 2), ys, color=col, lw=2.4, label=lab)
ax.set_yscale("log"); ax.set_yticks([0.5, 1, 2, 3, 4, 5]); ax.set_yticklabels(["0.5", "1", "2", "3", "4", "5"])
from matplotlib.ticker import NullFormatter, NullLocator
ax.yaxis.set_minor_formatter(NullFormatter()); ax.yaxis.set_minor_locator(NullLocator())
ax.set_ylabel("Noon shadow, in multiples of the height", fontproperties=FELL, fontsize=12)
ax.set_xticks([0, 59, 120, 181, 243, 304, 354]); ax.set_xticklabels(["1 Jan", "1 Mar", "1 May", "1 Jul", "1 Sep", "1 Nov", "21 Dec"], fontproperties=FELL, fontsize=11)
for t in ax.get_yticklabels(): t.set_fontproperties(FELL); t.set_fontsize(11)
ax.grid(color="#E2D3AE", lw=0.6); [ax.spines[s].set_visible(False) for s in ("top", "right")]
ax.legend(prop=FELL, frameon=False, loc="upper center")
sh = R["shard"]
fig.text(0.04, 0.95, "How long is a winter shadow?", fontproperties=FELL, fontsize=24, color=INKC, va="center")
fig.text(0.04, 0.91, "The shadow of anything tall at noon, as a multiple of its height", fontproperties=FELL, fontsize=12.5, color=MUT, va="center")
tx = [f"The Shard, {sh['h']:.0f} m in OpenStreetMap:", f"  21 June at noon: {sh['noon_jun_m']:,} m", f"  20 March at noon: {sh['noon_mar_m']:,} m",
      f"  21 December at noon: {sh['noon_dec_m']:,} m", f"  21 December, 2 hours from noon: about {sh['dec_2h_r10']:,} m", "",
      f"In London on 21 December a shadow at noon is", f"{R['london_noon_ratio']:.1f} times the height; in Edinburgh {R['edinburgh_noon_ratio']:.1f}."]
for i, t in enumerate(tx):
    fig.text(0.71, 0.78 - i * 0.055, t, fontproperties=FELL, fontsize=13, color=INKC if i else RED, va="center")
out(fig, "length")

# ---------- 5. cities compared
fig = plt.figure(figsize=(13, 7.4)); parchment(fig)
ax = fig.add_axes([0.17, 0.12, 0.56, 0.72])
ks = sorted(keys, key=lambda k: R["cities"][k]["dates"]["dec"]["mean_all_h"])
for j, k in enumerate(ks):
    d = R["cities"][k]["dates"]["dec"]
    ax.barh(j, d["flat_h"], color="#EFE3C4", edgecolor=INKC, lw=0.4, height=0.72)
    ax.barh(j, d["mean_ter_h"], color="#E2CFA0", edgecolor=INKC, lw=0.4, height=0.72)
    ax.barh(j, d["mean_low_h"], color="#7E6CA8", edgecolor=INKC, lw=0.4, height=0.72)
    ax.barh(j, d["mean_all_h"], color="#3B2F63", edgecolor=INKC, lw=0.4, height=0.72)
    ax.text(d["flat_h"] + 0.1, j, f"towers take {d['lost_tow_h']:.2f} h", fontproperties=FELL, fontsize=11, va="center", color=INKC)
ax.set_yticks(range(len(ks))); ax.set_yticklabels([CNAME[k] for k in ks], fontproperties=FELL, fontsize=12.5)
ax.set_xlabel("Hours on 21 December (average square metre of open ground)", fontproperties=FELL, fontsize=12)
for t in ax.get_xticklabels(): t.set_fontproperties(FELL); t.set_fontsize(11)
[ax.spines[s].set_visible(False) for s in ("top", "right")]
ax.set_xlim(0, 10.2)
lx = 0.76
for j, (c, t) in enumerate((("#3B2F63", "Direct sun, as built"), ("#7E6CA8", "Gained if the towers (50 m+) went"), ("#E2CFA0", "Gained if every building went"), ("#EFE3C4", "Lost to the lie of the land"))):
    fig.patches.append(plt.Rectangle((lx, 0.70 - j * 0.06), 0.022, 0.035, fc=c, ec=INKC, lw=0.5, transform=fig.transFigure))
    fig.text(lx + 0.03, 0.717 - j * 0.06, t, fontproperties=FELL, fontsize=12, color=INKC, va="center")
fig.text(0.04, 0.95, "Where the buildings take the winter sun", fontproperties=FELL, fontsize=24, color=INKC, va="center")
fig.text(0.04, 0.91, "Average hours of direct sun on open ground on 21 December, against a flat horizon, without buildings and without the towers",
         fontproperties=FELL, fontsize=12.5, color=MUT, va="center")
out(fig, "compare")

# ---------- 6. streets and squares that lose most to towers
stt = R["streets_tow"][:10] + [None] + R["open_tow"][:5]
fig = plt.figure(figsize=(13, 8.2)); parchment(fig)
ax = fig.add_axes([0.32, 0.08, 0.62, 0.78])
labs = []
for j, s in enumerate(stt):
    y = len(stt) - 1 - j
    if s is None:
        labs.append(""); continue
    ax.barh(y, s["dec_low"], color="#7E6CA8", edgecolor=INKC, lw=0.4, height=0.7)
    ax.barh(y, s["dec_all"], color="#3B2F63", edgecolor=INKC, lw=0.4, height=0.7)
    ax.text(s["dec_low"] + 0.08, y, f"{s['dec_all']:.1f} h left of {s['dec_low']:.1f} h", fontproperties=FELL, fontsize=11, va="center", color=INKC)
    labs.append(f"{s['name']}, {CNAME[s['city']]}")
ax.set_yticks(range(len(stt))); ax.set_yticklabels(labs[::-1], fontproperties=FELL, fontsize=12)
ax.set_xlim(0, 8.5)
for t in ax.get_xticklabels(): t.set_fontproperties(FELL); t.set_fontsize(11)
[ax.spines[s].set_visible(False) for s in ("top", "right")]
ax.set_xlabel("Hours of direct sun on 21 December (average along the street or over the space)", fontproperties=FELL, fontsize=12)
fig.text(0.04, 0.95, "The streets and squares the towers darken most", fontproperties=FELL, fontsize=24, color=INKC, va="center")
fig.text(0.04, 0.91, "Dark: direct sun on 21 December as built. Light: what the towers of 50 m or more take away. Streets above, open spaces below.",
         fontproperties=FELL, fontsize=12.5, color=MUT, va="center")
out(fig, "streets")

# ---------- 7. how complete the heights are
fig = plt.figure(figsize=(13, 6.4)); parchment(fig)
ax = fig.add_axes([0.17, 0.12, 0.55, 0.72])
for j, k in enumerate(keys[::-1]):
    hh = R["cities"][k]["heights"]
    l = 0
    for v, c in ((hh["other_pc"], "#3B2F63"), (hh["levels_pc"], "#A99BC0"), (hh["default_pc"], "#E2CFA0")):
        ax.barh(j, v, left=l, color=c, edgecolor=INKC, lw=0.4, height=0.7); l += v
ax.set_yticks(range(len(keys))); ax.set_yticklabels([CNAME[k] for k in keys[::-1]], fontproperties=FELL, fontsize=12.5)
ax.set_xlim(0, 100); ax.set_xlabel("Share of building footprint area (%)", fontproperties=FELL, fontsize=12)
for t in ax.get_xticklabels(): t.set_fontproperties(FELL); t.set_fontsize(11)
[ax.spines[s].set_visible(False) for s in ("top", "right")]
for j, (c, t) in enumerate((("#3B2F63", "A height in metres"), ("#A99BC0", "Height from the number of storeys"), ("#E2CFA0", "Neither: drawn 5 m high"))):
    fig.patches.append(plt.Rectangle((0.75, 0.66 - j * 0.07), 0.022, 0.04, fc=c, ec=INKC, lw=0.5, transform=fig.transFigure))
    fig.text(0.78, 0.68 - j * 0.07, t, fontproperties=FELL, fontsize=12, color=INKC, va="center")
fig.text(0.04, 0.95, "How tall are the buildings? OpenStreetMap often does not say", fontproperties=FELL, fontsize=24, color=INKC, va="center")
fig.text(0.04, 0.91, "Building footprint area in each city centre by where its height comes from (OpenMapTiles render_height)", fontproperties=FELL, fontsize=12.5, color=MUT, va="center")
out(fig, "heights")

# ---------- header 1200 x 630
fig = plt.figure(figsize=(12, 6.3)); parchment(fig, seed=11)
ax = fig.add_axes([0.42, 0.04, 0.56, 0.92])
k = 4
base = np.ones((h, w, 3)) * np.array([0.965, 0.93, 0.85])
sh = ((B >> k) & 1).astype(bool); tw = ((T >> k) & 1).astype(bool)
base[sh] = base[sh] * 0.25 + SHC * 0.75; base[tw] = base[tw] * 0.2 + TWC * 0.8; base[H > 0] = BLD; base[W > 0] = WAT
ax.imshow(base[rr0:rr1, cc0:cc1], interpolation="nearest", aspect="auto"); ax.axis("off")
fig.text(0.04, 0.80, "Shadows of", fontproperties=HAND, fontsize=44, color=INKC, va="center")
fig.text(0.04, 0.67, "the giants", fontproperties=HAND, fontsize=50, color=RED, va="center")
fig.text(0.045, 0.52, "Winter sun at street level in eight UK city centres", fontproperties=FELL, fontsize=16, color=INKC, va="center")
fig.text(0.045, 0.45, f"The Shard at noon on 21 December: a {R['shard']['noon_dec_km']:.2f} km shadow", fontproperties=FELLIT, fontsize=15, color=MUT, va="center")
fig.text(0.045, 0.39, f"Canary Wharf: towers take {cw['lost_tow_h']:.1f} h from every square metre", fontproperties=FELLIT, fontsize=15, color=MUT, va="center")
fig.text(0.045, 0.08, "Dr Tristan Hotham · maps.tristanhotham.com/tower-shadows", fontproperties=FELL, fontsize=12, color=MUT, va="center")
fig.text(0.43, 0.012, f"City of London, 21 December, {hrs[k]:02d}:00 GMT", fontproperties=FELL, fontsize=10, color=MUT)
fig.savefig(f"{ROOT}/header.png", dpi=100, facecolor=fig.get_facecolor()); plt.close(fig)
assert Image.open(f"{ROOT}/header.png").size == (1200, 630)
print("figures done")
