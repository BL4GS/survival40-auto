"""An additional 22:00 JST scheduled Threads post for today's VERIFIED new article.

Independent of the 08:00 / 20:00 Shiori posts. Public WordPress data only.
Fail closed: no public article, stale article, bad source, credentials or ledger ->
no Threads publication. Never retry an ambiguous Meta transaction.
"""
import datetime as dt
import json
import os
import pathlib
import re
import sys

from .article_feed import (ArticleSourceError, plain, require_article_url,
                           fetch_public_posts, build_article_text)
from .compose import JST
from .ledger import GithubLedger, LedgerError
from .meta_api import MetaThreadsClient, ThreadsApiError
from .scheduled_publisher import assert_scheduled_env
from .token_preflight import (TokenPreflightError, safe_get,
                              validate_debug_response, validate_profile)

START = dt.date(2026, 10, 19)
OUTPUT = pathlib.Path("threads-output/late-article.json")
EXPECTED_ACCOUNT = "@survival40_jp"
REPO = "BL4GS/survival40-auto"
LEDGER = "state/threads-ledger"


def allowed_clock(now):
    if now.tzinfo is None or now.utcoffset() != dt.timedelta(hours=9):
        return False
    return now.date() >= START and now.hour == 22


def latest_evening_article(posts, now):
    """Require a published post from TODAY at or after 20:45 JST.

    A previous day's article must never be recycled as today's news.
    """
    if not allowed_clock(now):
        raise ValueError("Outside authorized 22:00 JST article slot")
    if not isinstance(posts, list):
        raise ArticleSourceError("Public articles response invalid")
    cutoff = dt.datetime.combine(now.date(), dt.time(20, 45), tzinfo=JST)
    found = []
    for item in posts:
        if not isinstance(item, dict) or item.get("status") != "publish":
            continue
        try:
            ident = item.get("id")
            if type(ident) is not int or ident < 1:
                continue
            url = require_article_url(item.get("link"))
            raw = item.get("date_gmt")
            if not isinstance(raw, str):
                continue
            date = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if date.tzinfo is None:
                date = date.replace(tzinfo=dt.timezone.utc)
            published = date.astimezone(JST)
            if not cutoff <= published <= now:
                continue
            title = plain(item.get("title", {}).get("rendered"))
            body = plain(item.get("content", {}).get("rendered"))
            if not 8 <= len(title) <= 150 or len(body) < 120:
                continue
            found.append({"id": ident, "title": title, "url": url, "published": published})
        except (ValueError, TypeError, KeyError, AttributeError, ArticleSourceError):
            continue
    return max(found, key=lambda v: (v["published"], v["id"])) if found else None


def prepare(now, public_posts):
    source = latest_evening_article(public_posts, now)
    if source is None:
        return None
    text = build_article_text(source)
    return {
        "id": now.date().isoformat() + "-late-article",
        "article_id": source["id"],
        "article_title": source["title"],
        "article_url": source["url"],
        "source_published_jst": source["published"].isoformat(timespec="seconds"),
        "date_jst": now.date().isoformat(),
        "slot": "late-article",
        "account": EXPECTED_ACCOUNT,
        "kind": "article",
        "text": text,
        "generated_at_jst": now.isoformat(timespec="seconds"),
        "publish": False,
        "status": "prepared_for_separate_publish_gate",
    }


