"""Operator attribution.

One illegal operator typically runs many apps, domains and accounts. Artefacts are
linked when they share a *hard* identifier (developer account or e-mail, signing
certificate, exact privacy-policy URL, own domain, LINE id, hashed phone or bank
account, or an explicit reference such as a complaint naming an app). Optionally,
near-duplicate descriptions add *soft* links. Connected components are operators.

Phone and account numbers are stored only as salted hashes.
"""
from __future__ import annotations

import hashlib
from collections import defaultdict

from . import config as C
from .textutils import (extract_identifiers, host_of, normalize_text, registrable_domain,
                        salted_hash, url_key)


class _UnionFind:
    def __init__(self):
        self.parent: dict = {}

    def find(self, x):
        self.parent.setdefault(x, x)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[max(ra, rb)] = min(ra, rb)


def linkage_keys(art: dict, salt: str) -> set[tuple[str, str]]:
    """Hard identifiers carried by one artefact, as (kind, value) pairs."""
    keys: set[tuple[str, str]] = set()
    aid = art.get("artefact_id")
    if aid:
        keys.add(("ref", str(aid)))
    for ref in art.get("mentions_artefacts") or []:
        keys.add(("ref", str(ref)))
    if art.get("developer_id"):
        keys.add(("devid", f"{art.get('source')}:{art['developer_id']}"))
    email = (art.get("developer_email") or "").strip().lower()
    if "@" in email:
        keys.add(("email", email))
    if art.get("signing_cert_sha256"):
        keys.add(("cert", str(art["signing_cert_sha256"]).lower()))
    pp = url_key(art.get("privacy_policy_url"))
    if pp:
        keys.add(("privacy", pp))
    for u in (art.get("developer_website"), art.get("url") if art.get("source") == "web" else None):
        host = host_of(u)
        dom = registrable_domain(host)
        if dom and dom not in C.GENERIC_HOSTS and host not in C.GENERIC_HOSTS:
            keys.add(("site", dom))
    text = " ".join(str(x) for x in (art.get("description") or "", art.get("name") or "",
                                     " ".join(art.get("outbound_links") or [])))
    ids = extract_identifiers(text)
    for x in set(ids["line_ids"]) | {str(v).lower().lstrip("@") for v in art.get("line_ids") or []}:
        keys.add(("line", x))
    for x in ids["telegram"]:
        keys.add(("telegram", x))
    for x in set(ids["phones"]) | set(art.get("phones") or []):
        keys.add(("phone", salted_hash(str(x), salt)))
    for x in set(ids["bank_accounts"]) | set(art.get("bank_accounts") or []):
        keys.add(("bank", salted_hash(str(x), salt)))
    return keys


def _soft_pairs(artefacts: list[dict], threshold: float, min_chars: int):
    """Pairs of artefacts whose descriptions are near-duplicates (char n-gram TF-IDF)."""
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
    except ImportError:                 # pragma: no cover
        return []
    idx = [i for i, a in enumerate(artefacts)
           if len(normalize_text(a.get("description"))) >= min_chars]
    if len(idx) < 2:
        return []
    docs = [normalize_text(artefacts[i].get("description")) for i in idx]
    # Character n-grams need no Thai word segmentation.
    X = TfidfVectorizer(analyzer="char", ngram_range=(3, 5), min_df=1,
                        sublinear_tf=True).fit_transform(docs)
    sim = (X @ X.T).tocoo()
    return [(idx[i], idx[j], float(v)) for i, j, v in zip(sim.row, sim.col, sim.data)
            if i < j and v >= threshold]


def link_operators(artefacts: list[dict], salt: str, use_text_similarity: bool = False,
                   text_threshold: float = 0.92, min_chars: int = 200) -> dict:
    """Cluster artefacts into operators.

    Returns {"operator_of": {artefact_id: operator_id},
             "operators": {operator_id: {"members", "sources", "n", "link_kinds"}}}
    """
    uf = _UnionFind()
    by_key: dict[tuple[str, str], list[str]] = defaultdict(list)
    for a in artefacts:
        aid = str(a["artefact_id"])
        uf.find(aid)
        for k in linkage_keys(a, salt):
            by_key[k].append(aid)
    kinds_used: dict[str, set] = defaultdict(set)
    for (kind, value), members in by_key.items():
        if len(set(members)) < 2:
            continue
        first = members[0]
        for other in members[1:]:
            uf.union(first, other)
        for mbr in members:
            kinds_used[mbr].add(kind)
    if use_text_similarity:
        for i, j, _ in _soft_pairs(artefacts, text_threshold, min_chars):
            a, b = str(artefacts[i]["artefact_id"]), str(artefacts[j]["artefact_id"])
            uf.union(a, b)
            kinds_used[a].add("text")
            kinds_used[b].add("text")

    groups: dict[str, list[dict]] = defaultdict(list)
    for a in artefacts:
        groups[uf.find(str(a["artefact_id"]))].append(a)
    operator_of, operators = {}, {}
    for members in groups.values():
        ids = sorted(str(m["artefact_id"]) for m in members)
        op_id = "OP-" + hashlib.sha256("|".join(ids).encode()).hexdigest()[:10]
        kinds = sorted(set().union(*(kinds_used[i] for i in ids)))
        operators[op_id] = {
            "members": ids,
            "n": len(ids),
            "sources": sorted({m.get("source") for m in members if m.get("source")}),
            "link_kinds": kinds,
        }
        for i in ids:
            operator_of[i] = op_id
    return {"operator_of": operator_of, "operators": operators}
