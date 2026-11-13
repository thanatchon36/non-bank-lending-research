"""Dark README banner (style of thainowcast). Run: python docs/assets/make_banner.py"""
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

BG, AMBER, TEXT, MUTED = "#04070f", "#f5a623", "#e8ecf4", "#8a96b4"
rng = np.random.default_rng(7)
fig = plt.figure(figsize=(16.8, 6.24), dpi=100, facecolor=BG)

# left: operator network -- unlicensed clusters glow amber, licensed lenders dim blue
ax = fig.add_axes([0.03, 0.03, 0.30, 0.94], facecolor=BG); ax.axis("off")
centres = rng.uniform(0.1, 0.9, (14, 2))
for c in centres:
    n = rng.integers(3, 9)
    pts = c + rng.normal(0, 0.035, (n, 2))
    for p in pts:
        ax.plot([c[0], p[0]], [c[1], p[1]], color=AMBER, lw=0.6, alpha=0.35)
    for s, a in [(260, 0.05), (90, 0.12), (18, 0.9)]:
        ax.scatter(pts[:, 0], pts[:, 1], s=s, color=AMBER, alpha=a, lw=0)
    ax.scatter(*c, s=60, color="#ffe8a3", lw=0)
lic = rng.uniform(0.05, 0.95, (45, 2))
ax.scatter(lic[:, 0], lic[:, 1], s=14, color="#3a4a6e", lw=0)
ax.set_xlim(0, 1); ax.set_ylim(0, 1)

fig.text(0.35, 0.60, "non-bank lending", color=AMBER, fontsize=60, weight="bold")
fig.text(0.352, 0.44, "Regulating non-bank lenders in the digital age:\ntwelve regimes, a theory of enforcement, a roadmap for Thailand",
         color=TEXT, fontsize=18, linespacing=1.6)
fig.text(0.352, 0.25, "comparative coding · reporting-propensity trap · Monte Carlo · lendwatch-th detection pipeline",
         color=MUTED, fontsize=13)
fig.text(0.985, 0.04, "Illustration: synthetic operator network (amber = unlicensed clusters, blue = licensed lenders)",
         color=MUTED, fontsize=9, ha="right")
fig.savefig(Path(__file__).with_name("banner.png"), facecolor=BG)
