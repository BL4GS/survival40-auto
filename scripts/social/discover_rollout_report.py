"""Combine existing READ-ONLY WordPress OG audit with local asset inventory.

This is a triage report for a possible future isolated AIOSEO staging pilot,
not a Discover eligibility test or WordPress deployment. Never fetch, post or
change live WordPress/SNS data.
"""
import datetime as dt
import json
import os
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
        elif metadata.get("article_schema_image_source_hint") == "POSSIBLE_A8_AFFILIATE_IMAGE_REVIEW":
            category = "ARTICLE_SCHEMA_AFFILIATE_IMAGE_REVIEW"
        elif metadata.get("article_schema_image_source_hint") == "GRAVATAR_AVATAR_IMAGE_REVIEW":
            category = "ARTICLE_SCHEMA_AVATAR_IMAGE_REVIEW"
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



REVIEW_LABELS = {
    "LIVE_HTML_UNAVAILABLE_NEEDS_RECHECK": "公開HTMLの取得不可（再確認）",
    "DISCOVER_HTML_HINTS_UNAVAILABLE": "画像プレビュー情報が不明",
    "HTML_NOINDEX_REQUIRES_REVIEW": "HTMLのnoindex指定を確認",
    "IMAGE_PREVIEW_DIRECTIVE_REQUIRES_REVIEW": "画像プレビュー制限を確認",
    "KNOWN_PORTRAIT_OG_OPTIONAL_STAGE_ONLY_REVIEW": "栞さん縦長OG画像・横長候補あり",
    "ORIGINAL_LANDSCAPE_OG_DECLARED_NOT_GOOGLE_VERIFIED": "横長OG画像が指定済み・Google表示未確認",
    "ARTICLE_SCHEMA_AFFILIATE_IMAGE_REVIEW": "記事の構造化データにA8画像候補（要確認）",
    "ARTICLE_SCHEMA_AVATAR_IMAGE_REVIEW": "記事の構造化データにアバター画像候補（要確認）",
    "EXISTING_OG_SELECTION_NEEDS_REVIEW": "OG画像が不足／別画像／重複",
    "NO_SAFE_AUTOMATIC_OG_CONCLUSION": "自動判定不可",
}


def render_review_summary(result):
    """GitHub Actions-readable audit only, never a repair authorization."""
    if result.get("read_only") is not True or result.get("wordpress_modified") is not False:
        raise ValueError("Refusing to summarize a mutated site")
    lines = [
        "### Survival40 Discover画像の公開HTML監査",
        "",
        "この表は実サイトの一部記事を対象にした**読み取り専用**の分類です。",
        "Google Discover掲載・画像品質・実際の流入は確認していません。",
        "",
        "| 投稿ID | 監査による分類 |",
        "|---:|---|",
    ]
    for row in result["items"]:
        ident, category = row["article_id"], row["review_category"]
        if (type(ident) is not int or ident < 1 or category not in REVIEW_LABELS):
            raise ValueError("Untrusted report row")
        lines.append(f"| {ident} | {REVIEW_LABELS[category]} |")
    lines += [
        "",
        f"確認した記事数：{result['sampled_articles']}件（サイト全体ではありません）",
        "",
        "OG画像が不足していてもGoogle Discoverに掲載されないと断定はできません。",
        "本番WordPressでの一括変更は行わず、復元可能な検証環境での確認を優先してください。",
        "",
    ]
    return "\n".join(lines)



def run(source=SOURCE, manifest=MANIFEST, output=OUTPUT):
    result = summarize(
        json.loads(Path(source).read_text(encoding="utf-8")),
        json.loads(Path(manifest).read_text(encoding="utf-8")),
    )
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    # Only a GitHub Actions-provided path is written; otherwise return JSON only.
    summary = (os.environ.get("GITHUB_STEP_SUMMARY")
               if os.environ.get("SURVIVAL40_REAL_OG_AUDIT") == "1" else None)
    if summary:
        with open(summary, "a", encoding="utf-8") as file:
            file.write(render_review_summary(result))
    print("DISCOVER AUDIT TRIAGE: " + str(result["sampled_articles"]) +
          " sampled articles, " +
          str(result["review_category_counts"]) +
          "; no WordPress/SNS writes")
    return result


if __name__ == "__main__":
    run()
