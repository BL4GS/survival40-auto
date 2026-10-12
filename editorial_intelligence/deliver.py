#!/usr/bin/env python3
"""Deliver a validated research-only plan inbox payload; opt-in strictly OFF.

Sends no WordPress posts or article HTML. Uses only WordPress's authenticated
future editorial inbox route, never a generic WordPress posts API.
"""
import base64
import json
import os
import pathlib
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
INPUT = ROOT / "editorial-output" / "wp-plan-handoff.json"
ENDPOINT = "https://survival40.com/index.php?rest_route=%2Fsurvival40%2Fv1%2Feditorial-plans"
MAX_DOCUMENT_BYTES = 50_000


class DeliveryError(RuntimeError):
    pass


class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # WordPress Application Password must NEVER be forwarded to a redirect.
        raise DeliveryError("WordPress inbox redirected; delivery stopped")


def validate_handoff(document):
    if not isinstance(document, dict) or document.get("schema") != "survival40.wp_plan_handoff.v1":
        raise DeliveryError("Unexpected handoff schema")
    if (document.get("ready_to_publish") is not False
            or document.get("wp_posts_written") != 0
            or document.get("threads_posts_written") != 0):
        raise DeliveryError("Handoff is not explicitly nonpublishing")
    plans = document.get("plans")
    if not isinstance(plans, list) or len(plans) > 5:
        raise DeliveryError("Invalid plan list")
    for plan in plans:
        if (not isinstance(plan, dict)
                or plan.get("stage") != "needs_independent_source_research"
                or not isinstance(plan.get("topic_id"), str)
                or plan.get("safety", {}).get("publish_authorized") is not False
                or plan.get("safety", {}).get("no_affiliate_assigned") is not True
                or plan.get("plugin_planner_input", {}).get("amazon_query") != ""
                or plan.get("editorial", {}).get("verified_sources") != 0
                or plan.get("editorial", {}).get("sources_checked") is not False):
            raise DeliveryError("Plan is not a verified research-only handoff")
    payload = json.dumps(document, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(payload) > MAX_DOCUMENT_BYTES:
        raise DeliveryError("WordPress inbox payload too large")
    return payload, len(plans)


def deliver(document, username, app_password, opener=None):
    if not isinstance(username, str) or not username.strip() or not isinstance(app_password, str) or not app_password:
        raise DeliveryError("WordPress Application Password credentials absent")
    payload, count = validate_handoff(document)
    if not count:
        return {"accepted": 0, "duplicate": 0, "held": [], "wp_posts_created": 0}
    encoded = base64.b64encode((username + ":" + app_password).encode("utf-8")).decode("ascii")
    request = urllib.request.Request(
        ENDPOINT,
        data=payload,
        headers={
            "Authorization": "Basic " + encoded,
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json",
            "User-Agent": "Survival40-EditorialInbox/1.0",
        },
        method="POST",
    )
    transport = opener or urllib.request.build_opener(NoRedirects())
    try:
        with transport.open(request, timeout=25) as response:
            if response.status != 202:
                raise DeliveryError("Unexpected inbox response status")
            raw = response.read(65537)
            if len(raw) > 65536:
                raise DeliveryError("Oversized inbox response")
            result = json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as error:
        # Do not print response bodies, which might include authenticated context.
        raise DeliveryError(f"WordPress inbox refused delivery: HTTP {error.code}") from None
    except (urllib.error.URLError, TimeoutError, UnicodeDecodeError, ValueError):
        raise DeliveryError("WordPress inbox request failed or invalid response") from None
    if not isinstance(result, dict):
        raise DeliveryError("Unexpected inbox response")
    if (type(result.get("accepted")) is not int
            or type(result.get("duplicate")) is not int
            or not isinstance(result.get("held"), list)
            or result.get("wp_posts_created") != 0
            or result.get("ready_to_publish") is not False):
        raise DeliveryError("Inbox response does not confirm read-only plan acceptance")
    if result["accepted"] + result["duplicate"] + len(result["held"]) != count:
        raise DeliveryError("Inbox response does not account for every plan")
    return {
        "accepted": result["accepted"],
        "duplicate": result["duplicate"],
        "held": len(result["held"]),
        "wp_posts_created": 0,
    }


def main():
    if os.getenv("S40_WP_PLAN_DELIVERY_ENABLED") != "true":
        print("SKIP: WordPress editorial delivery disabled; no network request")
        return
    document = json.loads(INPUT.read_text(encoding="utf-8"))
    result = deliver(
        document,
        os.getenv("S40_WP_INBOX_USER", ""),
        os.getenv("S40_WP_INBOX_APP_PASSWORD", ""),
    )
    print(
        f"PASS: research-only plans delivered; accepted={result['accepted']}, "
        f"duplicate={result['duplicate']}, held={result['held']}, "
        "WP posts created=0"
    )


if __name__ == "__main__":
    try:
        main()
    except (DeliveryError, OSError, ValueError) as error:
        raise SystemExit("STOP: editorial plan inbox delivery failed: " + str(error))
