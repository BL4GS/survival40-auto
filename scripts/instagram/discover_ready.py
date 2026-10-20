"""Prove offline readiness of original Shiori article images for later Discover work.

Uses only the Pinterest image-backed RSS, its nonpublishing Instagram asset manifest,
and locally generated original PNGs. No WordPress/SNS requests or updates. A
1200x630 valid image is NOT proof of Google Discover eligibility or exposure.
"""
import datetime as dt
import hashlib
import json
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from scripts.instagram import build_assets as cards

READY = Path("instagram/ready-posts.json")
FEED = Path("pinterest/survival40-pins.xml")
PINS = Path("assets/pinterest/auto")
IG = Path("assets/instagram/auto")
OG = Path("assets/social/og")
REPORT = Path("social-audit/discover-image-readiness.json")
RAW = "https://raw.githubusercontent.com/BL4GS/survival40-auto/main/"
MAX_ASSET_BYTES = 8_000_000
MAX_ARTICLES = 90


def validate_image(path, expected):
    """Decode a real PNG and confirm dimensions; not just declared HTML width."""
    path = Path(path)
    if (not path.is_file() or not 16 <= path.stat().st_size <= MAX_ASSET_BYTES
            or path.is_symlink()):
        raise ValueError("Missing, symlinked or oversized original article image")
    try:
        with Image.open(path) as original:
            if original.format != "PNG" or original.size != expected:
                raise ValueError("Original image format or dimensions mismatch")
            original.verify()
        with Image.open(path) as image:
            image.load()
            if image.mode not in ("RGB", "RGBA"):
                raise ValueError("Unexpected image color mode")
            if image.size != expected:
                raise ValueError("Decoded image dimensions mismatch")
    except (OSError, UnidentifiedImageError, SyntaxError) as exc:
        raise ValueError("Original PNG could not be decoded") from None
    return {"width": expected[0], "height": expected[1],
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def verify(feed=FEED, pins=PINS, ready=READY, ig=IG, og=OG, report=REPORT,
           trusted_posts=None):
    """Fail closed on missing/mismatched source, manifest or rendered PNG."""
    # Actual production path invokes the existing verified Pinterest RSS/pin
    # validation. Test injection is for isolated synthetic fixtures only.
    posts = (cards.items_from_pinterest_feed(feed, pins)
             if trusted_posts is None else trusted_posts)
    if (not isinstance(posts, list) or not posts or len(posts) > MAX_ARTICLES
            or any(not isinstance(p, dict) for p in posts)):
        raise ValueError("Unverified Pinterest article inventory")
    try:
        manifest = json.loads(Path(ready).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError("Unreadable Instagram original-art manifest") from None
    if (not isinstance(manifest, dict)
            or manifest.get("brand") != "Survival40"
            or manifest.get("source") != "verified_Pinterest_static_feed"
            or manifest.get("publishing_enabled") is not False
            or not isinstance(manifest.get("items"), list)):
        raise ValueError("Unsafe Instagram manifest origin or publish flag")

    source = {}
    for item in posts:
        ident = item.get("id")
        if (type(ident) is not int or ident < 1 or ident in source
                or not isinstance(item.get("title"), str)
                or not isinstance(item.get("excerpt"), str)
                or not isinstance(item.get("article_url"), str)):
            raise ValueError("Invalid or duplicate Pinterest article")
        source[ident] = item

    seen, urls, rows = set(), set(), []
    for entry in manifest["items"]:
        if not isinstance(entry, dict):
            raise ValueError("Malformed social image manifest entry")
        ident = entry.get("article_id")
        if type(ident) is not int or ident not in source or ident in seen:
            raise ValueError("Unknown or duplicate manifest article")
        post = source[ident]
        url = post["article_url"]
        if (entry.get("title") != post["title"]
                or entry.get("article_url") != url
                or entry.get("caption_draft") != cards.caption_from_source(post)
                or entry.get("status") != "assets_ready_not_published"
                or entry.get("instagram_image") !=
                   RAW + "assets/instagram/auto/" + str(ident) + ".png"
                or entry.get("social_og_image") !=
                   RAW + "assets/social/og/" + str(ident) + ".png"
                or not url.startswith("https://www.survival40.com/")
                or url in urls):
            raise ValueError("Article/asset mapping differs from verified RSS")
        seen.add(ident)
        urls.add(url)
        ig_info = validate_image(Path(ig) / (str(ident) + ".png"), cards.IG_SIZE)
        og_info = validate_image(Path(og) / (str(ident) + ".png"), cards.OG_SIZE)
        rows.append({
            "article_id": ident, "article_url": url,
            "article_title": post["title"],
            "existing_instagram_image": entry["instagram_image"],
            "existing_instagram_image_proof": ig_info,
            "proposed_social_og_image": entry["social_og_image"],
            "proposed_social_og_image_proof": og_info,
            "candidate_image_width_at_least_1200": og_info["width"] >= 1200,
            "candidate_only": True,
            "wordpress_og_image_matches_candidate": None,
            "live_image_url_fetch_verified": False,
            "discover_eligibility_verified": False,
            "discover_impressions_verified": False,
        })
    if seen != set(source):
        raise ValueError("Article manifest does not cover the verified feed")
    rows.sort(key=lambda x: x["article_id"])
    result = {
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source": "local_verified_rss_and_original_assets",
        "read_only": True,
        "changed_wordpress": False,
        "published_to_social": False,
        "article_count": len(rows),
        "all_candidate_images_decode_1200x630": bool(rows) and all(
            r["candidate_image_width_at_least_1200"] for r in rows
        ),
        "scope_warning": (
            "Offline local-file integrity only. Neither WordPress AIOSEO image "
            "selection, remote public image delivery, Discover appearance, "
            "Google indexing nor semantic artwork quality is checked. "
            "DO NOT auto-install or publish based on this report."
        ),
        "items": rows,
    }
    dest = Path(report)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    print(f"VERIFIED LOCAL PNG PAIRS: {len(rows)}. No web requests or posting.")
    return result


if __name__ == "__main__":
    verify()
