"""LinkedIn poster (1440x1800). Run: FONT_DIR=/path/to/FiraSans python docs/assets/make_poster.py
Numbers come from analysis/data/ (simulated, hypothetical parameters)."""
import json, os
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parents[2]
fd = os.environ.get("FONT_DIR")
if fd:
    for f in Path(fd).glob("*.ttf"):
        fm.fontManager.addfont(str(f))
    plt.rcParams["font.family"] = "Fira Sans"

BG, AMBER, GOLD, TEXT, MUTED, CARD, LINE = "#04070f", "#f5a623", "#ffe8a3", "#e8ecf4", "#8a96b4", "#0b1020", "#1d2640"
sim = json.load(open(ROOT / "analysis/data/sim_summary.json"))
val = json.load(open(ROOT / "analysis/data/lendwatch_validation.json"))
reg = sim["regimes"]
free = sim["theory_K_over_theta"]["standard"]
cut = 1 - reg["P3: P2 + listing check"]["share_of_R_total"]
prec = np.mean([r["precision"] for r in val])

fig = plt.figure(figsize=(14.4, 18), dpi=100, facecolor=BG)
T = lambda x, y, s, **k: fig.text(x, y, s, **k)

T(.065, .952, "NON-BANK LENDING", color=AMBER, fontsize=21, weight="bold")
T(.27, .952, "open research on regulating digital lenders", color=MUTED, fontsize=19)

T(.055, .795, f"{free:.0f}", color=AMBER, fontsize=200, weight="bold")
T(.072, .758, "victims", color=GOLD, fontsize=52)
T(.072, .640, "An illegal loan app can harm that\nmany people before a complaint-driven\nregulator even opens a file:\nhowever big or small the app is.",
  color=TEXT, fontsize=24, linespacing=1.55)
T(.072, .570, "Detect first.\nDon't wait for complaints.", color=AMBER, fontsize=28, weight="semibold", linespacing=1.4)
T(.072, .530, "free-harm allowance = K / θ  (10 complaints ÷ 10% reporting rate)", color=MUTED, fontsize=14.5)

# right: glowing bars, mean victims per illegal app under four regimes
ax = fig.add_axes([.60, .40, .34, .40], facecolor=BG)
names = ["Complaint-\ndriven\n(today)", "Detection", "+ fast\ntakedown", "+ listing\ncheck"]
keys = ["R: complaint-driven", "P1: detection, same delay", "P2: detection + fast track", "P3: P2 + listing check"]
vals = [reg[k]["mean_all"] for k in keys]
x = np.arange(4)
cols = ["#5a6585", AMBER, AMBER, AMBER]
for w, a in [(0.95, .05), (0.80, .09), (0.66, 1)]:
    ax.bar(x, vals, width=w, color=cols, alpha=a, lw=0)
for xi, v in zip(x, vals):
    ax.text(xi, v + 10, f"{v:.0f}", ha="center", va="bottom", color=TEXT, fontsize=24, weight="bold")
ax.set_xticks(x, names, color=MUTED, fontsize=15)
ax.tick_params(length=0, pad=12); ax.set_yticks([])
for s in ax.spines.values(): s.set_visible(False)
ax.set_ylim(0, max(vals) * 1.15)
T(.60, .872, "Victims per illegal app", color=GOLD, fontsize=22, weight="semibold")
T(.60, .826, "harmed before the app is removed or exits\n(mean of 200,000 simulated apps)", color=MUTED, fontsize=15)

fig.add_artist(plt.Line2D([.065, .935], [.335, .335], color=LINE, lw=1.5))
stats = [("12", "regulatory regimes\ncoded and compared"), ("3", "formal models of\nenforcement"),
         (f"−{cut*100:.0f}%", "victims with the\nfull reform path*"), (f"{prec:.3f}", "precision of lendwatch-th\non 30 synthetic markets")]
for i, (n, l) in enumerate(stats):
    xx = .065 + i * .225
    T(xx, .265, n, color=AMBER, fontsize=58, weight="bold")
    T(xx, .208, l, color=MUTED, fontsize=17, linespacing=1.5)

fig.add_artist(FancyBboxPatch((.06, .06), .88, .125, boxstyle="round,pad=0,rounding_size=.012",
                              transform=fig.transFigure, fc=CARD, ec=LINE, lw=1.5))
T(.09, .158, "Paper + code", color=MUTED, fontsize=15)
T(.09, .137, "github.com/thanatchon36/non-bank-lending-research", color=TEXT, fontsize=19)
T(.09, .113, "Read the paper online", color=MUTED, fontsize=15)
T(.09, .092, "thanatchon36.github.io/non-bank-lending-research/paper", color=TEXT, fontsize=19)
T(.09, .07, "* All numbers are model-based or simulated under hypothetical parameters: they show mechanisms, not estimates for Thailand.",
  color=MUTED, fontsize=13.5)

T(.065, .025, "Thanatchon Chongmankhong  ·  views are my own  ·  DOI 10.5281/zenodo.24184054", color=MUTED, fontsize=15)
fig.savefig(Path(__file__).with_name("linkedin_poster.png"), facecolor=BG)
