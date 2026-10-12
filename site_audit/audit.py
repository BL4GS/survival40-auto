#!/usr/bin/env python3
"""Read-only public health audit for Survival40.

Only public WordPress REST and same-origin public pages are fetched.
This script does NOT login, publish, modify posts, change affiliate settings,
or treat any missing ad as a defect.
"""
import datetime as dt
from collections import Counter
from html.parser import HTMLParser
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

ORIGIN = "https://survival40.com"
REST_URL = ORIGIN + "/index.php?rest_route=%2Fwp%2Fv2%2Fposts"
MAX_POSTS = 90
PAGE_SIZE = 30
MAX_RESPONSE_BYTES = 1_500_000
MAX_CHECKED_PERMALINKS = 6
ROOT = pathlib.Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "site-audit-output"
AGENT = "Survival40-ReadOnly-HealthAudit/1.0"


class AuditSourceError(RuntimeError):
    pass


class StrictRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = urllib.parse.urlsplit(newurl)
        if target.scheme != "https" or target.netloc not in (
            "survival40.com", "www.survival40.com"
        ):
            raise AuditSourceError("Refused off-site redirect")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def public_get(url, max_bytes=MAX_RESPONSE_BYTES, head_only=False, preview=False):
    target = urllib.parse.urlsplit(url)
    if target.scheme != "https" or target.netloc not in (
        "survival40.com", "www.survival40.com"
    ) or target.username or target.password:
        raise AuditSourceError("Refused non-public or external URL")
    request = urllib.request.Request(url, headers={
        "User-Agent": AGENT, "Accept": "application/json, text/html",
    })
    try:
        with urllib.request.build_opener(StrictRedirects()).open(request, timeout=18) as response:
            # Page previews are capped independently of total HTML size.
            data = response.read(1024 if head_only else (500_000 if preview else max_bytes + 1))
            if not head_only and not preview and len(data) > max_bytes:
                raise AuditSourceError("Site response exceeds size limit")
            return response.status, dict(response.headers.items()), data
    except urllib.error.HTTPError as exc:
        # Never log full untrusted response bodies.
        return exc.code, {}, b""
    except (urllib.error.URLError, TimeoutError) as exc:
        raise AuditSourceError("Site connection failed: " + type(exc).__name__) from None


def safe_post_url(value):
    if not isinstance(value, str):
        raise ValueError("Missing permalink")
    u = urllib.parse.urlsplit(value)
    if u.scheme != "https" or u.netloc not in (
        "survival40.com", "www.survival40.com"
    ) or not u.path.startswith("/") or u.path == "/" or u.username or u.password:
        raise ValueError("Off-site or invalid permalink")
    if u.query or u.fragment:
        raise ValueError("Unexpected query/fragment in permalink")
    return value


