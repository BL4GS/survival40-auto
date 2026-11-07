#!/usr/bin/env python3
"""Read-only authenticated WordPress draft preflight.

This is deliberately NOT an article updater. It verifies the identity/status
and snapshots a SHA-256 of the raw draft for a later compare-and-swap design.
Never serialize draft HTML, credentials, headers or response bodies to output.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.request

ORIGIN = "https://www.survival40.com"
MAX_RESPONSE_BYTES = 2_000_000
DEFAULT_POST_ID = 620
DEFAULT_SLUG = "40s-male-razor-burn-shaving-care"


class PreflightError(RuntimeError):
    pass


class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise PreflightError("Authenticated WordPress GET redirected; stopping")


def validate_identity(post_id, slug):
    if type(post_id) is not int or not 1 <= post_id <= 999_999:
        raise PreflightError("Invalid WordPress post ID")
    if not isinstance(slug, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        raise PreflightError("Invalid expected post slug")


def draft_snapshot(document, post_id, expected_slug):
    validate_identity(post_id, expected_slug)
    if not isinstance(document, dict):
        raise PreflightError("Unexpected WordPress response type")
    if type(document.get("id")) is not int or document["id"] != post_id:
        raise PreflightError("WordPress post identity mismatch")
    if document.get("slug") != expected_slug:
        raise PreflightError("WordPress slug mismatch")
    if document.get("status") != "draft":
        raise PreflightError("Post is not a draft; refusing preflight")
    content = document.get("content")
    if not isinstance(content, dict) or not isinstance(content.get("raw"), str):
        raise PreflightError("Raw draft missing; edit-context authorization unverified")
    if not content["raw"].strip():
        raise PreflightError("Draft body is empty")
    categories = document.get("categories")
    if not isinstance(categories, list) or not all(type(x) is int and x > 0 for x in categories):
        raise PreflightError("Categories missing or malformed")
    return {
        "schema": "survival40.wp_draft_preflight.v1",
        "post_id": post_id,
        "slug": expected_slug,
        "status": "draft",
        "categories": categories,
        "raw_content_sha256": hashlib.sha256(content["raw"].encode("utf-8")).hexdigest(),
        "production_reads": 1,
        "production_writes": 0,
        "publication_authorized": False,
        "note": "Read-only identity fingerprint. No atomic write endpoint is enabled.",
    }


def inspect(post_id, expected_slug, username, app_password, opener=None):
    validate_identity(post_id, expected_slug)
    if not isinstance(username, str) or not username.strip() or not isinstance(app_password, str) or not app_password:
        raise PreflightError("WordPress read-only preflight credentials missing")
    endpoint = ORIGIN + (
        f"/index.php?rest_route=%2Fwp%2Fv2%2Fposts%2F{post_id}&context=edit"
    )
    basic = base64.b64encode((username + ":" + app_password).encode("utf-8")).decode("ascii")
    req = urllib.request.Request(
        endpoint,
        headers={
            "Authorization": "Basic " + basic,
            "Accept": "application/json",
            "User-Agent": "Survival40-ReadOnlyDraftPreflight/1.0",
        },
        method="GET",
    )
    transport = opener or urllib.request.build_opener(NoRedirects())
    try:
        with transport.open(req, timeout=20) as response:
            if response.status != 200:
                raise PreflightError("WordPress did not return HTTP 200")
            data = response.read(MAX_RESPONSE_BYTES + 1)
            if len(data) > MAX_RESPONSE_BYTES:
                raise PreflightError("WordPress response exceeded size limit")
            document = json.loads(data.decode("utf-8"))
    except urllib.error.HTTPError as error:
        # Never echo response body: it may include details from a private post.
        raise PreflightError(f"WordPress read-only preflight rejected: HTTP {error.code}") from None
    except (urllib.error.URLError, TimeoutError, ValueError, UnicodeDecodeError):
        raise PreflightError("WordPress read-only preflight failed") from None
    return draft_snapshot(document, post_id, expected_slug)


def main():
    parser = argparse.ArgumentParser(description="Read-only WordPress draft identity preflight")
    parser.add_argument("--post-id", type=int, default=DEFAULT_POST_ID)
    parser.add_argument("--expected-slug", default=DEFAULT_SLUG)
    parser.add_argument("--output", default="draft-preflight-output/post-620.json")
    args = parser.parse_args()
    report = inspect(
        args.post_id,
        args.expected_slug,
        os.getenv("S40_WP_INBOX_USER", ""),
        os.getenv("S40_WP_INBOX_APP_PASSWORD", ""),
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: authenticated read-only WordPress draft preflight id={report['post_id']}; writes=0")


if __name__ == "__main__":
    try:
        main()
    except (PreflightError, OSError) as error:
        raise SystemExit("STOP: " + str(error))
