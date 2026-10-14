"""Sourced, selective Shiori referrals to older published Survival40 articles.

Two existing 20:00 slots per week at most, after the protected October calendar.
Never posts itself; source and publication checks are enforced again by the gate.
"""
import datetime as dt

from .article_feed import plain, require_article_url

START = dt.date(2026, 10, 28)
# Manually checked against published WordPress posts on 2026-10-14.
# Do not include the four protected earlier article-calendar slugs again.
CAMPAIGN = {
    "2026-10-28": (442, "40s-male-scalp-shampoo-guide", "40代男性のスカルプシャンプーの選び方｜洗浄力だけで選ばない",
                   "シャンプーは洗浄力が強いほど良い、というわけでもないんですよね。頭皮の状態や使い続けやすさから、選び方を整理した記事です。", True),
    "2026-10-31": (512, "40s-eye-strain-massage-breaks", "眼精疲労に目のマッサージは効く？40代男性の疲れ目対策と休憩のコツ",
                   "画面を見続けた日の目の疲れ。つい目元を押したくなりますが、やり方によっては注意も必要です。休憩の取り方を記事で整理しました。", False),
    "2026-11-04": (450, "40s-male-protein-how-to-choose", "40代男性のプロテインの選び方｜筋トレ初心者は何を基準にする？",
                   "プロテインは種類が多すぎて迷います。味や値段だけでなく、食事で足りているかも含めて選び方をまとめています。", True),
    "2026-11-07": (433, "40s-male-pillow-how-to-choose", "40代男性の枕の選び方｜寝返りと高さを基準に考える",
                   "枕の高さが合っているか、寝ている間は案外わからないものですね。選ぶときに確かめたいポイントを記事にしています。", True),
    "2026-11-11": (389, "40s-male-bad-breath-care", "40代男性の口臭が気になるときに確認したい原因と対策",
                   "口臭が気になると、つい香りの強いものを選びたくなります。でも原因はいろいろ。まず確認したいことを記事にまとめました。", False),
    "2026-11-14": (533, "monovo-hair-tonic-grow-gel-guide", "MONOVOヘアトニックグロウジェルの成分・価格・注意点｜40代男性の薬用育毛剤選び",
                   "『育毛剤』と『AGA治療』は同じではありません。薬用育毛剤の成分や値段、選ぶ前の注意点を整理しています。", True),
    "2026-11-18": (514, "40s-fatigue-food-meal-balance", "疲れたときに何を食べる？40代男性の食事選びとコンビニでの組み合わせ",
                   "疲れた日の食事って、考えること自体が面倒だったりします。コンビニでも組み合わせを考えるヒントを記事にまとめました。", True),
    "2026-11-21": (400, "40s-male-waking-at-night", "40代男性が夜中に目が覚める原因｜睡眠の質を下げる習慣を見直す",
                   "夜中に目が覚めたとき、まず何を見直せばいいのか。寝室や日常の習慣など、考えられる点を記事で整理しています。", True),
    "2026-11-25": (454, "40s-male-body-soap-odor-guide", "40代男性のボディソープの選び方｜体臭対策は洗いすぎないことも大切",
                   "清潔にしたいからといって、強く洗えば良いわけではないんですよね。毎日の洗い方とボディソープの選び方について。", True),
    "2026-11-28": (446, "40s-male-mouthwash-guide", "40代男性のマウスウォッシュの選び方｜刺激の強さと続けやすさで比べる",
                   "マウスウォッシュも、刺激の強さだけで選ぶと続かないことがあります。自分に合う選び方を記事に整理しました。", False),
}


def slot_spec(now):
    if (now.tzinfo is None or now.utcoffset() != dt.timedelta(hours=9)
            or now.date() < START or now.hour != 20 or now.weekday() not in (2, 5)):
        return None
    return CAMPAIGN.get(now.date().isoformat())


def article_text(spec, url):
    prefix = "【PR】" if spec[4] else ""
    text = prefix + spec[3] + "\n\n" + require_article_url(url)
    if not 40 <= len(text) <= 500:
        raise ValueError("Invalid vetted evergreen copy")
    return text


def select_verified(now, posts):
    """Validate the original WordPress ID, exact slug/title and published body."""
    spec = slot_spec(now)
    if spec is None:
        return None
    if not isinstance(posts, list):
        raise ValueError("Article feed was not a list")
    pid, slug, title, _intro, _has_ads = spec
    expected_url = "https://www.survival40.com/" + slug + "/"
    for post in posts:
        if not isinstance(post, dict) or post.get("id") != pid:
            continue
        if post.get("status") != "publish" or post.get("link") != expected_url:
            return None
        if plain(post.get("title", {}).get("rendered")) != title:
            return None
        raw = post.get("date_gmt")
        if not isinstance(raw, str):
            return None
        published = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if published.tzinfo is None:
            published = published.replace(tzinfo=dt.timezone.utc)
        if not published.astimezone(dt.timezone.utc) < now.astimezone(dt.timezone.utc) - dt.timedelta(days=1):
            return None
        if len(plain(post.get("content", {}).get("rendered"))) < 120:
            return None
        return {"id": pid, "title": title, "url": require_article_url(expected_url),
                "text": article_text(spec, expected_url)}
    return None


def validate_draft(draft, now, validate_everyday, max_chars):
    """Static source signature and safe Gemini fallback; no network here."""
    spec = slot_spec(now)
    if spec is None:
        raise ValueError("Evergreen post outside approved date/slot")
    pid, slug, title, _intro, _has_ads = spec
    url = "https://www.survival40.com/" + slug + "/"
    if (draft.get("kind") != "article" or draft.get("article_id") != pid
            or draft.get("article_title") != title or draft.get("article_url") != url
            or draft.get("text") != article_text(spec, url)):
        raise ValueError("Evergreen referral does not match verified source calendar")
    fallback = draft.get("fallback_everyday_text")
    if not isinstance(fallback, str) or validate_everyday(fallback, "evening", max_chars) != fallback:
        raise ValueError("Missing or invalid ordinary Shiori fallback")
    return draft["text"]
