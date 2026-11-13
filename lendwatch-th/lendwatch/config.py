"""Central configuration for lendwatch-th.

IMPORTANT
---------
* Every legal figure below (interest ceilings, platform tenor rules) was written from
  secondary knowledge and MUST be verified against the current Bank of Thailand,
  Ministry of Finance, Google Play and Apple texts before any supervisory use.
* The score weights are a transparent starting point for triage. They are not
  calibrated: re-estimate them on reviewer-labelled data (see scoring.fit_supervised).
"""
from __future__ import annotations

VERSION = "0.1.0"

# --------------------------------------------------------------------------- #
# 1. Discovery terms
# --------------------------------------------------------------------------- #
SEARCH_TERMS_TH = [
    "เงินกู้", "กู้เงิน", "กู้เงินด่วน", "เงินด่วน", "สินเชื่อ", "สินเชื่อส่วนบุคคล",
    "สินเชื่อด่วน", "สินเชื่อออนไลน์", "เงินกู้ออนไลน์", "กู้ออนไลน์", "แอพกู้เงิน",
    "แอปกู้เงิน", "ยืมเงิน", "ยืมเงินด่วน", "เงินสดทันใจ", "กู้เงินไม่เช็คบูโร",
    "กู้เงินไม่ใช้เอกสาร", "เงินกู้รายวัน", "กู้เงินได้จริง", "เงินกู้ถูกกฎหมาย",
]
SEARCH_TERMS_EN = [
    "loan thailand", "cash loan", "quick loan", "instant loan", "personal loan",
    "baht loan", "money lending", "credit cash",
]
# Latin-script tokens used to query Certificate Transparency logs for new domains.
CT_QUERY_TERMS = ["ngern", "ngoen", "sinchuea", "thailoan", "loanthai", "bahtloan",
                  "thaicash", "cashthai", "kuungern", "ngernduan"]
DOMAIN_LENDING_TOKENS = ["loan", "ngern", "ngoen", "sinchue", "credit", "cash", "kuu",
                         "yuem", "duan", "lend"]
DOMAIN_THAI_TOKENS = ["thai", "siam", "baht", "bkk", "ngern", "ngoen", "sinchue"]
DOMAIN_THAI_SUFFIXES = (".th",)

# --------------------------------------------------------------------------- #
# 2. Legal and platform reference points (VERIFY BEFORE USE)
# --------------------------------------------------------------------------- #
LEGAL_CEILINGS_PCT_PA = {
    "ccc_654_unlicensed_lender": 15.0,   # Civil and Commercial Code s.654
    "credit_card": 16.0,
    "supervised_personal_loan": 25.0,
    "nano_finance": 33.0,
    "pico_finance": 36.0,
}
MAX_SUPERVISED_CEILING = max(LEGAL_CEILINGS_PCT_PA.values())      # 36.0
UNLICENSED_CEILING = LEGAL_CEILINGS_PCT_PA["ccc_654_unlicensed_lender"]
PLATFORM_MIN_TENOR_DAYS = 60   # app stores bar full repayment within 60 days

# --------------------------------------------------------------------------- #
# 3. Relevance vocabulary
# --------------------------------------------------------------------------- #
LENDING_TERMS = [
    "เงินกู้", "กู้เงิน", "สินเชื่อ", "ยืมเงิน", "เงินด่วน", "กู้ยืม", "ปล่อยกู้",
    "loan", "lending", "borrow", "cash advance", "credit line",
]
OFFER_TERMS = [   # the artefact itself offers credit (not just talks about it)
    "วงเงิน", "ขอสินเชื่อ", "สมัครกู้", "สมัครสินเชื่อ", "กู้ได้", "อนุมัติ", "รับเงิน",
    "ได้เงิน", "ยื่นกู้", "apply", "get a loan", "get loan", "approval", "disburse",
]
TOOL_ONLY_TERMS = [   # calculators, comparison, education: unlicensed but not lenders
    "คำนวณ", "เครื่องคิดเลข", "เปรียบเทียบ", "ความรู้", "calculator", "compare",
    "comparison", "education", "emi",
]

