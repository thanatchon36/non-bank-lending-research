"""Synthetic ecosystem with known ground truth.

Lets the whole pipeline run offline and lets you check the estimators against the
truth. EVERY name, app id, domain, phone and account number here is invented; domains
use the reserved ``.example`` TLD. Nothing refers to a real lender or person.

Operator types follow the paper's taxonomy:
  T1 predatory unlicensed lender, T2 advance-fee scam, T5 offline loan shark.
A share of T1 operators are "deceptive": clean listing text, harm visible only in
reviews and permissions.
"""
from __future__ import annotations

import math
import random
from datetime import datetime, timedelta, timezone

from .collectors import base_artefact

BENIGN = ["ใช้งานง่าย", "อนุมัติเร็วดี", "แอปค้างบ่อย", "ดอกเบี้ยโอเค", "บริการดี",
          "สมัครไม่ผ่าน", "ระบบช้าไปหน่อย", "พนักงานสุภาพ", "อัปเดตแล้วเข้าไม่ได้"]
HARM = ["กู้ 3000 ได้เงินไม่ครบ หักค่าธรรมเนียมไปเกือบครึ่ง",
        "ทวงหนี้โหดมาก โทรหาเพื่อนในรายชื่อผู้ติดต่อทุกคน",
        "ขู่จะประจานลงเฟส ทั้งที่ยังไม่ถึงกำหนด",
        "ตัดต่อรูปส่งไปที่ทำงาน แย่มาก",
        "ดอกโหด 7 วันต้องคืนเกือบสองเท่า",
        "แอปเถื่อน ผิดกฎหมาย อย่าโหลด",
        "ไม่ได้กดกู้แต่โอนเข้ามาเอง แล้วโทรทวงทุกวัน"]
SCAM = ["หลอกให้โอนค่าธรรมเนียมก่อน แล้วไม่ได้เงิน", "มิจฉาชีพ โดนหลอกโอน 2000",
        "โกง อย่าหลงเชื่อ ให้โอนค่าประกันก่อนแล้วเงียบหาย"]
PRAISE = ["ดีมาก ได้เงินจริง", "แนะนำเลย อนุมัติไวมาก", "สุดยอด 5 ดาว"]
STEMS = ["ngernwai", "kuungai", "bahtduan", "cashsabai", "ruaychat", "ngernsod", "thaiquick",
         "sinsabai", "ngernjing", "easybaht", "fastngern", "happykuu", "goldbaht",
         "luckycash", "ngernpuan", "duanjai", "kuudai", "siamquick"]
TH_NAMES = ["เงินไว", "กู้ง่าย", "บาทด่วน", "เงินสดสบาย", "รวยฉับ", "เงินสดทันที",
            "ไทยควิก", "สินสบาย", "เงินจริง", "อีซี่บาท"]
BRAND_STEMS = ["Lotus", "Mali", "Chaba", "Tuktuk", "Mango", "Orchid", "Banyan", "Jasmine",
               "Coral", "Bamboo", "Tamarind", "Papaya", "Longan", "Durian", "Rambutan",
               "Guava", "Pandan", "Ginger", "Basil", "Sesame", "Coconut", "Pomelo",
               "Lychee", "Taro", "Lime"]
SENSITIVE = ["Contacts: read your contacts", "SMS: read your text messages (SMS or MMS)",
             "Photos/Media/Files: read the contents of your USB storage",
             "Location: precise location (GPS and network-based)", "Phone: read call log"]
SAFE_PERMS = ["Camera: take pictures and videos", "Other: full network access"]
NOW = datetime(2026, 11, 1, tzinfo=timezone.utc)


def _sigmoid(x: float) -> float:
    return 1 / (1 + math.exp(-x))


def _shift(p: float, z: float, slope: float) -> float:
    """Move a base probability up or down with the operator's catchability z."""
    return _sigmoid(math.log(p / (1 - p)) + slope * z) if 0 < p < 1 else p


