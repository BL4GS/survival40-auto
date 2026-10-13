"""Guarded scheduled Threads publication: first reserve a durable slot, then post once.

Only callable by the scheduled GitHub Actions workflow on main, with valid account
and token preflight. The draft workflow and all previews remain nonpublishing.
No retries after any ambiguous Meta/GitHub state.
"""
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import sys

from .compose import CONFIG, JST, OUTPUT, choose_slot, validate_post
from .ledger import GithubLedger, LedgerError
from .meta_api import MetaThreadsClient, ThreadsApiError
from .prepare_schedule import ARTICLE_CALENDAR, FIRST_TEXT, START_DATE


EXPECTED_REPO = "BL4GS/survival40-auto"
LEDGER_BRANCH = "state/threads-ledger"


def verify_draft(draft, now, config):
    slot = choose_slot(now)
    if now.date() < START_DATE or slot is None:
        raise ValueError("Not in an authorized scheduled time")
    if config.get("mode") != "draft_only":
        raise ValueError("Unexpected editorial configuration")
    if (not isinstance(draft, dict)
            or draft.get("date_jst") != now.date().isoformat()
            or draft.get("slot") != slot
            or draft.get("id") != now.date().isoformat() + "-" + slot
            or draft.get("account") != "@survival40_jp"
            or draft.get("publish") is not False
            or draft.get("status") != "prepared_for_separate_publish_gate"):
        raise ValueError("Unexpected draft metadata")
    try:
        written = dt.datetime.fromisoformat(draft["generated_at_jst"])
    except (TypeError, ValueError, KeyError):
        raise ValueError("Missing or invalid draft timestamp") from None
    if (written.tzinfo is None or written.utcoffset() != dt.timedelta(hours=9)
            or not 0 <= (now - written).total_seconds() <= 600):
        raise ValueError("Draft is stale or from another timezone")
    text = draft.get("text")
    kind = draft.get("kind")
    if not isinstance(text, str) or not 18 <= len(text) <= 500:
        raise ValueError("Invalid draft text")
    if now.date().isoformat() == "2026-10-13" and slot == "evening":
        if kind != "everyday" or text != FIRST_TEXT:
            raise ValueError("First post is not the approved Shiori text")
    elif slot == "evening" and now.date().isoformat() in ARTICLE_CALENDAR:
        article = ARTICLE_CALENDAR[now.date().isoformat()]
        url = "https://www.survival40.com/" + article["slug"] + "/"
        expected = "【PR】" + article["intro"] + "\n\n" + url
        if (kind != "article" or text != expected
                or draft.get("article_title") != article["title"]):
            raise ValueError("Article text/URL diverged from verified calendar")
    else:
        if kind != "everyday" or draft.get("article_title") is not None:
            raise ValueError("Unexpected article outside approved calendar")
        validate_post(text, slot, config["max_characters"])
    return text


def assert_scheduled_env(env):
    if (env.get("GITHUB_EVENT_NAME") != "schedule"
            or env.get("GITHUB_REPOSITORY") != EXPECTED_REPO
            or env.get("GITHUB_REF") != "refs/heads/main"):
        raise ValueError("Not a scheduled main-branch run; nothing published")
    if not env.get("THREADS_ACCESS_TOKEN") or not env.get("THREADS_USER_ID"):
        raise ValueError("Threads credentials missing; nothing published")
    if not re.fullmatch(r"[0-9]{1,30}", env["THREADS_USER_ID"]):
        raise ValueError("Threads user ID invalid")
    if not env.get("GITHUB_TOKEN"):
        raise ValueError("GitHub ledger token missing; nothing published")


def publish(draft, now, config, env):
    assert_scheduled_env(env)
    text = verify_draft(draft, now, config)
    token = env["THREADS_ACCESS_TOKEN"].strip()
    account = env["THREADS_USER_ID"].strip()

    from .token_preflight import safe_get, validate_debug_response, validate_profile
    profile = safe_get("/me", token, {"fields": "id,username"})
    validate_profile(profile, account)
    debug = safe_get("/debug_token", token, {"input_token": token})
    validate_debug_response(
        debug, account, int(now.astimezone(dt.timezone.utc).timestamp())
    )
    client = MetaThreadsClient(token)
    client.verify_account(account)
    ledger = GithubLedger(EXPECTED_REPO, LEDGER_BRANCH, env["GITHUB_TOKEN"])
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    key = now.date().isoformat() + "-" + draft["slot"]
    # Persist reservation BEFORE every Meta POST; never retry an uncertain attempt.
    if not ledger.reserve(key, account, digest):
        print("SKIP: Slot already reserved; no duplicate post created.")
        return None
    container_id = client.create_text_container(text)
    post_id = client.publish_container(container_id)
    ledger.mark_published(key, post_id)
    print("PUBLISHED: " + key + "; Threads post ID: " + post_id)
    return post_id


def main():
    now = dt.datetime.now(JST)
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    # No access token is ever read by the code which generated the draft.
    if not OUTPUT.is_file():
        raise ValueError("No validated draft was generated; nothing published")
    draft = json.loads(OUTPUT.read_text(encoding="utf-8"))
    publish(draft, now, config, os.environ)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, OSError, KeyError,
            ThreadsApiError, LedgerError, json.JSONDecodeError) as exc:
        sys.exit("STOP: " + str(exc) + "; no automatic retry.")
