"""Reddit collage (r/dataisbeautiful style): a day of shadows in the City of London, the cities compared, and the Shard's
shadow, on parchment. Built from the blog figures made by code/05_figures.py (legends on paper, not over the map).
Output: reddit/tower_shadows_collage.png (2700 x 3900 px)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code"))
from figstyle import *
from PIL import Image

R = jload(f"{DATA}/results.json")
B = os.path.join(ROOT, "release", "blog")
fig = plt.figure(figsize=(9, 13), dpi=300); parchment(fig, seed=6, alpha=0.05)
fig.text(0.04, 0.975, "Shadows of the giants", fontproperties=HAND, fontsize=34, color=RED, va="center")
fig.text(0.04, 0.951, f"Winter sun at street level in eight UK city centres, from OpenStreetMap building heights. On 21 December a shadow in",
         fontproperties=FELL, fontsize=11, color=INKC, va="center")
fig.text(0.04, 0.936, f"London is {R['london_noon_ratio']:.1f} times the height of what casts it; the Shard's ({R['shard']['h']:.0f} m) reaches {R['shard']['noon_dec_m']:,} m at noon.",
         fontproperties=FELL, fontsize=11, color=INKC, va="center")


def panel(fn, box, crop=None):
    im = Image.open(f"{B}/{fn}").convert("RGB")
    if crop:
        w, h = im.size; im = im.crop((int(crop[0] * w), int(crop[1] * h), int(crop[2] * w), int(crop[3] * h)))
    ax = fig.add_axes(box); ax.imshow(im, aspect="auto"); ax.axis("off")


# day of shadows: 1800 x 1234 image, crop the title
panel("b_day.png", [0.01, 0.48, 0.98, 0.98 * 9 * (1234 * 0.88 / 1800) / 13], crop=(0, 0.12, 1, 1))
fig.text(0.04, 0.905, "The City of London and the Southbank, 21 December, hour by hour", fontproperties=FELLSC, fontsize=12, color=RED, va="center")
panel("b_compare.png", [0.01, 0.10, 0.98, 0.98 * 9 * (1025 * 0.86 / 1800) / 13], crop=(0, 0.14, 1, 1))
fig.text(0.04, 0.462, "Average hours of direct sun on open ground on 21 December", fontproperties=FELLSC, fontsize=12, color=RED, va="center")
cw = R["cities"]["canary"]["dates"]["dec"]; lo = R["cities"]["london"]["dates"]["dec"]
fig.text(0.04, 0.075, f"Ordinary buildings take most of the winter sun: removing the towers (50 m or more) would give central London back {lo['lost_tow_h']:.2f} h, Canary Wharf {cw['lost_tow_h']:.2f} h.",
         fontproperties=FELL, fontsize=10, color=INKC, va="center")
fig.text(0.04, 0.058, f"Caveat: {R['cities']['canary']['heights']['default_pc']:.0f}% to {R['cities']['liverpool']['heights']['default_pc']:.0f}% of building footprint has no height in OpenStreetMap and is drawn 5 m high, so streets look sunnier than they are.",
         fontproperties=FELL, fontsize=10, color=INKC, va="center")
fig.text(0.04, 0.02, "Data: OpenStreetMap contributors (ODbL) via OpenFreeMap tiles; AWS Terrain Tiles. Sun every 10 minutes on a 5 m grid; no trees or cloud.  maps.tristanhotham.com/tower-shadows",
         fontproperties=FELL, fontsize=8, color=MUT)
fig.savefig(os.path.join(ROOT, "reddit", "tower_shadows_collage.png"), dpi=300, facecolor=fig.get_facecolor())
print(Image.open(os.path.join(ROOT, "reddit", "tower_shadows_collage.png")).size)
