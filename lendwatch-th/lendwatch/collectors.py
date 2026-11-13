"""Live collectors. Public data only; polite by design.

Rules built into this module
----------------------------
* Only public listing metadata, public review text and public landing pages.
* Reviewer names and avatars are dropped at collection (data minimisation).
* A pause between requests, an identifying User-Agent, and robots.txt for websites.
* No log-ins, no circumvention of technical controls, no interaction with operators.

Check each platform's current terms and obtain a data-sharing agreement where one is
needed; a supervisor should prefer official feeds over crawling whenever they exist.

Optional dependencies: ``google-play-scraper`` (Google Play), ``requests`` and
``beautifulsoup4`` (App Store API, crt.sh, landing pages).
"""
from __future__ import annotations

import time
import urllib.robotparser
from datetime import datetime, timezone
from typing import Iterable, Optional
from urllib.parse import quote

from . import config as C
from .evidence import sha256_json, utc_now
from .textutils import extract_identifiers, host_of, registrable_domain

USER_AGENT = "lendwatch-th/%s (supervisory research; contact: SET-YOUR-EMAIL)" % C.VERSION


def _iso_from_ts(ts) -> Optional[str]:
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%d")
    except (TypeError, ValueError, OSError):
        return None


def _iso_from_text(s) -> Optional[str]:
    if not s:
        return None
    for fmt in ("%b %d, %Y", "%d %b %Y", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(str(s), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def base_artefact(**kw) -> dict:
    """The common schema every collector returns."""
    art = {
        "artefact_id": None, "source": None, "name": None, "url": None,
        "developer": None, "developer_id": None, "developer_email": None,
        "developer_website": None, "developer_address": None, "privacy_policy_url": None,
        "description": None, "category": None, "installs_min": None, "rating": None,
        "ratings_count": None, "released": None, "updated": None,
        "permissions": [], "reviews": [], "outbound_links": [], "line_ids": [],
        "phones": [], "bank_accounts": [], "apk_links": [], "mentions_artefacts": [],
        "signing_cert_sha256": None, "collected_at": utc_now(),
    }
    art.update(kw)
    return art


# --------------------------------------------------------------------------- #
# Google Play
# --------------------------------------------------------------------------- #
class GooglePlayCollector:
    def __init__(self, lang: str = "th", country: str = "th", pause: float = 1.5,
                 n_reviews: int = 200):
        try:
            import google_play_scraper as gps
        except ImportError as exc:      # pragma: no cover
            raise ImportError("pip install google-play-scraper") from exc
        self.gps, self.lang, self.country = gps, lang, country
        self.pause, self.n_reviews = pause, n_reviews

    def discover(self, terms: Iterable[str], n_hits: int = 30) -> list[str]:
        seen: dict[str, None] = {}
        for term in terms:
            try:
                hits = self.gps.search(term, lang=self.lang, country=self.country, n_hits=n_hits)
            except Exception as exc:    # network errors, layout changes
                print(f"[google_play] search failed for {term!r}: {exc}")
                hits = []
            for h in hits:
                if h.get("appId"):
                    seen.setdefault(h["appId"], None)
            time.sleep(self.pause)
        return list(seen)

    def fetch(self, app_id: str) -> Optional[dict]:
        try:
            d = self.gps.app(app_id, lang=self.lang, country=self.country)
        except Exception as exc:
            print(f"[google_play] details failed for {app_id}: {exc}")
            return None
        time.sleep(self.pause)
        perms: list[str] = []
        try:
            grouped = self.gps.permissions(app_id, lang="en", country=self.country)
            perms = [f"{group}: {p}" for group, items in (grouped or {}).items() for p in items]
        except Exception:
            pass
        time.sleep(self.pause)
        reviews: list[dict] = []
        try:
            got, _ = self.gps.reviews(app_id, lang=self.lang, country=self.country,
                                      sort=self.gps.Sort.NEWEST, count=self.n_reviews)
            # keep text, score and date only: no user names, no avatars
            reviews = [{"text": r.get("content"), "score": r.get("score"),
                        "date": r["at"].strftime("%Y-%m-%d") if r.get("at") else None}
                       for r in got]
        except Exception:
            pass
        time.sleep(self.pause)
        art = base_artefact(
            artefact_id=f"gp:{app_id}", source="google_play", name=d.get("title"),
            url=d.get("url") or f"https://play.google.com/store/apps/details?id={app_id}",
            developer=d.get("developer"), developer_id=str(d.get("developerId") or "") or None,
            developer_email=d.get("developerEmail"), developer_website=d.get("developerWebsite"),
            developer_address=d.get("developerAddress"), privacy_policy_url=d.get("privacyPolicy"),
            description=d.get("description"), category=d.get("genreId") or d.get("genre"),
            installs_min=d.get("minInstalls"), rating=d.get("score"), ratings_count=d.get("ratings"),
            released=_iso_from_text(d.get("released")), updated=_iso_from_ts(d.get("updated")),
            permissions=perms, reviews=reviews,
        )
        art["raw_sha256"] = sha256_json(d)
        return art


# --------------------------------------------------------------------------- #
# Apple App Store (official iTunes Search API + public review feed)
# --------------------------------------------------------------------------- #
class AppStoreCollector:
    SEARCH = "https://itunes.apple.com/search"
    REVIEWS = "https://itunes.apple.com/{cc}/rss/customerreviews/page=1/id={id}/sortby=mostrecent/json"

    def __init__(self, country: str = "th", pause: float = 3.0, timeout: int = 20):
        import requests
        self.s = requests.Session()
        self.s.headers["User-Agent"] = USER_AGENT
        self.country, self.pause, self.timeout = country, pause, timeout

    def discover(self, terms: Iterable[str], limit: int = 100) -> list[dict]:
        found: dict[int, dict] = {}
        for term in terms:
            try:
                r = self.s.get(self.SEARCH, timeout=self.timeout, params={
                    "term": term, "country": self.country, "entity": "software", "limit": limit})
                r.raise_for_status()
                for item in r.json().get("results", []):
                    if item.get("trackId"):
                        found.setdefault(item["trackId"], item)
            except Exception as exc:
                print(f"[app_store] search failed for {term!r}: {exc}")
            time.sleep(self.pause)
        return list(found.values())

    def _reviews(self, track_id) -> list[dict]:
        try:
            r = self.s.get(self.REVIEWS.format(cc=self.country, id=track_id), timeout=self.timeout)
            r.raise_for_status()
            entries = r.json().get("feed", {}).get("entry", [])
        except Exception:
            return []
        if isinstance(entries, dict):
            entries = [entries]
        out = []
        for e in entries:
            text = (e.get("content") or {}).get("label")
            if text is None:
                continue
            rating = (e.get("im:rating") or {}).get("label")
            out.append({"text": text, "score": float(rating) if rating else None,
                        "date": ((e.get("updated") or {}).get("label") or "")[:10] or None})
        return out

    def to_artefact(self, item: dict, with_reviews: bool = True) -> dict:
        tid = item["trackId"]
        art = base_artefact(
            artefact_id=f"ios:{tid}", source="app_store", name=item.get("trackName"),
            url=item.get("trackViewUrl"), developer=item.get("sellerName") or item.get("artistName"),
            developer_id=str(item.get("artistId") or "") or None,
            developer_website=item.get("sellerUrl"), description=item.get("description"),
            category=item.get("primaryGenreName"), rating=item.get("averageUserRating"),
            ratings_count=item.get("userRatingCount"),
            released=(item.get("releaseDate") or "")[:10] or None,
            updated=(item.get("currentVersionReleaseDate") or "")[:10] or None,
        )
        art["bundle_id"] = item.get("bundleId")
        if with_reviews:
            art["reviews"] = self._reviews(tid)
            time.sleep(self.pause)
        art["raw_sha256"] = sha256_json(item)
        return art


# --------------------------------------------------------------------------- #
# Web: new domains from Certificate Transparency logs, then landing pages
# --------------------------------------------------------------------------- #
def looks_thai_lending_domain(domain: str) -> bool:
    d = domain.lower()
    lending = any(tok in d for tok in C.DOMAIN_LENDING_TOKENS)
    thai = d.endswith(C.DOMAIN_THAI_SUFFIXES) or any(tok in d for tok in C.DOMAIN_THAI_TOKENS)
    return lending and thai


class WebCollector:
    CRT = "https://crt.sh/?q={q}&output=json"

    def __init__(self, pause: float = 5.0, timeout: int = 30):
        import requests
        self.s = requests.Session()
        self.s.headers["User-Agent"] = USER_AGENT
        self.pause, self.timeout = pause, timeout
        self._robots: dict[str, urllib.robotparser.RobotFileParser] = {}

    def discover(self, terms: Iterable[str] = tuple(C.CT_QUERY_TERMS)) -> list[str]:
        """Registrable domains whose certificates contain a Thai lending token."""
        domains: dict[str, None] = {}
        for term in terms:
            try:
                r = self.s.get(self.CRT.format(q=quote(f"%{term}%")), timeout=self.timeout)
                r.raise_for_status()
                rows = r.json()
            except Exception as exc:
                print(f"[ct] query failed for {term!r}: {exc}")
                rows = []
            for row in rows:
                for name in str(row.get("name_value", "")).split("\n"):
                    name = name.strip().lstrip("*.").lower()
                    if name and looks_thai_lending_domain(name):
                        domains.setdefault(registrable_domain(name), None)
            time.sleep(self.pause)
        return list(domains)

    def _allowed(self, url: str) -> bool:
        host = host_of(url)
        rp = self._robots.get(host)
        if rp is None:
            rp = urllib.robotparser.RobotFileParser()
            try:
                resp = self.s.get(f"https://{host}/robots.txt", timeout=10)
                rp.parse(resp.text.splitlines() if resp.status_code == 200 else [])
            except Exception:
                rp.parse([])
            self._robots[host] = rp
        return rp.can_fetch(USER_AGENT, url)

    def fetch(self, domain: str) -> Optional[dict]:
        from bs4 import BeautifulSoup
        url = f"https://{domain}/"
        if not self._allowed(url):
            return None
        try:
            r = self.s.get(url, timeout=self.timeout, allow_redirects=True)
        except Exception:
            return None
        finally:
            time.sleep(self.pause)
        if r.status_code != 200 or "html" not in r.headers.get("Content-Type", ""):
            return None
        html = r.text[:1_000_000]
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = " ".join(soup.get_text(" ").split())[:20_000]
        links = sorted({a["href"] for a in soup.find_all("a", href=True)})[:300]
        ids = extract_identifiers(text + " " + " ".join(links))
        art = base_artefact(
            artefact_id=f"web:{domain}", source="web", url=r.url,
            name=(soup.title.string.strip() if soup.title and soup.title.string else domain),
            description=text, outbound_links=links, line_ids=ids["line_ids"],
            phones=ids["phones"], bank_accounts=ids["bank_accounts"], apk_links=ids["apk_links"],
        )
        art["raw_sha256"] = sha256_json({"url": r.url, "html": html})
        return art


def collect_live(sources: Iterable[str] = ("google_play", "app_store", "web"),
                 max_per_source: int = 200) -> list[dict]:
    """Run the selected collectors once and return artefacts in the common schema."""
    terms = C.SEARCH_TERMS_TH + C.SEARCH_TERMS_EN
    out: list[dict] = []
    if "google_play" in sources:
        gp = GooglePlayCollector()
        for app_id in gp.discover(terms)[:max_per_source]:
            art = gp.fetch(app_id)
            if art:
                out.append(art)
    if "app_store" in sources:
        ios = AppStoreCollector()
        for item in ios.discover(terms)[:max_per_source]:
            out.append(ios.to_artefact(item))
    if "web" in sources:
        web = WebCollector()
        for dom in web.discover()[:max_per_source]:
            art = web.fetch(dom)
            if art:
                out.append(art)
    return out
