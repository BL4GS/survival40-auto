"""Read-only Survival40 public social-preview metadata audit.

Never edits WordPress, its SEO plugin, media, social posts, or GitHub history.
Only fetches canonical published URLs already present in verified Pinterest RSS.
"""
import datetime as dt
import json
import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

SITE = "https://www.survival40.com"
FEED = Path("pinterest/survival40-pins.xml")
REPORT = Path("social-audit/og-status.json")
PIN_PREFIX = "https://raw.githubusercontent.com/BL4GS/survival40-auto/main/assets/pinterest/auto/"
OG_PREFIX = "https://raw.githubusercontent.com/BL4GS/survival40-auto/main/assets/social/og/"
MAX_HTML_BYTES = 450_000
MAX_ITEMS = 10


class MetaParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags = {}
        self.in_head = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "head":
            self.in_head = True
        if tag != "meta" or not self.in_head:
            return
        key = attrs.get("property") or attrs.get("name")
        val = attrs.get("content")
        if key and val:
            self.tags.setdefault(key.lower(), []).append(val)

    def handle_endtag(self, tag):
        if tag == "head":
            self.in_head = False


def canonical(url):
    if not isinstance(url, str):
        raise ValueError("Non-text canonical URL")
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.netloc != "www.survival40.com"
            or parsed.query or parsed.fragment
            or parsed.path.startswith(("/wp-admin/", "/wp-login/"))
            or not re.fullmatch(r"/[a-z0-9][a-z0-9-]*/", parsed.path)):
        raise ValueError("Only verified published Survival40 permalink allowed")
    return url


def source_items(feed=FEED):
    root = ET.parse(feed).getroot()
    rows, ids, urls = [], set(), set()
    for item in root.findall("./channel/item"):
        link = canonical(item.findtext("link"))
        image_tag = item.find("enclosure")
        if image_tag is None:
            raise ValueError("Missing original RSS enclosure")
        image = image_tag.get("url", "")
        if not image.startswith(PIN_PREFIX):
            raise ValueError("Unexpected Pinterest media source")
        match = re.fullmatch(r"([1-9][0-9]*)[.]png", image[len(PIN_PREFIX):])
        if not match or image_tag.get("type") != "image/png":
            raise ValueError("Unverified pinned asset")
        ident = int(match.group(1))
        if ident in ids or link in urls:
            raise ValueError("Duplicate RSS identity")
        ids.add(ident)
        urls.add(link)
        rows.append({"article_id": ident, "article_url": link,
                     "expected_social_image": OG_PREFIX + str(ident) + ".png"})
    return rows[:MAX_ITEMS]


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Cross-origin or unreviewed redirect forbidden")


def fetch_public_head(url):
    canonical(url)
    request = urllib.request.Request(
        url, headers={"User-Agent": "Survival40-social-image-audit/1.0",
                      "Accept": "text/html"}, method="GET")
    with urllib.request.build_opener(NoRedirect()).open(request, timeout=12) as res:
        if res.status != 200:
            raise ValueError("Non-200 public article")
        if res.headers.get_content_type() != "text/html":
            raise ValueError("Not a public HTML document")
        raw = res.read(MAX_HTML_BYTES + 1)
        if len(raw) > MAX_HTML_BYTES:
            raise ValueError("HTML exceeds audit size limit")
    # The site is Japanese WordPress using UTF-8; only parse the head.
    text = raw.decode("utf-8", errors="replace")
    if "</head>" not in text.lower():
        raise ValueError("HTML head not available in audit")
    return text[:text.lower().index("</head>") + len("</head>")]



