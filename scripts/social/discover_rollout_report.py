"""Combine existing READ-ONLY WordPress OG audit with local asset inventory.

This is a triage report for a possible future isolated AIOSEO staging pilot,
not a Discover eligibility test or WordPress deployment. Never fetch, post or
change live WordPress/SNS data.
"""
import datetime as dt
import json
from pathlib import Path

SOURCE = Path("social-audit/og-status.json")
MANIFEST = Path("instagram/ready-posts.json")
OUTPUT = Path("social-audit/discover-rollout-review.json")
SITE = "https://www.survival40.com/"
RAW = "https://raw.githubusercontent.com/BL4GS/survival40-auto/main/"
MAX_ITEMS = 10


def summarize(observation, manifest):
    if not isinstance(observation, dict) or observation.get("read_only") is not True:
        raise ValueError("Expected read-only OG audit")
    if observation.get("site") != SITE[:-1] or not isinstance(observation.get("items"), list):
        raise ValueError("Unexpected OG source/site")
    if (not isinstance(manifest, dict) or manifest.get("brand") != "Survival40"
            or manifest.get("publishing_enabled") is not False
            or manifest.get("source") != "verified_Pinterest_static_feed"
            or not isinstance(manifest.get("items"), list)):
        raise ValueError("Not an original no-publish image manifest")
    assets = {}
    for asset in manifest["items"]:
        if not isinstance(asset, dict):
            raise ValueError("Invalid manifest item")
        ident = asset.get("article_id")
        if type(ident) is not int or ident in assets:
            raise ValueError("Duplicate/invalid original image identity")
        assets[ident] = asset
    seen, rows = set(), []
    checks = observation["items"]
    if not 1 <= len(checks) <= MAX_ITEMS:
        raise ValueError("Unexpected OG audit size")
    for row in checks:
        if not isinstance(row, dict):
            raise ValueError("Invalid OG audit row")
        ident = row.get("article_id")
        url = row.get("article_url")
        if (type(ident) is not int or ident in seen or
                not isinstance(url, str) or not url.startswith(SITE)):
            raise ValueError("Unverified or duplicate article observation")
        seen.add(ident)
        source = assets.get(ident)
        candidate = (source is not None
                     and source.get("article_url") == url
                     and source.get("status") == "assets_ready_not_published"
                     and source.get("social_og_image") ==
                     RAW + "assets/social/og/" + str(ident) + ".png"
                     and source.get("instagram_image") ==
                     RAW + "assets/instagram/auto/" + str(ident) + ".png")
        metadata = row.get("discover_metadata")
        state = row.get("status")
        if state == "UNAVAILABLE_UNVERIFIED":
            category = "LIVE_HTML_UNAVAILABLE_NEEDS_RECHECK"
        elif not isinstance(metadata, dict):
            category = "DISCOVER_HTML_HINTS_UNAVAILABLE"
        elif metadata.get("html_noindex_hint") is True:
            category = "HTML_NOINDEX_REQUIRES_REVIEW"
        elif metadata.get("html_large_image_preview_hint") in (
            "CONFLICTING_HTML_PREVIEW_DIRECTIVES_REVIEW",
            "LARGE_NOT_ALLOWED_BY_HTML_DIRECTIVE_REVIEW",
            "UNRECOGNIZED_HTML_PREVIEW_DIRECTIVE_REVIEW",
        ):
            category = "IMAGE_PREVIEW_DIRECTIVE_REQUIRES_REVIEW"
        elif state == "ORIGINAL_INSTAGRAM_CARD_WIDTH_UNVERIFIED" and candidate:
            category = "KNOWN_PORTRAIT_OG_OPTIONAL_STAGE_ONLY_REVIEW"
        elif state == "EXACT_ORIGINAL_SOCIAL_CARD" and candidate:
            category = "ORIGINAL_LANDSCAPE_OG_DECLARED_NOT_GOOGLE_VERIFIED"
        elif state in ("MISSING_OG_IMAGE", "MULTIPLE_OG_IMAGES_REVIEW",
                       "OTHER_IMAGE_REVIEW"):
            category = "EXISTING_OG_SELECTION_NEEDS_REVIEW"
        else:
            category = "NO_SAFE_AUTOMATIC_OG_CONCLUSION"
        rows.append({
            "article_id": ident,
            "article_url": url,
            "live_og_observation": state,
            "html_large_preview_hint": (
                metadata.get("html_large_image_preview_hint")
                if isinstance(metadata, dict) else None),
            "same_article_landscape_candidate_in_manifest": candidate,
            "candidate_url": source["social_og_image"] if candidate else None,
            "review_category": category,
            "recommendation": (
                "Consider one isolated reversible AIOSEO staging pilot only; "
                "preserve manual image selection and inspect actual image quality."
                if category == "KNOWN_PORTRAIT_OG_OPTIONAL_STAGE_ONLY_REVIEW"
                else "Read-only review; do not modify WordPress automatically."
            ),
        })
    counts = {}
    for row in rows:
        state = row["review_category"]
        counts[state] = counts.get(state, 0) + 1
    return {
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "read_only": True,
        "site": SITE[:-1],
        "sampled_articles": len(rows),
        "review_category_counts": counts,
        "wordpress_modified": False,
        "social_published": False,
        "actual_discover_impressions_verified": False,
        "remote_image_bytes_verified_by_this_join": False,
        "full_wordpress_article_inventory_covered": False,
        "note": (
            "Joins current sampled HTML OG observations to a local original-"
            "image manifest; it cannot certify actual pixel quality, remote "
            "image delivery, Google Discover placement or eligibility. "
            "A lack of an HTML max-image-preview tag is NOT proof of blocking. "
            "Staging and independently proven rollback required for any edit."
        ),
        "items": rows,
    }


def run(source=SOURCE, manifest=MANIFEST, output=OUTPUT):
    result = summarize(
        json.loads(Path(source).read_text(encoding="utf-8")),
        json.loads(Path(manifest).read_text(encoding="utf-8")),
    )
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print("DISCOVER AUDIT TRIAGE: " + str(result["sampled_articles"]) +
          " sampled articles, " +
          str(result["review_category_counts"]) +
          "; no WordPress/SNS writes")
    return result


if __name__ == "__main__":
    run()