def _poisson(rng: random.Random, lam: float) -> int:
    limit, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= limit:
            return k
        k += 1


def _reviews(rng, n, p_harm=0.0, p_scam=0.0, p_praise=0.0) -> list[dict]:
    out = []
    for _ in range(n):
        u = rng.random()
        if u < p_harm:
            text, score = rng.choice(HARM), 1
        elif u < p_harm + p_scam:
            text, score = rng.choice(SCAM), 1
        elif u < p_harm + p_scam + p_praise:
            text, score = rng.choice(PRAISE), 5
        else:
            text, score = rng.choice(BENIGN), rng.choice([2, 3, 4, 4, 5, 5])
        day = NOW - timedelta(days=rng.randint(1, 300))
        out.append({"text": text, "score": score, "date": day.strftime("%Y-%m-%d")})
    return out


def _date(rng, lo, hi) -> str:
    return (NOW - timedelta(days=rng.randint(lo, hi))).strftime("%Y-%m-%d")


def make_demo(seed: int = 7, n_licensed: int = 60, n_illegal: int = 300, n_tools: int = 40,
              n_coops: int = 30, n_fintech: int = 30, heterogeneity: float = 0.5) -> dict:
    """Return {"artefacts", "registry_rows", "truth"}."""
    rng = random.Random(seed)
    arts: list[dict] = []
    rows: list[dict] = []

    def add(truth_op, label, typ, **kw):
        a = base_artefact(**kw)
        a["collected_at"] = NOW.strftime("%Y-%m-%dT%H:%M:%SZ")
        a.update({"_true_operator": truth_op, "_true_label": label, "_true_type": typ})
        arts.append(a)
        return a

    # ---------------- licensed lenders -------------------------------------- #
    for i in range(n_licensed):
        series = "" if i < len(BRAND_STEMS) else str(i // len(BRAND_STEMS) + 1)
        brand = f"Demo{BRAND_STEMS[i % len(BRAND_STEMS)]}{series} Credit"
        ent_en = f"{brand} Co., Ltd."
        ent_th = f"บริษัท เดโม{i:02d} สินเชื่อ จำกัด"
        dom = f"demolender{i:02d}.example"
        gp_id, ios_id = f"th.demo.licensed{i:02d}", f"9000{i:03d}"
        rows.append({"entity_name_th": ent_th, "entity_name_en": ent_en, "brand_names": brand,
                     "licence_type": "supervised personal loan (DEMO)", "regulator": "BOT (DEMO)",
                     "app_ids": f"{gp_id};{ios_id}", "domains": dom,
                     "source_url": "synthetic", "as_of": "2026-11-01"})
        extra = rng.choice(["", "", "อนุมัติไว รู้ผลใน 15 นาที ", "ไม่ต้องใช้สลิปเงินเดือน "])
        desc = (f"{brand} สินเชื่อส่วนบุคคลจาก {ent_th} ผู้ให้บริการภายใต้การกำกับของธนาคารแห่งประเทศไทย "
                f"สมัครสินเชื่อออนไลน์ วงเงินสูงสุด 5 เท่าของรายได้ อัตราดอกเบี้ยสูงสุดร้อยละ 25 ต่อปี "
                f"ระยะเวลาผ่อนชำระ 12-60 เดือน {extra}กู้เท่าที่จำเป็นและชำระคืนไหว")
        perms = SAFE_PERMS + ([SENSITIVE[3]] if rng.random() < 0.1 else [])
        common = dict(developer=ent_en, developer_email=f"support@{dom}",
                      developer_website=f"https://www.{dom}", description=desc,
                      privacy_policy_url=f"https://www.{dom}/privacy")
        add(f"LIC{i}", 0, "licensed", artefact_id=f"gp:{gp_id}", source="google_play", name=brand,
            url=f"https://play.google.com/store/apps/details?id={gp_id}", category="FINANCE",
            developer_id=f"lic{i}", permissions=perms, installs_min=rng.choice([100_000, 500_000, 1_000_000]),
            reviews=_reviews(rng, rng.randint(60, 200), p_harm=0.004, p_praise=rng.uniform(0.1, 0.5)),
            released=_date(rng, 700, 3000), **common)
        if rng.random() < 0.6:
            add(f"LIC{i}", 0, "licensed", artefact_id=f"ios:{ios_id}", source="app_store", name=brand,
                url=f"https://apps.apple.com/th/app/id{ios_id}", category="Finance",
                reviews=_reviews(rng, rng.randint(20, 80), p_harm=0.004), released=_date(rng, 700, 3000), **common)
        add(f"LIC{i}", 0, "licensed", artefact_id=f"web:{dom}", source="web", name=brand,
            url=f"https://www.{dom}/", description=desc)
        if i < 4:   # a second app the licensee has not registered: name-only match
            add(f"LIC{i}", 0, "licensed_unregistered_channel", artefact_id=f"gp:th.demo.partner{i:02d}",
                source="google_play", name=f"{brand} Plus", category="FINANCE",
                url=f"https://play.google.com/store/apps/details?id=th.demo.partner{i:02d}",
                developer_id=f"partner{i}", permissions=SAFE_PERMS, installs_min=10_000,
                reviews=_reviews(rng, 40, p_harm=0.004), released=_date(rng, 30, 400), **common)

    # ---------------- unlicensed-but-harmless tools ------------------------- #
    for i in range(n_tools):
        add(f"TOOL{i}", 0, "tool", artefact_id=f"gp:app.demo.calc{i:02d}", source="google_play",
            name=f"เครื่องคำนวณเงินกู้ {i + 1}", category="FINANCE", developer=f"Indie Dev {i}",
            developer_id=f"indie{i}", developer_email=f"indie{i}@gmail.com",
            url=f"https://play.google.com/store/apps/details?id=app.demo.calc{i:02d}",
            privacy_policy_url=f"https://sites.google.com/view/calc{i}-privacy",
            description=("คำนวณค่างวดผ่อนบ้าน ผ่อนรถ สินเชื่อส่วนบุคคล เปรียบเทียบดอกเบี้ย"
                         "จากหลายธนาคาร แอปนี้ไม่มีการให้กู้ยืมเงิน"),
            permissions=["Other: full network access"], installs_min=10_000,
            reviews=_reviews(rng, rng.randint(10, 60)), released=_date(rng, 200, 2000))

    # ---------------- legal lenders outside the BOT registry ---------------- #
    # Savings cooperatives lend to members under another regulator. They offer credit
    # and match no BOT licence: the false-positive class a reviewer must screen out
    # (or the registry must be widened to cover).
    for i in range(n_coops):
        add(f"COOP{i}", 0, "cooperative", artefact_id=f"gp:coop.demo.saving{i:02d}",
            source="google_play", name=f"สหกรณ์ออมทรัพย์เดโม {i + 1}", category="FINANCE",
            developer=f"Demo Savings Cooperative {i + 1}", developer_id=f"coop{i}",
            developer_email=f"admin@democoop{i:02d}.example",
            url=f"https://play.google.com/store/apps/details?id=coop.demo.saving{i:02d}",
            privacy_policy_url=f"https://democoop{i:02d}.example/privacy",
            description=("แอปสหกรณ์ออมทรัพย์สำหรับสมาชิก ตรวจสอบเงินฝาก หุ้น ยื่นกู้สามัญ เงินกู้ฉุกเฉิน "
                         "อัตราดอกเบี้ยเงินกู้ร้อยละ 6 ต่อปี ระยะเวลาผ่อนชำระ 12-120 เดือน"),
            permissions=SAFE_PERMS, installs_min=5_000,
            reviews=_reviews(rng, rng.randint(10, 50), p_harm=0.01, p_praise=rng.uniform(0.1, 0.5)),
            released=_date(rng, 300, 2500))

    # Legitimate instalment / pay-later providers missing from the registry (for
    # example a stale registry). They look like unlicensed lenders to the rules and
    # land in the medium tier: the reason a score is never a finding.
    for i in range(n_fintech):
        dom = f"demopay{i:02d}.example"
        bits = ["บริการสินเชื่อผ่อนสินค้าออนไลน์ แบ่งจ่ายสบาย วงเงินสูงสุด 20,000 บาท สมัครง่าย"]
        bits += ["อนุมัติไว"] if rng.random() < 0.5 else []
        bits += ["ไม่ต้องใช้สลิปเงินเดือน"] if rng.random() < 0.3 else []
        bits += ["อัตราดอกเบี้ยสูงสุด 25% ต่อปี"] if rng.random() < 0.8 else []
        bits += ["ระยะเวลาผ่อนชำระ 3-12 เดือน"] if rng.random() < 0.8 else ["ชำระคืนภายใน 45 วัน"]
        bits += [f"ติดต่อไลน์: @demopay{i:02d}"] if rng.random() < 0.15 else []
        add(f"FIN{i}", 0, "legit_not_in_registry", artefact_id=f"gp:app.demo.paylater{i:02d}",
            source="google_play", name=f"DemoPayLater {i + 1}",
            category="SHOPPING" if rng.random() < 0.2 else "FINANCE",
            developer=f"DemoPay Technologies {i + 1} Co., Ltd.", developer_id=f"fin{i}",
            developer_email=f"demopay{i:02d}@gmail.com" if rng.random() < 0.1 else f"support@{dom}",
            developer_website=f"https://{dom}",
            url=f"https://play.google.com/store/apps/details?id=app.demo.paylater{i:02d}",
            privacy_policy_url=f"https://{dom}/privacy", description=" ".join(bits),
            permissions=SAFE_PERMS + ([SENSITIVE[3]] if rng.random() < 0.3 else [])
            + ([SENSITIVE[0]] if rng.random() < 0.05 else []),
            installs_min=100_000,
            reviews=_reviews(rng, rng.randint(30, 120), p_harm=rng.uniform(0.0, 0.03),
                             p_praise=rng.uniform(0.1, 0.5)),
            released=_date(rng, 200, 1500))

    # ---------------- illegal operators ------------------------------------- #
    base = {  # P(channel) by type: google_play, app_store, web, ad, complaint
        "T1": (0.60, 0.15, 0.40, 0.30, 0.12),
        "T2": (0.35, 0.08, 0.55, 0.40, 0.35),
        "T5": (0.05, 0.00, 0.50, 0.35, 0.10),
    }
    observed_ops = 0
    for i in range(n_illegal):
        typ = rng.choices(["T1", "T2", "T5"], weights=[0.60, 0.25, 0.15])[0]
        z = rng.gauss(0, 1)
        on = [rng.random() < _shift(p, z, heterogeneity) for p in base[typ]]
        if not any(on):
            continue                                    # hidden: no list sees it
        observed_ops += 1
        stem, num = rng.choice(STEMS), rng.randint(10, 999)
        key = f"{stem}{num}x{i}"
        line = f"{stem}{num}_{i}"
        phone = f"0{rng.choice('689')}{rng.randint(0, 9)}{rng.randint(1000000, 9999999)}"
        bank = f"{rng.randint(100, 999)}-{rng.randint(0, 9)}-{rng.randint(10000, 99999)}-{rng.randint(0, 9)}"
        email = f"{key}@{'gmail.com' if rng.random() < 0.8 else key + '.example'}"
        privacy = f"https://sites.google.com/view/{key}-privacy"
        deceptive = typ == "T1" and rng.random() < 0.25
        if deceptive and rng.random() < 0.7:   # looks corporate: own domain for e-mail and policy
            email = f"support@{key}.example"
            privacy = f"https://{key}.example/privacy"
        th_name = rng.choice(TH_NAMES)
        line_part = lambda p=0.6: f"แอดไลน์ @{line}" if rng.random() < p else ""

        def describe(name: str) -> str:
            if typ == "T1" and deceptive:
                bits = [f"{name} สินเชื่อออนไลน์ สมัครง่าย วงเงินสูงสุด 50,000 บาท ปลอดภัย เชื่อถือได้"]
                bits += ["อนุมัติไว"] if rng.random() < 0.6 else []
                bits += ["ไม่ต้องใช้สลิปเงินเดือน"] if rng.random() < 0.5 else []
                u = rng.random()
                bits += (["อัตราดอกเบี้ยต่อปี 18%"] if u < 0.6 else
                         ["อัตราดอกเบี้ยสูงสุด 25% ต่อปี"] if u < 0.8 else [])
                bits += ["ระยะเวลาผ่อนชำระ 91-180 วัน"] if rng.random() < 0.8 else ["ชำระคืนภายใน 62 วัน"]
                bits += [f"ติดต่อไลน์: @{line}"] if rng.random() < 0.2 else []
                return " ".join(bits)
            if typ == "T1":
                rate = f"ดอกเบี้ย {rng.choice([0.5, 1, 1.5, 2])}% ต่อวัน" if rng.random() < 0.5 else ""
                return (f"{name} แอปเงินกู้ออนไลน์ อนุมัติไวภายใน 5 นาที ไม่เช็คบูโร ไม่ต้องใช้เอกสาร "
                        f"ใช้บัตรประชาชนใบเดียว วงเงินสูงสุด 20,000 บาท ระยะเวลากู้ {rng.choice([7, 14])} วัน "
                        f"ค่าบริการ {rng.choice([15, 20, 30])}% {rate} {line_part()}")
            if typ == "T2":
                return (f"{name} สินเชื่อด่วน อนุมัติทุกอาชีพ ติดบูโรก็กู้ได้ วงเงินสูงสุด 500,000 บาท "
                        "ดอกเบี้ยต่ำ 1% ต่อเดือน เพียงชำระค่าธรรมเนียมล่วงหน้าเพื่อยืนยันตัวตน "
                        f"รับเงินทันที {line_part(0.8)}")
            return (f"เงินกู้รายวัน {name} ได้เงินจริง ไม่ต้องค้ำ ส่งรายวัน ดอกเบี้ยร้อยละ 20 "
                    f"ระยะเวลา 24 วัน อนุมัติไว โทร {phone} {line_part(0.8)}")

        mine: list[str] = []
        p_harm = rng.uniform(0.02, 0.06) if deceptive else 0.12 if typ in ("T1", "T5") else 0.02
        p_sens = 0.4 if deceptive else 0.8 if typ == "T1" else 0.3
        p_scam = 0.15 if typ == "T2" else 0.0
        p_praise = rng.uniform(0.0, 0.6)
        if on[0]:
            for j in range(1 + (_poisson(rng, 1.2) if typ == "T1" else 0)):
                app_id = f"com.{key}.loan{j}"
                name = f"{th_name} {rng.choice(['Cash', 'Loan', 'Credit', 'เงินด่วน'])} {rng.randint(1, 99)}"
                if typ == "T2" and rng.random() < 0.10:
                    name = f"Demo{rng.choice(BRAND_STEMS)} Credit สินเชื่อด่วน"
                sens = rng.sample(SENSITIVE, rng.randint(2, 5)) if rng.random() < p_sens else []
                add(f"ILL{i}", 1, typ, artefact_id=f"gp:{app_id}", source="google_play", name=name,
                    url=f"https://play.google.com/store/apps/details?id={app_id}",
                    category="FINANCE" if rng.random() < 0.7 else rng.choice(["TOOLS", "LIFESTYLE"]),
                    developer=f"{stem.title()} Tech Studio {rng.randint(1, 99)}",
                    developer_id=f"dev-{key}-{j if rng.random() < 0.3 else 0}",
                    developer_email=email if rng.random() < 0.85 else f"{key}.{j}@outlook.com",
                    developer_website=f"https://{key}-0.example" if rng.random() < 0.5 else None,
                    privacy_policy_url=privacy if rng.random() < 0.7 else None,
                    description=describe(name), permissions=SAFE_PERMS + sens,
                    installs_min=rng.choice([10_000, 50_000, 100_000, 1_000_000]),
                    reviews=_reviews(rng, rng.randint(20, 150), p_harm, p_scam, p_praise),
                    released=_date(rng, 20, 400))
                mine.append(f"gp:{app_id}")
        if on[1]:
            ios_id = f"7{i:06d}"
            name = f"{th_name} Loan {rng.randint(1, 99)}"
            add(f"ILL{i}", 1, typ, artefact_id=f"ios:{ios_id}", source="app_store", name=name,
                url=f"https://apps.apple.com/th/app/id{ios_id}", category="Finance",
                developer=f"{stem.title()} Tech Studio", developer_id=f"ios-{key}",
                developer_website=f"https://{key}.example", description=describe(name) + f" ไลน์: {line}",
                reviews=_reviews(rng, rng.randint(10, 60), p_harm, p_scam, p_praise), released=_date(rng, 20, 400))
            mine.append(f"ios:{ios_id}")
        if on[2]:
            for j in range(1 + (_poisson(rng, 0.5) if typ == "T1" else 0)):
                dom = f"{key}-{j}.example"
                bits = [describe(th_name)]
                bits.append(f"ไลน์: {line}" if rng.random() < 0.8 else "")
                bits.append(f"โทร {phone}" if rng.random() < 0.6 else "")
                bits.append(f"โอนเข้าบัญชี {bank}" if rng.random() < 0.3 else "")
                apk = [f"https://dl.{key}.example/app{j}.apk"] if typ == "T1" and rng.random() < 0.5 else []
                add(f"ILL{i}", 1, typ, artefact_id=f"web:{dom}", source="web", name=f"{th_name} | {dom}",
                    url=f"https://{dom}/", description=" ".join(b for b in bits if b),
                    outbound_links=apk + ([f"https://{key}.example"] if rng.random() < 0.5 else []))
                mine.append(f"web:{dom}")
        if on[3]:
            ref = [rng.choice(mine)] if mine and rng.random() < 0.7 else []
            add(f"ILL{i}", 1, typ, artefact_id=f"ad:AD{i:04d}", source="ad", name=f"โฆษณา {th_name}",
                description=f"{describe(th_name)} ไลน์: {line}" if rng.random() < 0.8 or not ref
                else describe(th_name), mentions_artefacts=ref)
        if on[4]:
            for j in range(1 + _poisson(rng, 0.4)):
                ref = [rng.choice(mine)] if mine and rng.random() < 0.6 else []
                bits = [rng.choice(HARM if typ != "T2" else SCAM)]
                if rng.random() < 0.5 or not ref:
                    bits.append(f"ติดต่อผ่านไลน์: {line}")
                if rng.random() < 0.5:
                    bits.append(f"โอนเงินเข้าบัญชี {bank}")
                if rng.random() < 0.4:
                    bits.append(f"เบอร์ที่โทรมา {phone}")
                add(f"ILL{i}", 1, typ, artefact_id=f"complaint:CP{i:04d}-{j}", source="complaint",
                    name="คำร้องเรียน", description=" ".join(bits), mentions_artefacts=ref)

    rng.shuffle(arts)
    truth = {"n_illegal_operators": n_illegal, "n_illegal_operators_observed": observed_ops,
             "n_licensed": n_licensed, "n_tools": n_tools, "n_coops": n_coops,
             "n_fintech": n_fintech, "seed": seed}
    return {"artefacts": arts, "registry_rows": rows, "truth": truth}
