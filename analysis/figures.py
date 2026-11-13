"""All figures for the paper. Vector PDF output, one consistent style."""
import json
import textwrap
from pathlib import Path
HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
FIGS = HERE.parent / "paper" / "figs"
DATA.mkdir(exist_ok=True)

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch, Polygon

# ----------------------------------------------------------------------------- style
NAVY, BLUE, SKY, ICE = "#12355B", "#2E6DA4", "#8DB6DB", "#E3EEF8"
ORANGE, RED, GREEN = "#D9822B", "#B23A3A", "#3C8D5A"
INK, MUTED, RULE, PAPER = "#1F2933", "#5F6B7A", "#C9D1DA", "#F6F8FA"
mpl.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8.5, "axes.titlesize": 9.5,
    "axes.titleweight": "bold", "axes.labelsize": 8.5, "axes.labelcolor": INK,
    "axes.edgecolor": MUTED, "axes.linewidth": 0.7, "xtick.color": MUTED, "ytick.color": MUTED,
    "xtick.labelsize": 7.8, "ytick.labelsize": 7.8, "legend.fontsize": 7.6, "legend.frameon": False,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "grid.color": "#E6EAEE", "grid.linewidth": 0.6, "axes.axisbelow": True,
    "pdf.fonttype": 42, "ps.fonttype": 42, "savefig.bbox": "tight", "savefig.pad_inches": 0.03,
    "text.color": INK, "axes.titlelocation": "left", "axes.titlepad": 8,
})
W = 6.5  # text width in inches


def save(fig, name):
    FIGS.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGS / f"{name}.pdf")
    fig.savefig(FIGS / f"{name}.png", dpi=170)
    plt.close(fig)


def box(ax, x, y, w, h, title, sub=None, face="white", edge=MUTED, lw=0.9, tsize=8.6, ssize=7.3,
        tcolor=INK, bold=True):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.6",
                                fc=face, ec=edge, lw=lw, zorder=2))
    if sub:
        ax.text(x + w / 2, y + h * 0.63, title, ha="center", va="center", fontsize=tsize,
                fontweight="bold" if bold else "normal", color=tcolor, zorder=3)
        ax.text(x + w / 2, y + h * 0.30, sub, ha="center", va="center", fontsize=ssize,
                color=MUTED, zorder=3, linespacing=1.15)
    else:
        ax.text(x + w / 2, y + h / 2, title, ha="center", va="center", fontsize=tsize,
                fontweight="bold" if bold else "normal", color=tcolor, zorder=3)


def arrow(ax, p, q, color=MUTED, lw=1.0, style="-|>", ms=8, ls="-", conn="arc3"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=ms, color=color, lw=lw,
                                 linestyle=ls, connectionstyle=conn, zorder=1, shrinkA=0, shrinkB=0))


# ----------------------------------------------------------------------------- Fig 1
def diagram_axes(h):
    fig = plt.figure(figsize=(W, h))
    ax = fig.add_axes([0, 0, 1, 1])
    return fig, ax


def fig_pipeline():
    fig, ax = diagram_axes(3.0)
    ax.set_xlim(0, 100), ax.set_ylim(0, 47), ax.axis("off")
    bw, bh, gap, x0 = 17.4, 8.6, 2.9, 0.8
    xs = [x0 + i * (bw + gap) for i in range(5)]
    rows = {
        "today": (30.5, [("Harm", "borrower abused"), ("Complaint", "few victims report"),
                         ("Investigation", "agency by agency"), ("Court order", "URL by URL"),
                         ("Block", "app or URL removed")],
                  RED, "#FBECEC", "Today: the trigger is a harmed borrower",
                  "the operator relaunches under a new name"),
        "proposed": (7.5, [("Monitor", "stores, web, ads"), ("Allow-list", "licensed or not?"),
                           ("Evidence pack", "score and hashes"), ("Human review", "notice and reply"),
                           ("Disrupt", "all gatekeepers")],
                     BLUE, ICE, "Proposed: the trigger is detection, not harm",
                     "clones are re-detected through operator links"),
    }
    for key, (y, steps, accent, tint, label, loop) in rows.items():
        ax.text(x0, y + bh + 3.2, label, fontsize=8.6, fontweight="bold", color=INK, va="bottom")
        for i, (t, s) in enumerate(steps):
            first = i == 0
            box(ax, xs[i], y, bw, bh, t, s, face=tint if first else "white",
                edge=accent if first else MUTED, lw=1.6 if first else 0.9, tsize=8.2, ssize=6.9)
            if i < 4:
                arrow(ax, (xs[i] + bw + 0.4, y + bh / 2), (xs[i + 1] - 0.4, y + bh / 2))
        # feedback loop under the row
        yl = y - 3.4
        ax.plot([xs[4] + bw / 2, xs[4] + bw / 2, xs[0] + bw / 2], [y, yl, yl], color=MUTED, lw=0.9,
                ls=(0, (3, 2)), zorder=1)
        arrow(ax, (xs[0] + bw / 2, yl), (xs[0] + bw / 2, y - 0.2), ls=(0, (3, 2)))
        ax.text((xs[0] + xs[4] + bw) / 2, yl - 0.4, loop, ha="center", va="top", fontsize=7.3,
                color=MUTED, style="italic",
                bbox=dict(fc="white", ec="none", pad=0.6))
    save(fig, "fig1_pipeline")


