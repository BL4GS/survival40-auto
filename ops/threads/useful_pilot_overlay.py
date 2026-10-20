"""No-publisher, one-for-one Shiori helpful-post trial overlay.

Executed *after* the existing immutable-Shiori-generator creates its safe
everyday fallback, *before* the existing, independently guarded publisher.
Four Thursday 16:00 JST posts only, never extra slots and never article links.
The source is a separately pinned and reviewed GitHub checkout.
"""
import datetime as dt
import importlib.util
import json
import re
import urllib.error
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urlsplit
from pathlib import Path
from zoneinfo import ZoneInfo

ACCOUNT = "@survival40_jp"
START = dt.date(2026, 10, 22)
END = dt.date(2026, 11, 12)
JST = ZoneInfo("Asia/Tokyo")


def eligible(now, draft):
    if (not isinstance(now, dt.datetime) or now.tzinfo is None
            or now.utcoffset() != dt.timedelta(hours=9)
            or not isinstance(draft, dict)):
        return False
    day = now.date()
    if (not START <= day <= END or day.weekday() != 3
            or now.hour != 16
            or draft.get("slot") != "afternoon"
            or draft.get("kind") != "everyday"
            or draft.get("date_jst") != day.isoformat()
            or draft.get("id") != day.isoformat() + "-afternoon"
            or draft.get("account") != ACCOUNT
            or draft.get("article_id") is not None
            or draft.get("article_url") is not None
            or draft.get("article_title") is not None
            or draft.get("publish") is not False
            or draft.get("status") != "prepared_for_separate_publish_gate"):
        return False
    # A generated draft from today, not an old/other-account message.
    try:
        generated = dt.datetime.fromisoformat(draft["generated_at_jst"])
    except (TypeError, ValueError, KeyError):
        return False
    if (generated.tzinfo is None
            or generated.utcoffset() != dt.timedelta(hours=9)
            or not 0 <= (now - generated).total_seconds() <= 600):
        return False
    return True


def choose_helpful(now, approved_root):
    """Require exact reviewed RSS excerpts/IDs, otherwise no replacement."""
    root = Path(approved_root).resolve()
    helper_file = root / "scripts/threads/useful_preview.py"
    if not helper_file.is_file():
        raise ValueError("Missing approved helpful text/source validator")
    spec = importlib.util.spec_from_file_location("approved_helpful_only", helper_file)
    if spec is None or spec.loader is None:
        raise ValueError("Unusable approved helpful validator")
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    entries = helper.verified_articles(root / "pinterest/survival40-pins.xml")
    candidates = helper.make_previews(entries)
    # Four approved, distinct pieces of source-backed copy. Missing an entry
    # means ordinary Shiori continues, rather than shifting topics.
    expected_ids = (608, 610, 616, 617)
    if [p["source_post_id"] for p in candidates] != list(expected_ids):
        raise ValueError("Approval inventory changed")
    pilot_week = (now.date() - START).days // 7
    if not 0 <= pilot_week < len(candidates):
        raise ValueError("Outside approved four-post campaign")
    selected = candidates[pilot_week]
    if (selected.get("status") != "REVIEW_PREVIEW_ONLY"
            or selected.get("publish") is not False
            or selected.get("account") != ACCOUNT
            or selected.get("source_url") != entries[selected["source_post_id"]]["url"]
            or selected.get("requires_live_post_recheck") is not True):
        raise ValueError("Changed approved helper metadata")
    return selected



