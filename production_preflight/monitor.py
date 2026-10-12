"""Bounded post-release watch: public HTTP checks ONLY, never WP admin or writes.

Run through GitHub Actions with an archived, verified pre-update article baseline.
Passing checks cannot prove the installed plugin version, draft safety, or ConoHa
DB restore integrity; these require separate authenticated checks.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from production_preflight.baseline import snapshot
from production_preflight.verify import verify
from site_audit.audit import ORIGIN, fetch_posts, public_get, AuditSourceError
from site_audit.discovery import html_paths, public_path

CANONICAL = "https://www.survival40.com"
NAVIGATOR = ("normal", "explain", "caution", "summary")
REQUIRED_UI = (
    'class="s40-home-guide"',
    'class="s40-home-card',
    'class="s40-home-more-reading"',
)
DEFAULT_REPORT = Path("postrelease-watch-output/result.json")


class WatchFailure(RuntimeError):
    pass


def check_homepage(html, article_urls):
    """Treat only known published post URLs as valid discovery links."""
    if not isinstance(html, str):
        raise WatchFailure("Homepage response is not HTML text")
    missing_ui = [marker for marker in REQUIRED_UI if marker not in html]
    if missing_ui:
        raise WatchFailure("Missing existing homepage UI: " + ", ".join(missing_ui))
    expected = {public_path(url) for url in article_urls}
    if None in expected or "/" in expected:
        raise WatchFailure("Invalid canonical published permalink")
    linked = html_paths(html, CANONICAL + "/")
    missing = sorted(expected - linked)
    if missing:
        raise WatchFailure("Homepage lost published post links: " + ", ".join(missing))
    return {"linked_published": len(expected), "expected_published": len(expected),
            "ui_markers_present": len(REQUIRED_UI)}


def check_probe(before, posts, homepage_html, page_statuses, navigator_statuses):
    """Pure function; test with mocks; do not touch live data here."""
    if before.get("schema") != "survival40.public_baseline.v1":
        raise WatchFailure("Unsupported archived public baseline")
    after = snapshot(posts, len(posts))
    compared = verify(before, after)
    if not compared["unchanged"]:
        raise WatchFailure("Published article identifiers/titles/URLs/bodies changed")
    if compared["before_count"] != 23 or compared["after_count"] != 23:
        raise WatchFailure("Expected published article count 23")
    home = check_homepage(homepage_html, [p["url"] for p in after["articles"]])
    if any(value != 200 for value in page_statuses.values()):
        raise WatchFailure("Public page returned non-200")
    if set(navigator_statuses) != set(NAVIGATOR):
        raise WatchFailure("Four navigator images were not inspected")
    if any(value != 200 for value in navigator_statuses.values()):
        raise WatchFailure("Navigator image unavailable")
    return {
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "public_articles_unchanged": 23,
        "public_page_count": len(page_statuses),
        "navigator_images_available": len(NAVIGATOR),
        "homepage": home,
        "no_production_writes": True,
        "requires_separate_verification": [
            "actual_installed_plugin_version",
            "16_private_drafts",
            "global_automation_and_advertising_controls",
            "restored_ConoHa_DB_tables_and_rows",
            "visual_mobile_layout",
            "continuous_monitoring_after_this_run",
        ],
    }


def read_probe(before):
    # Bounded: 1 public REST snapshot, 1 home GET, 2 public article reads,
    # 4 navigator existence GETs of at most 1 KiB each. No writes/credentials.
    posts, _ = fetch_posts()
    checks = {}
    home_status, _, homepage = public_get(CANONICAL + "/", preview=True)
    checks["homepage"] = home_status
    for post in (posts[0], posts[-1]) if posts else ():
        url = post.get("link")
        if not isinstance(url, str) or not url.startswith(CANONICAL + "/"):
            raise WatchFailure("Unexpected published post URL")
        status, _, _ = public_get(url, head_only=True)
        checks[url] = status
    images = {}
    for name in NAVIGATOR:
        url = CANONICAL + "/wp-content/plugins/survival40-auto/assets/navigator/" + name + ".webp"
        code, _, _ = public_get(url, head_only=True)
        images[name] = code
    return check_probe(before, posts, homepage.decode("utf-8", errors="replace"),
                       checks, images)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--baseline", required=True, type=Path)
    p.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = p.parse_args()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    try:
        before = json.loads(args.baseline.read_text(encoding="utf-8"))
        result = {"status": "pass", **read_probe(before)}
    except (ValueError, KeyError, IndexError, WatchFailure, AuditSourceError) as exc:
        result = {"status": "fail", "reason": str(exc)[:500],
                  "checked_utc": datetime.now(timezone.utc).isoformat(),
                  "no_production_writes": True}
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    if result["status"] != "pass":
        raise SystemExit("STOP: public website watch failed: " + result["reason"])
    print("PASS: 23 article fingerprints, homepage links/UI, public pages, four Shiori images")
    print("UNKNOWN: active plugin version, private drafts, ad controls, ConoHa restored DB data")
    print("Read-only: no WordPress updates, ZIP distribution, or automated rollback")


if __name__ == "__main__":
    main()
