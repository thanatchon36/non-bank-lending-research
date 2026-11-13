"""End-to-end analysis: artefacts in, supervisory outputs out.

Outputs (in ``out_dir``)
  watchlist.csv     one row per scored artefact, highest risk first
  operators.csv     one row per linked operator cluster
  mse.json          hidden-population estimates with all estimators side by side
  summary.md        counts, estimates and (if labels exist) evaluation
  cases/*.md        evidence packs for the highest-risk artefacts
  evidence/         raw snapshots + hash-chained manifest
"""
from __future__ import annotations

import csv
import json
import os
from collections import Counter
from typing import Optional

import numpy as np

from . import config as C
from .evidence import EvidenceStore, evidence_pack
from .features import compute_features
from .linkage import link_operators
from .mse import estimate_population
from .registry import LicensedRegistry
from .scoring import auc, choose_threshold, fit_supervised, precision_at_k, rule_score

SCORED_SOURCES = ("google_play", "app_store", "web", "ad")
MSE_LISTS = ("google_play", "app_store", "web", "ad", "complaint")
WATCHLIST_COLUMNS = [
    "risk_score", "tier", "artefact_id", "source", "name", "developer", "url", "operator_id",
    "operator_size", "licence_status", "matched_licensee", "impersonates", "reasons",
    "max_annualised_rate", "rate_evidence", "tenor_min_days", "tenor_max_days",
    "sensitive_permissions", "n_reviews", "harm_review_share", "collected_at", "content_sha256",
]


def _public(art: dict) -> dict:
    """Drop ground-truth fields (keys starting with '_') before storing or scoring."""
    return {k: v for k, v in art.items() if not k.startswith("_")}


def _write_csv(path: str, rows: list[dict], columns: list[str]) -> None:
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in columns})