class ContentReader(HTMLParser):
    """Extract reader-visible text, links and article image-alt data."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text = []
        self.links = []
        self.images = 0
        self.images_without_alt = 0
        self.hidden_depth = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ("script", "style"):
            self.hidden_depth += 1
        if self.hidden_depth:
            return
        if tag in ("p", "li", "h2", "h3", "h4", "div"):
            self.text.append(" ")
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
        if tag == "img":
            self.images += 1
            if not (attrs.get("alt") or "").strip():
                self.images_without_alt += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.hidden_depth:
            self.hidden_depth -= 1
        elif tag in ("p", "li", "h2", "h3", "h4", "div") and not self.hidden_depth:
            self.text.append(" ")

    def handle_data(self, data):
        if not self.hidden_depth:
            self.text.append(data)

    @property
    def words(self):
        return re.sub(r"\s+", " ", "".join(self.text)).strip()


def plain(html):
    parser = ContentReader()
    parser.feed(html if isinstance(html, str) else "")
    return parser.words


def fetch_posts():
    posts = []
    total_reported = None
    for page in range(1, MAX_POSTS // PAGE_SIZE + 1):
        params = urllib.parse.urlencode({
            "status": "publish", "orderby": "date", "order": "desc",
            "page": page, "per_page": PAGE_SIZE,
            "_fields": "id,status,link,date_gmt,modified_gmt,title,excerpt,content",
        })
        status, headers, raw = public_get(REST_URL + "&" + params)
        if status != 200:
            raise AuditSourceError(f"Public WordPress listing returned HTTP {status}")
        if "application/json" not in headers.get("Content-Type", ""):
            raise AuditSourceError("WordPress listing was not JSON")
        try:
            page_posts = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            raise AuditSourceError("WordPress listing contained invalid JSON") from None
        if not isinstance(page_posts, list):
            raise AuditSourceError("WordPress API did not return an article list")
        try:
            total_reported = int(headers.get("X-WP-Total", "0")) or total_reported
        except ValueError:
            pass
        posts.extend(page_posts)
        if len(page_posts) < PAGE_SIZE:
            break
    return posts, total_reported


def evaluate(posts, total_reported=None):
    findings = []
    seen_titles = {}
    checked = 0
    total_images_missing_alt = 0
    for post in posts:
        if not isinstance(post, dict):
            findings.append({"severity": "warning", "code": "invalid_post", "post_id": None,
                             "detail": "API item is not an object"})
            continue
        post_id = post.get("id")
        if type(post_id) is not int or post_id < 1:
            findings.append({"severity": "warning", "code": "missing_id", "post_id": None,
                             "detail": "Post has invalid ID"})
            continue
        checked += 1
        prefix = {"post_id": post_id}
        if post.get("status") != "publish":
            findings.append({**prefix, "severity": "warning", "code": "non_published_returned",
                             "detail": "API returned a non-published post"})
            continue
        try:
            safe_post_url(post.get("link"))
        except ValueError:
            findings.append({**prefix, "severity": "warning", "code": "unsafe_permalink",
                             "detail": "Public article URL is missing/off-site/invalid"})
        rendered_title = post.get("title") if isinstance(post.get("title"), dict) else {}
        title = plain(rendered_title.get("rendered", ""))
        if len(title) < 5:
            findings.append({**prefix, "severity": "warning", "code": "short_title",
                             "detail": "Article title has fewer than 5 characters"})
        key = re.sub(r"\s+", "", title).casefold()
        if key and key in seen_titles:
            findings.append({**prefix, "severity": "warning", "code": "duplicate_title",
                             "detail": f"Same normalized title as post {seen_titles[key]}"})
        seen_titles[key] = post_id
        rendered_content = post.get("content") if isinstance(post.get("content"), dict) else {}
        html = rendered_content.get("rendered", "")
        reader = ContentReader()
        if isinstance(html, str):
            reader.feed(html)
        length = len(reader.words)
        if length < 220:
            findings.append({**prefix, "severity": "warning", "code": "short_content",
                             "detail": f"Only {length} visible characters (threshold 220)"})
        total_images_missing_alt += reader.images_without_alt
        if reader.images_without_alt:
            findings.append({**prefix, "severity": "info", "code": "missing_image_alt",
                             "detail": f"{reader.images_without_alt}/{reader.images} article images have empty alt; decorative images may be intentional"})
        internal_links = 0
        for raw_href in reader.links:
            dest = urllib.parse.urlsplit(urllib.parse.urljoin(ORIGIN, raw_href))
            if dest.scheme == "https" and dest.netloc in ("survival40.com", "www.survival40.com"):
                if dest.path not in ("/", "") and not dest.path.startswith(("/wp-content/", "/wp-json/", "/wp-admin/")):
                    internal_links += 1
        if length >= 500 and internal_links == 0:
            findings.append({**prefix, "severity": "info", "code": "no_internal_links",
                             "detail": "Long article with no visible same-site content link; editorial choice may be intentional"})
        # Signals to inspect, not accusations of unsound health advice.
        if re.search(r"絶対に治る|必ず治る|100%治る|一発で治る|確実に治る", reader.words):
            findings.append({**prefix, "severity": "review", "code": "strong_health_claim",
                             "detail": "Possible unconditional health claim; review evidence and qualifiers"})
    if total_reported and total_reported > len(posts):
        findings.append({"severity": "info", "code": "sampling_limit", "post_id": None,
                         "detail": f"API reported {total_reported} posts; audit read {len(posts)} (cap {MAX_POSTS})"})
    return {
        "post_count": checked, "posts_sampled": len(posts),
        "total_api_reported": total_reported,
        "image_alt_gaps": total_images_missing_alt,
        "findings": findings,
        "finding_counts": dict(Counter(f["severity"] for f in findings)),
        "advertising_policy": "No-ad articles are valid. Missing ads are never a health-audit defect.",
    }


def probe_public_pages(posts):
    # Bound checks to homepage + 6 article pages. Compare HTML anchors with
    # known publicly published post permalinks, without executing JavaScript.
    urls = [ORIGIN + "/"]
    post_paths = set()
    for post in posts:
        try:
            url = safe_post_url(post.get("link") if isinstance(post, dict) else None)
            post_paths.add(urllib.parse.urlsplit(url).path.rstrip("/"))
            if url not in urls and len(urls) < MAX_CHECKED_PERMALINKS + 1:
                urls.append(url)
        except ValueError:
            pass
    results = []
    for url in urls:
        try:
            status, _, html = public_get(url, head_only=(url == ORIGIN + "/"),
                                         preview=(url != ORIGIN + "/"))
            outcome = "ok" if status == 200 else ("blocked" if status in (401, 403, 429) else "error")
            result = {"url": url, "status": status, "outcome": outcome}
            if status == 200 and url != ORIGIN + "/":
                reader = ContentReader()
                reader.feed(html.decode("utf-8", errors="replace"))
                own_path = urllib.parse.urlsplit(url).path.rstrip("/")
                linked_post_paths = set()
                for href in reader.links:
                    parsed = urllib.parse.urlsplit(urllib.parse.urljoin(url, href))
                    path = parsed.path.rstrip("/")
                    if (parsed.scheme == "https" and parsed.netloc in
                            ("survival40.com", "www.survival40.com") and
                            path != own_path and path in post_paths):
                        linked_post_paths.add(path)
                # Whole page includes navigation/footer. This is NOT
                # proof of editorial links inside the article text.
                result["rendered_other_post_links"] = len(linked_post_paths)
            results.append(result)
        except AuditSourceError as error:
            results.append({"url": url, "status": None, "outcome": "network_error",
                            "detail": str(error)})
    return results


def write_reports(report, destination=REPORT_DIR):
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rows = [
        "# Survival40 public site audit (read-only)",
        "",
        f"Generated UTC: {report['generated_at_utc']}",
        f"Published posts inspected: **{report['post_count']}**",
        f"Public API total reported: {report['total_api_reported'] or 'not provided'}",
        "No WordPress updates, releases, affiliate changes, or Threads posts were made.",
        "",
        "## Advisory findings",
    ]
    for finding in report["findings"][:100]:
        rows.append(f"- [{finding['severity']}] post #{finding['post_id'] or 'N/A'}: {finding['code']} — {finding['detail']}")
    if not report["findings"]:
        rows.append("- No automatic content findings in inspected posts. This does not certify factual accuracy.")
    rows += ["", "## Public page GET checks"]
    for result in report["page_checks"]:
        rows.append(f"- {result['status'] or 'N/A'} {result['outcome']}: {result['url']}" + (f" — links to other published posts in rendered page: {result['rendered_other_post_links']}" if "rendered_other_post_links" in result else ""))
    rows += ["", "## Important scope notes",
             "- The audit uses public WordPress REST responses and limited same-origin HTTP GETs only.",
             "- Missing affiliate links are not errors. Zero-ad articles remain valid.",
             "- Content flags are advisory and cannot prove incorrect health claims, poor SEO or broken rendering.",
             "- HTTP 403/429 may be site bot protection, not broken pages.",
             "- Rendered-page crosslinks include header/footer/sidebar; they do not prove article-body links.",
             "- Never auto-edit/publish or remove an article from audit findings.", ""]
    (destination / "audit.md").write_text("\n".join(rows), encoding="utf-8")


def main():
    posts, total_reported = fetch_posts()
    if not posts:
        raise AuditSourceError("No public posts returned: cannot certify site from empty response")
    report = evaluate(posts, total_reported)
    report["generated_at_utc"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    report["page_checks"] = probe_public_pages(posts)
    write_reports(report)
    print(f"PASS: Read-only audit of {report['post_count']} public posts")
    print(f"FINDINGS: {report['finding_counts']}")
    print(f"PAGE CHECKS: {[(x['status'], x['outcome']) for x in report['page_checks']]}")
    print("ARTIFACT: site-audit-output/audit.md (no production mutation)")


if __name__ == "__main__":
    try:
        main()
    except AuditSourceError as error:
        sys.exit("ERROR: read-only public audit failed: " + str(error))
