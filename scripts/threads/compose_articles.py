#!/usr/bin/env python3
"""Generate ONE safe, review-only article promotion draft from published WordPress data."""
import datetime as dt
import json
import os
import pathlib
import re
import sys

from .articles import ArticleSourceError, fetch_public_posts, select_article
from .compose import JST, gemini_generate

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "threads-output" / "article-draft.json"


def validate_article_copy(body, article):
    if not isinstance(body, str):
        raise ValueError("Missing generated text")
    text = body.strip()
    if not 50 <= len(text) <= 270:
        raise ValueError("Copy must be 50-270 characters")
    if re.search(r"https?://|[#＃][\w-]+", text):
        raise ValueError("Unexpected URL or hashtag from model")
    forbidden = (
        "絶対に治る", "確実に治る", "100%治る", "必ず改善", "個人的に使ってみ",
        "私が実際に", "購入はこちら", "PR案件", "医師として", "専門家として",
    )
    if any(word in text for word in forbidden):
        raise ValueError("Unverifiable, impersonating or promotional claim")
    published = f"{text}\n\n{article['url']}"
    if len(published) > 500:
        raise ValueError("Threads text exceeds platform limit")
    return published


def make_prompt(article):
    return json.dumps({
        "persona": "栞さん、Survival40の案内役。読者は40代男性が中心。",
        "article_title": article["title"],
        "article_excerpt": article["excerpt"],
        "article_body_excerpt": article["body"],
        "task": [
            "この記事の内容だけを使って、有用なThreads紹介文を日本語で作る。",
            "単純な要約や宣伝ではなく、読者が実行できる小さな気づきを一つ伝える。",
            "見下す語りや過度の煽り、脅し、押し売りは避け、柔らかい語りかけにする。",
            "書かれていない医学的・科学的・効能の主張、統計、数字、実体験を追加しない。",
            "記事自体の記述が断定的であっても、医学的断言に強めない。",
            "URLは別処理で追加する。本文にURLやハッシュタグ、宣伝文句を入れない。",
            "50〜270文字、基本は90〜190文字。",
            '返答は {"text":"..."} のJSONのみ。'
        ]
    }, ensure_ascii=False)


def main():
    now = dt.datetime.now(dt.timezone.utc)
    article = select_article(fetch_public_posts(), now=now, hours=24)
    if not article:
        print("SKIP: no eligible recent public post; no Gemini call, no Threads post")
        return
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError("Gemini secret absent; no content generated")
    generated = gemini_generate(make_prompt(article), key)
    copy = validate_article_copy(generated, article)
    output = {
        "id": f"article-{article['id']}",
        "account": "@survival40_jp",
        "article_id": article["id"],
        "article_title": article["title"],
        "canonical_url": article["url"],
        "source_published_at_utc": article["published_at_utc"],
        "text": copy,
        "publish": False,
        "status": "review_draft_only",
        "generated_at_utc": now.isoformat(timespec="seconds"),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PASS: review-only Threads article draft for WordPress post " + article["id"])
    print("No Threads publication or user authorization attempted")


if __name__ == "__main__":
    try:
        main()
    except (ArticleSourceError, RuntimeError, ValueError, KeyError, TypeError) as exc:
        sys.exit(str(exc))
