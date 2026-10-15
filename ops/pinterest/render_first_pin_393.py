"""Render one Pinterest-ready Survival40 pin using the *existing* Shiori illustration.

No image generation, no WordPress change, no Pinterest API call.
"""
import base64
import io
import json
import os
import urllib.request
import urllib.error
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

URL = "https://www.survival40.com/wp-content/plugins/survival40-auto/assets/navigator/explain.webp"
OWNER = "BL4GS/survival40-auto"
OUTPUT = "assets/pinterest/40s-belly-activity-393-v2.png"
BACKGROUND = "#F8F8FF"
INK = "#273041"


def font(size):
    for candidate in [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
    ]:
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate, size, index=0)
    raise RuntimeError("Noto CJK Japanese font is missing; never draw tofu glyphs")


def get_shiori():
    req = urllib.request.Request(URL, headers={"User-Agent": "Survival40PinAssetBuilder/1.0", "Accept": "image/webp"})
    with urllib.request.urlopen(req, timeout=25) as response:
        raw = response.read(2_000_001)
        if len(raw) > 2_000_000 or not raw:
            raise RuntimeError("Shiori art too large or empty")
        if "image/" not in response.headers.get("Content-Type", "").lower():
            raise RuntimeError("Shiori art not an image")
    im = Image.open(io.BytesIO(raw))
    im.load()
    if im.width < 120 or im.height < 120:
        raise RuntimeError("Shiori source artwork resolution insufficient")
    return im.convert("RGBA")


def main():
    output = Path(OUTPUT)
    assert not output.exists(), "Do not overwrite a previously approved pin"
    artwork = get_shiori()
    # Preserve the original Shiori face and gesture with no synthetic edits.
    scale = min(430 / artwork.height, 380 / artwork.width)
    artwork = artwork.resize((int(artwork.width * scale), int(artwork.height * scale)), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (1000, 1500), BACKGROUND)
    draw = ImageDraw.Draw(canvas)
    heavy = font(90)
    medium = font(46)
    small = font(34)
    brand = font(40)

    draw.text((94, 128), "40代でお腹が", font=heavy, fill=INK)
    draw.text((94, 260), "出てきたら", font=heavy, fill=INK)
    draw.text((98, 470), "体重だけ", font=medium, fill=INK)
    draw.text((98, 540), "見ていませんか？", font=medium, fill=INK)

    draw.line([(98, 677), (902, 677)], fill="#CAD0DF", width=2)
    draw.text((98, 713), "食事・筋トレ・日々の活動量", font=small, fill="#46536C")
    draw.text((98, 764), "今から見直せることを整理", font=small, fill="#46536C")

    # Lower-left guide, no crop, no face or pose modification.
    x, y = 24, 1490 - artwork.height
    canvas.alpha_composite(artwork, (x, y))

    draw.text((490, 1268), "Survival40", font=brand, fill=INK)
    draw.text((490, 1335), "40代からの生存戦略", font=small, fill="#46536C")
    draw.text((904, 1440), "PR", font=font(22), fill="#8990A0")
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(output, "PNG", optimize=True)
    print(f"RENDERED: {OUTPUT}; {output.stat().st_size} bytes; 1000x1500")


def upload_public_asset():
    token = os.getenv("GITHUB_TOKEN", "")
    if not token:
        raise RuntimeError("GitHub token missing; will not attempt upload")
    raw = Path(OUTPUT).read_bytes()
    if len(raw) < 10000:
        raise RuntimeError("Unexpectedly small Pinterest image")
    url = f"https://api.github.com/repos/{OWNER}/contents/{OUTPUT}"
    # Always create without 'sha': an existing asset fails safely (never overwrites).
    body = json.dumps({
        "message": "assets: add one owner-approved Shiori Pinterest pin",
        "branch": "main",
        "content": base64.b64encode(raw).decode("ascii"),
    }).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="PUT", headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2022-11-28"
    })
    with urllib.request.urlopen(req, timeout=45) as response:
        result = json.load(response)
    if not isinstance(result, dict) or result.get("content", {}).get("path") != OUTPUT:
        raise RuntimeError("GitHub did not acknowledge expected image file")
    print("UPLOADED PUBLIC PIN ART: " + result["content"]["html_url"])


if __name__ == "__main__":
    main()
    upload_public_asset()
