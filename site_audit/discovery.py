"""Read-only internal article discovery coverage, from already fetched public data.

No extra WordPress REST requests; homepage HTML comes from the existing page probe.
This is *not* a complete crawl and cannot prove search indexation or true orphans.
"""
from collections import Counter
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

HOSTS = frozenset(("survival40.com", "www.survival40.com"))


class Anchors(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href")
            if isinstance(href, str):
                self.hrefs.append(href)


def public_path(value, base="https://www.survival40.com/"):
    """Accept same-site HTTPS links only; normalize trailing slash/query/fragment."""
    if not isinstance(value, str):
        return None
    parsed = urlsplit(urljoin(base, value))
    if (parsed.scheme != "https" or parsed.hostname not in HOSTS
            or parsed.username or parsed.password or parsed.port not in (None, 443)):
        return None
    return parsed.path.rstrip("/") or "/"


def html_paths(html, base):
    if not isinstance(html, str):
        return set()
    reader = Anchors()
    reader.feed(html)
    return set(filter(None, (public_path(href, base) for href in reader.hrefs)))


def analyze_discovery(posts, homepage_html=None):
    """Page links vs article-body crosslinks, without requesting any further pages."""
    paths = {}
    for post in posts:
        if not isinstance(post, dict) or post.get("status") != "publish":
            continue
        post_id = post.get("id")
        path = public_path(post.get("link"))
        if type(post_id) is int and post_id > 0 and path and path != "/":
            paths[path] = post_id

    homepage_ids = None
    if isinstance(homepage_html, str):
        homepage_ids = sorted({
            paths[path] for path in html_paths(homepage_html, "https://www.survival40.com/")
            if path in paths
        })

    inbound = Counter()
    outgoing = {}
    for post in posts:
        if not isinstance(post, dict) or post.get("status") != "publish":
            continue
        post_id = post.get("id")
        base = post.get("link")
        if not isinstance(base, str) or post_id not in paths.values():
            continue
        content = post.get("content")
        html = content.get("rendered", "") if isinstance(content, dict) else ""
        linked = {
            paths[path] for path in html_paths(html, base)
            if path in paths and paths[path] != post_id
        }
        outgoing[post_id] = len(linked)
        inbound.update(linked)

    listed = set(paths.values())
    missing = None if homepage_ids is None else sorted(listed - set(homepage_ids))
    no_body_inbound = sorted(post_id for post_id in listed if inbound[post_id] == 0)
    return {
        "posts_in_inventory": len(listed),
        "homepage_inspected": homepage_ids is not None,
        "homepage_links_to_published_posts": len(homepage_ids) if homepage_ids is not None else None,
        "homepage_linked_ids": homepage_ids,
        "not_linked_on_homepage_ids": missing,
        "no_other_post_body_inbound_ids": no_body_inbound,
        "articles_with_no_body_outgoing_ids": sorted(pid for pid, cnt in outgoing.items() if cnt == 0),
        "body_inbound_counts": {str(pid): inbound[pid] for pid in sorted(listed)},
        "not_linked_from_home_or_post_body_ids": (
            sorted(set(missing).intersection(no_body_inbound))
            if missing is not None else None
        ),
        "scope_note": (
            "Public REST article-body links + one homepage HTML snapshot only. "
            "Other pages, categories, dynamically rendered recommendations, search engine "
            "indexation and hidden navigation were not crawled. Zero counted links "
            "does NOT prove an article is orphaned."
        ),
    }
