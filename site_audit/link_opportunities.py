"""Review-only internal-link candidates from already fetched public WordPress REST posts.

No network requests, no automatic edits, no claims that same-category pages are
semantically equivalent. Matches are hypotheses for editorial review only.
"""
from collections import Counter
from html.parser import HTMLParser
import re

from site_audit.discovery import html_paths, public_path

MAX_CANDIDATES = 12
MAX_POSTS_FOR_PAIRING = 100
STOP_PHRASES = (
    "40代", "男性", "女性", "解説", "対策", "方法", "選び方", "おすすめ",
    "比較", "違い", "ポイント", "初心者", "注意点", "使い方", "見直し方",
)


class TitleReader(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.fragments = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.fragments.append(data)


def title_text(post):
    item = post.get("title")
    html = item.get("rendered", "") if isinstance(item, dict) else ""
    if not isinstance(html, str):
        return ""
    reader = TitleReader()
    reader.feed(html)
    return " ".join(reader.fragments).strip()


def title_grams(title):
    clean = title.casefold()
    for phrase in STOP_PHRASES:
        clean = clean.replace(phrase, " ")
    # Character n-grams work for Japanese without extra packages, but are
    # only rough lexical signals. Preserve boundaries around punctuation.
    tokens = re.findall(r"[a-z0-9\u3040-\u30ff\u3400-\u9fffー]+", clean)
    grams = set()
    for token in tokens:
        if len(token) >= 4:
            grams.update(token[i:i+4] for i in range(len(token) - 3))
        if len(token) >= 5:
            grams.update(token[i:i+5] for i in range(len(token) - 4))
    return grams


def review_candidates(posts, inbound_counts=None, limit=MAX_CANDIDATES):
    """Find unlinked article pairs sharing a category and rare title phrases.

    Inbound counts are advisory only and should come from analyze_discovery.
    Existing internal links are found in REST article bodies, NOT page chrome.
    """
    if type(limit) is not int or limit < 1 or limit > MAX_CANDIDATES:
        raise ValueError("Invalid candidate limit")
    if not isinstance(posts, list):
        raise ValueError("Posts inventory must be a list")
    if len(posts) > MAX_POSTS_FOR_PAIRING:
        # Never infer coverage from a partial/truncated inventory.
        return {"candidates": [], "scope": "inventory_too_large", "inspected": 0}

    entries = []
    for post in posts:
        if not isinstance(post, dict) or post.get("status") != "publish":
            continue
        pid = post.get("id")
        raw_categories = post.get("categories")
        path = public_path(post.get("link"))
        if (type(pid) is not int or pid < 1 or not path or path == "/"
                or not isinstance(raw_categories, list)
                or any(type(c) is not int or c <= 1 for c in raw_categories)):
            # Category 1 is WordPress Uncategorized: don't infer topical ties.
            continue
        content = post.get("content")
        html = content.get("rendered") if isinstance(content, dict) else None
        if not isinstance(html, str):
            continue
        title = title_text(post)
        grams = title_grams(title)
        if not title or not grams:
            continue
        links = html_paths(html, post["link"])
        entries.append({
            "id": pid, "path": path, "title": title, "categories": set(raw_categories),
            "grams": grams, "outgoing_paths": links,
        })
    # Repeated title boilerplate must not make every same-category post a match.
    frequency = Counter(g for e in entries for g in e["grams"])
    unique = [e for e in entries if len({x["id"] for x in entries}) == len(entries)]
    if len(unique) != len(entries):
        return {"candidates": [], "scope": "duplicate_post_ids", "inspected": len(entries)}
    inbound_counts = inbound_counts if isinstance(inbound_counts, dict) else {}
    proposed = []
    for source in entries:
        for target in entries:
            if source["id"] == target["id"]:
                continue
            shared_categories = source["categories"] & target["categories"]
            if not shared_categories or target["path"] in source["outgoing_paths"]:
                continue
            overlap = {
                g for g in source["grams"] & target["grams"]
                if frequency[g] <= max(2, len(entries) // 3)
            }
            if len(overlap) < 2:
                continue
            # Never assert a real editorial connection from lexical overlap.
            score = len(overlap)
            inbound = inbound_counts.get(str(target["id"]))
            if type(inbound) is not int or inbound < 0:
                inbound = None
            proposed.append((
                -score, inbound if inbound is not None else 10**6,
                source["id"], target["id"],
                {
                    "source_post_id": source["id"],
                    "target_post_id": target["id"],
                    "source_title": source["title"],
                    "target_title": target["title"],
                    "shared_category_ids": sorted(shared_categories),
                    "overlapping_title_grams": score,
                    "target_known_body_inbound": inbound,
                    "status": "REVIEW_ONLY_NOT_APPLIED",
                },
            ))
    proposed.sort()
    return {
        "candidates": [entry[-1] for entry in proposed[:limit]],
        "scope": "published_rest_body_links_and_shared_nondefault_category_only",
        "inspected": len(entries),
        "limitations": (
            "Lexical overlap is not semantic verification; title similarity may be "
            "coincidental. Candidate links must improve reader understanding and "
            "be checked for factual fit and anchor placement. No links were added."
        ),
    }
