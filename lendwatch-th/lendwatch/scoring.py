"""Risk scoring.

Two layers:
1. ``rule_score``  - additive, capped, fully explainable index used for triage.
2. ``fit_supervised`` - logistic regression on reviewer labels, evaluated out of fold,
   to re-estimate the weights and to report precision / recall honestly.

A score is a queue position for a human reviewer. It is never a finding of illegality.
"""
from __future__ import annotations

from typing import Optional

import numpy as np

from . import config as C

NUMERIC_FEATURES = [
    "offers_credit", "unlicensed_offering_credit", "impersonates_licensed_brand",
    "name_only_licence_match", "rate_above_any_ceiling", "rate_above_unlicensed_cap",
    "short_tenor", "advance_fee", "no_bureau_check", "daily_repayment", "no_documents",
    "instant_approval", "messaging_only_contact", "n_sensitive_permissions",
    "harm_review_share", "low_rating_share", "category_mismatch", "free_email_developer",
    "no_privacy_policy", "privacy_on_free_host", "apk_sideload_link", "operator_size",
]


def rule_score(f: dict, weights: Optional[dict] = None) -> tuple[int, str, list[str]]:
    """Return (score 0-100, tier, reasons) for one feature dict."""
    w = weights or C.SCORE_WEIGHTS
    score, reasons = 0, []

    def add(key: str, label: str, points: Optional[int] = None):
        nonlocal score
        pts = w[key] if points is None else points
        if pts:
            score += pts
            reasons.append(f"{label} (+{pts})")

    if not f.get("is_lending_related"):
        return 0, "not_relevant", ["not lending-related"]
    if f.get("licence_status") in ("licensed_exact", "licensed_domain"):
        # Registered channel of a licensee: conduct issues belong to market-conduct
        # supervision, not to the unlicensed-lending queue.
        return 0, "licensed_channel", [f"registered channel of {f.get('matched_licensee')}"]

    if f.get("unlicensed_offering_credit"):
        add("unlicensed_offering_credit", "offers credit, no licence match")
    if f.get("impersonates_licensed_brand"):
        add("impersonates_licensed_brand", f"uses licensed brand '{f.get('impersonates')}'")
    if f.get("name_only_licence_match"):
        add("name_only_licence_match", f"claims '{f.get('matched_licensee')}' but channel not registered")
    if f.get("rate_above_any_ceiling"):
        add("rate_above_any_ceiling", f"annualised rate ~{f.get('max_annualised_rate'):.0f}% above every ceiling")
    elif f.get("rate_above_unlicensed_cap"):
        add("rate_above_unlicensed_cap", f"annualised rate ~{f.get('max_annualised_rate'):.0f}% above 15% cap")
    if f.get("short_tenor"):
        add("short_tenor", f"tenor from {f.get('tenor_min_days')} days")
    for key, label in (("advance_fee", "asks for fees before disbursement"),
                       ("no_bureau_check", "advertises no credit-bureau check"),
                       ("daily_repayment", "daily repayment"),
                       ("no_documents", "no documents needed"),
                       ("instant_approval", "instant approval"),
                       ("messaging_only_contact", "contact via messaging app"),
                       ("category_mismatch", "lending app outside Finance category"),
                       ("free_email_developer", "developer uses free e-mail"),
                       ("no_privacy_policy", "no privacy policy"),
                       ("privacy_on_free_host", "privacy policy on free hosting"),
                       ("apk_sideload_link", "links to sideloaded APK")):
        if f.get(key):
            add(key, label)
    n_sens = int(f.get("n_sensitive_permissions") or 0)
    if n_sens:
        pts = min(w["sensitive_permission_cap"], n_sens * w["sensitive_permission_each"])
        add("sensitive_permission_each", f"sensitive permissions: {f.get('sensitive_permissions')}", pts)
    share = float(f.get("harm_review_share") or 0.0)
    if share >= 0.05:
        add("harm_reviews_high", f"{share:.0%} of reviews report harm")
    elif share >= 0.01:
        add("harm_reviews_some", f"{share:.0%} of reviews report harm")
    if int(f.get("operator_size") or 1) >= 3:
        add("clone_cluster", f"operator controls {f.get('operator_size')} artefacts")

    score = int(min(100, score))
    tier = "high" if score >= C.TIER_HIGH else "medium" if score >= C.TIER_MEDIUM else "low"
    return score, tier, reasons


# --------------------------------------------------------------------------- #
# Evaluation helpers
# --------------------------------------------------------------------------- #
def auc(y_true, scores) -> float:
    """Area under the ROC curve via the rank-sum identity (ties get mid-ranks)."""
    y = np.asarray(y_true, dtype=int)
    s = np.asarray(scores, dtype=float)
    n1, n0 = int(y.sum()), int((1 - y).sum())
    if n1 == 0 or n0 == 0:
        return float("nan")
    order = np.argsort(s, kind="mergesort")
    ranks = np.empty(len(s))
    i = 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and s[order[j + 1]] == s[order[i]]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return float((ranks[y == 1].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0))


def precision_at_k(y_true, scores, k: int) -> float:
    y = np.asarray(y_true, dtype=int)
    k = min(k, len(y))
    if k == 0:
        return float("nan")
    top = np.argsort(-np.asarray(scores, dtype=float), kind="mergesort")[:k]
    return float(y[top].mean())


def choose_threshold(y_true, scores, cost_fp: float = 1.0, cost_fn: float = 5.0) -> dict:
    """Threshold minimising expected cost. cost_fn > cost_fp encodes that a missed
    predatory lender is worse than a wasted review; set the ratio explicitly."""
    y = np.asarray(y_true, dtype=int)
    s = np.asarray(scores, dtype=float)
    best = None
    for t in np.unique(s):
        pred = s >= t
        fp = int((pred & (y == 0)).sum())
        fn = int((~pred & (y == 1)).sum())
        tp = int((pred & (y == 1)).sum())
        cost = cost_fp * fp + cost_fn * fn
        if best is None or cost < best["cost"]:
            best = {"threshold": float(t), "cost": float(cost), "tp": tp, "fp": fp, "fn": fn,
                    "precision": tp / max(1, tp + fp), "recall": tp / max(1, tp + fn)}
    return best or {}


def fit_supervised(rows: list[dict], labels: list[int], n_splits: int = 5, seed: int = 0) -> dict:
    """Out-of-fold logistic regression on NUMERIC_FEATURES.

    Returns out-of-fold probabilities, AUC, precision@k and standardised coefficients.
    Use reviewer labels; with fewer than ~200 labelled cases prefer the rule score.
    """
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import StratifiedKFold
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    X = np.array([[float(r.get(k) or 0.0) for k in NUMERIC_FEATURES] for r in rows])
    y = np.asarray(labels, dtype=int)
    oof = np.zeros(len(y))
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    for tr, te in cv.split(X, y):
        model = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=2000))
        model.fit(X[tr], y[tr])
        oof[te] = model.predict_proba(X[te])[:, 1]
    final = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=2000)).fit(X, y)
    coefs = dict(zip(NUMERIC_FEATURES, final[-1].coef_[0].round(3).tolist()))
    k = max(1, int(y.sum()))
    return {
        "oof_probability": oof,
        "auc": auc(y, oof),
        "precision_at_n_positives": precision_at_k(y, oof, k),
        "coefficients": dict(sorted(coefs.items(), key=lambda kv: -abs(kv[1]))),
        "model": final,
    }
