"""Step 7: the paper. Fills code/paper_template.tex from data/results.json, adds tables, compiles with xelatex.
Output: release/paper/Hotham_Tower_Shadows.pdf and .tex beside the f_*.png figures.
The DOI stays a placeholder (https://doi.org/10.5281/zenodo.24075303 printed) unless DOI is set: DOI=10.5281/zenodo.N python3 code/07_paper.py"""
import subprocess
from common import *

R = jload(f"{DATA}/results.json")
C = R["cities"]
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Tower_Shadows"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")
means = {k: C[k]["dates"]["dec"]["mean_all_h"] for k in C}
assert min(means, key=means.get) == "edinburgh" and max(means, key=means.get) == "leeds"
assert R["towers_longest"][0]["h"] == R["shard"]["h"] and R["cities"]["edinburgh"]["towers50"] == 1


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "pc": return f"{round(float(v))}\\%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    return tex(str(v))


rows = ""
for k, *_ in CITIES:
    c = C[k]; d = c["dates"]["dec"]
    rows += (f"{tex(c['name'])} & {c['towers50']} & {c['heights']['default_pc']:.0f} & {d['flat_h']:.2f} & {d['mean_ter_h']:.2f} & {d['mean_low_h']:.2f} & "
             f"{d['mean_all_h']:.2f} & {d['zero_pc']:.1f} & {d['lost_tow_h']:.2f} & {d['tow_lost1h_pc']:.1f}\\\\\n")
TC = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{Eight centres on 21 December: towers (50 m or more, footprint 300 m$^2$ or more), share of building footprint at the 5 m default (\\%), "
      "and average hours of direct sun on open ground with a flat horizon, with terrain only, without towers and as built; share of open ground with no direct sun (\\%); "
      "hours taken by towers; share of open ground losing an hour or more to towers (\\%).}\\label{tab:cities}"
      "\\begin{tabular}{lrrrrrrrrr}\\toprule Centre & Towers & Default & Flat & Terrain & No towers & As built & No sun & Towers take & $\\ge$1 h\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{tex(CNAME[t['city']])} & {t['h']:.0f} & {t['lat']:.4f}, {t['lon']:.4f} & {t['noon_dec_m']:,} & {t['dec_2h_m']:,}\\\\\n" for t in R["towers_longest"])
TT = ("\\begin{table}[tbp]\\centering\\small\\caption{Towers with the longest noon shadows on 21 December (flat ground), with the shadow two hours either side of noon. Heights are OpenStreetMap render heights; the first is the Shard.}"
      "\\label{tab:towers}\\begin{tabular}{lrlrr}\\toprule Centre & Height (m) & Position & Noon (m) & $\\pm$2 h (m)\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{tex(s['name'])} & {tex(CNAME[s['city']])} & {s['dec_all']:.2f} & {s['dec_low']:.2f} & {s['dec_ter']:.2f}\\\\\n" for s in R["streets_tow"][:10])
rows += "\\midrule\n" + "".join(f"{tex(s['name'])} & {tex(CNAME[s['city']])} & {s['dec_all']:.2f} & {s['dec_low']:.2f} & {s['dec_ter']:.2f}\\\\\n" for s in R["open_tow"][:5])
TS = ("\\begin{table}[tbp]\\centering\\small\\caption{Streets (above) and open spaces (below) losing most direct sun to towers on 21 December: average hours as built, without towers and without buildings.}"
      "\\label{tab:streets}\\begin{tabular}{llrrr}\\toprule Name & Centre & As built & No towers & No buildings\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
t = t.replace("{{AI}}", AI).replace("{{PAGE}}", PAGE).replace("{{REPO}}", REPO)
t = t.replace("{{TABLE_CITIES}}", TC).replace("{{TABLE_TOWERS}}", TT).replace("{{TABLE_STREETS}}", TS)
t = re.sub(r"\{\{(?!TABLE_|DOI)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
DOI = os.environ.get("DOI")
t = t.replace("https://doi.org/10.5281/zenodo.24075303", f"\\url{{https://doi.org/{DOI}}}" if DOI else "\\{\\{DOI\\_URL\\}\\}")
assert "{{" not in t and "--" not in t and "—" not in t and "–" not in t
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
for ext in (".aux", ".log", ".out", ".bbl", ".blg"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("—") + txt.count("–") + txt.count("--"))