def validate_prepared(draft, now):
    if not allowed_clock(now):
        raise ValueError("Outside authorized 22:00 JST article slot")
    if not isinstance(draft, dict):
        raise ValueError("Missing draft")
    if (draft.get("id") != now.date().isoformat() + "-late-article"
            or draft.get("date_jst") != now.date().isoformat()
            or draft.get("slot") != "late-article"
            or draft.get("account") != EXPECTED_ACCOUNT
            or draft.get("kind") != "article"
            or draft.get("publish") is not False
            or draft.get("status") != "prepared_for_separate_publish_gate"):
        raise ValueError("Draft metadata mismatch")
    identity = draft.get("article_id")
    title = draft.get("article_title")
    url = draft.get("article_url")
    if (type(identity) is not int or identity <= 0
            or not isinstance(title, str) or not 8 <= len(title) <= 150
            or not isinstance(url, str) or require_article_url(url) != url):
        raise ValueError("Unverified article identity, title or URL")
    if draft.get("text") != build_article_text({"title": title, "url": url}):
        raise ValueError("Article introduction diverged from verified metadata")
    for timestamp in ("generated_at_jst", "source_published_jst"):
        try:
            value = dt.datetime.fromisoformat(draft[timestamp])
        except (KeyError, TypeError, ValueError):
            raise ValueError("Missing timestamp: " + timestamp) from None
        if value.tzinfo is None or value.utcoffset() != dt.timedelta(hours=9):
            raise ValueError("Invalid timestamp timezone")
        if timestamp == "generated_at_jst":
            if not 0 <= (now - value).total_seconds() <= 600:
                raise ValueError("Prepared text is stale")
        else:
            start = dt.datetime.combine(now.date(), dt.time(20, 45), tzinfo=JST)
            if not start <= value <= now:
                raise ValueError("Article was not published this evening")
    return draft["text"]


def publish_once(draft, now, env):
    assert_scheduled_env(env)
    text = validate_prepared(draft, now)
    token = env["THREADS_ACCESS_TOKEN"].strip()
    expected_id = env["THREADS_USER_ID"].strip()
    if not re.fullmatch(r"[0-9]{1,30}", expected_id):
        raise ValueError("Invalid Meta account")
    validate_profile(safe_get("/me", token, {"fields": "id,username"}), expected_id)
    validate_debug_response(safe_get("/debug_token", token, {"input_token": token}),
                            expected_id, int(now.astimezone(dt.timezone.utc).timestamp()))
    client = MetaThreadsClient(token)
    client.verify_account(expected_id)
    ledger = GithubLedger(REPO, LEDGER, env["GITHUB_TOKEN"])
    import hashlib
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    slot = draft["id"]
    # Reserve both slot and article identity BEFORE a Meta POST. Previously
    # introduced article IDs cannot be used again, even on another date.
    if not ledger.reserve(slot, expected_id, digest):
        print("SKIP: Late article slot already reserved.")
        return None
    if not ledger.reserve("article-" + str(draft["article_id"]), expected_id, digest):
        print("SKIP: Same published article was already introduced.")
        return None
    # Same single-request TEXT path as the regular 4-slot publisher.
    # Existing durable article + slot reservations remain unchanged.
    post_id = client.publish_text(text)
    ledger.mark_published(slot, post_id)
    ledger.mark_published("article-" + str(draft["article_id"]), post_id)
    print("PUBLISHED: One additional Threads article introduction for " + slot)
    return post_id


def main():
    now = dt.datetime.now(JST)
    if not allowed_clock(now):
        print("SKIP: First late-article slot is 2026-10-19 at 22:00 JST.")
        return
    mode = sys.argv[1] if len(sys.argv) == 2 else ""
    if mode == "prepare":
        article = prepare(now, fetch_public_posts())
        if not article:
            print("SKIP: No newly published eligible 21:00 article today.")
            return
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(json.dumps(article, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")
        print("PREPARED: " + article["id"] + ", article " + str(article["article_id"]))
    elif mode == "publish":
        if not OUTPUT.exists():
            print("SKIP: No verified newly published article to introduce.")
            return
        publish_once(json.loads(OUTPUT.read_text(encoding="utf-8")), now, os.environ)
    else:
        raise ValueError("Use prepare or publish mode")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, OSError, KeyError, TypeError,
            ArticleSourceError, TokenPreflightError, ThreadsApiError,
            LedgerError, json.JSONDecodeError) as exc:
        sys.exit("STOP: " + str(exc) + "; no automatic retry.")
