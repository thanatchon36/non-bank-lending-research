"""Multiple systems estimation (capture-recapture) of the hidden operator population.

Each data source ("list") either captures an operator or not. Operators seen by no
list are unobserved; their number is predicted from the overlap pattern among lists.

Estimators
----------
* Chapman (two lists)      - nearly unbiased Lincoln-Petersen.
* Chao lower bound         - robust to unequal catchability; a floor, not a point estimate.
* Log-linear models        - Poisson regression on capture histories with main effects
                             and any subset of pairwise list interactions; models are
                             compared by BIC and averaged with BIC weights.

Assumptions to defend in any write-up: closed population over the window, correct
linkage of records to operators, and no unmodelled dependence or heterogeneity.
"""
from __future__ import annotations

import itertools
import math
from typing import Optional, Sequence

import numpy as np


def chapman(n1: int, n2: int, m: int) -> dict:
    """Two-list estimator. n1, n2 = list sizes, m = operators on both."""
    n_hat = (n1 + 1) * (n2 + 1) / (m + 1) - 1
    var = (n1 + 1) * (n2 + 1) * (n1 - m) * (n2 - m) / ((m + 1) ** 2 * (m + 2))
    se = math.sqrt(max(var, 0.0))
    return {"N": n_hat, "se": se, "ci95": (max(n1 + n2 - m, n_hat - 1.96 * se), n_hat + 1.96 * se)}


def chao_lower_bound(capture: np.ndarray) -> dict:
    """Chao's lower bound from f1 (seen on exactly one list) and f2 (exactly two)."""
    k = capture.sum(axis=1)
    n = int((k > 0).sum())
    f1, f2 = int((k == 1).sum()), int((k == 2).sum())
    if f2 > 0:
        f0 = f1 ** 2 / (2 * f2)
        r = f1 / f2
        var = f2 * (0.25 * r ** 4 + r ** 3 + 0.5 * r ** 2)
    else:
        f0 = f1 * (f1 - 1) / 2
        var = f1 * (f1 - 1) / 2 + f1 * (2 * f1 - 1) ** 2 / 4 - f1 ** 4 / (4 * max(n, 1))
    return {"N": n + f0, "unobserved": f0, "se": math.sqrt(max(var, 0.0)), "f1": f1, "f2": f2}


def _poisson_glm(X: np.ndarray, y: np.ndarray, max_iter: int = 200, tol: float = 1e-9):
    """Poisson regression by iteratively reweighted least squares."""
    p = X.shape[1]
    beta = np.zeros(p)
    beta[0] = math.log(max(y.mean(), 1e-8))
    ridge = 1e-9 * np.eye(p)
    converged = False
    for _ in range(max_iter):
        eta = np.clip(X @ beta, -30, 30)
        mu = np.exp(eta)
        z = eta + (y - mu) / mu
        xtw = X.T * mu
        new = np.linalg.solve(xtw @ X + ridge, xtw @ z)
        if not np.all(np.isfinite(new)):
            break
        if np.max(np.abs(new - beta)) < tol:
            beta, converged = new, True
            break
        beta = new
    eta = np.clip(X @ beta, -30, 30)
    mu = np.exp(eta)
    cov = np.linalg.pinv((X.T * mu) @ X + ridge)
    llf = float(np.sum(y * eta - mu - np.array([math.lgamma(v + 1) for v in y])))
    return beta, cov, llf, converged


