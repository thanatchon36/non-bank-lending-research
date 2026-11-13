from lendwatch.registry import LicensedRegistry, Licensee
from lendwatch.textutils import (extract_identifiers, normalize_company_name, normalize_text,
                                 registrable_domain, salted_hash)


def test_normalisation_keeps_thai_sara_am():
    # NFKC would split U+0E33; the normaliser must put it back
    assert "จำกัด" in normalize_text("บริษัท จำกัด")
    assert normalize_text("ค่าธรรมเนียม ๒０％") == "ค่าธรรมเนียม 20%"


def test_company_names():
    assert normalize_company_name("บริษัท เงินดี ลิสซิ่ง จำกัด (มหาชน)") == "เงินดี ลิสซิ่ง"
    assert normalize_company_name("ABC Capital (Thailand) Co., Ltd.") == "abc capital"
    assert registrable_domain("app.lender.co.th") == "lender.co.th"


def test_identifiers():
    ids = extract_identifiers("แอดไลน์ @ngernwai88 โทร 081-234-5678 บัญชี 123-4-56789-0 "
                              "https://dl.x.example/a.apk line.me/R/ti/p/@quickbaht")
    assert ids["line_ids"] == ["ngernwai88", "quickbaht"]
    assert ids["phones"] == ["0812345678"]
    assert ids["bank_accounts"] == ["1234567890"]
    assert ids["apk_links"] == ["https://dl.x.example/a.apk"]
    assert salted_hash("0812345678", "a") != salted_hash("0812345678", "b")


def _registry():
    return LicensedRegistry([Licensee(
        entity_name_th="บริษัท เดโม สินเชื่อ จำกัด", entity_name_en="Demo Lotus Credit Co., Ltd.",
        brand_names=["Demo Lotus Credit"], app_ids=["th.demo.lotus"], domains=["demolotus.example"])])


def test_registered_channels_are_authoritative():
    reg = _registry()
    assert reg.match(app_id="th.demo.lotus").status == "licensed_exact"
    assert reg.match(own_urls=("https://www.demolotus.example/apply",)).status == "licensed_domain"


def test_claims_are_weaker_than_registered_channels():
    reg = _registry()
    # anyone can type a licensee's name or website into a store listing
    assert reg.match(app_id="x.y", developer="Demo Lotus Credit Company Limited").status == "licensed_name"
    assert reg.match(app_id="x.y", claimed_urls=("https://demolotus.example",)).status == "licensed_name"


def test_impersonation_and_unmatched():
    reg = _registry()
    m = reg.match(app_id="x.y", developer="Fast Studio", name="Demo Lotus Credit สินเชื่อด่วน")
    assert m.status == "unmatched" and m.impersonates == "Demo Lotus Credit Co., Ltd."
    assert reg.match(app_id="x.y", developer="Fast Studio", name="เงินไว").impersonates is None
