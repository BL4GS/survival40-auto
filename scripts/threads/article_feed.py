"""Read-only selection of newly published Survival40 articles for occasional Threads links.

Uses only the publicly visible WordPress REST API, never admin credentials or
WordPress writes. Failures are treated as no eligible article: daily character
posts remain possible without claiming that an article exists.
"""
import datetime as dt
import html
from html.parser import HTMLParser
import json
import re
import urllib.error
import urllib.parse
import urllib.request

SITE = "https://www.survival40.com"
API = SITE + "/wp-json/wp/v2/posts"
FALLBACK_API = SITE + "/index.php?rest_route=%2Fwp%2Fv2%2Fposts"
MAX_BYTES = 600_000
MAX_AGE = dt.timedelta(days=4)


class ArticleSourceError(RuntimeError):
    pass


class TextOnly(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.hidden += 1
        if tag in ("p", "div", "li", "h2", "h3") and not self.hidden:
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.hidden:
            self.hidden -= 1
        if tag in ("p", "div", "li", "h2", "h3") and not self.hidden:
            self.parts.append(" ")

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def plain(value):
    if not isinstance(value, str):
        return ""
    parser = TextOnly()
    parser.feed(value[:20_000])
    return re.sub(r"\s+", " ", "".join(parser.parts)).strip()


def require_article_url(value):
    if not isinstance(value, str):
        raise ArticleSourceError("Missing article URL")
    url = urllib.parse.urlsplit(value)
    if (url.scheme != "https" or url.netloc not in
            ("survival40.com", "www.survival40.com") or
            not re.fullmatch(r"/[A-Za-z0-9_-]+/", url.path) or
            url.query or url.fragment or url.username or url.password or url.port):
        raise ArticleSourceError("Noncanonical or off-site article URL")
    return value


class SameSiteHTTPS(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        url = urllib.parse.urlsplit(newurl)
        if url.scheme != "https" or url.netloc not in ("survival40.com", "www.survival40.com"):
            raise ArticleSourceError("Article source redirect leaves allowlist")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_public_posts():
    params = urllib.parse.urlencode({
        "status": "publish", "per_page": 40, "orderby": "date", "order": "desc",
        "_fields": "id,date_gmt,link,status,title,excerpt,content"
    })
    candidates = [API + "?" + params, FALLBACK_API + "&" + params]
    for index, url in enumerate(candidates):
        request = urllib.request.Request(url, headers={
            "Accept": "application/json", "User-Agent": "Survival40-Shiori/1.0"
        })
        try:
            with urllib.request.build_opener(SameSiteHTTPS()).open(request, timeout=20) as response:
                if response.headers.get("Content-Type", "").split(";")[0] != "application/json":
                    raise ArticleSourceError("Public WordPress endpoint did not return JSON")
                raw = response.read(MAX_BYTES + 1)
                if len(raw) > MAX_BYTES:
                    raise ArticleSourceError("Too much article data")
                data = json.loads(raw.decode("utf-8"))
                if not isinstance(data, list):
                    raise ArticleSourceError("Invalid published article listing")
                return data
        except urllib.error.HTTPError as exc:
            if index == 0 and exc.code in (403, 404):
                continue
            raise ArticleSourceError("WordPress public API HTTP " + str(exc.code)) from None
        except (urllib.error.URLError, TimeoutError, UnicodeError,
                json.JSONDecodeError) as exc:
            raise ArticleSourceError("Cannot read verified article feed") from None
    raise ArticleSourceError("Both verified article feed paths unavailable")


def last_link_slot(now):
    """Wednesday and Saturday evening; returns the preceding such slot.

    The exclusive cutoff prevents choosing the same article on consecutive
    article slots without needing any untrusted persistent browser storage.
    """
    if now.tzinfo is None:
        raise ValueError("Time zone is required")
    if now.weekday() not in (2, 5) or now.hour != 20:
        raise ValueError("Only Wednesday/Saturday 20h are link slots")
    previous = now.date() - dt.timedelta(days=4 if now.weekday() == 2 else 3)
    return dt.datetime.combine(previous, dt.time(20), tzinfo=now.tzinfo)


def select_recent(posts, now):
    if now.tzinfo is None:
        raise ValueError("Time zone is required")
    cutoff = last_link_slot(now).astimezone(dt.timezone.utc)
    utcnow = now.astimezone(dt.timezone.utc)
    ready = []
    if not isinstance(posts, list):
        raise ArticleSourceError("Invalid source data")
    for article in posts:
        if not isinstance(article, dict) or article.get("status") != "publish":
            continue
        try:
            post_id = article.get("id")
            if type(post_id) is not int or post_id <= 0:
                continue
            url = require_article_url(article.get("link"))
            published_raw = article.get("date_gmt")
            if not isinstance(published_raw, str):
                continue
            published = dt.datetime.fromisoformat(published_raw.replace("Z", "+00:00"))
            if published.tzinfo is None:
                published = published.replace(tzinfo=dt.timezone.utc)
            published = published.astimezone(dt.timezone.utc)
            if not cutoff < published <= utcnow:
                continue
            title = plain(article.get("title", {}).get("rendered"))
            excerpt = plain(article.get("excerpt", {}).get("rendered"))
            body = plain(article.get("content", {}).get("rendered"))
            if not 8 <= len(title) <= 150 or len(body) < 120:
                continue
            ready.append({"id": post_id, "title": title, "excerpt": excerpt[:240],
                          "url": url, "published": published.isoformat()})
        except (AttributeError, TypeError, ValueError, ArticleSourceError):
            continue
    return max(ready, key=lambda a: (a["published"], a["id"])) if ready else None


def build_article_text(article):
    """Use only article metadata, not model-made product/health claims."""
    url = require_article_url(article["url"])
    title = article["title"]
    if not isinstance(title, str) or not 8 <= len(title) <= 150:
        raise ValueError("Article title invalid")
    text = "【PR】今日はSurvival40の記事から、ひとつ。\n「" + title + "」\n\n" + url
    if not 50 <= len(text) <= 500:
        raise ValueError("Article introduction exceeds limit")
    return text
