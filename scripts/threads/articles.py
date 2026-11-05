"""Read *public, published* Survival40 WordPress articles for Threads drafts.

No WordPress credentials, no admin endpoints, no publishing actions.
All network requests are restricted to the canonical Survival40 origin.
"""
import datetime as dt
from html.parser import HTMLParser
import json
import re
import urllib.error
import urllib.parse
import urllib.request


SITE = "https://survival40.com"
API = SITE + "/wp-json/wp/v2/posts"
FALLBACK_API = SITE + "/index.php?rest_route=%2Fwp%2Fv2%2Fposts"
USER_AGENT = "Survival40-Threads-Article-Drafts/0.1"
MAX_BYTES = 512_000


class ArticleSourceError(RuntimeError):
    pass


class VisibleHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.output = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("style", "script"):
            self.hidden += 1
        if tag in ("p", "div", "li", "h2", "h3") and not self.hidden:
            self.output.append(" ")

    def handle_endtag(self, tag):
        if tag in ("style", "script") and self.hidden:
            self.hidden -= 1
        if tag in ("p", "div", "li", "h2", "h3") and not self.hidden:
            self.output.append(" ")

    def handle_data(self, data):
        if not self.hidden:
            self.output.append(data)


def plain_text(html):
    if not isinstance(html, str):
        return ""
    parser = VisibleHTML()
    parser.feed(html[:35_000])
    return re.sub(r"\s+", " ", "".join(parser.output)).strip()


def safe_article_url(url):
    if not isinstance(url, str):
        raise ArticleSourceError("Missing article URL")
    parsed = urllib.parse.urlsplit(url)
    if (parsed.scheme != "https" or parsed.netloc not in
            ("survival40.com", "www.survival40.com") or
            not parsed.path.startswith("/") or parsed.path == "/" or
            parsed.username or parsed.password):
        raise ArticleSourceError("Off-site, insecure or non-article URL")
    if parsed.query or parsed.fragment:
        raise ArticleSourceError("Article URL has unverified query or fragment")
    return url


class StrictHTTPS(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Prevent following redirects to other hosts, LANs or private endpoints.
        parsed = urllib.parse.urlsplit(newurl)
        if parsed.scheme != "https" or parsed.netloc not in ("survival40.com", "www.survival40.com"):
            raise ArticleSourceError("WordPress redirect leaves allowed domain")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_public_posts():
    query = urllib.parse.urlencode({
        "status": "publish", "per_page": 30, "orderby": "date", "order": "desc",
        "_fields": "id,date_gmt,link,status,title,excerpt,content",
    })
    endpoints = [API + "?" + query, FALLBACK_API + "&" + query]
    for index, endpoint in enumerate(endpoints):
        request = urllib.request.Request(endpoint, headers={
            "Accept": "application/json", "User-Agent": USER_AGENT,
        })
        try:
            with urllib.request.build_opener(StrictHTTPS()).open(request, timeout=25) as response:
                if response.headers.get("Content-Type", "").split(";")[0] != "application/json":
                    raise ArticleSourceError("WordPress REST API did not return JSON")
                raw = response.read(MAX_BYTES + 1)
                if len(raw) > MAX_BYTES:
                    raise ArticleSourceError("WordPress response too large")
                data = json.loads(raw.decode("utf-8"))
                if not isinstance(data, list):
                    raise ArticleSourceError("Unexpected WordPress article listing")
                return data
        except urllib.error.HTTPError as exc:
            if index == 0 and exc.code in (403, 404):
                # Some WordPress security configurations block pretty REST paths
                # while allowing the equivalent canonical index.php rest_route.
                continue
            raise ArticleSourceError(f"WordPress article source rejected request (HTTP {exc.code})") from None
        except (urllib.error.URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ArticleSourceError("WordPress REST API unavailable or invalid: " + type(exc).__name__) from None
    raise ArticleSourceError("Both approved public WordPress article endpoints unavailable")


def select_article(posts, now=None, hours=24):
    now = now or dt.datetime.now(dt.timezone.utc)
    if now.tzinfo is None:
        raise ValueError("UTC-aware now required")
    candidates = []
    for article in posts:
        if not isinstance(article, dict) or article.get("status") != "publish":
            continue
        post_id = article.get("id")
        if type(post_id) is not int or post_id <= 0:
            continue
        try:
            url = safe_article_url(article.get("link"))
            timestamp = dt.datetime.fromisoformat(article["date_gmt"].replace("Z", "+00:00"))
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=dt.timezone.utc)
            age = now - timestamp.astimezone(dt.timezone.utc)
            if not dt.timedelta(0) <= age <= dt.timedelta(hours=hours):
                continue
            title = plain_text(article.get("title", {}).get("rendered"))
            excerpt = plain_text(article.get("excerpt", {}).get("rendered"))
            body = plain_text(article.get("content", {}).get("rendered"))
            if len(title) < 5 or len(body) < 120:
                continue
            candidates.append({
                "id": str(post_id), "title": title[:180], "url": url,
                "excerpt": excerpt[:600], "body": body[:3400],
                "published_at_utc": timestamp.astimezone(dt.timezone.utc).isoformat()
            })
        except (KeyError, TypeError, ValueError, ArticleSourceError):
            continue
    candidates.sort(key=lambda post: (post["published_at_utc"], int(post["id"])), reverse=True)
    return candidates[0] if candidates else None
