"""Offline, read-only PNG size audit for fixed Survival40 OG triage articles.

This inspects committed repository files only. It never requests a URL, changes
WordPress, or asserts that an asset is served by the live site or Google.
"""
import json
import struct
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ARTICLE_IDS = (387, 389, 438, 596)
ASSET_DIRS = {
    "og": Path("assets/social/og"),
    "instagram": Path("assets/instagram/auto"),
    "pinterest": Path("assets/pinterest/auto"),
}
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def png_size(path):
    """Read only the PNG signature and IHDR; reject missing or invalid files."""
    try:
        with path.open("rb") as stream:
            head = stream.read(24)
    except FileNotFoundError:
        return None
    if (len(head) != 24 or head[:8] != PNG_SIGNATURE
            or head[8:12] != b"\x00\x00\x00\r"
            or head[12:16] != b"IHDR"):
        raise ValueError("Invalid PNG IHDR")
    width, height = struct.unpack(">II", head[16:24])
    if not (1 <= width <= 50000 and 1 <= height <= 50000):
        raise ValueError("Invalid PNG dimensions")
    return width, height


def audit(root=REPO_ROOT):
    """No external input controls file names; all inspected paths are fixed."""
    root = Path(root)
    rows = []
    for article_id in ARTICLE_IDS:
        assets = {}
        for kind, directory in ASSET_DIRS.items():
            path = directory / f"{article_id}.png"
            try:
                size = png_size(root / path)
            except (ValueError, OSError):
                assets[kind] = {"path": path.as_posix(), "status": "INVALID_UNVERIFIED"}
                continue
            if size is None:
                assets[kind] = {"path": path.as_posix(), "status": "ABSENT"}
            else:
                width, height = size
                assets[kind] = {
                    "path": path.as_posix(),
                    "status": "WIDTH_GE_1200" if width >= 1200 else "WIDTH_LT_1200",
                    "width": width, "height": height,
                }
        rows.append({"article_id": article_id, "assets": assets})
    return {
        "read_only": True,
        "local_repository_assets_only": True,
        "live_og_image_verified": False,
        "public_image_http_retrieval_verified": False,
        "google_discover_appearance_verified": False,
        "note": "A local 1200px OG asset is only a candidate; the WordPress HTML, "
                "image URL, robots policy and actual public fetch need separate checks.",
        "items": rows,
    }


if __name__ == "__main__":
    print(json.dumps(audit(), ensure_ascii=False, indent=2))
