"""Build a non-publishing Instagram candidate queue from verified public article assets.

This deliberately cannot authenticate to Metricool or Instagram. Live duplicate
checks, pilot-publication verification and scheduling are separate gates.
"""
import datetime as dt
import email.utils
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlsplit

from PIL import Image

from scripts.instagram import build_assets as cards

READY = Path("instagram/ready-posts.json")
QUEUE = Path("instagram/publish-queue.json")
FEED = Path("pinterest/survival40-pins.xml")
ART = Path("assets/instagram/auto")
CUTOFF = dt.datetime(2026, 10, 16, tzinfo=dt.timezone(dt.timedelta(hours=9)))
PILOT_RESERVED = frozenset({512, 516})
RAW_PREFIX = "https://raw.githubusercontent.com/BL4GS/survival40-auto/main/assets/instagram/auto/"
SITE = "https://www.survival40.com"


def canonical_article(url):
    if not isinstance(url, str) or len(url) > 250:
        raise ValueError("Article URL is invalid")
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.netloc != "www.survival40.com"
            or parsed.query or parsed.fragment or parsed.username or parsed.password
            or not re.fullmatch(r"/[a-z0-9][a-z0-9-]*/", parsed.path)):
        raise ValueError("Article URL is not an allowed canonical permalink")
    return url


def feed_dates(feed_path):
    result, seen_urls = {}, set()
    for item in ET.parse(feed_path).getroot().findall("./channel/item"):
        enclosure = item.find("enclosure")
        if enclosure is None:
            raise ValueError("Missing verified feed media")
        image = enclosure.get("url", "")
        base = cards.PIN_PREFIX
        if not image.startswith(base):
            raise ValueError("Unrecognized Pinterest original-image URL")
        tail = image[len(base):]
        if not re.fullmatch(r"[1-9][0-9]*[.]png", tail):
            raise ValueError("Unsafe Pinterest image identifier")
        ident = int(tail[:-4])
        url = canonical_article(item.findtext("link"))
        if ident in result or url in seen_urls:
            raise ValueError("Duplicated article or id in public RSS")
        pub = email.utils.parsedate_to_datetime(item.findtext("pubDate", ""))
        if pub.tzinfo is None:
            raise ValueError("Article publication date has no timezone")
        result[ident] = (pub, url, item.findtext("title"))
        seen_urls.add(url)
    return result


def verify_image(ident, url, images_dir):
    expected = RAW_PREFIX + str(ident) + ".png"
    if url != expected:
        raise ValueError("Untrusted Instagram image URL")
    path = Path(images_dir) / (str(ident) + ".png")
    if not path.is_file():
        raise ValueError("Missing original Instagram image for article")
    with Image.open(path) as image:
        if image.format != "PNG" or image.size != cards.IG_SIZE:
            raise ValueError("Instagram image is not the expected 1080x1350 PNG")
        image.verify()
    return expected


def prepare(feed_path=FEED, ready_path=READY, images_dir=ART,
            queue_path=QUEUE, trusted_posts=None):
    raw = json.loads(Path(ready_path).read_text(encoding="utf-8"))
    if (raw.get("brand") != "Survival40"
            or raw.get("source") != "verified_Pinterest_static_feed"
            or raw.get("publishing_enabled") is not False
            or not isinstance(raw.get("items"), list)):
        raise ValueError("Manifest is not verified, non-publishing Survival40 data")
    dates = feed_dates(feed_path)
    # The producer verifies each RSS image and permitted permalink. Allow
    # injection only in local isolated tests, never through CLI arguments.
    trusted_posts = (cards.items_from_pinterest_feed(feed_path)
                     if trusted_posts is None else trusted_posts)
    posts = {p["id"]: p for p in trusted_posts}
    if len(posts) != len(trusted_posts) or set(posts) != set(dates):
        raise ValueError("Trusted Pinterest RSS items do not match feed dates")
    present, urls, rows = set(), set(), []
    for entry in raw["items"]:
        ident = entry.get("article_id")
        if type(ident) is not int or ident not in dates or ident in present:
            raise ValueError("Untrusted or duplicate Instagram manifest article")
        pub, url, title = dates[ident]
        post = posts[ident]
        if (entry.get("title") != title or post["title"] != title
                or entry.get("article_url") != url or post["article_url"] != url
                or entry.get("caption_draft") != cards.caption_from_source(post)
                or entry.get("status") != "assets_ready_not_published"):
            raise ValueError("Instagram draft does not match original published article")
        if url in urls:
            raise ValueError("Duplicate destination in Instagram manifest")
        verify_image(ident, entry.get("instagram_image"), images_dir)
        present.add(ident)
        urls.add(url)
        if pub.astimezone(CUTOFF.tzinfo) < CUTOFF or ident in PILOT_RESERVED:
            continue
        rows.append({
            "article_id": ident, "article_url": url, "title": title,
            "published_at": pub.isoformat(),
            "instagram_image": entry["instagram_image"],
            "caption_draft": entry["caption_draft"],
            "status": "NOT_SCHEDULED_REQUIRES_METRICOOL_CHECK",
        })
    # If the feed has changed since the previous card generation, skip its new
    # entries until matching image/card assets exist; NEVER guess their URLs.
    rows.sort(key=lambda p: (p["published_at"], p["article_id"]))
    payload = {
        "brand": "Survival40", "publishing_enabled": False,
        "metricool_connected_account": "survival40_jp",
        "pilot_article_id": 516, "pilot_success_verified": False,
        "requires": [
            "Confirm Instagram pilot ID 516 is PUBLISHED, not PENDING/FAILED",
            "Read live Metricool existing posts and check duplicate URLs/titles",
            "Check plan limits and future publication slot",
            "Schedule at most one image-backed post; verify persisted PENDING",
        ],
        "items": rows,
    }
    dest = Path(queue_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode()
    if not dest.exists() or dest.read_bytes() != data:
        dest.write_bytes(data)
    print(f"Prepared {len(rows)} Instagram candidates; zero posts scheduled")
    return payload


if __name__ == "__main__":
    prepare()