def inspect_discover_metadata(meta):
    """Report *HTML head metadata*, never assert Google Discover eligibility.

    This audit cannot inspect X-Robots-Tag HTTP headers, AMP, Google indexing,
    Google Search Console Discover impressions, or actual image dimensions.
    Missing an explicit HTML large-preview tag is not a negative eligibility
    verdict: Google might have other signals and settings.
    """
    values = (meta.tags.get("robots", []) +
              meta.tags.get("googlebot", []))
    directives = []
    for value in values:
        if isinstance(value, str):
            directives.extend(
                part.strip().casefold() for part in value.split(",")
                if part.strip()
            )
    previews = {d for d in directives if d.startswith("max-image-preview:")}
    if len(previews) > 1:
        preview = "CONFLICTING_HTML_PREVIEW_DIRECTIVES_REVIEW"
    elif "max-image-preview:large" in previews:
        preview = "LARGE_DECLARED_IN_HTML"
    elif previews & {"max-image-preview:standard", "max-image-preview:none"}:
        preview = "LARGE_NOT_ALLOWED_BY_HTML_DIRECTIVE_REVIEW"
    elif previews:
        preview = "UNRECOGNIZED_HTML_PREVIEW_DIRECTIVE_REVIEW"
    else:
        preview = "NOT_DECLARED_IN_HTML_HEADER_NOT_CHECKED"

    image_candidates = (meta.tags.get("og:image", []) +
                        meta.tags.get("og:image:url", []))
    width = meta.tags.get("og:image:width", [])
    height = meta.tags.get("og:image:height", [])
    return {
        "html_large_image_preview_hint": preview,
        "html_noindex_hint": "noindex" in directives,
        "og_image_count": len(image_candidates),
        "og_image_width_claim": width[:2],
        "og_image_height_claim": height[:2],
        "schema_images_checked": False,
        "http_x_robots_tag_checked": False,
        "image_bytes_or_dimensions_verified": False,
        "google_indexing_checked": False,
        "discover_appearance_checked": False,
        "note": (
            "Read-only HTML metadata observations, not Google Discover "
            "eligibility or appearance. Absence of og:image does not prove "
            "absence of a schema image. Dimensions are untrusted declarations."
        ),
    }

def inspect(item, html):
    meta = MetaParser()
    meta.feed(html)
    og = meta.tags.get("og:image", []) + meta.tags.get("og:image:url", [])
    twitter = meta.tags.get("twitter:image", []) + meta.tags.get("twitter:image:src", [])
    expected = item["expected_social_image"]
    if len(og) == 0:
        status = "MISSING_OG_IMAGE"
    elif len(og) != 1:
        status = "MULTIPLE_OG_IMAGES_REVIEW"
    elif og[0] == expected:
        status = "EXACT_ORIGINAL_SOCIAL_CARD"
    else:
        status = "OTHER_IMAGE_REVIEW"
    return {
        **item, "status": status,
        "og_images": og[:5], "twitter_images": twitter[:5],
        "og_title_present": bool(meta.tags.get("og:title")),
        "twitter_card": (meta.tags.get("twitter:card") or [None])[0],
        "discover_metadata": inspect_discover_metadata(meta),
        "note": "Metadata audit only: not proof of social cache or image legibility",
    }


def run(feed=FEED, report=REPORT, fetcher=fetch_public_head):
    items = source_items(feed)
    rows = []
    for item in items:
        try:
            rows.append(inspect(item, fetcher(item["article_url"])))
        except (OSError, UnicodeError, ValueError,
                urllib.error.URLError, urllib.error.HTTPError) as exc:
            rows.append({**item, "status": "UNAVAILABLE_UNVERIFIED",
                         "error_type": type(exc).__name__})
    result = {
        "site": SITE, "read_only": True, "changed_site": False,
        "checked_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "checked": len(rows), "items": rows,
        "all_original_og_verified": bool(rows) and all(
            row["status"] == "EXACT_ORIGINAL_SOCIAL_CARD" for row in rows),
    }
    report = Path(report)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    for row in rows:
        print(f'Article #{row["article_id"]}: {row["status"]}')
    print("READ-ONLY: no WordPress or social post changes")
    return result


if __name__ == "__main__":
    run()
