"""Step 1: download the OpenFreeMap zoom-14 tiles covering each city centre plus a buffer (cached in TILES)."""
import sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from common import *

tj = json.load(urllib.request.urlopen(urllib.request.Request("https://tiles.openfreemap.org/planet", headers=UA)))
URL = tj["tiles"][0]
jsave({"tiles_url": URL, "version": URL.split("/")[-4]}, f"{WORK}/tiles_version.json")
n = 2 ** Z


def txy(lon, lat):
    return int((lon + 180) / 360 * n), int((1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n)


need = set()
for key, nm, lo0, lo1, la0, la1 in CITIES:
    dlat = (BUFFER_M + 300) / 111195; dlon = dlat / math.cos(math.radians((la0 + la1) / 2))
    x0, y1 = txy(lo0 - dlon, la0 - dlat); x1, y0 = txy(lo1 + dlon, la1 + dlat)
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            need.add((x, y))
print(len(need), "tiles", file=sys.stderr)


def fetch(t):
    x, y = t
    f = f"{TILES}/{x}_{y}.pbf"
    if os.path.exists(f) and os.path.getsize(f) > 0:
        return 0
    for k in range(5):
        try:
            b = urllib.request.urlopen(urllib.request.Request(URL.format(z=Z, x=x, y=y), headers=UA), timeout=60).read()
            open(f, "wb").write(b)
            return len(b)
        except Exception as e:
            time.sleep(2 + 3 * k)
    raise RuntimeError(f"tile {t}")


with ThreadPoolExecutor(6) as ex:
    sizes = list(ex.map(fetch, sorted(need)))
print("downloaded", sum(sizes) // 1024, "KB")
