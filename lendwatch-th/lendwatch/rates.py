"""Extract advertised rates and tenors from Thai/English text and annualise them.

Annualisation is simple (nominal, no compounding): daily x365, weekly x52, monthly x12.
That is conservative: true effective rates of short loans with upfront deductions are
higher. Every parsed figure is a lead for a human reviewer, never a finding.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Optional

from .textutils import normalize_text

_NUM = r"\d{1,4}(?:[.,]\d{1,3})?"
_PCT = re.compile(
    rf"ร้อยละ\s*(?P<a>{_NUM})(?:\s*%)?|(?P<b>{_NUM})\s*(?:%|เปอร์เซ็นต์|เปอร์เซนต์|percent)"
)
_MULT = {"day": 365.0, "week": 52.0, "month": 12.0, "year": 1.0}
_CONN = r"(?:ต่อ|/|per|a|each)\s*"

# Period cue directly AFTER the number: "1% ต่อวัน", "2%/เดือน", "25% p.a."
_AFTER = [
    ("day", re.compile(rf"^\s*(?:{_CONN}(?:วัน|day)|รายวัน|daily)")),
    ("week", re.compile(rf"^\s*(?:{_CONN}(?:สัปดาห์|อาทิตย์|week|wk)|รายสัปดาห์|weekly)")),
    ("month", re.compile(rf"^\s*(?:{_CONN}(?:เดือน|month|mo(?![a-z]))|รายเดือน|monthly)")),
    ("year", re.compile(rf"^\s*(?:{_CONN}(?:ปี|year|annum|yr)|รายปี|p\.?\s?a\.?(?![a-z])|apr|annual|yearly)")),
]


def _before(prefix_cue: str, tight_cue: str, suffix_cue: str, en_cue: str) -> re.Pattern:
    """Period cue BEFORE the number, each form with its own maximum gap."""
    parts = [
        rf"(?:{prefix_cue})[^%\d]{{0,10}}$",                 # "วันละเพียง 1%"
        rf"(?:{tight_cue})[^%\d]{{0,3}}$",                   # "รายวัน 1%"
        rf"(?<!%)(?<!% )(?:{suffix_cue})[^%\d]{{0,16}}$",    # "ดอกเบี้ยต่อปี (APR) สูงสุด 25%"
        rf"(?:{en_cue})[a-z ]{{0,24}}(?:rate|interest)[^%\d]{{0,10}}$",
    ]
    return re.compile("|".join(parts))


_BEFORE = [
    ("day", _before("วันละ", "รายวัน|daily", "ต่อวัน|per day", "daily")),
    ("week", _before("สัปดาห์ละ|อาทิตย์ละ", "รายสัปดาห์|weekly", "ต่อสัปดาห์|per week", "weekly")),
    ("month", _before("เดือนละ", "รายเดือน|monthly", "ต่อเดือน|per month", "monthly")),
    ("year", _before("ปีละ", "รายปี", "ต่อปี|per year|per annum|apr", "annual|yearly")),
]
_COST_CUE = re.compile(r"(ดอกเบี้ย|ดอก|ค่าธรรมเนียม|ค่าบริการ|ค่าดำเนินการ|interest|fee|charge)[^%\d]{0,14}$")

_UNIT_DAYS = {"วัน": 1, "day": 1, "days": 1, "เดือน": 30, "month": 30, "months": 30,
              "ปี": 365, "year": 365, "years": 365}
_UNIT = r"(วัน|days?|เดือน|months?|ปี|years?)"
_SEP = r"(?:-|–|ถึง|to|~)"
_TENOR_CUE = (
    r"(?:ระยะเวลา|ผ่อน|ชำระคืน|คืนเงิน|กำหนดชำระ|ครบกำหนด|tenor|tenure|loan term|"
    r"repayment|repay)"
)
_RANGE = re.compile(rf"(\d{{1,3}})\s*{_UNIT}?\s*{_SEP}\s*(\d{{1,3}})\s*{_UNIT}")
_SINGLE = re.compile(rf"{_TENOR_CUE}[^\d%]{{0,22}}?(\d{{1,3}})\s*{_UNIT}")
# Durations that are NOT loan tenors: approval/processing times, ages, promo periods.
_NOT_TENOR = re.compile(
    r"(อนุมัติ|approv|ได้เงิน|เงินเข้า|ปลอดดอก|แรก|first|อายุ|aged?|ทราบผล|ภายใน|within)[^\d]{0,14}$"
)
_IS_TENOR = re.compile(_TENOR_CUE + r"[^\d]{0,22}$")


@dataclass
class RateMention:
    raw: str                      # text snippet around the figure
    pct: float                    # the percentage as written
    period: Optional[str]         # day | week | month | year | tenor | None
    annualised: Optional[float]   # simple annualised % ; None if period unknown
    method: str                   # how the period was inferred

    def to_dict(self) -> dict:
        return asdict(self)


def _to_float(s: str) -> float:
    if "," in s:
        head, tail = s.split(",", 1)
        s = head + tail if len(tail) == 3 else head + "." + tail
    return float(s)


def extract_tenor_days(text) -> tuple[Optional[int], Optional[int]]:
    """Return (shortest, longest) loan tenor in days mentioned in the text."""
    t = normalize_text(text)
    found: list[int] = []
    for m in _RANGE.finditer(t):
        pre = t[max(0, m.start() - 26):m.start()]
        if t[m.end():m.end() + 6].lstrip().startswith("ทำการ"):      # "working days"
            continue
        if _NOT_TENOR.search(pre) and not _IS_TENOR.search(pre):
            continue
        lo, unit_lo, hi, unit_hi = m.group(1), m.group(2), m.group(3), m.group(4)
        found.append(int(lo) * _UNIT_DAYS[unit_lo or unit_hi])
        found.append(int(hi) * _UNIT_DAYS[unit_hi])
    for m in _SINGLE.finditer(t):
        found.append(int(m.group(1)) * _UNIT_DAYS[m.group(2)])
    found = [d for d in found if 0 < d <= 365 * 30]
    return (min(found), max(found)) if found else (None, None)


def extract_rates(text) -> list[RateMention]:
    """Find every percentage in the text and try to attach a period to it."""
    t = normalize_text(text)
    _, tenor_max = extract_tenor_days(t)
    out: list[RateMention] = []
    for m in _PCT.finditer(t):
        pct = _to_float(m.group("a") or m.group("b"))
        after = t[m.end():m.end() + 16]
        before = t[max(0, m.start() - 44):m.start()]
        period, method = None, "unknown"
        for name, rx in _AFTER:
            if rx.search(after):
                period, method = name, "cue_after"
                break
        if period is None:
            for name, rx in _BEFORE:
                if rx.search(before):
                    period, method = name, "cue_before"
                    break
        annualised = None
        if period:
            annualised = pct * _MULT[period]
        elif tenor_max and tenor_max <= 90 and _COST_CUE.search(before):
            # a flat charge quoted against a short loan: spread over the longest tenor
            period, method = "tenor", f"flat_over_{tenor_max}_days"
            annualised = pct * 365.0 / tenor_max
        snippet = t[max(0, m.start() - 30):m.end() + 16]
        out.append(RateMention(snippet, pct, period, annualised, method))
    return out


def max_annualised_rate(text) -> tuple[Optional[float], list[RateMention]]:
    mentions = extract_rates(text)
    vals = [r.annualised for r in mentions if r.annualised is not None]
    return (max(vals) if vals else None), mentions
