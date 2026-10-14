"""Build sourced article-introduction drafts; no WordPress or Threads API calls.

This module only prepares a prompt. A caller must provide the actual article
title, HTTPS URL and article text. It does not fetch sites, invoke Gemini, or
publish. The normal 08:00/20:00 greeting workflow never uses this module.
"""
import json
from urllib.parse import urlsplit


def build_article_prompt(article, config):
    if not isinstance(article, dict):
        raise ValueError("Article source must be a dictionary")
    title = article.get("title")
    source_text = article.get("text")
    url = article.get("url")
    if not isinstance(title, str) or not 6 <= len(title.strip()) <= 150:
        raise ValueError("Article title required")
    if not isinstance(source_text, str) or not 80 <= len(source_text.strip()) <= 5000:
        raise ValueError("Real article text/excerpt (80-5000 chars) required")
    if not isinstance(url, str):
        raise ValueError("Article URL required")
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.hostname not in
            ("survival40.com", "www.survival40.com")
            or parsed.username or parsed.password or parsed.port
            or not parsed.path.strip("/") or parsed.query or parsed.fragment):
        raise ValueError("Only canonical Survival40 HTTPS article URLs are allowed")
    if config.get("mode") != "draft_only":
        raise ValueError("Article preview disabled unless draft_only")
    if "voice" not in config:
        raise ValueError("Voice rules missing")

    return json.dumps({
        "post_kind": "article_introduction",
        "publication": False,
        "article": {
            "title": title.strip(),
            "url": url,
            "excerpt": source_text.strip()
        },
        "voice": config["voice"],
        "guidelines": [
            "これは通常の雑談ではなく、Survival40の掲載記事を紹介するための下書き",
            "記事本文に含まれる事実だけを使い、読者が記事から分かることを正確に紹介",
            "抜粋から分からない効果や実体験、製品評価、統計、体験談は作らない",
            "抜粋を読んでも要点が分からない場合は、推測で補わず生成不可と判断する",
            "40代男性への説教、煽り、健康効果の断定、押し売りをしない",
            "丁寧で読みやすい文章。通常の雑談ほどくだける必要はない",
            "日本語80〜200字を目安に、記事の具体的な要点とリンクを含む",
            "JSONだけを返す。text (string) および supported (boolean) の2プロパティ。"
        ]
    }, ensure_ascii=False)