# ----------------------------------------------------------------------------- Fig 2
def fig_timeline():
    events = [
        (1972, "Revolutionary\nCouncil\nAnnouncement 58", "D1"),
        (2002, "Credit bureau\nlaw (NCB)", "D5"),
        (2005, "Non-bank\npersonal loans\nunder BOT", "D2"),
        (2015, "Nano-finance;\nDebt Collection\nAct", "D2"),
        (2016, "Pico-finance\nunder the Fiscal\nPolicy Office", "D2"),
        (2017, "Excessive\nInterest Act", "D7"),
        (2020, "Ceilings cut;\ndigital personal\nloans", "D4"),
        (2022, "Market-conduct\nrules; PDPA\nin force", "D6"),
        (2023, "Informal debt\nmade a national\nagenda", "D7"),
        (2024, "Responsible-\nlending rules", "D5"),
        (2025, "Tech-crime\ndecree: shared\nliability", "D7"),
    ]
    dim_color = {"D1": NAVY, "D2": BLUE, "D4": ORANGE, "D5": GREEN, "D6": "#7A5195", "D7": RED}
    dim_name = {"D1": "Legal basis", "D2": "Perimeter", "D4": "Price", "D5": "Affordability",
                "D6": "Digital channels", "D7": "Unlicensed lending"}
    fig, ax = diagram_axes(2.9)
    n = len(events)
    xs = np.arange(n)
    ax.set_xlim(-0.75, n - 0.25), ax.set_ylim(-2.75, 2.15), ax.axis("off")
    ax.plot([-0.5, n - 0.5], [0, 0], color=MUTED, lw=1.2, zorder=1)
    for i, (yr, txt, d) in enumerate(events):
        up = i % 2 == 0
        c = dim_color[d]
        ax.scatter([i], [0], s=46, color=c, zorder=3, edgecolor="white", linewidth=0.8)
        ax.text(i, -0.42 if up else 0.42, str(yr), ha="center", va="top" if up else "bottom",
                fontsize=7.6, fontweight="bold", color=INK)
        y_tip = 0.95 if up else -0.95
        ax.plot([i, i], [0.12 if up else -0.12, y_tip], color=c, lw=0.8, zorder=2)
        ax.text(i, y_tip + (0.08 if up else -0.08), txt, ha="center", va="bottom" if up else "top",
                fontsize=6.9, color=INK, linespacing=1.18)
    if True:
        ax.text(-0.6, -2.12, "Spacing between events is not to scale. Colour shows the design dimension (Section 3):",
                fontsize=6.9, color=MUTED, va="center")
        handles = [Line2D([0], [0], marker="o", ls="", color=dim_color[k], markersize=5.5,
                          label=dim_name[k]) for k in ("D1", "D2", "D4", "D5", "D6", "D7")]
        ax.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.008, 0.0), ncol=6,
                  fontsize=6.9, handletextpad=0.2, columnspacing=1.0, borderaxespad=0)
    save(fig, "fig2_thai_timeline")


# ----------------------------------------------------------------------------- coding data
DIMS = ["D1\nLegal\nbasis", "D2\nPeri-\nmeter", "D3\nConduct\nsupervisor", "D4\nPrice\nrules",
        "D5\nAfford-\nability", "D6\nDigital\nchannels", "D7\nUnlicensed\nlending"]
