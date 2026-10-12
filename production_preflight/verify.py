"""Verify a live site's public articles against a pre-upgrade read-only baseline.

This does NOT access WordPress Admin or execute a plugin upgrade.
"""
import argparse
import json
from pathlib import Path

from production_preflight.baseline import snapshot, compare
from site_audit.audit import fetch_posts, public_get, ORIGIN


def verify(before, after):
    if before.get("schema") != "survival40.public_baseline.v1":
        raise ValueError("Unsupported baseline schema")
    if after.get("schema") != before["schema"]:
        raise ValueError("Unsupported current snapshot schema")
    if before.get("production_writes") != 0 or after.get("production_writes") != 0:
        raise ValueError("One snapshot does not claim read-only origin")
    for name, document in (("before", before), ("after", after)):
        articles = document.get("articles")
        if not isinstance(articles, list) or not articles:
            raise ValueError(name + " lacks article list")
        ids = [x.get("id") for x in articles]
        if len(set(ids)) != len(ids) or len(ids) != document.get("public_post_count"):
            raise ValueError(name + " contains inconsistent post IDs")
        if any(type(x.get("id")) is not int or
               len(x.get("content_sha256", "")) != 64 or
               not isinstance(x.get("title"), str) or
               not isinstance(x.get("url"), str) for x in articles):
            raise ValueError(name + " contains invalid record fields")
    result = compare(before, after)
    old = {x["id"]: x for x in before["articles"]}
    new = {x["id"]: x for x in after["articles"]}
    result["changed_titles"] = sorted(
        idx for idx in old.keys() & new.keys()
        if old[idx]["title"] != new[idx]["title"]
    )
    result["unchanged"] = not any(result.values())
    result["before_count"] = before["public_post_count"]
    result["after_count"] = after["public_post_count"]
    result["requires_wp_admin_verification"] = [
        "installed_version_and_activation",
        "draft_count_expected_16",
        "published_count_expected_23",
        "advertising_switches_unchanged",
        "shiori_frontend_appearance",
        "backup_restore_rehearsal",
    ]
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("postcheck-output/compare.json"))
    args = parser.parse_args()
    before = json.loads(args.baseline.read_text(encoding="utf-8"))
    posts, total = fetch_posts()
    after = snapshot(posts, total)
    for url in [ORIGIN + "/"] + [x["url"] for x in after["articles"][:2]]:
        status, _, _ = public_get(url, head_only=True)
        if status != 200:
            raise ValueError("Public page check failed: HTTP " + str(status))
    findings = verify(before, after)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(findings, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    if not findings["unchanged"]:
        raise SystemExit("STOP: public articles differ; review before calling update successful")
    print("PASS: public article IDs, titles, content hashes and URLs match prior baseline")
    print("Still unverified: nonpublic drafts, current plugin version, backup restore and ad settings")
    print("Read only, zero WordPress writes, zero release actions")


if __name__ == "__main__":
    main()
