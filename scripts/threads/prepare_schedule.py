"""Prepare exactly one scheduled Shiori text, with a tiny sourced article calendar.

This module only writes a draft. The publishing gate is completely separate.
The first live slot uses a previously human-approved everyday example.
"""
import datetime as dt
import json
import os
import sys

from .compose import (CONFIG, JST, OUTPUT, build_prompt, choose_slot,
                      gemini_generate, validate_post)
from .article_feed import ArticleSourceError, fetch_public_posts
from .evergreen_links import select_verified, slot_spec
from .topic_discovery import read_safe_signal

START_DATE = dt.date(2026, 10, 13)
FIRST_TEXT = (
    "洗面台に置く小物がいつの間にか増えていて、"
    "どこに並べるのが一番使いやすいのか最近ずっと考えています。"
    "でも結局、いつも適当な位置に戻してしまうんですよね。"
)
# Verified published Survival40 article titles and HTTPS permalink URLs.
# One article takes the place of that evening's everyday post, never added on top.
MORNING_GREETING = "おはようございます。"


def add_morning_greeting(text):
    """A consistent opening for 08:00, never a duplicated model-generated greeting.

    Evening posts and article introductions are intentionally not modified.
    """
    import re
    if not isinstance(text, str):
        raise ValueError("Morning copy must be text")
    body = re.sub(r"^\s*おはようございます[。！!、,\s]*", "", text).strip()
    if not body:
        raise ValueError("Morning copy must include content beyond a greeting")
    return MORNING_GREETING + "\n" + body


ARTICLE_CALENDAR = {
    "2026-10-14": {
        "title": "40代男性の日焼け止めの選び方｜毎日使いやすい条件を整理",
        "slug": "40s-male-sunscreen-how-to-choose",
        "intro": "日焼け止め、選ぶだけでも種類が多くて迷いますよね。40代男性が毎日使うことを考えた選び方を記事にまとめています。",
    },
    "2026-10-17": {
        "title": "40代男性の筋トレ用ヨガマットの選び方｜薄すぎると続かない理由",
        "slug": "40s-male-yoga-mat-home-training",
        "intro": "ヨガマットって、厚みの違いをどこまで気にすればいいのか迷います。自宅で運動するときの選び方を記事にまとめました。",
    },
    "2026-10-21": {
        "title": "40代男性の電動歯ブラシの選び方｜続けやすさで比べるポイント",
        "slug": "40s-male-electric-toothbrush-guide",
        "intro": "電動歯ブラシも、機能が多ければいいとは限らないですよね。無理なく続けられるものを選ぶポイントについての記事です。",
    },
    "2026-10-24": {
        "title": "40代男性のオールインワン化粧品の選び方｜続けやすさを優先する",
        "slug": "40s-male-all-in-one-skincare-guide",
        "intro": "スキンケアは、続けられるかどうかも大事だと思います。40代男性向けに、オールインワンの選び方を整理した記事です。",
    },
}


def choose_copy(now, config, gemini_key):
    slot = choose_slot(now)
    if slot is None or now.date() < START_DATE:
        return None
    date = now.date().isoformat()
    article_id, article_url, fallback_text = None, None, None
    if date == "2026-10-13" and slot == "evening":
        text, kind, title = FIRST_TEXT, "everyday", None
    elif slot == "evening" and date in ARTICLE_CALENDAR:
        article = ARTICLE_CALENDAR[date]
        from urllib.parse import urlsplit
        url = "https://www.survival40.com/" + article["slug"] + "/"
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.hostname != "www.survival40.com":
            raise ValueError("Article is not an approved Survival40 URL")
        text = "【PR】" + article["intro"] + "\n\n" + url
        title, kind = article["title"], "article"
        article_url = url
    else:
        # Always prepare an ordinary Shiori post as the safe fallback.
        # This preserves the regular cadence if an older article is unavailable,
        # unpublished, or already introduced on the independent 22:00 slot.
        if not gemini_key:
            raise ValueError("Gemini key is required for ordinary posts")
        # Only Tue/Fri 20:00 ordinary slots may use a fresh, aggregated,
        # source-verified topic. Missing scope/data keeps the old editorial plan.
        signal = read_safe_signal(
            now, os.getenv("GITHUB_TOKEN", ""), config, slot
        ) if slot == "evening" and date not in ARTICLE_CALENDAR else None
        instruction = build_prompt(now, slot, config, topic_signal=signal)
        generated = gemini_generate(instruction["prompt"], gemini_key)
        if slot == "morning":
            generated = add_morning_greeting(generated)
        ordinary_text = validate_post(generated, slot, config["max_characters"])
        evergreen = None
        if slot_spec(now) is not None:
            try:
                evergreen = select_verified(now, fetch_public_posts())
            except (ArticleSourceError, ValueError, TypeError, OSError, TimeoutError):
                evergreen = None
        if evergreen is not None:
            text, kind, title = evergreen["text"], "article", evergreen["title"]
            article_id, article_url = evergreen["id"], evergreen["url"]
            fallback_text = ordinary_text
        else:
            text, kind, title = ordinary_text, "everyday", None
    if kind == "everyday":
        validate_post(text, slot, config["max_characters"])
    elif not 30 <= len(text) <= 500:
        raise ValueError("Invalid article post length")
    draft = {
        "id": date + "-" + slot, "date_jst": date,
        "slot": slot, "account": "@survival40_jp",
        "kind": kind, "article_title": title,
        "article_id": article_id, "article_url": article_url,
        "text": text, "publish": False,
        "status": "prepared_for_separate_publish_gate",
        "generated_at_jst": now.isoformat(timespec="seconds"),
    }
    if fallback_text is not None:
        draft["fallback_everyday_text"] = fallback_text
    return draft


def main():
    now = dt.datetime.now(JST)
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    draft = choose_copy(
        now, config,
        os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    )
    if draft is None:
        print("SKIP: Not in a valid scheduled slot after launch date.")
        return
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(draft, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )
    print("PREPARED: " + draft["id"] + " (" + draft["kind"] + "); nothing published yet.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, KeyError) as exc:
        sys.exit("STOP: " + str(exc))
