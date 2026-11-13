import pytest

from lendwatch.rates import extract_tenor_days, max_annualised_rate

CASES = [
    ("ดอกเบี้ย 1% ต่อวัน", 365.0),
    ("ดอกเบี้ยวันละ 1.5%", 547.5),
    ("ดอกเบี้ยเพียง ๒% ต่อเดือน", 24.0),                      # Thai digits
    ("อัตราดอกเบี้ยสูงสุดร้อยละ 25 ต่อปี", 25.0),               # formal "ร้อยละ"
    ("อัตราดอกเบี้ยต่อปี (APR) สูงสุด 25%", 25.0),            # period before the figure
    ("ระยะเวลากู้ 7 วัน ค่าบริการ 20%", 20 * 365 / 7),          # flat fee over tenor
    ("ระยะเวลา 7-14 วัน ค่าธรรมเนียม 25%", 25 * 365 / 14),     # longest tenor: conservative
    ("เงินกู้รายวัน ดอกเบี้ยร้อยละ 20 ระยะเวลา 24 วัน", 20 * 365 / 24),
    ("Interest 0.8% per day, repay in 14 days", 292.0),
    ("Maximum APR 36%. Repayment period: 91 days to 365 days", 36.0),
    ("ดอกเบี้ย 0,5%/วัน", 182.5),                              # decimal comma
    ("ดอกเบี้ย 2% ต่อเดือน ค่าธรรมเนียม 10%", 24.0),           # fee is not "per month"
]


@pytest.mark.parametrize("text,expected", CASES)
def test_annualised(text, expected):
    rate, _ = max_annualised_rate(text)
    assert rate == pytest.approx(expected, rel=1e-6)


@pytest.mark.parametrize("text", ["อนุมัติ 99% ภายใน 5 นาที", "ผ่อนรายวัน ดอกเบี้ย 20%", "ส่วนลด 50%"])
def test_no_period_means_no_guess(text):
    rate, mentions = max_annualised_rate(text)
    assert rate is None and len(mentions) == 1


def test_tenor():
    assert extract_tenor_days("ระยะเวลาผ่อนชำระ 12-60 เดือน") == (360, 1800)
    assert extract_tenor_days("ระยะเวลากู้ 7 วัน") == (7, 7)
    assert extract_tenor_days("repayment period: 91 days to 365 days") == (91, 365)
    # ages and processing times are not tenors
    assert extract_tenor_days("อายุ 20-60 ปี") == (None, None)
    assert extract_tenor_days("ทราบผลภายใน 1-3 วันทำการ") == (None, None)
    assert extract_tenor_days("อนุมัติภายใน 1-2 วัน") == (None, None)