# --------------------------------------------------------------------------- #
# 4. Red-flag phrase patterns (regex, applied to normalised lower-case text)
# --------------------------------------------------------------------------- #
RED_FLAG_PATTERNS = {
    "no_bureau_check": [
        r"ไม่เช็ค\s*บูโร", r"ไม่ตรวจ\s*บูโร", r"ไม่ดู\s*บูโร", r"ไม่ดูประวัติ",
        r"ติด\s*บูโร.{0,12}(กู้|ผ่าน|ได้)", r"ติด\s*แบล็[คก]ลิสต์.{0,12}(กู้|ผ่าน|ได้)",
        r"no credit check", r"blacklist(ed)? (ok|welcome|accepted)",
    ],
    "no_documents": [
        r"ไม่ต้องใช้เอกสาร", r"ไม่ใช้เอกสาร", r"ไม่ต้องใช้สลิป", r"ไม่ใช้สลิป",
        r"ไม่ต้องมีสลิป", r"ไม่ต้องค้ำ", r"ไม่มีคนค้ำ", r"บัตรประชาชนใบเดียว",
        r"no documents?", r"only (an? )?id card",
    ],
    "instant_approval": [
        r"อนุมัติ(ภายใน|ใน)?\s*\d+\s*นาที", r"อนุมัติ(ไว|เร็ว|ทันที|ง่าย|ทุกอาชีพ)",
        r"ได้เงิน(ทันที|ไว|เร็ว|ภายใน)", r"เงินเข้า(บัญชี)?(ทันที|ไว|ภายใน)",
        r"instant approval", r"approved? in \d+ min",
    ],
    "daily_repayment": [
        r"เงินกู้รายวัน", r"ส่งรายวัน", r"ผ่อนรายวัน", r"เก็บรายวัน", r"ดอก(เบี้ย)?รายวัน",
        r"daily (repayment|collection|instal)",
    ],
    "advance_fee": [
        r"ค่าธรรมเนียม(ล่วงหน้า|ก่อน)", r"โอน(เงิน)?(มา)?ก่อน", r"ค่า(ค้ำ)?ประกัน(เงินกู้|ก่อน|ล่วงหน้า)",
        r"ค่าปลดล็อ[คก]", r"ค่าเปิดบัญชี", r"ค่าดำเนินการ(ก่อน|ล่วงหน้า)", r"เงินมัดจำ",
        r"ค่าเอกสาร(ก่อน|ล่วงหน้า)", r"upfront fee", r"fee before disbursement",
        r"unlock fee", r"security deposit",
    ],
    "messaging_only_contact": [
        r"แอด\s*ไลน์", r"ทัก\s*ไลน์", r"ติดต่อ(ทาง)?ไลน์", r"line\s*id", r"lin\.ee/",
        r"line\.me/", r"t\.me/",
    ],
}

# --------------------------------------------------------------------------- #
# 5. Harassment and harm vocabulary for user reviews / complaints
# --------------------------------------------------------------------------- #
HARM_TERMS = {
    "threat": ["ข่มขู่", "ขู่", "คุกคาม", "จะมาที่บ้าน", "ทำร้าย"],
    "shaming": ["ประจาน", "ตัดต่อรูป", "ตัดต่อภาพ", "ส่งรูป", "แฉ"],
    "third_party_contact": [
        "โทรหาเพื่อน", "โทรหาญาติ", "โทรหาที่ทำงาน", "โทรไปที่ทำงาน", "โทรหาหัวหน้า",
        "โทรหาแม่", "โทรหาครอบครัว", "ส่งข้อความหาเพื่อน", "ทักหาเพื่อน",
        "รายชื่อในเครื่อง", "รายชื่อผู้ติดต่อ", "เบอร์ในเครื่อง",
    ],
    "abusive_collection": ["ทวงหนี้", "ทวงโหด", "โทรทวง", "โดนด่า", "ด่าทอ", "หยาบคาย"],
    "extortionate_terms": [
        "ดอกโหด", "ดอกแพง", "ดอกเบี้ยโหด", "ดอกเบี้ยแพง", "หักหัว", "หักค่าธรรมเนียม",
        "ได้ไม่ครบ", "ได้เงินไม่ครบ", "ได้ไม่เต็ม", "7 วัน", "7วัน", "เจ็ดวัน",
    ],
    "forced_loan": ["ไม่ได้กดกู้", "ไม่ได้กู้", "โอนเข้ามาเอง", "โอนมาเอง"],
    "illegality": ["ผิดกฎหมาย", "แอปเถื่อน", "แอพเถื่อน", "เงินกู้เถื่อน", "นอกระบบ",
                   "แจ้งความ", "แจ้งตำรวจ"],
    "scam": ["หลอก", "โกง", "มิจฉาชีพ"],
}

