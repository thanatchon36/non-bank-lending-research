"""Numerical results for Sections 7-8: Monte Carlo of enforcement regimes and model curves.
All parameter values are illustrative (hypothetical), chosen only to show mechanisms."""
import json
import numpy as np
from pathlib import Path
HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
FIGS = HERE.parent / "paper" / "figs"
DATA.mkdir(exist_ok=True)

rng = np.random.default_rng(20261110)
P = dict(n_apps=200_000, u_median=5.0, u_sigma=1.0, theta_std=0.10, theta_shame=0.02,
         share_shame=0.5, K=10, D=30.0, eta=0.5, D_fast=7.0, exit_days=180.0, gate_block=0.5)

n = P["n_apps"]
u = np.exp(np.log(P["u_median"]) + P["u_sigma"] * rng.standard_normal(n))
shame = rng.random(n) < P["share_shame"]
theta = np.where(shame, P["theta_shame"], P["theta_std"])
exit_t = rng.exponential(P["exit_days"], n)

t_trigger = rng.gamma(P["K"], 1.0 / (theta * u))           # time to K-th complaint
t_detect = rng.exponential(1.0 / P["eta"], n)               # automated detection
blocked = rng.random(n) < P["gate_block"]                   # stopped at listing by allow-list check

regimes = {
    "R: complaint-driven": t_trigger + P["D"],
    "P1: detection, same delay": t_detect + P["D"],
    "P2: detection + fast track": t_detect + P["D_fast"],
    "P3: P2 + listing check": np.where(blocked, 0.0, t_detect + P["D_fast"]),
}
victims = {}
for name, t_act in regimes.items():
    life = np.minimum(t_act, exit_t)
    victims[name] = rng.poisson(u * life)

summary = {"params": P, "regimes": {}}
base = victims["R: complaint-driven"].sum()
for name, v in victims.items():
    summary["regimes"][name] = {
        "mean_all": float(v.mean()), "median_all": float(np.median(v)),
        "mean_standard": float(v[~shame].mean()), "mean_shaming": float(v[shame].mean()),
        "median_standard": float(np.median(v[~shame])), "median_shaming": float(np.median(v[shame])),
        "share_of_R_total": float(v.sum() / base),
        "share_removed_before_exit": float((regimes[name] < exit_t).mean()),
    }
# Reactive regime: how often does enforcement happen at all before the operator exits?
summary["R_triggered_before_exit_standard"] = float((t_trigger[~shame] + P["D"] < exit_t[~shame]).mean())
summary["R_triggered_before_exit_shaming"] = float((t_trigger[shame] + P["D"] < exit_t[shame]).mean())

# Size independence check (Proposition 1): mean victims before trigger by size quintile, no exit, no delay
q = np.quantile(u, [0, .2, .4, .6, .8, 1])
size_rows = []
for lo, hi in zip(q[:-1], q[1:]):
    m = (u >= lo) & (u <= hi) & ~shame
    v_trig = rng.poisson(u[m] * t_trigger[m])
    size_rows.append({"u_lo": float(lo), "u_hi": float(hi), "mean_victims_before_trigger": float(v_trig.mean())})
summary["size_independence_standard"] = size_rows
summary["theory_K_over_theta"] = {"standard": P["K"] / P["theta_std"], "shaming": P["K"] / P["theta_shame"]}

# Fragmentation (Proposition 2): operator with total flow U split across M apps, no exit
U, Ms, frag = 60.0, [1, 2, 4, 8, 12, 16, 20], []
for M in Ms:
    uu = U / M
    rec = {"M": M}
    for th in (P["theta_std"], P["theta_shame"]):
        sims = []
        for _ in range(4000):
            tk = rng.gamma(P["K"], 1 / (th * uu), M)
            sims.append(rng.poisson(uu * (tk + P["D"])).sum())
        rec[f"R_theta_{th}"] = float(np.mean(sims))
        rec[f"R_theta_{th}_theory"] = M * P["K"] / th + U * P["D"]
    sims = [rng.poisson(uu * (rng.exponential(1 / P["eta"], M) + P["D_fast"])).sum() for _ in range(4000)]
    rec["P2"] = float(np.mean(sims))
    rec["P2_theory"] = U / P["eta"] + U * P["D_fast"]
    frag.append(rec)
summary["fragmentation"] = {"U": U, "rows": frag}

# Model 3: optimal cap as a function of enforcement intensity
def optimal_cap(rho0, b, omega, h, s):
    A = (b + s * h) * (1 + rho0) / omega
    return (-(1 - rho0) + np.sqrt((1 - rho0) ** 2 + 4 * (rho0 + A))) / 2
m3 = dict(rho0=0.12, b=0.10, omega=1.0, s0=0.8, delta0=1.0)
summary["model3"] = {"params": m3, "examples": {
    f"h={h}": {f"delta={d}": float(optimal_cap(m3["rho0"], m3["b"], m3["omega"], h, m3["s0"] / (1 + d / m3["delta0"])))
               for d in (0, 1, 5, 50)} for h in (0.2, 0.5, 1.0)}}

json.dump(summary, open(DATA / "sim_summary.json", "w"), indent=1)
np.savez_compressed(DATA / "sim_victims.npz", shame=shame, **{k.split(":")[0]: v for k, v in victims.items()})
print(json.dumps({k: v for k, v in summary.items() if k not in ("params",)}, indent=1))