def run_analysis(artefacts: list[dict], registry: LicensedRegistry, salt: str, out_dir: str,
                 use_text_similarity: bool = False, n_cases: int = 25,
                 truth_labels: Optional[dict] = None, truth_operators: Optional[dict] = None,
                 truth_total_operators: Optional[int] = None) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    arts = [_public(a) for a in artefacts]

    # 1. evidence ------------------------------------------------------------ #
    store = EvidenceStore(os.path.join(out_dir, "evidence"))
    manifest = {a["artefact_id"]: store.save(a) for a in arts}

    # 2. operator linkage ---------------------------------------------------- #
    link = link_operators(arts, salt, use_text_similarity=use_text_similarity)
    op_of, ops = link["operator_of"], link["operators"]

    # 3-4. features and rule score ------------------------------------------- #
    rows = []
    for a in arts:
        if a.get("source") not in SCORED_SOURCES:
            continue
        f = compute_features(a, registry)
        f["operator_id"] = op_of[a["artefact_id"]]
        f["operator_size"] = ops[f["operator_id"]]["n"]
        score, tier, reasons = rule_score(f)
        f.update({"risk_score": score, "tier": tier, "reasons": "; ".join(reasons),
                  "name": a.get("name"), "developer": a.get("developer"), "url": a.get("url"),
                  "collected_at": a.get("collected_at"),
                  "content_sha256": manifest[a["artefact_id"]]["content_sha256"]})
        f["_reasons_list"] = reasons
        rows.append(f)
    rows.sort(key=lambda r: (-r["risk_score"], str(r["artefact_id"])))
    _write_csv(os.path.join(out_dir, "watchlist.csv"), rows, WATCHLIST_COLUMNS)

    # 5. operator table ------------------------------------------------------ #
    by_op: dict[str, list[dict]] = {}
    for r in rows:
        by_op.setdefault(r["operator_id"], []).append(r)
    op_rows = []
    for op_id, info in ops.items():
        members = by_op.get(op_id, [])
        licensed = any(m["licensed"] for m in members)
        max_score = max((m["risk_score"] for m in members), default=0)
        suspected = (not licensed) and (max_score >= C.TIER_HIGH or "complaint" in info["sources"])
        review = (not licensed) and not suspected and max_score >= C.TIER_MEDIUM
        op_rows.append({
            "operator_id": op_id, "n_artefacts": info["n"], "sources": ";".join(info["sources"]),
            "link_kinds": ";".join(info["link_kinds"]), "max_risk_score": max_score,
            "status": ("licensed" if licensed else "suspected_unlicensed" if suspected
                       else "needs_review" if review else "other"),
            "members": ";".join(info["members"]),
            **{f"on_{s}": int(s in info["sources"]) for s in MSE_LISTS},
        })
    op_rows.sort(key=lambda r: (-r["max_risk_score"], -r["n_artefacts"]))
    _write_csv(os.path.join(out_dir, "operators.csv"), op_rows,
               ["operator_id", "status", "max_risk_score", "n_artefacts", "sources", "link_kinds"]
               + [f"on_{s}" for s in MSE_LISTS] + ["members"])

    # 6. hidden-population estimate ------------------------------------------ #
    suspected = [r for r in op_rows if r["status"] == "suspected_unlicensed"]
    lists = [s for s in MSE_LISTS if sum(r[f"on_{s}"] for r in suspected) > 0]
    mse = {"error": "fewer than two lists with data"}
    if len(lists) >= 2 and suspected:
        capture = np.array([[r[f"on_{s}"] for s in lists] for r in suspected])
        mse = estimate_population(capture, lists)
    with open(os.path.join(out_dir, "mse.json"), "w", encoding="utf-8") as fh:
        json.dump(mse, fh, indent=2, ensure_ascii=False, default=float)

    # 7. evidence packs ------------------------------------------------------ #
    case_dir = os.path.join(out_dir, "cases")
    os.makedirs(case_dir, exist_ok=True)
    for i, r in enumerate([r for r in rows if r["tier"] == "high"][:n_cases], 1):
        safe = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in str(r["artefact_id"]))
        with open(os.path.join(case_dir, f"{i:03d}_{safe}.md"), "w", encoding="utf-8") as fh:
            fh.write(evidence_pack(r, r["_reasons_list"], manifest[r["artefact_id"]]))

    # 8. summary and evaluation ---------------------------------------------- #
    result = {
        "n_artefacts": len(arts), "n_scored": len(rows), "tiers": dict(Counter(r["tier"] for r in rows)),
        "licence_status": dict(Counter(r["licence_status"] for r in rows)),
        "n_operators": len(ops), "operator_status": dict(Counter(r["status"] for r in op_rows)),
        "largest_operator": max((r["n_artefacts"] for r in suspected), default=0),
        "mse": mse, "evidence_chain_valid": store.verify(),
    }
    if truth_labels:
        result["evaluation"] = _evaluate(rows, op_of, truth_labels, truth_operators or {},
                                         truth_total_operators, mse,
                                         {a["artefact_id"]: a.get("source") for a in arts})
    with open(os.path.join(out_dir, "summary.md"), "w", encoding="utf-8") as fh:
        fh.write(render_summary(result))
    return result


