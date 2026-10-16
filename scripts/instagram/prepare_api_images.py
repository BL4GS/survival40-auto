"""Generate JPEG media for a possible future official Instagram API integration.

Meta's Instagram content-publishing API accepts public JPEG for single images.
This stage ONLY writes files to GitHub; it does not authenticate or publish.
Keep the existing Metricool PNG assets and booking untouched.
"""
import hashlib
import io
import json
from pathlib import Path

from PIL import Image

from scripts.instagram import build_assets as cards
from scripts.instagram.prepare_queue import canonical_article

READY = Path("instagram/ready-posts.json")
PNG_DIR = Path("assets/instagram/auto")
JPG_DIR = Path("assets/instagram/api-jpeg")
OUTPUT = Path("instagram/api-media-assets.json")
PNG_PREFIX = "https://raw.githubusercontent.com/BL4GS/survival40-auto/main/assets/instagram/auto/"
JPG_PREFIX = "https://raw.githubusercontent.com/BL4GS/survival40-auto/main/assets/instagram/api-jpeg/"
MAX_ORIGINAL_BYTES = 6_000_000


def build(ready_path=READY, png_dir=PNG_DIR, jpg_dir=JPG_DIR, output=OUTPUT):
    ready = json.loads(Path(ready_path).read_text(encoding="utf-8"))
    if (ready.get("brand") != "Survival40"
            or ready.get("source") != "verified_Pinterest_static_feed"
            or ready.get("publishing_enabled") is not False
            or not isinstance(ready.get("items"), list)):
        raise ValueError("Unverified or publishing-enabled Instagram source")
    result = []
    used = set()
    for post in ready["items"]:
        ident = post.get("article_id")
        if type(ident) is not int or ident < 1 or ident in used:
            raise ValueError("Invalid or repeated Instagram article ID")
        used.add(ident)
        expected_png = PNG_PREFIX + str(ident) + ".png"
        url = canonical_article(post.get("article_url"))
        if (post.get("instagram_image") != expected_png
                or post.get("status") != "assets_ready_not_published"
                or not isinstance(post.get("caption_draft"), str)
                or "プロフィールのリンク" not in post["caption_draft"]):
            raise ValueError("Instagram asset metadata mismatch")
        source = Path(png_dir) / (str(ident) + ".png")
        if not source.is_file() or source.stat().st_size > MAX_ORIGINAL_BYTES:
            raise ValueError("Missing or oversized Instagram PNG")
        with Image.open(source) as picture:
            if picture.format != "PNG" or picture.size != cards.IG_SIZE:
                raise ValueError("Invalid 1080x1350 Instagram original image")
            image = picture.convert("RGB")
        bytes_out = io.BytesIO()
        image.save(bytes_out, format="JPEG", quality=90, subsampling=0, optimize=True)
        data = bytes_out.getvalue()
        if len(data) > 6_000_000:
            raise ValueError("JPEG media unexpectedly large")
        destination = Path(jpg_dir) / (str(ident) + ".jpg")
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.is_file() or destination.read_bytes() != data:
            destination.write_bytes(data)
        with Image.open(destination) as converted:
            if converted.format != "JPEG" or converted.size != cards.IG_SIZE:
                raise ValueError("JPEG conversion failed")
            converted.verify()
        result.append({
            "article_id": ident,
            "article_url": url,
            "source_png": expected_png,
            "public_jpeg_url": JPG_PREFIX + str(ident) + ".jpg",
            "sha256": hashlib.sha256(data).hexdigest(),
            "status": "MEDIA_ONLY_NOT_PUBLISHED",
        })
    payload = {
        "brand": "Survival40", "publishing_enabled": False,
        "official_instagram_api_enabled": False,
        "account": "survival40_jp",
        "requires": "Meta Business Login, verified app/token, pilot PUBLISHED, duplicate ledger and owner approval before new publisher",
        "items": result,
    }
    dest = Path(output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode()
    if not dest.exists() or dest.read_bytes() != encoded:
        dest.write_bytes(encoded)
    print(f"Prepared {len(result)} official Instagram API JPEG media files; NO POSTS")
    return payload


if __name__ == "__main__":
    build()
