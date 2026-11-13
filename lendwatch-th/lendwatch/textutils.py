"""Thai-safe text normalisation, name/domain helpers and identifier extraction."""
from __future__ import annotations

import hashlib
import re
import unicodedata
from urllib.parse import urlparse

_THAI_DIGITS = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")
_MULTI_SUFFIXES = {
    "co.th", "in.th", "or.th", "ac.th", "go.th", "net.th", "mi.th", "co.uk", "org.uk",
    "com.cn", "com.hk", "com.sg", "com.my", "co.id", "com.vn", "com.ph", "co.in",
    "com.au", "co.jp", "co.kr",
}
_COMPANY_NOISE = [
    r"บริษัท", r"จำกัด", r"\(?มหาชน\)?", r"ห้างหุ้นส่วน", r"หจก\.?", r"บจก\.?", r"บมจ\.?",
    r"\(?ประเทศไทย\)?", r"\bpublic company limited\b", r"\bcompany limited\b",
    r"\bco\.?\s*,?\s*ltd\.?", r"\blimited\b", r"\bltd\.?", r"\bpcl\.?", r"\bplc\.?",
    r"\binc\.?", r"\bcorp(oration)?\.?", r"\(?thailand\)?",
]


def normalize_text(s) -> str:
    """Lower-case, NFKC-fold (full-width forms), Thai digits -> Arabic, collapse spaces.

    NFKC splits THAI SARA AM (U+0E33) into U+0E4D U+0E32, which would break matching
    against ordinary Thai literals, so the pair is re-composed afterwards.
    """
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", str(s)).replace("\u0e4d\u0e32", "\u0e33")
    s = s.translate(_THAI_DIGITS).lower().replace("\u200b", "")
    return re.sub(r"\s+", " ", s).strip()


def normalize_company_name(s) -> str:
    s = normalize_text(s)
    for pat in _COMPANY_NOISE:
        s = re.sub(pat, " ", s)
    s = re.sub(r"[^\w\u0e00-\u0e7f]+", " ", s)      # keep Thai combining marks
    return re.sub(r"\s+", " ", s).strip()


def host_of(url) -> str:
    if not url:
        return ""
    u = str(url).strip()
    if "://" not in u:
        u = "http://" + u
    try:
        host = urlparse(u).hostname or ""
    except ValueError:
        return ""
    host = host.lower()
    return host[4:] if host.startswith("www.") else host


def registrable_domain(host: str) -> str:
    parts = [p for p in (host or "").split(".") if p]
    if len(parts) <= 2:
        return ".".join(parts)
    if ".".join(parts[-2:]) in _MULTI_SUFFIXES:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def url_key(url) -> str:
    """host + path, lower-cased, without scheme/query: stable key for an exact URL."""
    if not url:
        return ""
    u = str(url).strip()
    if "://" not in u:
        u = "http://" + u
    try:
        p = urlparse(u)
    except ValueError:
        return ""
    host = (p.hostname or "").lower()
    host = host[4:] if host.startswith("www.") else host
    return (host + p.path.rstrip("/")).lower()


def salted_hash(value: str, salt: str) -> str:
    """Pseudonymous linkage key. The salt stays with the authority, so numbers can be
    linked across sources without storing them in clear."""
    return hashlib.sha256(f"{salt}|{value}".encode("utf-8")).hexdigest()[:16]


# --------------------------------------------------------------------------- #
# Identifier extraction (operator linkage keys found in public text and links)
# --------------------------------------------------------------------------- #
_LINE = [
    re.compile(r"line\.me/(?:r/)?ti/p/(?:~|%40|@)?([a-z0-9._\-]{3,30})"),
    re.compile(r"(lin\.ee/[a-z0-9]{4,12})"),
    re.compile(r"(?:line\s*id|ไลน์\s*ไอดี|ไอดีไลน์|line|ไลน์)\s*[:：]\s*(@?[a-z0-9._\-]{4,30})"),
    re.compile(r"(?:line|ไลน์|แอด)\s*(@[a-z0-9._\-]{3,30})"),
]
_PHONE = re.compile(r"(?<![\d\-])(?:\+66[\s\-]?|0)[689]\d[\s\-]?\d{3}[\s\-]?\d{4}(?![\d\-])")
_BANK = re.compile(r"(?<![\d\-])\d{3}-\d-\d{5}-\d(?![\d\-])")
_TELEGRAM = re.compile(r"t\.me/([a-z0-9_]{4,32})")
_APK = re.compile(r"https?://[^\s\"'<>]+?\.apk(?![a-z0-9])")


def extract_identifiers(text) -> dict:
    """Return LINE ids, Telegram handles, phone numbers, bank accounts and APK links."""
    t = normalize_text(text)
    line_ids = set()
    for rx in _LINE:
        for m in rx.findall(t):
            line_ids.add(m.lstrip("@").strip("._-"))
    phones = set()
    for m in _PHONE.findall(t):
        digits = re.sub(r"\D", "", m)
        if digits.startswith("66"):
            digits = "0" + digits[2:]
        if len(digits) == 10:
            phones.add(digits)
    return {
        "line_ids": sorted(x for x in line_ids if x),
        "telegram": sorted(set(_TELEGRAM.findall(t))),
        "phones": sorted(phones),
        "bank_accounts": sorted({re.sub(r"\D", "", m) for m in _BANK.findall(t)}),
        "apk_links": sorted(set(_APK.findall(t))),
    }


def mask_numbers(text) -> str:
    """Replace phone and bank-account numbers with a placeholder for analysis tables."""
    return _BANK.sub("[number]", _PHONE.sub("[number]", str(text or "")))
