"""Read-only public transport probe for the EXISTING native Pinterest RSS source.

This checks whether the exact public GitHub RAW XML and one original image are
fetchable and match the verified repository bytes. It cannot read a Pinterest
account, confirm imported Pins, or establish website sessions/clicks.
No credentials, WordPress writes, Pinterest posting or feed mutation.
"""
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit

FEED_URL = ("https://raw.githubusercontent.com/BL4GS/survival40-auto/"
            "main/pinterest/survival40-pins.xml")
PIN_URL_ROOT = ("https://raw.githubusercontent.com/BL4GS/survival40-auto/"
                "main/assets/pinterest/auto/")
FEED = Path("pinterest/survival40-pins.xml")
PIN_DIR = Path("assets/pinterest/auto")
REPORT = Path("pinterest-audit/rss-delivery.json")
MAX_FEED = 300_000
MAX_IMAGE = 2_000_000
ARTICLE_HOST = "www.survival40.com"


class TransportCheckError(ValueError):
    pass


class DenyRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise TransportCheckError("Unexpected remote redirect; not followed")


def get_bytes(url, max_size):
    if url != FEED_URL and not re.fullmatch(
        re.escape(PIN_URL_ROOT) + r"[1-9][0-9]*[.]png", url
    ):
        raise TransportCheckError("URL outside the fixed approved source")
    req = urllib.request.Request(url, headers={
        "User-Agent": "Survival40-readonly-Pinterest-RSS-check/1.0",
        "Accept": "application/rss+xml, application/xml, image/png, */*;q=0.1",
        "Accept-Encoding": "identity",
    }, method="GET")
    try:
        with urllib.request.build_opener(DenyRedirects()).open(req, timeout=12) as response:
            if response.status != 200:
                raise TransportCheckError("Remote source was not HTTP 200")
            kind = response.headers.get("Content-Type", "unknown")
            raw = response.read(max_size + 1)
    except (urllib.error.HTTPError, urllib.error.URLError,
            TimeoutError, OSError) as exc:
        raise TransportCheckError("Public fetch failed: " + type(exc).__name__) from None
    if not raw or len(raw) > max_size:
        raise TransportCheckError("Remote data missing or over byte budget")
    return raw, kind


def local_article_media_pairs(feed_bytes):
    if len(feed_bytes) > MAX_FEED:
        raise TransportCheckError("Local feed exceeds budget")
    try:
        root = ET.fromstring(feed_bytes)
    except ET.ParseError:
        raise TransportCheckError("RSS is not valid XML") from None
    if root.tag != "rss" or not root.attrib.get("version", "").startswith("2."):
        raise TransportCheckError("Not RSS 2.x")
    channel = root.find("channel")
    if channel is None:
        raise TransportCheckError("Missing feed channel")
    rows, ids, urls = [], set(), set()
    for item in channel.findall("item"):
        url = item.findtext("link")
        enclosure = item.find("enclosure")
        guid = item.findtext("guid")
        if (not isinstance(url, str) or enclosure is None
                or guid != url or url in urls):
            raise TransportCheckError("Missing or duplicate article destination")
        parsed = urlsplit(url)
        if (parsed.scheme != "https" or parsed.netloc != ARTICLE_HOST
                or not re.fullmatch(r"/[a-z0-9][a-z0-9-]*/", parsed.path)
                or parsed.query or parsed.fragment):
            raise TransportCheckError("RSS links leave verified article domain")
        media = enclosure.attrib.get("url", "")
        match = re.fullmatch(
            re.escape(PIN_URL_ROOT) + r"([1-9][0-9]*)[.]png", media
        )
        if (not match or enclosure.attrib.get("type") != "image/png"
                or int(match.group(1)) in ids or not item.findtext("title")
                or not item.findtext("description")):
            raise TransportCheckError("Unverified image identity, title or description")
        article_id = int(match.group(1))
        ids.add(article_id)
        urls.add(url)
        rows.append((article_id, media, url))
    if not rows or len(rows) > 100:
        raise TransportCheckError("Unexpected RSS inventory size")
    return rows


def probe(feed=FEED, pins=PIN_DIR, report=REPORT, fetch=get_bytes):
    """One XML + one image GET, both fixed allowlisted GitHub RAW endpoints."""
    local = Path(feed).read_bytes()
    rows = local_article_media_pairs(local)
    result = {
        "checked_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "feed_url": FEED_URL,
        "configured_native_rss_source_unchanged": True,
        "read_only": True,
        "network_get_budget": 2,
        "checked_local_items": len(rows),
        "published_pinterest_pin_verified": False,
        "pinterest_rss_subscription_verified_by_this_probe": False,
        "website_sessions_verified": False,
        "note": ("External RAW transport only. A reachable RSS and image do NOT "
                 "prove Pinterest accepted or published an imported Pin."),
    }
    try:
        remote, xml_type = fetch(FEED_URL, MAX_FEED)
        result["remote_feed_content_type"] = xml_type
        result["remote_rss_byte_identical"] = (remote == local)
        # RSS bytes must match the exact checked-in, article-validated feed.
        # If the branch is ahead of GitHub's RAW CDN, do not infer failure of
        # Pinterest's native RSS importer: label this stale/unknown.
        if remote != local:
            result["status"] = "REMOTE_RSS_DIFFERS_REVIEW_CACHE_OR_UPDATE"
        else:
            ident, media, destination = rows[0]
            image_path = Path(pins) / (str(ident) + ".png")
            if (not image_path.is_file()
                    or image_path.stat().st_size > MAX_IMAGE):
                raise TransportCheckError("Verified local image missing or oversized")
            local_image = image_path.read_bytes()
            actual, image_type = fetch(media, MAX_IMAGE)
            result["sample_article_id"] = ident
            result["sample_article_url"] = destination
            result["sample_image_url"] = media
            result["remote_image_content_type"] = image_type
            result["remote_image_sha256_matches_local"] = (
                hashlib.sha256(actual).digest()
                == hashlib.sha256(local_image).digest()
            )
            result["status"] = (
                "RSS_AND_SAMPLE_IMAGE_TRANSPORT_OK"
                if result["remote_image_sha256_matches_local"]
                else "REMOTE_IMAGE_DIFFERS_REVIEW"
            )
    except (TransportCheckError, OSError, UnicodeError) as exc:
        result["status"] = "UNAVAILABLE_UNVERIFIED"
        result["error_type"] = type(exc).__name__
    dest = Path(report)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    print("PINTEREST RAW TRANSPORT: " + result["status"])
    print("Pinterest native RSS imported Pin: NOT VERIFIED by this probe")
    return result


if __name__ == "__main__":
    probe()
