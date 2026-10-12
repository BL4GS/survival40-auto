"""Read-only public baseline for comparing WordPress articles before/after updates."""
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

from site_audit.audit import fetch_posts, public_get, ORIGIN, plain, safe_post_url

OUTPUT = Path("preflight-output/baseline.json")


def snapshot(posts, observed_total=None):
    if not isinstance(posts, list) or not posts:
        raise ValueError("No published articles, cannot establish a baseline")
    rows = []
    for p in posts:
        if p.get("status") != "publish" or type(p.get("id")) is not int:
            raise ValueError("Unexpected public article")
        url = safe_post_url(p.get("link"))
        html = p.get("content", {}).get("rendered")
        title = plain(p.get("title", {}).get("rendered", ""))
        if not isinstance(html, str) or not title:
            raise ValueError("Missing public article content")
        rows.append({
            "id": p["id"], "url": url, "title": title,
            "content_sha256": hashlib.sha256(html.encode("utf-8")).hexdigest(),
        })
    if len({x["id"] for x in rows}) != len(rows):
        raise ValueError("Duplicate public article ID")
    return {
        "schema": "survival40.public_baseline.v1",
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "public_post_count": len(rows),
        "api_total": observed_total,
        "articles": rows,
        "requires_admin_verification": [
            "actual_installed_plugin_version_and_active_state",
            "draft_and_scheduled_posts",
            "global_advertising_switches",
            "backup_restore_proof",
        ],
        "production_writes": 0,
    }


def compare(before, after):
    old = {x["id"]: x for x in before["articles"]}
    new = {x["id"]: x for x in after["articles"]}
    return {
        "removed": sorted(old.keys() - new.keys()),
        "added": sorted(new.keys() - old.keys()),
        "changed_content": sorted(
            i for i in old.keys() & new.keys()
            if old[i]["content_sha256"] != new[i]["content_sha256"]),
        "changed_urls": sorted(
            i for i in old.keys() & new.keys() if old[i]["url"] != new[i]["url"]),
    }


def main():
    posts, total = fetch_posts()
    data = snapshot(posts, total)
    page_urls = [ORIGIN + "/"] + [p["url"] for p in data["articles"][:2]]
    checks = []
    for url in page_urls:
        status, _, _ = public_get(url, head_only=True)
        checks.append({"url": url, "status": status})
        if status != 200:
            raise ValueError("Public page response not HTTP 200")
    data["page_checks"] = checks
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PASS: public baseline, articles:", data["public_post_count"])
    print("UNKNOWN: installed plugin, drafts, verified backup restore")
    print("Read-only; no production changes")


if __name__ == "__main__":
    main()