# --------------------------------------------------------------------------- #
# 6. Sensitive permissions (substrings matched in lower-cased permission text)
# --------------------------------------------------------------------------- #
SENSITIVE_PERMISSIONS = {
    "contacts": ["read_contacts", "read your contacts", "contacts:"],
    "call_log": ["read_call_log", "read call log"],
    "sms": ["read_sms", "receive_sms", "read your text messages", "receive text messages"],
    "media_storage": ["read_external_storage", "read_media_images", "photos/media/files",
                      "read the contents of your"],
    "precise_location": ["access_fine_location", "precise location"],
    "microphone": ["record_audio", "record audio"],
}

FREE_EMAIL_DOMAINS = {
    "gmail.com", "outlook.com", "hotmail.com", "yahoo.com", "icloud.com", "proton.me",
    "protonmail.com", "163.com", "126.com", "qq.com", "foxmail.com", "sina.com",
    "yandex.com", "mail.com", "gmx.com",
}
FREE_HOSTING = {
    "sites.google.com", "docs.google.com", "github.io", "blogspot.com", "wordpress.com",
    "wixsite.com", "weebly.com", "notion.site", "telegra.ph", "firebaseapp.com",
    "web.app", "pages.dev", "netlify.app", "vercel.app", "termsfeed.com",
    "freeprivacypolicy.com", "privacypolicies.com", "flycricket.io",
}
# Hosts too generic to identify an operator on their own.
GENERIC_HOSTS = FREE_HOSTING | {
    "facebook.com", "fb.com", "google.com", "play.google.com", "apple.com",
    "apps.apple.com", "line.me", "lin.ee", "t.me", "youtube.com", "tiktok.com",
    "instagram.com", "twitter.com", "x.com", "bit.ly",
}

# --------------------------------------------------------------------------- #
# 7. Rule-based triage score (0-100). Transparent, additive, capped.
# --------------------------------------------------------------------------- #
SCORE_WEIGHTS = {
    "unlicensed_offering_credit": 25,   # offers credit, no registry match
    "impersonates_licensed_brand": 20,
    "name_only_licence_match": 8,       # claims a licensee's name; channel not registered
    "rate_above_any_ceiling": 25,       # annualised rate > 36 %
    "rate_above_unlicensed_cap": 10,    # unlicensed and annualised rate > 15 %
    "short_tenor": 10,                  # repayment within 60 days
    "advance_fee": 20,
    "no_bureau_check": 8,
    "daily_repayment": 10,
    "no_documents": 3,
    "instant_approval": 2,
    "messaging_only_contact": 5,
    "sensitive_permission_each": 5,     # per permission family, capped below
    "sensitive_permission_cap": 20,
    "harm_reviews_high": 15,            # >= 5 % of reviews mention harm terms
    "harm_reviews_some": 8,             # >= 1 %
    "category_mismatch": 5,             # lending app listed outside Finance
    "free_email_developer": 4,
    "no_privacy_policy": 5,
    "privacy_on_free_host": 3,
    "apk_sideload_link": 10,
    "clone_cluster": 10,                # operator controls >= 3 artefacts
}
TIER_HIGH = 60
TIER_MEDIUM = 35

# Legal hooks shown in evidence packs (pointers for the reviewer, not legal findings).
LEGAL_HOOKS = {
    "unlicensed_offering_credit": "Lending as a business without a licence (Revolutionary Council Announcement No. 58; MOF notifications)",
    "impersonates_licensed_brand": "Possible fraud / passing off; Computer Crime Act s.14",
    "name_only_licence_match": "Check for rent-a-licence or impersonation: licensee name on an unregistered channel",
    "rate_above_any_ceiling": "Act Prohibiting Excessive Interest B.E. 2560",
    "rate_above_unlicensed_cap": "Civil and Commercial Code s.654; Act Prohibiting Excessive Interest B.E. 2560",
    "short_tenor": "App-store personal-loan policies (60-day rule)",
    "advance_fee": "Criminal Code fraud; Emergency Decree on Technology Crime B.E. 2566",
    "sensitive_permissions": "Personal Data Protection Act B.E. 2562; app-store permission rules",
    "harm_reviews": "Debt Collection Act B.E. 2558; PDPA; Criminal Code (threats, defamation)",
}