CODES = {  # 0-2 ordinal codes, see the codebook in Appendix B (provisional)
    "Thailand":       [0, 0, 0, 1, 0, 0, 0],
    "India":          [1, 1, 1, 0, 1, 2, 1],
    "Indonesia":      [1, 1, 1, 2, 1, 2, 2],
    "Philippines":    [2, 1, 1, 2, 0, 1, 1],
    "Malaysia":       [2, 1, 0, 1, 0, 1, 0],
    "Singapore":      [2, 1, 1, 2, 2, 1, 0],
    "Japan":          [2, 1, 1, 1, 2, 0, 1],
    "Kenya":          [1, 2, 1, 0, 0, 2, 1],
    "United Kingdom": [2, 2, 2, 2, 0, 2, 2],
    "Australia":      [2, 2, 2, 2, 0, 1, 1],
    "European Union": [2, 2, 1, 1, 0, 1, 0],
    "United States":  [1, 1, 0, 1, 0, 0, 0],
}


def fig_heatmap():
    names = sorted(CODES, key=lambda k: (-sum(CODES[k]), k))
    M = np.array([CODES[k] for k in names])
    totals = M.sum(axis=1)
    fig = plt.figure(figsize=(W, 4.15))
    gs = fig.add_gridspec(1, 2, width_ratios=[4.3, 1.25], wspace=0.06)
    ax, bx = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
    cmap = ListedColormap(["#EEF2F6", SKY, NAVY])
    ax.imshow(M, cmap=cmap, norm=BoundaryNorm([-0.5, 0.5, 1.5, 2.5], 3), aspect="auto")
    ax.set_xticks(range(len(DIMS)), DIMS, fontsize=7.0, linespacing=1.05)
    ax.xaxis.tick_top()
    ax.set_yticks(range(len(names)), names, fontsize=7.8)
    ax.tick_params(length=0, pad=4)
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            ax.text(j, i, str(M[i, j]), ha="center", va="center", fontsize=7.6,
                    color="white" if M[i, j] == 2 else INK)
    ax.set_xticks(np.arange(-0.5, M.shape[1]), minor=True)
    ax.set_yticks(np.arange(-0.5, M.shape[0]), minor=True)
    ax.grid(which="minor", color="white", linewidth=1.6)
    ax.tick_params(which="minor", length=0)
    ti = names.index("Thailand")
    ax.add_patch(plt.Rectangle((-0.5, ti - 0.5), M.shape[1], 1, fill=False, ec=ORANGE, lw=1.8, zorder=5,
                               clip_on=False))
    ax.get_yticklabels()[ti].set_fontweight("bold")
    ax.get_yticklabels()[ti].set_color(ORANGE)
    # composite bar
    colors = [ORANGE if n == "Thailand" else BLUE for n in names]
    bx.barh(range(len(names)), totals, color=colors, height=0.62)
    bx.set_ylim(len(names) - 0.5, -0.5)
    bx.set_yticks([])
    bx.set_xlim(0, 14)
    bx.set_xticks([0, 7, 14])
    bx.xaxis.tick_top()
    bx.tick_params(axis="x", labelsize=7.2, length=0)
    bx.spines["left"].set_visible(False), bx.spines["bottom"].set_visible(False)
    bx.grid(axis="y", visible=False)
    bx.set_title("Composite score\n(0–14, unweighted)", fontsize=7.2, fontweight="normal", color=MUTED,
                 loc="center", pad=16)
    for i, t in enumerate(totals):
        bx.text(t + 0.35, i, str(t), va="center", fontsize=7.4, color=INK)
    handles = [Patch(fc="#EEF2F6", ec=RULE, label="0 = weakest option"), Patch(fc=SKY, label="1 = intermediate"),
               Patch(fc=NAVY, label="2 = strongest option")]
    fig.legend(handles=handles, loc="lower center", ncol=3, bbox_to_anchor=(0.43, 0.0), fontsize=7.4)
    save(fig, "fig3_heatmap")


