"""Evidence integrity.

Every raw snapshot is stored with its SHA-256 hash and UTC time in an append-only,
hash-chained manifest (each line commits to the previous one), so that a watchlist
entry can later be shown to a court, a platform or the operator exactly as collected.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone

from . import config as C


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_json(obj) -> str:
    blob = json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _safe(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name)[:120]


class EvidenceStore:
    def __init__(self, base_dir: str):
        self.base = base_dir
        self.raw_dir = os.path.join(base_dir, "raw")
        self.manifest = os.path.join(base_dir, "manifest.jsonl")
        os.makedirs(self.raw_dir, exist_ok=True)
        self._prev = self._last_hash()

    def _last_hash(self) -> str:
        if not os.path.exists(self.manifest):
            return "0" * 64
        last = ""
        with open(self.manifest, encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    last = line
        return json.loads(last)["entry_sha256"] if last else "0" * 64

    def save(self, artefact: dict) -> dict:
        """Persist one artefact snapshot; return its manifest entry."""
        digest = sha256_json(artefact)
        ts = artefact.get("collected_at") or utc_now()
        fname = f"{_safe(str(artefact.get('artefact_id')))}_{_safe(ts)}_{digest[:8]}.json"
        with open(os.path.join(self.raw_dir, fname), "w", encoding="utf-8") as fh:
            json.dump(artefact, fh, ensure_ascii=False, sort_keys=True, default=str)
        entry = {
            "artefact_id": artefact.get("artefact_id"), "source": artefact.get("source"),
            "source_url": artefact.get("url"), "collected_at": ts, "file": f"raw/{fname}",
            "content_sha256": digest, "collector_version": C.VERSION, "prev_entry_sha256": self._prev,
        }
        entry["entry_sha256"] = sha256_json(entry)
        with open(self.manifest, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        self._prev = entry["entry_sha256"]
        return entry

    def verify(self) -> bool:
        """Re-compute the chain and every file hash. True if nothing was altered."""
        prev = "0" * 64
        if not os.path.exists(self.manifest):
            return True
        with open(self.manifest, encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                e = json.loads(line)
                claimed = e.pop("entry_sha256")
                if e["prev_entry_sha256"] != prev or sha256_json(e) != claimed:
                    return False
                with open(os.path.join(self.base, e["file"]), encoding="utf-8") as raw:
                    if sha256_json(json.load(raw)) != e["content_sha256"]:
                        return False
                prev = claimed
        return True


def evidence_pack(row: dict, reasons: list[str], manifest_entry: dict | None = None) -> str:
    """One-page Markdown case file for a human reviewer."""
    hooks = []
    for key, text in C.LEGAL_HOOKS.items():
        if row.get(key) or (key == "sensitive_permissions" and row.get("n_sensitive_permissions")) \
                or (key == "harm_reviews" and float(row.get("harm_review_share") or 0) >= 0.01):
            hooks.append(f"- {text}")
    lines = [
        f"# Case file: {row.get('name') or row.get('artefact_id')}",
        "",
        "> Automated triage output for human review. Not a finding of illegality.",
        "> Verify every item against the stored snapshot before any action.",
        "",
        f"- Artefact: `{row.get('artefact_id')}` ({row.get('source')})",
        f"- URL: {row.get('url') or 'n/a'}",
        f"- Developer / seller: {row.get('developer') or 'n/a'}",
        f"- Operator cluster: `{row.get('operator_id')}` ({row.get('operator_size')} artefacts)",
        f"- Licence match: {row.get('licence_status')} {row.get('matched_licensee') or ''}".rstrip(),
        f"- Risk score: {row.get('risk_score')} ({row.get('tier')})",
        "",
        "## Red flags",
        *[f"- {r}" for r in reasons],
        "",
        "## Parsed terms (verify against snapshot)",
        "- Highest annualised rate parsed: " + (
            f"about {float(row['max_annualised_rate']):.0f}% (simple annualisation)"
            if row.get("max_annualised_rate") is not None else "none"),
        f"- Rate text: {row.get('rate_evidence') or 'n/a'}",
        f"- Tenor (days): {row.get('tenor_min_days')} to {row.get('tenor_max_days')}",
        f"- Sensitive permissions: {row.get('sensitive_permissions') or 'none'}",
        f"- Reviews reporting harm: {float(row.get('harm_review_share') or 0):.1%} of {row.get('n_reviews')}",
        "",
        "## Legal hooks to consider",
        *(hooks or ["- none identified automatically"]),
    ]
    if manifest_entry:
        lines += ["", "## Evidence integrity",
                  f"- Collected at (UTC): {manifest_entry['collected_at']}",
                  f"- Snapshot file: {manifest_entry['file']}",
                  f"- SHA-256: `{manifest_entry['content_sha256']}`"]
    return "\n".join(lines) + "\n"