def _evaluate(rows, op_of, labels, true_ops, true_total, mse, source_of) -> dict:
    """Compare outputs with ground truth (synthetic data or reviewer labels)."""
    lab_rows = [r for r in rows if r["artefact_id"] in labels]
    y = [labels[r["artefact_id"]] for r in lab_rows]
    s = [r["risk_score"] for r in lab_rows]
    high = [r["tier"] == "high" for r in lab_rows]
    tp = sum(1 for h, t in zip(high, y) if h and t)
    ev = {
        "n_labelled": len(y), "n_positive": int(sum(y)),
        "rule_auc": auc(y, s), "rule_precision_at_n_positives": precision_at_k(y, s, int(sum(y))),
        "high_tier_precision": tp / max(1, sum(high)), "high_tier_recall": tp / max(1, sum(y)),
        "false_positives_in_high_tier": int(sum(1 for h, t in zip(high, y) if h and not t)),
        "cost_optimal_threshold": choose_threshold(y, s, cost_fp=1.0, cost_fn=5.0),
    }
    try:
        sup = fit_supervised(lab_rows, y)
        ev["supervised_oof_auc"] = sup["auc"]
        ev["supervised_precision_at_n_positives"] = sup["precision_at_n_positives"]
        ev["supervised_top_coefficients"] = dict(list(sup["coefficients"].items())[:8])
    except Exception as exc:            # scikit-learn missing or too few labels
        ev["supervised_error"] = str(exc)
    if true_ops:
        # linkage quality: do clusters correspond one-to-one with true operators?
        by_cluster: dict[str, set] = {}
        for a, o in true_ops.items():
            if a in op_of:
                by_cluster.setdefault(op_of[a], set()).add(o)
        ev["true_illegal_operators_observed"] = len({o for o in true_ops.values() if o.startswith("ILL")})
        ev["clusters_holding_them"] = sum(1 for v in by_cluster.values()
                                          if any(o.startswith("ILL") for o in v))
        ev["clusters_mixing_operators"] = sum(1 for v in by_cluster.values() if len(v) > 1)
    if true_total and "loglinear" in mse and "N" in mse["loglinear"]:
        ev["true_total_illegal_operators"] = true_total
        ev["suspected_operators_observed"] = mse["n_observed"]
        ev["mse_estimate"] = mse["loglinear"]["N"]
        ev["mse_ci95"] = mse["loglinear"]["ci95"]
    if true_total and true_ops:
        # Same estimator with perfect linkage and perfect labels: separates estimator
        # error (heterogeneity, dependence) from linkage and classification error.
        seen: dict[str, set] = {}
        for a, o in true_ops.items():
            if o.startswith("ILL") and source_of.get(a) in MSE_LISTS:
                seen.setdefault(o, set()).add(source_of[a])
        lists = [x for x in MSE_LISTS if any(x in v for v in seen.values())]
        oracle = estimate_population(np.array([[int(x in v) for x in lists] for v in seen.values()]), lists)
        if "N" in oracle.get("loglinear", {}):
            ev["oracle_linkage_mse_estimate"] = oracle["loglinear"]["N"]
            ev["oracle_linkage_mse_ci95"] = oracle["loglinear"]["ci95"]
            ev["oracle_linkage_chao_lower_bound"] = oracle["chao_lower_bound"]["N"]
    return ev


def render_summary(res: dict) -> str:
    out = ["# lendwatch-th run summary", "",
           "> Triage output for human review. Scores are not findings of illegality.", "",
           f"- Artefacts collected: {res['n_artefacts']} (scored: {res['n_scored']})",
           f"- Risk tiers: {res['tiers']}",
           f"- Licence match: {res['licence_status']}",
           f"- Operator clusters: {res['n_operators']} {res['operator_status']}",
           f"- Largest suspected operator: {res['largest_operator']} artefacts",
           f"- Evidence chain valid: {res['evidence_chain_valid']}", ""]
    mse = res.get("mse", {})
    ll = mse.get("loglinear", {})
    if "N" in ll:
        lo, hi = ll["ci95"]
        out += ["## Hidden population of suspected unlicensed operators", "",
                f"- Observed on at least one list: {mse['n_observed']}",
                f"- List sizes: {mse['list_sizes']}",
                f"- Log-linear, model-averaged: N = {ll['N']:.0f} (95% CI {lo:.0f}-{hi:.0f}); "
                f"total / observed = {ll['ratio_total_to_observed']:.2f}",
                f"- Best model interactions: {ll['top_models'][0]['interactions'] or 'none'}",
                f"- Chao lower bound: {mse['chao_lower_bound']['N']:.0f}", ""]
    elif mse:
        out += ["## Hidden population", "", f"- Not estimated: {ll.get('error') or mse.get('error')}", ""]
    ev = res.get("evaluation")
    if ev:
        out += ["## Evaluation against ground truth", ""]
        for k, v in ev.items():
            if isinstance(v, float):
                v = round(v, 3)
            out.append(f"- {k}: {v}")
        out.append("")
    return "\n".join(out)