class PublishedArticleHead(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.canonical_urls = []
        self.og_urls = []
        self.body_parts = []
        self.in_body = False
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        props = dict(attrs)
        if tag == "body":
            self.in_body = True
        if tag in ("script", "style", "noscript"):
            self.hidden += 1
        if tag == "link" and "canonical" in props.get("rel", "").split():
            self.canonical_urls.append(props.get("href"))
        if tag == "meta" and props.get("property") == "og:url":
            self.og_urls.append(props.get("content"))

    def handle_endtag(self, tag):
        if tag == "body":
            self.in_body = False
        if tag in ("script", "style", "noscript") and self.hidden:
            self.hidden -= 1

    def handle_data(self, data):
        if self.in_body and not self.hidden:
            self.body_parts.append(data)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Unexpected published-article redirect")


def fetch_public_article(url):
    parsed = urlsplit(url)
    if (parsed.scheme != "https"
            or parsed.netloc != "www.survival40.com"
            or not re.fullmatch(r"/[a-z0-9][a-z0-9-]*/", parsed.path)
            or parsed.query or parsed.fragment):
        raise ValueError("Unverified site article URL")
    request = urllib.request.Request(url, method="GET", headers={
        "User-Agent": "Survival40-Shiori-helpful-article-readonly/1.0",
        "Accept": "text/html",
    })
    with urllib.request.build_opener(NoRedirect()).open(request, timeout=12) as response:
        if response.status != 200 or response.headers.get_content_type() != "text/html":
            raise ValueError("Article not publicly served as HTML")
        payload = response.read(450_001)
    if len(payload) > 450_000:
        raise ValueError("Article HTML exceeds read-only limit")
    return payload.decode("utf-8", errors="replace")


def verify_live_article(selected, fetcher=fetch_public_article):
    """Current *public HTML* proof, not a WordPress authenticated status query."""
    if not isinstance(selected, dict):
        return False
    url = selected.get("source_url")
    evidence = selected.get("evidence_terms")
    if (not isinstance(url, str)
            or not isinstance(evidence, list) or len(evidence) < 2
            or any(not isinstance(term, str) or not term for term in evidence)):
        return False
    try:
        body = fetcher(url)
        if not isinstance(body, str) or len(body) > 450_000:
            return False
        parser = PublishedArticleHead()
        parser.feed(body)
        visible = " ".join(parser.body_parts)
        if (parser.canonical_urls != [url] or
                any(other != url for other in parser.og_urls) or
                len(visible.strip()) < 120):
            return False
        # Require two independently sourced literal topic anchors actually
        # present in the CURRENT publicly rendered article body.
        return sum(term in visible for term in evidence) >= 2
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError,
            OSError, UnicodeError, ValueError, TypeError):
        return False


def apply(draft_path, approved_root, now, validate_post, live_check=verify_live_article):
    """Only mutates one pre-existing draft on a 4-date pilot; never posts."""
    path = Path(draft_path)
    draft = json.loads(path.read_text(encoding="utf-8"))
    if not eligible(now, draft):
        return "SKIPPED_NOT_APPROVED_SLOT"
    try:
        selected = choose_helpful(now, approved_root)
        reviewed_text = validate_post(selected["text"], "afternoon", 300)
        if reviewed_text != selected["text"]:
            raise ValueError("Reviewed wording mutated")
        if live_check(selected) is not True:
            raise ValueError("Current public article check unavailable")
    except (ValueError, OSError, UnicodeError, KeyError, TypeError,
            ImportError, AttributeError):
        # Source/wording drift: preserve vetted Gemini everyday draft as-is.
        return "SKIPPED_SOURCE_INVALID_ORDINARY_PRESERVED"
    updated = dict(draft)
    updated["text"] = reviewed_text
    updated["helpful_source_post_id"] = selected["source_post_id"]
    updated["helpful_source_url"] = selected["source_url"]
    updated["helpful_overlay_kind"] = "one_slot_grounded_pilot"
    encoded = json.dumps(updated, ensure_ascii=False, indent=2) + "\n"
    path.write_text(encoded, encoding="utf-8")
    return "PREPARED_ONE_FOR_ONE_HELPFUL_POST_NO_PUBLISH"


def main():
    # Main action deliberately has NO Meta credentials and NO API client.
    from scripts.threads.compose import OUTPUT, validate_post
    root = Path(__file__).resolve().parents[2]
    now = dt.datetime.now(JST)
    status = apply(OUTPUT, root, now, validate_post)
    print(status)


if __name__ == "__main__":
    main()
