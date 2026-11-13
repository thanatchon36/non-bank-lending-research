"""Allow-list of licensed lenders and their digital channels.

The registry is the heart of detection-driven supervision: anything offering credit
that cannot be matched to it is *presumptively* unlicensed and goes to human review.
Build the CSV from the official Bank of Thailand and Fiscal Policy Office lists
(see data/licensed_registry_template.csv for the columns).
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from typing import Optional

from .textutils import host_of, normalize_company_name, normalize_text, registrable_domain

try:                                    # rapidfuzz is fast; difflib is the fallback
    from rapidfuzz import fuzz

    def _ratio(a: str, b: str) -> float:
        return max(fuzz.ratio(a, b), fuzz.token_sort_ratio(a, b))

    def _partial(a: str, b: str) -> float:
        return fuzz.partial_ratio(a, b)
except ImportError:                     # pragma: no cover
    from difflib import SequenceMatcher

    def _ratio(a: str, b: str) -> float:
        return 100.0 * SequenceMatcher(None, a, b).ratio()

    def _partial(a: str, b: str) -> float:
        return 100.0 if a in b else _ratio(a, b)


def _split(cell: str) -> list[str]:
    return [x.strip() for x in (cell or "").split(";") if x.strip()]


@dataclass
class Licensee:
    entity_name_th: str = ""
    entity_name_en: str = ""
    brand_names: list[str] = field(default_factory=list)
    licence_type: str = ""
    regulator: str = ""
    app_ids: list[str] = field(default_factory=list)
    domains: list[str] = field(default_factory=list)
    source_url: str = ""
    as_of: str = ""

    @property
    def label(self) -> str:
        return self.entity_name_en or self.entity_name_th


@dataclass
class Match:
    status: str                         # licensed_exact | licensed_domain | licensed_name | unmatched
    licensee: Optional[str] = None
    score: float = 0.0
    impersonates: Optional[str] = None  # licensed brand named by an unmatched artefact

    @property
    def licensed(self) -> bool:
        return self.status != "unmatched"


class LicensedRegistry:
    def __init__(self, licensees: list[Licensee], name_threshold: float = 90.0,
                 brand_threshold: float = 92.0):
        self.licensees = licensees
        self.name_threshold = name_threshold
        self.brand_threshold = brand_threshold
        self._app_ids, self._domains, self._names, self._brands = {}, {}, [], []
        for lic in licensees:
            for a in lic.app_ids:
                self._app_ids[a.lower()] = lic
            for d in lic.domains:
                self._domains[registrable_domain(host_of(d))] = lic
            for n in (lic.entity_name_th, lic.entity_name_en):
                n = normalize_company_name(n)
                if n:
                    self._names.append((n, lic))
            for b in lic.brand_names:
                b = normalize_text(b)
                if len(b) >= 4:
                    self._brands.append((b, lic))

    @classmethod
    def from_csv(cls, path: str, **kw) -> "LicensedRegistry":
        rows = []
        with open(path, encoding="utf-8-sig", newline="") as fh:
            for r in csv.DictReader(fh):
                rows.append(Licensee(
                    entity_name_th=(r.get("entity_name_th") or "").strip(),
                    entity_name_en=(r.get("entity_name_en") or "").strip(),
                    brand_names=_split(r.get("brand_names", "")),
                    licence_type=(r.get("licence_type") or "").strip(),
                    regulator=(r.get("regulator") or "").strip(),
                    app_ids=_split(r.get("app_ids", "")),
                    domains=_split(r.get("domains", "")),
                    source_url=(r.get("source_url") or "").strip(),
                    as_of=(r.get("as_of") or "").strip(),
                ))
        return cls(rows, **kw)

    def __len__(self) -> int:
        return len(self.licensees)

    def match(self, *, app_id: str = "", developer: str = "", name: str = "",
              own_urls: tuple = (), claimed_urls: tuple = ()) -> Match:
        """Match an artefact to a licensee.

        Registered channels are authoritative: a registered app id, or the artefact's
        OWN domain (a website). Names and self-declared developer websites are only
        claims that anyone can type into a store listing, so they give the weaker
        status ``licensed_name`` and should be confirmed by a reviewer.
        """
        if app_id and app_id.lower() in self._app_ids:
            return Match("licensed_exact", self._app_ids[app_id.lower()].label, 100.0)
        for u in own_urls:
            dom = registrable_domain(host_of(u))
            if dom and dom in self._domains:
                return Match("licensed_domain", self._domains[dom].label, 100.0)
        for u in claimed_urls:
            dom = registrable_domain(host_of(u))
            if dom and dom in self._domains:
                return Match("licensed_name", self._domains[dom].label, 95.0)
        dev = normalize_company_name(developer)
        best, best_lic = 0.0, None
        if dev:
            for n, lic in self._names:
                s = _ratio(dev, n)
                if s > best:
                    best, best_lic = s, lic
        if best_lic is not None and best >= self.name_threshold:
            return Match("licensed_name", best_lic.label, best)
        title = normalize_text(name)
        for b, lic in self._brands:
            if title and _partial(b, title) >= self.brand_threshold:
                return Match("unmatched", None, best, impersonates=lic.label)
        return Match("unmatched", None, best)
