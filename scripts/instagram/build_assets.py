"""Prepare original Shiori Instagram and social preview cards from VERIFIED Pinterest RSS.

This creates assets and a reviewable manifest ONLY; it never interacts with Meta,
Metricool, WordPress, or Pinterest posting APIs. Avoids WordPress article og:image
which may point to an affiliate banner. Existing Pinterest workflow untouched.
"""
import io
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageDraw

from scripts.pinterest import build_rss as pins
from scripts.pinterest.verify_static_feed import validate as verify_pinterest_rss

ASSET_DIR = Path("assets/instagram/auto")
OG_DIR = Path("assets/social/og")
MANIFEST = Path("instagram/ready-posts.json")
IG_SIZE = (1080, 1350)
OG_SIZE = (1200, 630)
BG = "#F8F8FF"
TEXT = "#273041"
MUTED = "#47556F"
DOMAIN = "https://www.survival40.com"
PIN_PREFIX = pins.RAW + "assets/pinterest/auto/"


def items_from_pinterest_feed(feed_path=pins.RSS_PATH, pin_dir=pins.ASSET_DIR):
    """Return only content from our already validated, original-image Pinterest feed."""
    verify_pinterest_rss(feed_path, pin_dir)
    root = ET.parse(feed_path).getroot()
    posts = []
    for item in root.findall("./channel/item"):
        img = item.find("enclosure").get("url")
        name = img[len(PIN_PREFIX):]
        if not re.fullmatch(r"[1-9][0-9]*[.]png", name):
            raise ValueError("Unexpected image file in Pinterest feed")
        posts.append({
            "id": int(name[:-4]),
            "title": item.findtext("title"),
            "excerpt": item.findtext("description"),
            "article_url": item.findtext("link"),
        })
    return posts


def lines_that_fit(draw, text, width, max_lines, sizes):
    for fontsize in sizes:
        font = pins.font(fontsize)
        try:
            lines = pins.wrap(draw, text, font, width, max_lines)
        except RuntimeError:
            continue
        return font, lines
    raise ValueError("Title too long to render safely")


def scaled_shiori(portrait, maxwidth, maxheight):
    scale = min(maxwidth / portrait.width, maxheight / portrait.height)
    return portrait.resize(
        (round(portrait.width * scale), round(portrait.height * scale)),
        Image.Resampling.LANCZOS,
    ).convert("RGBA")


def complete_subtitle(text):
    """Choose a source-verifiable COMPLETE sentence, never sever a number or word."""
    sentences = re.findall(r"[^。！？!?]+[。！？!?]", text.strip())
    if not sentences:
        raise ValueError("Missing complete source sentence for Instagram card")
    # Article RSS teasers often start by repeating the headline as a question.
    # Prefer the immediately following complete explanatory sentence, if any.
    return sentences[1].strip() if sentences[0].endswith(("？", "?")) and len(sentences) > 1 else sentences[0].strip()


def write_changed_png(canvas, out):
    """Regenerate cards when typography/source improves; avoid noop Git commits."""
    memory = io.BytesIO()
    canvas.save(memory, format="PNG", optimize=True)
    data = memory.getvalue()
    if not out.exists() or out.read_bytes() != data:
        out.write_bytes(data)


def render_instagram(post, portrait, asset_dir=ASSET_DIR):
    """Instagram feed 4:5; reflows typography rather than cropping the Pinterest art."""
    canvas = Image.new("RGB", IG_SIZE, BG)
    draw = ImageDraw.Draw(canvas)
    title_font, lines = lines_that_fit(
        draw, post["title"], 900, 4, (78, 73, 68, 62, 57, 52))
    y = 105
    for line in lines:
        draw.text((88, y), line, font=title_font, fill=TEXT)
        y += title_font.size + 22
    y = max(615, y + 40)
    if y > 780:
        raise ValueError("Title encroaches on Instagram body")
    draw.line([(88, y), (992, y)], fill="#C8D0DD", width=3)
    excerpt = complete_subtitle(post["excerpt"])
    description_font = pins.font(34, False)
    for line in pins.wrap(draw, excerpt, description_font, 906, 3):
        y += 51
        draw.text((88, y), line, font=description_font, fill=MUTED)
    shiori = scaled_shiori(portrait, 370, 376)
    canvas.paste(shiori, (30, IG_SIZE[1] - shiori.height - 8), shiori)
    draw.text((440, 1155), "Survival40", font=pins.font(49), fill=TEXT)
    draw.text((440, 1230), "40代からの生存戦略",
              font=pins.font(31, False), fill=MUTED)
    out = Path(asset_dir) / (str(post["id"]) + ".png")
    out.parent.mkdir(parents=True, exist_ok=True)
    write_changed_png(canvas, out)
    return out


