"""Single, hard-gated test publication. Staging only; never called by schedules.

Requires token_preflight module (PR #33), explicit user confirmation, owner-only
dispatch and a separate disabled-by-default GitHub repository variable. The
GitHub ledger reservation happens BEFORE every Meta POST; ambiguous attempts
stay reserved and require manual reconciliation.
"""
import datetime as dt
import hashlib
import os
import sys

from .ledger import GithubLedger, LedgerError
from .meta_api import MetaThreadsClient, ThreadsApiError

TEST_KEY = "test-20261013-v1"
TEST_TEXT = (
    "Survival40のThreads投稿テストです。"
    "現在、投稿システムの連携を確認しています。"
    "通常の投稿は準備中です。"
)
CONFIRM_PHRASE = "I_APPROVE_ONE_TEST_POST"
REPOSITORY = "BL4GS/survival40-auto"
LEDGER_BRANCH = "state/threads-ledger"


def assert_approval(env):
    if (env.get("THREADS_TEST_PUBLISH_ENABLED") != "true"
            or env.get("THREADS_TEST_ACK") != CONFIRM_PHRASE
            or env.get("GITHUB_ACTOR") != "BL4GS"
            or env.get("GITHUB_REF") != "refs/heads/main"
            or env.get("GITHUB_REPOSITORY") != REPOSITORY
            or env.get("GITHUB_EVENT_NAME") != "workflow_dispatch"):
        raise ValueError("Live-test approval gate is closed; no post")


def preview():
    print("PREVIEW ONLY - no Threads API call")
    print("Account: @survival40_jp")
    print("One-time publication key: " + TEST_KEY)
    print("Text: " + TEST_TEXT)
    print("Live publication requires another explicit review, secrets, a ledger branch,")
    print("owner-only manual dispatch, the exact approval phrase and a GitHub enable variable.")


def live_publish(env):
    assert_approval(env)
    token = env.get("THREADS_ACCESS_TOKEN", "").strip()
    account = env.get("THREADS_USER_ID", "").strip()
    github_token = env.get("GITHUB_TOKEN", "").strip()
    if not token or not account or not github_token:
        raise ValueError("Required tokens absent; no post")

    # Always verify current profile, scopes and expiration BEFORE a ledger write.
    from .token_preflight import safe_get, validate_profile, validate_debug_response
    import time

    profile = safe_get("/me", token, {"fields": "id,username"})
    validate_profile(profile, account)
    debug = safe_get("/debug_token", token, {"input_token": token})
    validate_debug_response(debug, account, int(time.time()))

    digest = hashlib.sha256(TEST_TEXT.encode("utf-8")).hexdigest()
    ledger = GithubLedger(REPOSITORY, LEDGER_BRANCH, github_token)
    if not ledger.reserve(TEST_KEY, account, digest):
        raise LedgerError("Test already reserved; manual reconciliation required, no retry")

    # There is NO automatic retry after reservation, container creation or publish.
    client = MetaThreadsClient(token)
    client.verify_account(account)
    container = client.create_text_container(TEST_TEXT)
    post_id = client.publish_container(container)
    ledger.mark_published(TEST_KEY, post_id)
    print("PASS: One approved Threads test publication was recorded.")
    print("Threads post ID: " + post_id)
    print("No recurring publication enabled.")


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("preview", "live"):
        raise ValueError("Choose preview or live")
    if sys.argv[1] == "preview":
        preview()
        return
    live_publish(os.environ)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, ThreadsApiError, LedgerError) as exc:
        sys.exit("STOP: " + str(exc))
