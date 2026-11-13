import csv
import glob
import json
import os
import re

from lendwatch.cli import main
from lendwatch.evidence import EvidenceStore
from lendwatch.textutils import extract_identifiers


def test_demo_end_to_end(tmp_path):
    out = str(tmp_path / "run")
    assert main(["demo", "--out", out, "--operators", "120", "--seed", "5"]) == 0
    for name in ("watchlist.csv", "operators.csv", "mse.json", "summary.md"):
        assert os.path.exists(os.path.join(out, name))
    rows = list(csv.DictReader(open(os.path.join(out, "watchlist.csv"), encoding="utf-8-sig")))
    scores = [int(r["risk_score"]) for r in rows]
    assert scores == sorted(scores, reverse=True)
    # registered channels of licensees never enter the unlicensed queue
    assert all(r["tier"] == "licensed_channel" for r in rows
               if r["licence_status"] in ("licensed_exact", "licensed_domain"))
    # analysis tables must not leak raw phone or account numbers (linkage uses hashes)
    numbers = set()
    for line in open(os.path.join(out, "demo_artefacts.jsonl"), encoding="utf-8"):
        ids = extract_identifiers(json.loads(line).get("description") or "")
        numbers |= set(ids["phones"]) | set(ids["bank_accounts"])
    assert numbers
    for name in ("watchlist.csv", "operators.csv", "summary.md", "mse.json"):
        text = re.sub(r"[\s\-]", "", open(os.path.join(out, name), encoding="utf-8-sig").read())
        assert not any(n in text for n in numbers), name
    assert glob.glob(os.path.join(out, "cases", "*.md"))
    mse = json.load(open(os.path.join(out, "mse.json"), encoding="utf-8"))
    assert mse["loglinear"]["N"] >= mse["n_observed"]


def test_evidence_chain_detects_tampering(tmp_path):
    store = EvidenceStore(str(tmp_path / "ev"))
    for i in range(3):
        store.save({"artefact_id": f"gp:app{i}", "source": "google_play", "name": f"app {i}",
                    "collected_at": "2026-11-01T00:00:00Z"})
    assert store.verify()
    victim = sorted(glob.glob(str(tmp_path / "ev" / "raw" / "*.json")))[1]
    data = json.load(open(victim, encoding="utf-8"))
    data["name"] = "edited after collection"
    json.dump(data, open(victim, "w", encoding="utf-8"), ensure_ascii=False, sort_keys=True)
    assert not EvidenceStore(str(tmp_path / "ev")).verify()