def render_social_og(post, portrait, asset_dir=OG_DIR):
    """Optional 1200x630 image asset for future WordPress OG/featured-media rollout."""
    canvas = Image.new("RGB", OG_SIZE, BG)
    draw = ImageDraw.Draw(canvas)
    title_font, lines = lines_that_fit(
        draw, post["title"], 760, 4, (63, 59, 54, 50, 46, 41))
    y = 70
    for line in lines:
        draw.text((68, y), line, font=title_font, fill=TEXT)
        y += title_font.size + 24
    if y > 520:
        raise ValueError("Social card title overlaps footer")
    draw.line([(68, 523), (850, 523)], fill="#C8D0DD", width=3)
    draw.text((68, 547), "Survival40", font=pins.font(41), fill=TEXT)
    shiori = scaled_shiori(portrait, 339, 485)
    canvas.paste(shiori, (OG_SIZE[0] - shiori.width - 4, 623 - shiori.height), shiori)
    out = Path(asset_dir) / (str(post["id"]) + ".png")
    out.parent.mkdir(parents=True, exist_ok=True)
    write_changed_png(canvas, out)
    return out


def caption_from_source(post):
    """Public Instagram caption: complete article-based thought and real profile CTA.

    Do not use a non-clickable raw URL, fabricate a hands-on testimonial, or
    truncate survey sample counts/medical context in the middle of a sentence.
    The website is affiliate-funded, so PR disclosure is conservative.
    """
    title = post["title"].strip()
    subtitle = complete_subtitle(post["excerpt"])
    if not 9 <= len(title) <= 160 or not 12 <= len(subtitle) <= 210:
        raise ValueError("Unverifiable or oversized Instagram introduction")
    text = (
        "【PR】\n" + title
        + "\n\n" + subtitle
        + "\n\n詳しくはプロフィールのリンクからSurvival40へ。"
        + "\n\n#40代男性 #Survival40"
    )
    if len(text) > 500:
        raise ValueError("Instagram caption exceeds review limit")
    return text


def manifest_entry(post, ig_path, og_path):
    return {
        "article_id": post["id"],
        "title": post["title"],
        "article_url": post["article_url"],
        "instagram_image": pins.RAW + "assets/instagram/auto/" + ig_path.name,
        "social_og_image": pins.RAW + "assets/social/og/" + og_path.name,
        "caption_draft": caption_from_source(post),
        "status": "assets_ready_not_published",
        "requires": "verified connected Instagram business account; no automatic scheduling without publication gate",
    }


def build(feed_path=pins.RSS_PATH, pin_dir=pins.ASSET_DIR,
          portrait=None, instagram_dir=ASSET_DIR, og_dir=OG_DIR,
          manifest_path=MANIFEST):
    posts = items_from_pinterest_feed(feed_path, pin_dir)
    if portrait is None:
        source = pins.request_bytes(pins.SOURCE_ART, 2_000_000)
        with Image.open(io.BytesIO(source)) as source_image:
            portrait = source_image.convert("RGBA")
    if portrait.width < 120 or portrait.height < 120:
        raise ValueError("Original Shiori art is too small")
    entries = []
    for post in posts:
        ig_path = render_instagram(post, portrait, instagram_dir)
        og_path = render_social_og(post, portrait, og_dir)
        entries.append(manifest_entry(post, ig_path, og_path))
    ids = [entry["article_id"] for entry in entries]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate Instagram draft entry")
    payload = {
        "brand": "Survival40",
        "publishing_enabled": False,
        "source": "verified_Pinterest_static_feed",
        "items": entries,
    }
    manifest_path = Path(manifest_path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(payload, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    if not manifest_path.exists() or manifest_path.read_bytes() != data:
        manifest_path.write_bytes(data)
    print("PREPARED:", len(entries), "Instagram/OG pairs. NO SOCIAL POSTING")
    return payload


if __name__ == "__main__":
    build()
