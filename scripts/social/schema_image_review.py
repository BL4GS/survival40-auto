"""Bounded, offline inspection of Article JSON-LD image sources in public HTML.

Never follows image URLs, checks pixels, changes WordPress, or certifies Discover.
Only inspects <head> JSON-LD from already-fetched canonical article HTML.
"""
import json
from html.parser import HTMLParser
from urllib.parse import urlsplit

MAX_SCRIPTS = 12
MAX_SCRIPT_CHARS = 64_000
MAX_NODES = 250
ARTICLE_TYPES = {"article", "blogposting", "newsarticle"}


class _HeadJSONLD(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_head = False
        self.in_ld = False
        self.parts = []
        self.size = 0
        self.scripts = []
        self.incomplete = False

    def handle_starttag(self, tag, attrs):
        if tag == "head":
            self.in_head = True
        if tag == "script" and self.in_head and not self.in_ld:
            attributes = dict(attrs)
            mime = attributes.get("type", "").split(";", 1)[0].strip().lower()
            if mime == "application/ld+json":
                self.in_ld = True
                self.parts = []
                self.size = 0

    def handle_data(self, data):
        if self.in_ld:
            self.size += len(data)
            if self.size <= MAX_SCRIPT_CHARS:
                self.parts.append(data)
            else:
                self.incomplete = True

    def handle_endtag(self, tag):
        if tag == "script" and self.in_ld:
            if len(self.scripts) < MAX_SCRIPTS:
                self.scripts.append("".join(self.parts) if self.size <= MAX_SCRIPT_CHARS else None)
            else:
                self.incomplete = True
            self.in_ld = False
            self.parts = []
        if tag == "head":
            self.in_head = False


def _nodes(value):
    """Walk only likely JSON-LD graph containers; bound depth and node count."""
    stack = [(value, 0)]
    seen = 0
    while stack and seen < MAX_NODES:
        obj, depth = stack.pop()
        seen += 1
        if depth > 12:
            continue
        if isinstance(obj, list):
            stack.extend((child, depth + 1) for child in reversed(obj[:MAX_NODES]))
        elif isinstance(obj, dict):
            yield obj
            for key in ("@graph", "mainEntity", "hasPart"):
                if key in obj:
                    stack.append((obj[key], depth + 1))


def _image_urls(image):
    if isinstance(image, str):
        yield image
    elif isinstance(image, list):
        for value in image[:20]:
            yield from _image_urls(value) if not isinstance(value, list) else ()
    elif isinstance(image, dict):
        for key in ("url", "contentUrl"):
            value = image.get(key)
            if isinstance(value, str):
                yield value


def _article_type(node):
    types = node.get("@type", [])
    if isinstance(types, str):
        types = [types]
    return isinstance(types, list) and any(
        isinstance(t, str) and t.casefold().split("/")[-1] in ARTICLE_TYPES
        for t in types
    )


def review_schema_images(html):
    """Return triage hints only; never claim Google indexing or image suitability."""
    parser = _HeadJSONLD()
    parser.feed(html)
    incomplete = parser.incomplete or parser.in_ld
    images = []
    for raw in parser.scripts:
        if raw is None:
            incomplete = True
            continue
        try:
            data = json.loads(raw)
        except (ValueError, TypeError):
            incomplete = True
            continue
        for node in _nodes(data):
            if _article_type(node):
                images.extend(_image_urls(node.get("image")))
    images = list(dict.fromkeys(images))[:30]
    hosts = []
    for url in images:
        try:
            parsed = urlsplit(url)
            host = (parsed.hostname or "").casefold() if parsed.scheme in ("https", "http") else ""
        except ValueError:
            host = ""
        hosts.append(host)

    if any(host == "a8.net" or host.endswith(".a8.net") for host in hosts):
        state = "POSSIBLE_A8_AFFILIATE_IMAGE_REVIEW"
    elif any(host == "gravatar.com" or host.endswith(".gravatar.com") for host in hosts):
        state = "GRAVATAR_AVATAR_IMAGE_REVIEW"
    elif images:
        state = "OTHER_ARTICLE_SCHEMA_IMAGE_DIMENSIONS_UNVERIFIED"
    elif incomplete:
        state = "SCHEMA_JSON_UNPARSEABLE_REVIEW"
    else:
        state = "NO_ARTICLE_SCHEMA_IMAGE_OBSERVED"

    return {
        "schema_images_checked": bool(parser.scripts) and not incomplete,
        "schema_json_ld_scripts_seen": len(parser.scripts),
        "schema_parse_incomplete": incomplete,
        "article_schema_image_count": len(images),
        "article_schema_image_source_hint": state,
        "schema_review_note": (
            "Limited to Article/BlogPosting/NewsArticle JSON-LD in the fetched "
            "HTML head. A8 or Gravatar host is a review signal, not proof of "
            "advertising misuse. No image URL fetched, dimensions verified, "
            "Discover appearance checked, or WordPress setting changed."
        ),
    }