def fig_quadrant():
    fig, ax = plt.subplots(figsize=(W, 3.9))
    ax.set_xlim(0, 2), ax.set_ylim(0, 2)
    ax.grid(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(MUTED)
    ax.set_xticks([]), ax.set_yticks([])
    ax.axvline(1, color=RULE, lw=0.9), ax.axhline(1, color=RULE, lw=0.9)
    ax.add_patch(plt.Rectangle((0, 0), 1, 1, color="#FCF1E6", zorder=0))
    quad = {(0, 1): "Narrow perimeter, wider toolkit",
            (1, 1): "Activity-based perimeter, wider toolkit",
            (0, 0): "Narrow perimeter, criminal law only",
            (1, 0): "Activity-based perimeter, criminal law only"}
    for (qx, qy), t in quad.items():
        ax.text(qx + 0.04, qy + 0.93, t, fontsize=7.3, color=MUTED, va="top", style="italic")
    pts = {(0, 1): ["India", "Indonesia", "Philippines", "Japan"],
           (1, 1): ["United Kingdom", "Australia", "Kenya"],
           (0, 0): ["Thailand", "Singapore", "Malaysia", "United States"],
           (1, 0): ["European Union"]}
    for (qx, qy), names in pts.items():
        for k, nme in enumerate(names):
            px = qx + 0.10 + (k % 2) * 0.44
            py = qy + 0.62 - (k // 2) * 0.24
            th = nme == "Thailand"
            ax.scatter([px], [py], s=90 if th else 38, color=ORANGE if th else BLUE, zorder=3,
                       edgecolor="white", linewidth=0.8)
            ax.text(px + 0.045, py, nme, va="center", fontsize=8.4 if th else 8.0,
                    fontweight="bold" if th else "normal", color=INK)
    ax.text(0.10 + 0.045, 0.62 - 0.24 - 0.09, "new regime from 2025", fontsize=6.8,
            color=MUTED, va="center", style="italic")
    ax.set_xlabel("Perimeter (D2):   product or entity licences  \u2192  activity-based", labelpad=6)
    ax.set_ylabel("Response to unlicensed lenders (D6, D7):\ncriminal law only  \u2192  registers, task forces,\ncivil consequences",
                  labelpad=6, fontsize=7.8)
    save(fig, "fig4_quadrant")


# ----------------------------------------------------------------------------- Model figures
def fig_model1():
    fig, (a, b) = plt.subplots(1, 2, figsize=(W, 2.75), gridspec_kw={"wspace": 0.42})
    th = np.linspace(0.01, 0.5, 400)
    for K, c in zip([1, 5, 10, 20], [SKY, BLUE, NAVY, "#0A1E33"]):
        a.plot(th, K / th, color=c, lw=1.5, label=f"K = {K}")
    a.axhline(10, color=ORANGE, lw=1.4, ls="--")
    a.text(0.495, 7.6, "proactive: u/\u03b7 = 10", color=ORANGE, fontsize=7.3, ha="right", va="top")
    a.set_yscale("log"), a.set_ylim(1.5, 4000), a.set_xlim(0, 0.5)
    a.set_xlabel("Reporting propensity \u03b8")
    a.set_ylabel("Expected victims before trigger, K/\u03b8")
    a.set_title("(a) The free-harm allowance")
    a.legend(loc="upper right", ncol=2, columnspacing=0.8, handlelength=1.6)
    # (b) ratio of expected victims, reactive / proactive, equal processing delays
    T, U = np.meshgrid(np.linspace(0.01, 0.4, 300), np.logspace(-1, 2.3, 300))
    K, eta = 10, 0.5
    ratio = (K / T) / (U / eta)
    lev = [0.1, 0.3, 1, 3, 10, 30, 100, 300, 1000]
    cs = b.contourf(T, U, ratio, levels=[0.03] + lev + [1e4], cmap="RdBu", norm=mpl.colors.LogNorm(1e-3, 1e3),
                    alpha=0.85, extend="neither")
    cl = b.contour(T, U, ratio, levels=[1], colors=INK, linewidths=1.2)
    b.clabel(cl, fmt={1: "equal harm"}, fontsize=7, inline_spacing=3, manual=[(0.3, 30)])
    b.set_yscale("log"), b.grid(False)
    b.set_xlabel("Reporting propensity \u03b8")
    b.set_ylabel("New victims per day, u")
    b.set_title("(b) Where detection beats complaints")
    b.text(0.03, 0.2, "detection\nprevents more", fontsize=7.4, color="white", fontweight="bold", va="bottom")
    b.text(0.385, 150, "complaints act first\n(large apps, high \u03b8)", fontsize=7.2, color=RED,
           fontweight="bold", ha="right", va="top")
    cb = fig.colorbar(cs, ax=b, ticks=lev, pad=0.03, fraction=0.06)
    cb.ax.set_yticklabels([str(v) for v in lev], fontsize=7)
    cb.set_label("Victims before trigger: reactive / proactive", fontsize=7.2)
    cb.outline.set_visible(False)
    save(fig, "fig5_model1")


def fig_model2():
    fig, (a, b) = plt.subplots(1, 2, figsize=(W, 2.75), gridspec_kw={"wspace": 0.38})
    rho = 0.0003
    d = np.logspace(-3, 0, 300)
    for kap, c in zip([0.0, 0.5, 1.0, 2.0], [RULE, SKY, BLUE, NAVY]):
        N = (rho + d) ** (-kap) / d
        N0 = (rho + 0.01) ** (-kap) / 0.01
        a.plot(d, N / N0, color=c if kap else MUTED, lw=1.5, ls="--" if kap == 0 else "-",
               label="\u03ba = 0 (no entry response)" if kap == 0 else f"\u03ba = {kap:g}")
    a.set_xscale("log"), a.set_yscale("log")
    a.axvline(0.01, color=RULE, lw=0.8)
    a.set_xlabel("Takedown hazard \u03b4 (per day)")
    a.set_ylabel("Steady-state operators, N*/N*(\u03b4 = 0.01)")
    a.set_title("(a) Takedown speed and entry")
    a.legend(loc="lower left", handlelength=1.6)
    # (b) reactive vs proactive stock as a function of theta
    th = np.linspace(0.01, 0.3, 300)
    u, K, D, eta, Dp = 5.0, 10, 30.0, 0.5, 7.0
    dR = 1 / (K / (th * u) + D)
    dP = 1 / (1 / eta + Dp)
    for kap, c in zip([0.5, 1.0, 2.0], [SKY, BLUE, NAVY]):
        rel = ((rho + dR) ** (-kap) / dR) / ((rho + dP) ** (-kap) / dP)
        b.plot(th, rel, color=c, lw=1.5, label=f"\u03ba = {kap:g}")
    b.set_yscale("log")
    b.axhline(1, color=ORANGE, lw=1.3, ls="--")
    b.text(0.295, 1.35, "proactive regime", color=ORANGE, fontsize=7.3, ha="right")
    b.set_xlabel("Reporting propensity \u03b8")
    b.set_ylabel("Operators, complaint-driven / proactive")
    b.set_title("(b) Stock under complaints, by \u03b8")
    b.legend(loc="upper right")
    save(fig, "fig6_model2")


def fig_model3():
    s = json.load(open(DATA / "sim_summary.json"))["model3"]["params"]
    rho0, bb, om, s0, d0 = s["rho0"], s["b"], s["omega"], s["s0"], s["delta0"]
    dl = np.logspace(-2, 2, 300)
    fig, ax = plt.subplots(figsize=(W * 0.62, 2.7))
    for h, c in zip([0.2, 0.5, 1.0], [SKY, BLUE, NAVY]):
        A = (bb + s0 / (1 + dl / d0) * h) * (1 + rho0) / om
        r = (-(1 - rho0) + np.sqrt((1 - rho0) ** 2 + 4 * (rho0 + A))) / 2
        ax.plot(dl, 100 * r, color=c, lw=1.6, label=f"harm per illegal loan h = {h:g}")
    ax.axhline(25, color=ORANGE, lw=1.2, ls="--")
    ax.text(0.011, 26.0, "Thai ceiling \u2248 25%", color=ORANGE, fontsize=7.0, va="bottom")
    ax.set_xscale("log")
    ax.set_ylim(15, 75)
    ax.set_xlabel("Enforcement intensity against unlicensed lenders, \u03b4/\u03b4\u2080")
    ax.set_ylabel("Welfare-maximising cap r\u0304* (% a year)")
    ax.legend(loc="upper right")
    save(fig, "fig7_model3")


# ----------------------------------------------------------------------------- simulations
def fig_montecarlo():
    z = np.load(DATA / "sim_victims.npz")
    shame = z["shame"]
    labels = ["R", "P1", "P2", "P3"]
    long = {"R": "R\ncomplaints", "P1": "P1\ndetection", "P2": "P2\n+ fast\ntrack", "P3": "P3\n+ listing\ncheck"}
    fig, (a, b) = plt.subplots(1, 2, figsize=(W, 2.95), gridspec_kw={"wspace": 0.34, "width_ratios": [1.25, 1]})
    pos = np.arange(len(labels))
    for k, (mask, col, off, nm) in enumerate([(~shame, BLUE, -0.18, "standard collection (\u03b8 = 0.10)"),
                                             (shame, RED, 0.18, "shaming collection (\u03b8 = 0.02)")]):
        means = [z[l][mask].mean() for l in labels]
        q25 = [np.percentile(z[l][mask], 25) for l in labels]
        q75 = [np.percentile(z[l][mask], 75) for l in labels]
        med = [np.median(z[l][mask]) for l in labels]
        a.bar(pos + off, means, width=0.34, color=col, alpha=0.88, label=nm)
        a.errorbar(pos + off, med, yerr=[np.array(med) - q25, np.array(q75) - med], fmt="o", ms=3,
                   color=INK, lw=0.9, capsize=2)
    a.set_xticks(pos, [long[l] for l in labels], fontsize=7.0, linespacing=1.1)
    a.set_ylabel("Victims per app before removal")
    a.set_title("(a) Harm per app by regime")
    a.legend(loc="upper right", fontsize=7.0)
    a.text(0.99, 0.80, "bars: mean\ndots, whiskers: median, IQR",
           transform=a.transAxes, ha="right", fontsize=6.6, color=MUTED, va="top")
    a.set_ylim(0, 900)
    s = json.load(open(DATA / "sim_summary.json"))["fragmentation"]["rows"]
    M = [r["M"] for r in s]
    b.plot(M, [r["R_theta_0.02_theory"] / 1000 for r in s], color=RED, lw=1.5, label="complaint-driven, \u03b8 = 0.02")
    b.plot(M, [r["R_theta_0.1_theory"] / 1000 for r in s], color=BLUE, lw=1.5, label="complaint-driven, \u03b8 = 0.10")
    b.plot(M, [r["P2_theory"] / 1000 for r in s], color=GREEN, lw=1.5, label="detection + fast track")
    b.scatter(M, [r["R_theta_0.02"] / 1000 for r in s], color=RED, s=12, zorder=3)
    b.scatter(M, [r["R_theta_0.1"] / 1000 for r in s], color=BLUE, s=12, zorder=3)
    b.scatter(M, [r["P2"] / 1000 for r in s], color=GREEN, s=12, zorder=3)
    b.set_xlabel("Apps run by one operator, M")
    b.set_ylabel("Victims before all apps removed ('000)")
    b.set_title("(b) Cloning pays under complaints")
    b.legend(loc="upper left", fontsize=7.0)
    b.set_ylim(0, 13.5)
    save(fig, "fig8_montecarlo")


def fig_validation():
    rows = json.load(open(DATA / "lendwatch_validation.json"))
    rows = sorted(rows, key=lambda r: r["N_hat"])
    fig, (a, b) = plt.subplots(1, 2, figsize=(W, 3.05), gridspec_kw={"wspace": 0.30, "width_ratios": [1.3, 1.1]})
    y = np.arange(len(rows))
    a.axvline(300, color=ORANGE, lw=1.4, ls="--", zorder=1)
    a.hlines(y, [r["lo"] for r in rows], [r["hi"] for r in rows], color=SKY, lw=2.2, zorder=2)
    a.scatter([r["N_hat"] for r in rows], y, color=NAVY, s=12, zorder=3)
    a.scatter([r["flagged_observed"] for r in rows], y, color=MUTED, marker="|", s=40, zorder=3)
    a.set_yticks([])
    a.set_ylim(-1, len(rows))
    a.set_xlim(220, 420)
    a.set_xlabel("Number of illegal operators")
    a.set_title("(a) 30 synthetic markets, sorted")
    a.grid(axis="y", visible=False)
    handles = [Line2D([0], [0], color=ORANGE, ls="--", lw=1.4, label="true population (300)"),
               Line2D([0], [0], color=SKY, lw=2.2, marker="o", markerfacecolor=NAVY, markeredgecolor=NAVY,
                      markersize=4, label="estimate, 95% CI"),
               Line2D([0], [0], color=MUTED, marker="|", ls="", markersize=7, label="operators flagged")]
    a.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=3, fontsize=6.8,
             handlelength=1.6, columnspacing=0.9)
    err = {
        "Observed\ncount": [r["flagged_observed"] / 300 - 1 for r in rows],
        "Chao\nbound": [r["chao"] / 300 - 1 for r in rows],
        "LL,\npipeline\nlinks": [r["N_hat"] / 300 - 1 for r in rows],
        "LL,\nperfect\nlinks": [r["oracle"] / 300 - 1 for r in rows],
    }
    data = [100 * np.array(v) for v in err.values()]
    bp = b.boxplot(data, widths=0.5, patch_artist=True, medianprops=dict(color=INK, lw=1.1),
                   whiskerprops=dict(color=MUTED), capprops=dict(color=MUTED), flierprops=dict(ms=3))
    for p_, c in zip(bp["boxes"], [RULE, SKY, BLUE, NAVY]):
        p_.set_facecolor(c), p_.set_edgecolor(MUTED)
    b.axhline(0, color=ORANGE, lw=1.2, ls="--")
    b.set_xticks(range(1, 5), list(err.keys()), fontsize=6.8, linespacing=1.1)
    b.set_ylabel("Error relative to truth (%)")
    b.set_title("(b) Estimator error")
    save(fig, "fig9_validation")


def fig_roadmap():
    fig, ax = diagram_axes(2.3)
    ax.set_xlim(0, 100), ax.set_ylim(0, 37), ax.axis("off")
    bw, bh, y0 = 29.0, 21.0, 15.0
    xs = [0.5, 35.5, 70.5]
    phases = [("Phase 1: existing powers", "0\u201312 months", "BOT notifications",
               ["Channel register and API", "All-in price on every loan", "Service-provider duties"]),
              ("Phase 2: MOF and Cabinet", "1\u20133 years", "MOF rules, Cabinet",
               ["One consumer-credit rulebook", "System-wide borrowing limit", "Standing task force"]),
              ("Phase 3: new statute", "3\u20135 years", "Act of Parliament",
               ["Activity-based perimeter", "Administrative sanctions", "Unenforceable illegal loans"])]
    for i, (x, (t, when, inst, items)) in enumerate(zip(xs, phases)):
        first = i == 0
        ax.add_patch(FancyBboxPatch((x, y0), bw, bh, boxstyle="round,pad=0,rounding_size=1.4",
                                    fc=ICE if first else "white", ec=BLUE if first else MUTED,
                                    lw=1.6 if first else 0.9))
        ax.text(x + 1.6, y0 + bh - 2.6, t, fontsize=8.2, fontweight="bold", va="center")
        ax.text(x + 1.6, y0 + bh - 5.9, f"{when}  \u00b7  {inst}", fontsize=7.0, color=MUTED, va="center")
        for k, it in enumerate(items):
            ax.text(x + 2.2, y0 + bh - 10.0 - 3.3 * k, "\u2022  " + it, fontsize=7.2, va="center")
    for gx, lab in [((xs[0] + bw + xs[1]) / 2, "Gate 1: register covers\nall licensed channels"),
                    ((xs[1] + bw + xs[2]) / 2, "Gate 2: Cabinet approves\nConsumer Credit Bill")]:
        ax.add_patch(Polygon([[gx - 2.1, y0 + bh / 2], [gx, y0 + bh / 2 + 2.1], [gx + 2.1, y0 + bh / 2],
                              [gx, y0 + bh / 2 - 2.1]], closed=True, fc=ORANGE, ec="none", zorder=3))
        ax.plot([gx, gx], [y0 + bh / 2 - 2.1, y0 - 2.2], color=ORANGE, lw=0.9)
        ax.text(gx, y0 - 2.8, lab, ha="center", va="top", fontsize=6.9, color=INK, linespacing=1.15)
    ax.add_patch(FancyBboxPatch((0.5, 0.6), 99, 5.2, boxstyle="round,pad=0,rounding_size=1.2", fc=PAPER, ec=RULE,
                                lw=0.8))
    ax.text(50, 3.2, "Alongside all phases: expand legal small-dollar credit and debt advice (divert)",
            ha="center", va="center", fontsize=7.6, color=INK)
    save(fig, "fig10_roadmap")


if __name__ == "__main__":
    for f in (fig_pipeline, fig_timeline, fig_heatmap, fig_quadrant, fig_model1, fig_model2, fig_model3,
              fig_montecarlo, fig_validation, fig_roadmap):
        f()
        print("ok", f.__name__)