def capture_histories(capture: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """All 2^K - 1 observable histories and how many operators show each."""
    k = capture.shape[1]
    hist = np.array([h for h in itertools.product([0, 1], repeat=k) if any(h)], dtype=int)
    index = {tuple(h): i for i, h in enumerate(hist)}
    counts = np.zeros(len(hist))
    for row in capture.astype(int):
        if row.any():
            counts[index[tuple(row)]] += 1
    return hist, counts


def loglinear_mse(capture: np.ndarray, list_names: Optional[Sequence[str]] = None,
                  max_interactions: Optional[int] = None) -> dict:
    """Model-averaged log-linear estimate of the total number of operators.

    capture : (n_operators, K) 0/1 matrix; rows that are all zero are ignored.
    """
    capture = np.asarray(capture).astype(int)
    capture = capture[capture.sum(axis=1) > 0]
    n_obs, k = capture.shape
    names = list(list_names or [f"L{i + 1}" for i in range(k)])
    if k < 2:
        raise ValueError("need at least two lists")
    hist, counts = capture_histories(capture)
    pairs = list(itertools.combinations(range(k), 2))
    limit = len(pairs) if max_interactions is None else max_interactions
    fits = []
    for r in range(0, limit + 1):
        for subset in itertools.combinations(pairs, r):
            cols = [np.ones(len(hist))] + [hist[:, j] for j in range(k)]
            cols += [hist[:, a] * hist[:, b] for a, b in subset]
            X = np.column_stack(cols).astype(float)
            if len(hist) - X.shape[1] < 1:          # saturated: no degrees of freedom
                continue
            beta, cov, llf, ok = _poisson_glm(X, counts)
            se0 = math.sqrt(max(cov[0, 0], 0.0))
            if not ok or not math.isfinite(beta[0]) or se0 > 5 or abs(beta[0]) > 25:
                continue                            # unidentified (e.g. empty overlap)
            fits.append({
                "interactions": [f"{names[a]}x{names[b]}" for a, b in subset],
                "log_unobserved": float(beta[0]), "se_log": se0,
                "unobserved": math.exp(beta[0]),
                "bic": -2 * llf + X.shape[1] * math.log(n_obs),
            })
    if not fits:
        raise RuntimeError("no identifiable log-linear model; lists may not overlap")
    best_bic = min(f["bic"] for f in fits)
    raw = np.array([math.exp(-0.5 * (f["bic"] - best_bic)) for f in fits])
    wts = raw / raw.sum()
    theta = float(np.sum(wts * np.array([f["log_unobserved"] for f in fits])))
    # Unconditional SE (Buckland et al. 1997): within-model + between-model spread.
    se = float(np.sum(wts * np.sqrt(np.array([f["se_log"] ** 2 + (f["log_unobserved"] - theta) ** 2
                                              for f in fits]))))
    for f, wt in zip(fits, wts):
        f["weight"] = float(wt)
        f["N"] = n_obs + f["unobserved"]
    fits.sort(key=lambda f: f["bic"])
    unobs = math.exp(theta)
    return {
        "lists": names,
        "n_observed": int(n_obs),
        "unobserved": unobs,
        "N": n_obs + unobs,
        "ci95": (n_obs + math.exp(theta - 1.96 * se), n_obs + math.exp(theta + 1.96 * se)),
        "ratio_total_to_observed": (n_obs + unobs) / n_obs,
        "n_models": len(fits),
        "top_models": fits[:5],
    }


def estimate_population(capture: np.ndarray, list_names: Optional[Sequence[str]] = None) -> dict:
    """All estimators side by side, so their disagreement is visible."""
    capture = np.asarray(capture).astype(int)
    capture = capture[capture.sum(axis=1) > 0]
    names = list(list_names or [f"L{i + 1}" for i in range(capture.shape[1])])
    out = {"n_observed": int(len(capture)),
           "list_sizes": {n: int(capture[:, i].sum()) for i, n in enumerate(names)},
           "chao_lower_bound": chao_lower_bound(capture), "pairwise_chapman": {}}
    for a, b in itertools.combinations(range(len(names)), 2):
        m = int((capture[:, a] & capture[:, b]).sum())
        if m > 0:
            out["pairwise_chapman"][f"{names[a]}x{names[b]}"] = chapman(
                int(capture[:, a].sum()), int(capture[:, b].sum()), m)
    try:
        out["loglinear"] = loglinear_mse(capture, names)
    except (RuntimeError, ValueError, np.linalg.LinAlgError) as exc:
        out["loglinear"] = {"error": str(exc)}
    return out
