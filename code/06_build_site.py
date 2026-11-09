"""Step 6: index.html from code/page_template.html, filled from data/results.json, with the full-screen snippet.
10.5281/zenodo.24075303, https://doi.org/10.5281/zenodo.24075303 and https://blog.tristanhotham.com/2026/10/31/tower-shadows/ stay as placeholders for the publisher."""
from common import *

R = jload(f"{DATA}/results.json")
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}
C = R["cities"]
# facts stated in words
assert R["shard"]["h"] == 310 and abs(R["shard"]["lon"] + 0.0864) < 0.002 and abs(R["shard"]["lat"] - 51.5044) < 0.002
assert 3.5 < R["london_noon_ratio"] < 4.0 and R["hypo300"]["london_dec_m"] == round(300 * R["london_noon_ratio"])
assert max(C, key=lambda k: C[k]["dates"]["dec"]["lost_tow_h"]) == "canary"
assert sorted(C, key=lambda k: -C[k]["dates"]["dec"]["lost_tow_h"])[1] == "manchester"
assert max(C, key=lambda k: C[k]["dates"]["dec"]["zero_pc"]) == "edinburgh" and C["edinburgh"]["towers50"] <= 2
assert 0.8 < C["edinburgh"]["dates"]["dec"]["flat_h"] - C["edinburgh"]["dates"]["dec"]["mean_ter_h"] < 1.3
assert min(C, key=lambda k: C[k]["heights"]["default_pc"]) == "canary" and max(C, key=lambda k: C[k]["heights"]["default_pc"]) == "liverpool"
assert R["streets_tow"][0]["city"] == "canary" and R["open_tow"][0]["city"] == "canary" and R["streets_tow"][1]["name"] == "Circus Road South"
t = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
t = t.replace("{{FULLSCREEN}}", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
t = t.replace("{{REPO}}", REPO).replace("{{AI}}", AI).replace("{{BYLINE}}", BYLINE).replace("{{VERSION}}", "20261108")
t = re.sub(r"\{\{([^{}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(R, m.group(1)), m.group(3)), t)
assert set(re.findall(r"\{\{([^}]+)\}\}", t)) <= KEEP
vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", t, flags=re.S)
for bad in ("—", "–", "--", "DSIT", "DCMS"):
    assert bad not in vis, bad
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(t)
print("index.html", len(t) // 1024, "KB")
