"""Build Pinterest-specific RSS plus original Shiori-backed cards from PUBLIC WordPress RSS.

Intentionally separate from WordPress's own RSS, the Survival40 Auto release pipeline,
and Metricool's individual scheduling flow. No Pinterest/WordPress credentials.
Do not enable more than ONE RSS auto-publisher for the same article set.
"""
import datetime as dt
import html
import io
import json
import os
import re
from email.utils import parsedate_to_datetime
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SITE = "https://www.survival40.com"
API = SITE + "/feed/"
SOURCE_ART = SITE + "/wp-content/plugins/survival40-auto/assets/navigator/explain.webp"
RAW = "https://raw.githubusercontent.com/BL4GS/survival40-auto/main/"
RSS_PATH = Path("pinterest/survival40-pins.xml")
ASSET_DIR = Path("assets/pinterest/auto")
START_UTC = dt.datetime(2026, 10, 15, 15, 0, 0, tzinfo=dt.timezone.utc)
SEED_ID = 512   # One verified older article, never post the earlier Metricool Pin 393 again.
MAX_ITEMS = 24


def request_bytes(url, limit=600_000):
    req = urllib.request.Request(url, headers={"User-Agent": "Survival40-PinterestRSS/1.0", "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=25) as response:
        data = response.read(limit + 1)
        if len(data) > limit or not data:
            raise RuntimeError("Source response is empty or exceeds maximum")
        return data


def plain(raw):
    text = re.sub(r"<[^>]+>", " ", html.unescape(raw if isinstance(raw, str) else ""))
    return re.sub(r"\s+", " ", text).strip()


def verify_rss_item(item, now=None):
    """Accept only public WordPress RSS items on the claimed canonical domain."""
    if not isinstance(item, ET.Element):
        return None
    raw_link = (item.findtext("link") or "").strip()
    parsed = urllib.parse.urlsplit(raw_link)
    if parsed.scheme != "https" or parsed.netloc != "www.survival40.com":
        return None
    # WordPress AIOSEO adds tracking parameters to feed URLs. Remove them
    # only if they are the expected first-party RSS tracking keys and values.
    pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    allowed = {"utm_source": "rss", "utm_medium": "rss",
               "utm_campaign": parsed.path.strip("/")}
    if any(k not in allowed or v != allowed[k] for k,v in pairs):
        return None
    url = urllib.parse.urlunsplit((parsed.scheme,parsed.netloc,parsed.path,"",""))
    if not re.fullmatch(r"https://www[.]survival40[.]com/[A-Za-z0-9_-]+/",url):
        return None
    title = plain(item.findtext("title"))
    desc_html = item.findtext("description") or ""
    # Strip the WordPress RSS "The post ... first appeared on ..." boilerplate.
    desc_html = re.split(r"<p>\s*The post\s",desc_html,1,flags=re.I)[0]
    excerpt = plain(desc_html)
    if not 9 <= len(title) <= 160 or len(excerpt) < 15:
        return None
    pid = item.findtext("{com-wordpress:feed-additions:1}post-id")
    guid = item.findtext("guid") or ""
    # Both ID representations must agree to eliminate accidental re-mapping.
    match = re.fullmatch(r"https://www[.]survival40[.]com/\?p=([1-9][0-9]{0,17})",guid)
    if not match or not pid or not pid.isdigit() or int(pid) != int(match.group(1)):
        return None
    try:
        when = parsedate_to_datetime(item.findtext("pubDate") or "")
        if when.tzinfo is None:
            return None
        when = when.astimezone(dt.timezone.utc)
    except (TypeError,ValueError,OverflowError,IndexError):
        return None
    now = now or dt.datetime.now(dt.timezone.utc)
    if when > now + dt.timedelta(minutes=1):
        return None
    return {"id":int(pid),"link":url,"title":title,"excerpt":excerpt,"date":when,
            # These are links into an affiliate-funded site, so an explicit
            # PR label is safe even if the source RSS excludes ad markup.
            "has_ads":True}


def collect():
    # Do not use the WordPress REST API: GitHub runners receive HTTP 403
    # for /wp-json, while the PUBLIC WordPress RSS and artwork return 200.
    root = ET.fromstring(request_bytes(API,800_000))
    if root.tag != "rss" or root.get("version") != "2.0":
        raise RuntimeError("Unexpected source feed format; refuse to publish")
    items = root.findall("./channel/item")
    if len(items) > 30:
        raise RuntimeError("Unexpectedly large source RSS; refuse to backfill")
    valid = [p for item in items if (p:=verify_rss_item(item)) is not None]
    # No mass backfill: a single previously reviewed seed article, then
    # articles newly published since the owner-approved automation start.
    selected = [p for p in valid if (p["date"] >= START_UTC or p["id"] == SEED_ID)
                and p["id"] != 393]
    dedup = {p["id"]:p for p in selected}
    if not dedup:
        raise RuntimeError("No eligible public articles in the RSS; leave prior feed untouched")
    return sorted(dedup.values(),key=lambda p:(p["date"],p["id"]))[-MAX_ITEMS:]

def font(size, bold=True):
    choices = ([
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
    ] if bold else [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    ])
    for path in choices:
        if Path(path).exists():
            return ImageFont.truetype(path, size, index=0)
    raise RuntimeError("Missing Japanese Noto CJK font")


def wrap(draw, text, f, max_width, max_lines):
    lines, acc = [], ""
    for char in text:
        if draw.textlength(acc + char, font=f) > max_width and acc:
            lines.append(acc)
            acc = char
        else:
            acc += char
    if acc:
        lines.append(acc)
    if len(lines) > max_lines:
        raise RuntimeError("Card title does not fit safely")
    return lines


def render(post, portrait):
    canvas = Image.new("RGB", (1000, 1500), "#F8F8FF")
    draw = ImageDraw.Draw(canvas)
    head = None
    lines = None
    for size in (81, 76, 70, 64, 58, 52):
        candidate = font(size)
        try:
            attempt = wrap(draw, post["title"], candidate, 825, 4)
        except RuntimeError:
            continue
        if len(attempt) <= 4:
            head, lines = candidate, attempt
            break
    if head is None:
        raise RuntimeError("No safe title size for card " + str(post["id"]))
    y = 135
    for line in lines:
        draw.text((88, y), line, fill="#273041", font=head)
        y += head.size + 34
    # The original art should stay on the bottom left, but still remain legible in feeds.
    shiori = portrait.copy()
    scale = min(430 / shiori.height, 380 / shiori.width)
    shiori = shiori.resize((int(shiori.width * scale), int(shiori.height * scale)), Image.Resampling.LANCZOS)
    if shiori.mode != "RGBA":
        shiori = shiori.convert("RGBA")
    canvas.paste(shiori, (22, 1490 - shiori.height), shiori)
    sub = font(40, False)
    desc = wrap(draw, post["excerpt"][:48].rstrip("、。") + "。", sub, 825, 3)
    y = max(700, y + 55)
    draw.line([(88, y), (912, y)], fill="#C8D0DD", width=3)
    y += 46
    for line in desc:
        draw.text((88, y), line, font=sub, fill="#47556F")
        y += 61
    draw.text((478, 1265), "Survival40", font=font(40), fill="#273041")
    draw.text((478, 1331), "40代からの生存戦略", font=font(31, False), fill="#47556F")
    if post["has_ads"]:
        draw.text((894, 1440), "PR", font=font(23, False), fill="#8790A2")
    output = ASSET_DIR / (str(post["id"]) + ".png")
    output.parent.mkdir(parents=True, exist_ok=True)
    # A source article edit must not silently change an already-published pin's art.
    if not output.exists():
        canvas.save(output, format="PNG", optimize=True)
    return output


def rss(posts):
    from email.utils import format_datetime
    root = ET.Element("rss", {"version": "2.0"})
    ch = ET.SubElement(root, "channel")
    ET.SubElement(ch, "title").text = "Survival40 - Pinterest記事紹介"
    ET.SubElement(ch, "link").text = SITE + "/"
    ET.SubElement(ch, "description").text = "40代男性の美容・健康・生活を考えるSurvival40のオリジナル記事"
    ET.SubElement(ch, "language").text = "ja"
    for post in posts:
        item = ET.SubElement(ch, "item")
        ET.SubElement(item, "title").text = post["title"]
        ET.SubElement(item, "link").text = post["link"]
        ET.SubElement(item, "guid", {"isPermaLink": "true"}).text = post["link"]
        ET.SubElement(item, "description").text = post["excerpt"][:220]
        ET.SubElement(item, "pubDate").text = format_datetime(post["date"])
        ET.SubElement(item, "enclosure", {
            "url": RAW + str(ASSET_DIR / (str(post["id"]) + ".png")),
            "length": str((ASSET_DIR / (str(post["id"]) + ".png")).stat().st_size),
            "type": "image/png",
        })
    ET.indent(root)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def main():
    posts = collect()
    portrait_raw = request_bytes(SOURCE_ART, 2_000_000)
    portrait = Image.open(io.BytesIO(portrait_raw))
    portrait.load()
    portrait = portrait.convert("RGBA")
    if portrait.width < 120 or portrait.height < 120:
        raise RuntimeError("Original Shiori artwork unavailable")
    for post in posts:
        render(post, portrait)
    xml = rss(posts)
    ET.fromstring(xml)
    RSS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not RSS_PATH.exists() or RSS_PATH.read_bytes() != xml:
        RSS_PATH.write_bytes(xml)
    print("VERIFIED RSS: " + str(RSS_PATH) + " (" + str(len(posts)) + " articles)")
    print("All article links under " + SITE + " ; no legacy backfill besides seed " + str(SEED_ID))


if __name__ == "__main__":
    main()
