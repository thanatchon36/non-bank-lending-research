"""Run the lendwatch-th pipeline on synthetic markets with known truth, many seeds."""
import json, sys, tempfile, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
FIGS = HERE.parent / "paper" / "figs"
DATA.mkdir(exist_ok=True)
sys.path.insert(0, str(HERE.parent / "lendwatch-th"))
from lendwatch.demo import make_demo
from lendwatch.pipeline import run_analysis
from lendwatch.registry import LicensedRegistry, Licensee
from lendwatch.registry import _split

rows = []
t0 = time.time()
for seed in range(1, 31):
    d = make_demo(seed=seed)
    reg = LicensedRegistry([Licensee(entity_name_th=r["entity_name_th"], entity_name_en=r["entity_name_en"],
                                     brand_names=_split(r["brand_names"]), app_ids=_split(r["app_ids"]),
                                     domains=_split(r["domains"])) for r in d["registry_rows"]])
    arts = d["artefacts"]
    with tempfile.TemporaryDirectory() as tmp:
        res = run_analysis(arts, reg, "salt", tmp,
                           truth_labels={a["artefact_id"]: a["_true_label"] for a in arts},
                           truth_operators={a["artefact_id"]: a["_true_operator"] for a in arts},
                           truth_total_operators=d["truth"]["n_illegal_operators"])
    ev, ll = res["evaluation"], res["mse"]["loglinear"]
    rows.append({"seed": seed, "truth": 300, "true_observed": ev["true_illegal_operators_observed"],
                 "flagged_observed": res["mse"]["n_observed"], "N_hat": ll["N"], "lo": ll["ci95"][0], "hi": ll["ci95"][1],
                 "oracle": ev["oracle_linkage_mse_estimate"], "oracle_lo": ev["oracle_linkage_mse_ci95"][0],
                 "oracle_hi": ev["oracle_linkage_mse_ci95"][1], "chao": res["mse"]["chao_lower_bound"]["N"],
                 "oracle_chao": ev["oracle_linkage_chao_lower_bound"],
                 "precision": ev["high_tier_precision"], "recall": ev["high_tier_recall"], "auc": ev["rule_auc"],
                 "sup_auc": ev.get("supervised_oof_auc"), "clusters": ev["clusters_holding_them"],
                 "mixing": ev["clusters_mixing_operators"]})
    print(seed, round(ll["N"], 1), round(ev["oracle_linkage_mse_estimate"], 1), ev["true_illegal_operators_observed"], round(time.time() - t0, 1), flush=True)
json.dump(rows, open(DATA / "lendwatch_validation.json", "w"), indent=1)
