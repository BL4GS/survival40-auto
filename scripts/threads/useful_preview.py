"""Preview-only Shiori practical notes based on validated Survival40 RSS excerpts.

No API calls, no generative model, no authentication, no publication, and no
modification of existing Threads scheduler or draft filenames.
"""
import datetime as dt
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

FEED = Path("pinterest/survival40-pins.xml")
OUTPUT = Path("threads-output/useful-preview.json")
ACCOUNT = "@survival40_jp"
SITE = "https://www.survival40.com"
IMG_ROOT = (
    "https://raw.githubusercontent.com/BL4GS/"
    "survival40-auto/main/assets/pinterest/auto/"
)
MAX_FEED_BYTES = 1_000_000
MAX_NOTE_CHARS = 240
JST = ZoneInfo("Asia/Tokyo")

# A small set of literal, pre-reviewed, non-medical tips; each one must be
# independently backed by the current, exactly matching public-feed excerpt.
# The RSS is a historical publication signal, NOT a live WordPress status check.
RULES = (
    {
        "id": 608,
        "slug": "40s-mens-clothing-size-fit-guide",
        "title_terms": ("服のサイズ選び", "肩幅"),
        "evidence_terms": ("肩幅", "身幅", "着丈", "返品条件"),
        "text": (
            "通販で服のサイズを選ぶとき、肩幅・身幅・着丈を見比べるだけでも"
            "判断材料が増えます。返品条件も先に確認しておきたいですね。"
        ),
    },
    {
        "id": 610,
        "slug": "40s-clothes-odor-after-washing-guide",
        "title_terms": ("洗濯", "ニオイ"),
        "evidence_terms": ("洗剤量", "詰め込み", "乾燥", "洗濯槽"),
        "text": (
            "洗濯したのに服のニオイが残るなら、洗剤の量だけでなく、"
            "洗濯物の詰め込み方や乾燥、洗濯槽も確認してみるとよさそうです。"
        ),
    },
    {
        "id": 616,
        "slug": "40s-mens-casual-clothes-how-many",
        "title_terms": ("私服", "何着"),
        "evidence_terms": ("週末の外出回数", "洗濯頻度", "季節", "棚卸し"),
        "text": (
            "私服が何着あれば足りるかは、外出回数や洗濯頻度、季節でも"
            "変わります。買い足す前に、手持ちの服を数えてみるのもいいですね。"
        ),
    },
    {
        "id": 617,
        "slug": "40s-mens-shoe-odor-foot-care",
        "title_terms": ("靴", "臭い"),
        "evidence_terms": ("足の洗い方", "靴下の交換", "靴の乾燥"),
        "text": (
            "靴のニオイが気になるときは、靴そのものだけでなく、"
            "足の洗い方、靴下の交換、靴を乾かすことも見直しの候補です。"
        ),
    },
)


class PreviewSourceError(ValueError):
    """Feed does not supply enough verified, unchanged metadata."""


def require_permalink(url, slug):
    if not isinstance(url, str) or url != SITE + "/" + slug + "/":
        raise PreviewSourceError("Article permalink is not the approved canonical URL")
    parsed = urlsplit(url)
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise PreviewSourceError("Article permalink has unexpected URL attributes")
    return url


def verified_articles(feed=FEED):
    path = Path(feed)
    if path.stat().st_size > MAX_FEED_BYTES:
        raise PreviewSourceError("RSS exceeds safe size limit")
    raw = path.read_bytes()
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        raise PreviewSourceError("Invalid RSS document") from None
    if root.tag != "rss":
        raise PreviewSourceError("Unexpected feed root")
    channel = root.find("channel")
    if channel is None:
        raise PreviewSourceError("Missing RSS channel")
    rows = {}
    seen_urls = set()
    for entry in channel.findall("item"):
        url = entry.findtext("link")
        if not isinstance(url, str) or url in seen_urls:
            raise PreviewSourceError("Duplicate or missing public article URL")
        seen_urls.add(url)
        image = entry.find("enclosure")
        title = entry.findtext("title")
        description = entry.findtext("description")
        for rule in RULES:
            if url != SITE + "/" + rule["slug"] + "/":
                continue
            if (not isinstance(title, str) or
                not isinstance(description, str) or
                not all(term in title for term in rule["title_terms"]) or
                not all(term in description for term in rule["evidence_terms"]) or
                image is None or
                image.attrib.get("url") != IMG_ROOT + str(rule["id"]) + ".png" or
                image.attrib.get("type") != "image/png"):
                raise PreviewSourceError(
                    "Approved excerpt and original article identity do not match"
                )
            rows[rule["id"]] = {
                "id": rule["id"],
                "title": title,
                "url": require_permalink(url, rule["slug"]),
                "evidence": { "excerpt_terms": list(rule["evidence_terms"]) },
                "text": rule["text"],
            }
    return rows


def make_previews(entries):
    """Return samples only; absence of any source fails closed for that sample."""
    if not isinstance(entries, dict):
        raise PreviewSourceError("Invalid preview input")
    previews = []
    for rule in RULES:
        row = entries.get(rule["id"])
        if row is None:
            continue
        text = row["text"]
        if (not isinstance(text, str) or
            not 25 <= len(text) <= MAX_NOTE_CHARS or
            any(token in text for token in (
                "https://", "http://", "#", "今すぐ購入", "絶対に治る",
                "必ず治る", "私が使った", "買ってよかった", "【PR】"
            )) or
            text.count("？") + text.count("?") > 1):
            raise PreviewSourceError("Unsafe useful-note text")
        previews.append({
            "account": ACCOUNT,
            "kind": "grounded_helpful_note",
            "text": text,
            "source_post_id": row["id"],
            "source_url": row["url"],
            "source_title": row["title"],
            "evidence_terms": row["evidence"]["excerpt_terms"],
            "publish": False,
            "status": "REVIEW_PREVIEW_ONLY",
            "requires_live_post_recheck": True,
        })
    return previews


def main():
    entries = verified_articles()
    result = {
        "generated_at_jst": dt.datetime.now(JST).isoformat(timespec="seconds"),
        "account": ACCOUNT,
        "publish": False,
        "mode": "preview_only_no_meta_credentials",
        "requires_fresh_wordpress_verification_before_any_later_live_use": True,
        "posts": make_previews(entries),
        "note": (
            "Text is limited to four pre-reviewed practical notes whose source "
            "title/excerpt and article URL matched GitHub's original-image RSS. "
            "No current live publishing status was rechecked. This file MUST "
            "NOT be passed to the existing Meta publisher."
        ),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("PREVIEW ONLY: " + str(len(result["posts"])) +
          " matched notes. No Threads/WordPress requests or posts.")


if __name__ == "__main__":
    main()
