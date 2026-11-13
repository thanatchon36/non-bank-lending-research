"""Turn one collected artefact (app listing, website, ad) into red-flag features."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Optional

from . import config as C
from .rates import extract_tenor_days, max_annualised_rate
from .registry import LicensedRegistry
from .textutils import (extract_identifiers, host_of, mask_numbers, normalize_text,
                        registrable_domain)

_FLAG_RX = {k: [re.compile(p) for p in pats] for k, pats in C.RED_FLAG_PATTERNS.items()}


def _count_terms(text: str, terms: list[str]) -> int:
    return sum(1 for t in terms if t in text)


def review_signals(reviews: list[dict]) -> dict:
    """Share of reviews that mention each family of harm (collection abuse, scams...)."""
    n = len(reviews or [])
    out = {"n_reviews": n, "harm_review_share": 0.0, "low_rating_share": 0.0}
    for fam in C.HARM_TERMS:
        out[f"harm_{fam}_share"] = 0.0
    if n == 0:
        return out
    any_hit = low = 0
    fam_hits = {fam: 0 for fam in C.HARM_TERMS}
    for r in reviews:
        txt = normalize_text(r.get("text"))
        hit = False
        for fam, terms in C.HARM_TERMS.items():
            if any(t in txt for t in terms):
                fam_hits[fam] += 1
                hit = True
        any_hit += hit
        score = r.get("score")
        low += 1 if (score is not None and float(score) <= 2) else 0
    out["harm_review_share"] = any_hit / n
    out["low_rating_share"] = low / n
    for fam, k in fam_hits.items():
        out[f"harm_{fam}_share"] = k / n
    return out


def sensitive_permissions(perms: list[str]) -> list[str]:
    blob = " | ".join(perms or []).lower()
    return [fam for fam, needles in C.SENSITIVE_PERMISSIONS.items()
            if any(nd in blob for nd in needles)]


def _age_days(iso: Optional[str], now: datetime) -> Optional[int]:
    if not iso:
        return None
    try:
        d = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
    except ValueError:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return max(0, (now - d).days)


def compute_features(art: dict, registry: LicensedRegistry,
                     now: Optional[datetime] = None) -> dict:
    """Return a flat dict of features for one artefact. Booleans are 0/1 ints."""
    now = now or datetime.now(timezone.utc)
    name = normalize_text(art.get("name"))
    desc = normalize_text(art.get("description"))
    text = f"{name} . {desc}"
    f: dict = {"artefact_id": art.get("artefact_id"), "source": art.get("source")}

    # --- relevance -------------------------------------------------------- #
    lend_name = _count_terms(name, C.LENDING_TERMS)
    lend_desc = _count_terms(desc, C.LENDING_TERMS)
    f["is_lending_related"] = int(lend_name + lend_desc >= 1)
    offers = _count_terms(text, C.OFFER_TERMS)
    tool = _count_terms(text, C.TOOL_ONLY_TERMS)
    f["offers_credit"] = int(f["is_lending_related"] and offers >= 1 and not (tool >= 1 and offers <= 1))
    cat = (art.get("category") or "").lower()
    f["category_mismatch"] = int(bool(cat) and f["offers_credit"] == 1
                                 and "financ" not in cat and "การเงิน" not in cat)

    # --- licence match ---------------------------------------------------- #
    aid = str(art.get("artefact_id") or "")
    app_id = aid.split(":", 1)[1] if ":" in aid else aid
    is_web = art.get("source") == "web"
    own = (art.get("url"),) if is_web and art.get("url") else ()
    claimed = (art.get("developer_website"),) if art.get("developer_website") else ()
    m = registry.match(app_id=app_id, developer=art.get("developer") or "",
                       name=art.get("name") or "", own_urls=own, claimed_urls=claimed)
    f["licence_status"] = m.status
    f["matched_licensee"] = m.licensee or ""
    f["impersonates"] = m.impersonates or ""
    f["licensed"] = int(m.licensed)
    f["name_only_licence_match"] = int(m.status == "licensed_name")
    f["impersonates_licensed_brand"] = int(bool(m.impersonates))
    f["unlicensed_offering_credit"] = int(not m.licensed and f["offers_credit"] == 1)

    # --- price and tenor -------------------------------------------------- #
    rate, mentions = max_annualised_rate(text)
    f["max_annualised_rate"] = rate
    f["rate_evidence"] = mask_numbers(
        " || ".join(r.raw for r in mentions if r.annualised is not None))[:400]
    f["rate_above_any_ceiling"] = int(rate is not None and rate > C.MAX_SUPERVISED_CEILING)
    f["rate_above_unlicensed_cap"] = int(rate is not None and not m.licensed
                                         and C.UNLICENSED_CEILING < rate <= C.MAX_SUPERVISED_CEILING)
    tmin, tmax = extract_tenor_days(text)
    f["tenor_min_days"], f["tenor_max_days"] = tmin, tmax
    f["short_tenor"] = int(tmin is not None and tmin <= C.PLATFORM_MIN_TENOR_DAYS)

    # --- marketing language ----------------------------------------------- #
    for flag, rxs in _FLAG_RX.items():
        f[flag] = int(any(rx.search(text) for rx in rxs))

    # --- permissions ------------------------------------------------------ #
    sens = sensitive_permissions(art.get("permissions") or [])
    f["sensitive_permissions"] = ";".join(sens)
    f["n_sensitive_permissions"] = len(sens)

    # --- reviews ---------------------------------------------------------- #
    f.update(review_signals(art.get("reviews") or []))

    # --- developer / hosting metadata ------------------------------------- #
    email = (art.get("developer_email") or "").lower()
    f["free_email_developer"] = int("@" in email and email.split("@")[-1] in C.FREE_EMAIL_DOMAINS)
    is_store = art.get("source") in ("google_play", "app_store")
    pp_host = host_of(art.get("privacy_policy_url"))
    f["no_privacy_policy"] = int(is_store and not pp_host)
    f["privacy_on_free_host"] = int(bool(pp_host) and (
        pp_host in C.FREE_HOSTING or registrable_domain(pp_host) in C.FREE_HOSTING))
    ids = extract_identifiers(" ".join(str(x) for x in (
        art.get("description") or "", " ".join(art.get("outbound_links") or []))))
    f["apk_sideload_link"] = int(bool(ids["apk_links"] or art.get("apk_links")))
    f["n_messaging_ids"] = len(set(ids["line_ids"]) | set(art.get("line_ids") or []))
    f["age_days"] = _age_days(art.get("released"), now)
    f["installs_min"] = art.get("installs_min")
    return f
