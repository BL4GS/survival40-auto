"""Fail closed if the GENERATED static Pinterest RSS does not match its local images.

This validates the repository artifact, not whether Pinterest actually published
a Pin. No network, credentials or WordPress writes are needed.
"""
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlsplit

from PIL import Image

from scripts.pinterest.build_rss import ASSET_DIR, MAX_ITEMS, RAW, RSS_PATH, SITE


class InvalidPinterestFeed(ValueError):
    pass


def ensure(condition, reason):
    if not condition:
        raise InvalidPinterestFeed(reason)


def validate(rss_path=RSS_PATH, asset_dir=ASSET_DIR, now=None):
    rss_path, asset_dir = Path(rss_path), Path(asset_dir)
    ensure(rss_path.is_file(), "RSS file missing")
    ensure(100 <= rss_path.stat().st_size <= 100_000, "Unexpected RSS file size")
    try:
        root = ET.parse(rss_path).getroot()
    except ET.ParseError as exc:
        raise InvalidPinterestFeed("RSS XML malformed") from exc
    ensure(root.tag == "rss" and root.get("version") == "2.0", "Not RSS 2.0")
    channel = root.find("channel")
    ensure(channel is not None and channel.findtext("link") == SITE + "/",
           "RSS channel does not identify the claimed website")
    items = channel.findall("item")
    ensure(1 <= len(items) <= MAX_ITEMS, "Unsafe feed item count")
    seen = set()
    now = now or datetime.now(timezone.utc)
    expected_raw = RAW + "assets/pinterest/auto/"
    for item in items:
        ensure(all(child.tag in {"title", "link", "guid", "description",
                                 "pubDate", "enclosure"} for child in item),
               "Unexpected item tag: may generate additional pins")
        link = (item.findtext("link") or "").strip()
        ensure(bool(re.fullmatch(r"https://www[.]survival40[.]com/[A-Za-z0-9_-]+/", link)),
               "Pin destination is not a canonical claimed-domain article")
        ensure(link not in seen, "Duplicate article in RSS")
        seen.add(link)
        ensure(item.findtext("guid") == link
               and item.find("guid") is not None
               and item.find("guid").get("isPermaLink") == "true",
               "RSS GUID must agree with article URL")
        title = (item.findtext("title") or "").strip()
        desc = (item.findtext("description") or "").strip()
        ensure(9 <= len(title) <= 160 and len(desc) >= 15,
               "Empty or suspiciously short Pin text")
        try:
            published = parsedate_to_datetime(item.findtext("pubDate") or "")
            ensure(published.tzinfo is not None
                   and published.astimezone(timezone.utc) <= now + timedelta(minutes=1),
                   "Invalid or future publication date")
        except (TypeError, ValueError, OverflowError, IndexError) as exc:
            raise InvalidPinterestFeed("Invalid publication date") from exc
        enclosure = item.findall("enclosure")
        ensure(len(enclosure) == 1, "Each article requires exactly one image")
        image_url = enclosure[0].get("url") or ""
        ensure(image_url.startswith(expected_raw)
               and bool(re.fullmatch(r"[1-9][0-9]*[.]png", image_url[len(expected_raw):])),
               "Image URL must point to its dedicated first-party-built static card")
        filename = image_url[len(expected_raw):]
        ensure(filename != "393.png", "Prevent duplicate of the Metricool first Pin")
        image_path = asset_dir / filename
        ensure(image_path.is_file(), "Referenced Pin image missing: " + filename)
        ensure(enclosure[0].get("type") == "image/png"
               and enclosure[0].get("length") == str(image_path.stat().st_size),
               "Pin image type or declared byte length is incorrect")
        try:
            with Image.open(image_path) as image:
                ensure(image.format == "PNG" and image.size == (1000, 1500),
                       "Pin card must be a PNG with 2:3 vertical proportions")
                ensure(image.convert("RGB").getpixel((999, 1499)) == (248, 248, 255),
                       "Pin card does not have expected Ghost White base")
                image.verify()
        except (OSError, ValueError) as exc:
            raise InvalidPinterestFeed("Unreadable or invalid Pin card") from exc
    return len(items)


if __name__ == "__main__":
    count = validate()
    print("VALIDATED: Pinterest static RSS with", count,
          "claimed-domain article(s), image assets and unique destinations")
