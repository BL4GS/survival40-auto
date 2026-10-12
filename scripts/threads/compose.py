#!/usr/bin/env python3
"""Survival40 Threads: draft-only morning/evening copy with Gemini free tier.

There is intentionally NO Threads publication code or token handling here.
"""
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parents[2]
CONFIG = ROOT / "threads" / "editorial.json"
OUTPUT = ROOT / "threads-output" / "draft.json"
JST = ZoneInfo("Asia/Tokyo")

def choose_slot(now, requested="auto"):
    if requested in ("morning", "evening"):
        return requested
    if requested != "auto":
        raise ValueError("Invalid slot")
    # A late Actions start never creates a stale greeting.
    if now.hour == 8 and now.minute <= 59:
        return "morning"
    if now.hour == 20 and now.minute <= 59:
        return "evening"
    return None

def select_theme(today, slot, themes):
    seed = f"{today.isoformat()}:{slot}".encode()
    index = int(hashlib.sha256(seed).hexdigest()[:8], 16) % len(themes)
    return themes[index]

def select_editorial_topic(today, slot, groups, weekly_limits):
    """Allocate exactly one bounded small-talk slot per 14 morning/evening drafts.

    The weekly category sequence is shuffled deterministically, so small talk
    never becomes a fixed weekday gimmick. Topics come only from explicit
    editorial allowlists, not open-ended subject discovery.
    """
    if slot not in ("morning", "evening"):
        raise ValueError("Unknown posting slot")
    categories = ("grooming", "movement", "daily_routine", "small_talk")
    if (not isinstance(weekly_limits, dict)
            or set(weekly_limits) != set(categories)
            or set(groups) != set(categories)
            or any(type(weekly_limits.get(k)) is not int or weekly_limits[k] < 0
                   for k in categories)
            or sum(weekly_limits.values()) != 14
            or weekly_limits["small_talk"] > 1):
        raise ValueError("Invalid or overbroad editorial topic quota")
    week = today.isocalendar()
    weekly_order = sorted(
        range(14),
        key=lambda i: hashlib.sha256(
            f"editorial-v1:{week.year}:{week.week}:{i}".encode()
        ).digest()
    )
    slot_number = today.weekday() * 2 + (0 if slot == "morning" else 1)
    rank = weekly_order.index(slot_number)
    for group in categories:
        count = weekly_limits[group]
        if rank < count:
            break
        rank -= count
    allowed = groups[group]
    if not isinstance(allowed, list) or not allowed or not all(
            isinstance(x, str) and x.strip() for x in allowed):
        raise ValueError("Invalid editorial topic group")
    morning_only = ("朝", "外出前")
    evening_only = ("夜", "帰宅後", "寝る前")
    eligible = [
        x for x in allowed
        if slot != "evening" or not any(k in x for k in morning_only)
        if slot != "morning" or not any(k in x for k in evening_only)
    ]
    if not eligible:
        raise ValueError("No topics eligible for selected slot")
    return {"topic_group": group, "theme": select_theme(today, slot, eligible)}


def select_shape(today, slot):
    """Rotate conversational formats; small fictional daily incidents are allowed."""
    options = ("short_observation", "small_detail", "quiet_remark", "light_question")
    digest = hashlib.sha256(f"style:{today.isoformat()}:{slot}".encode()).digest()
    return options[int.from_bytes(digest[:4], "big") % len(options)]


def select_tone_mode(today, slot):
    """Permit a rare casual aside without mandating one or creating a calendar pattern."""
    if slot not in ("morning", "evening"):
        raise ValueError("Unknown posting slot")
    index = today.toordinal() * 2 + (0 if slot == "morning" else 1)
    def candidate(n):
        digest = hashlib.sha256(f"shiori-voice-v1:{n}".encode()).digest()
        return int.from_bytes(digest[:4], "big") % 100 < 22
    if candidate(index) and not any(candidate(index - i) for i in (1, 2)):
        return "relaxed_allowed"
    return "polite"


def build_prompt(now, slot, config):
    """One canonical prompt for daily drafts and evaluation previews."""
    if slot not in ("morning", "evening"):
        raise ValueError("Unknown posting slot")
    editorial = select_editorial_topic(
        now.date(), slot, config["topic_groups"],
        config["editorial_limits"]["per_14_weekly_slots"]
    )
    theme, topic_group = editorial["theme"], editorial["topic_group"]
    shape = select_shape(now.date(), slot)
    tone_mode = select_tone_mode(now.date(), slot)
    weekday = ("月", "火", "水", "木", "金", "土", "日")[now.weekday()]
    prompt = json.dumps({
        "post_kind": "everyday_chat",
        "date_jst": now.date().isoformat(), "weekday": weekday,
        "slot": slot, "theme": theme, "shape": shape, "topic_group": topic_group,
        "voice": config["voice"], "tone_mode": tone_mode,
        "topic_guardrail": (
            "これは週に最大1回だけ許可された、身の回りの持ち物や小さな家事の雑談です。"
            "主題を変えて政治、芸能、ニュース、ゲーム、恋愛、ビジネス、買い物レビューなどへ広げない。"
            "教訓や役立つ話に変換せず、軽い一言で終わって構いません。"
            if topic_group == "small_talk" else
            "Survival40の中心領域である身だしなみ、スキンケア、軽い運動、毎日の基本習慣から逸れない。"
            "雑談に脱線せず、設定された具体的なテーマに留まる。"
        ),
        "tone_mode_instructions": (
            "自然な『です・ます』口調を維持する。砕けた語尾、笑、くだけたツッコミを意図的に挿入しない。"
            if tone_mode == "polite" else
            "基本は丁寧語。場面に自然に合う場合のみ、ごく短いラフな一言や控えめなユーモアを許可する。"
            "自然でなければ丁寧語のままでよい。『笑』や砕けた語尾を入れる必要はない。"
        ),
        "shape_notes": {
            "short_observation": "身近なものを一つ取り上げ、そのことだけを素直に述べる。教訓なし。",
            "small_detail": "栞さん自身のちょっとした行動や失敗を一つ描いてよい。説明しすぎず、話題を逸らさない。",
            "quiet_remark": "一文〜二文で十分。言いたいことが薄ければ飾らず短く終える。",
            "light_question": "実際に聞いてみたくなる平易な疑問だけを一つ。無理に作らない。"
        }[shape],
        "editorial_priority": [
            "これは毎日の雑談下書き。役立つ情報を教える記事紹介とは役割が違う",
            "ひとりの人物が身近な物事について普通に話している雰囲気を優先する",
            "読者が最初に見る投稿でも、何の話か一読で分かる",
            "話題は再登場して構わない。ただし表現や問いかけを毎回同じ型にしない",
            "話題に意味や価値を持たせる必要はない。どうでもいい小さな話で終えてもよい",
            "事実を教える、改善策を勧める、自己啓発の結論を出すことを目的にしない",
            "短く素直に話せるなら一文で止める。説明を足して文字数を稼がない",
            "質問は本当に話しかけたいときだけ。毎回質問して読者を誘導しない",
            "栞さんは物語上の人物。ありそうな日常の小さな体験は一人称で創作してよい。出来事を語ることで人柄を感じさせる",
            "毎回体験談にする必要はない。感想だけ、疑問だけ、ちょっと情けない失敗だけでもよい",
            "人物の継続設定になる仕事・家族・住居・年齢・交友関係を勝手に作らない",
            "抽象的な比喩、読者心理の憶測、意味の通らない因果関係を使わない",
            "朝夜の枠に話題が合うようにするが、今朝や今夜何かをしたとは捏造しない"
        ],
        "guidelines": [
            "日本語25〜100字程度。短く自然なら一文でもよい。最大240字",
            "基本は『です・ます』の自然な丁寧語。敬語の堅さは不要だが、最初から友達口調にはしない",
            "tone_mode の指示を守り、毎回ラフな言葉を入れない",
            "『笑』やツッコミ、句点を抜く演出を定型化しない。語尾をわざと砕けさせない",
            "冒頭の挨拶は任意。『おはようございます』『お疲れ様です』を毎回繰り返さない",
            "40代男性の日常を見下さず、指導者ではなく程よい距離感の案内役として書く",
            "AIやシステム、投稿テスト、運用中、連携といった舞台裏の話題は出さない",
            "根拠のない季節の状況、今日の天気、祝日、時事・地域イベントには触れない",
            "身近な家事・持ち物・動作の小さな一人称エピソードは創作してよい。ただし本人の職歴、家族構成、実在の商品購入歴は勝手に設定しない",
            "ブランド商品の使用レビュー・アフィリエイト上の体験談・美容や健康の効果など、事実に基づくべき証言は捏造しない",
            "健康効果を断定しない。これは通常の雑談であり、記事紹介や商品宣伝を混ぜない",
            "努力・癒し・自分磨きなどの説教、無理な励まし、毎回の問いかけやまとめを避ける",
            "書き出し、リズム、長さを変える。啓蒙系の独白ではなく、実写アイコンの人物が自然に話す文章"
        ]
    }, ensure_ascii=False)
    return {"prompt": prompt, "theme": theme, "topic_group": topic_group,
            "shape": shape, "tone_mode": tone_mode}


def validate_post(text, slot, max_chars):
    if slot not in ("morning", "evening"):
        raise ValueError("Unknown posting slot")
    if not isinstance(text, str):
        raise ValueError("Text is not a string")
    text = text.strip()
    if not 18 <= len(text) <= min(max_chars, 240):
        raise ValueError("Out-of-range text length")
    # Genuine greetings are fine but must not appear on every post.
    forbidden = ("http://", "https://", "survival40.com", "PR案件", "絶対に治る",
                 "必ず治る", "確実に治る", "今すぐ購入", "購入はこちら", "今日の祝日は",
                 "本日が祝日", "今日は祝日", "今日は国民の祝日",
                 "投稿テスト", "投稿システム", "連携を確認", "自動投稿",
                 "本日は皆様に", "ご紹介します", "いかがでしょうか",
                 "小さな一歩を", "自分のペースで頑張", "今日も一日頑張りましたね",
                 "朝の空気は少しだけ静か", "視界に入る情報量", "小さな余白")
    if any(word in text for word in forbidden):
        raise ValueError("Unverified claim, system message, or template-like copy")
    if text.count("？") + text.count("?") > 1:
        raise ValueError("Too many questions")
    if re.search(r"[#＃][\w\-]+", text):
        raise ValueError("No hashtags in regular posts")
    return text

def gemini_generate(prompt, key, model="gemini-3.5-flash-lite"):
    payload = {
        "systemInstruction": {"parts": [{"text": (
            "Write ONE short natural Japanese Threads post for 栞, the Survival40 guide. "
            "She is a calm observer, not a motivational coach, salesperson, or doctor. "
            "Her voice is natural, mostly conversational Japanese desu/masu polite style, "
            "suited to a realistic photo-profile account: respectful without being stiff. "
            "Only occasionally, an unforced casual aside or light dry humor may appear; "
            "do not add casual endings, '笑', jokes or intimacy to every post. "
            "Avoid consistently casual speech, exaggerated honorifics, overly familiar "
            "friend-speak, forced sympathy, or an inspirational-coach persona. "
            "Start in different ways; greetings are optional, and never use forced cheer. "
            "Use one specific familiar object or activity and make the point "
            "instantly understandable to someone scrolling without context. "
            "Prioritize direct literal Japanese over imagery, cryptic metaphors, "
            "vague abstractions, decorative emotional interpretations, or awkward "
            "cause-and-effect. One topic per post, no invented logical leaps. "
            "Keep wording simple and relatively short. "
            "This is a casual everyday post, NOT an article promotion or advice column. "
            "No requirement for lessons, useful tips, improvement plans, or conclusions. "
            "An ordinary trivial observation or a mildly embarrassing, "
            "relatable everyday incident is an acceptable complete post. "
            "Allow topics to repeat over time, but not canned phrasing. "
            "Do not imitate previous sample posts or repeat their sentence structures. "
            "Stay tightly within the assigned theme and topic group; avoid "
            "unrelated entertainment, news, politics, or broad lifestyle chatter. "
            "It is fine to stop after a single observation; do not force a moral, "
            "summary, instruction, question, or call to action. Avoid corporate or "
            "AI-assistant expressions and inspirational clichés. "
            "Shiori is a fictional persona written as an ordinary person. "
            "Allow modest fictional first-person everyday anecdotes, funny failed "
            "attempts, and relatable lazy moments, but never invent lasting "
            "biographical facts such as family, employment or specific residence. "
            "Do not fabricate actual purchases, branded product endorsements, "
            "firsthand product test results, or medical outcomes. "
            "No unverified health effects, statistics, "
            "weather, holidays, local happenings, or news. No links, products, hashtags, "
            "marketing, or claims that a post is automated or a system test. "
            'Respond ONLY JSON with one property "text".'
        )}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "maxOutputTokens": 800}
    }
    request = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"x-goog-api-key": key, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.load(response)
    except urllib.error.HTTPError as error:
        # 429 = quota exhausted. Fail safe: no retry, no paid model fallback.
        raise RuntimeError(f"Gemini unavailable (HTTP {error.code}); draft skipped") from None
    except (urllib.error.URLError, TimeoutError) as error:
        raise RuntimeError(f"Gemini connection error: {type(error).__name__}") from None
    output = "".join(
        part.get("text", "")
        for candidate in data.get("candidates", [])
        for part in candidate.get("content", {}).get("parts", [])
        if isinstance(part, dict)
    )
    return json.loads(output)["text"]

def main():
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    now = dt.datetime.now(JST)
    requested = os.environ.get("THREADS_SLOT", "auto")
    slot = choose_slot(now, requested)
    if slot is None:
        print("SKIP: outside the scheduled 08:00/20:00 JST window")
        return
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise SystemExit("SKIP: Gemini secret unavailable; no generated post")
    instruction = build_prompt(now, slot, config)
    theme, topic_group = instruction["theme"], instruction["topic_group"]
    shape, tone_mode = instruction["shape"], instruction["tone_mode"]
    prompt = instruction["prompt"]
    post = validate_post(gemini_generate(prompt, key), slot, config["max_characters"])
    draft = {
        "id": f"{now.date().isoformat()}-{slot}", "date_jst": now.date().isoformat(),
        "slot": slot, "account": config["account"], "theme": theme,
        "topic_group": topic_group, "shape": shape,
        "tone_mode": tone_mode, "text": post, "publish": False, "status": "review_draft_only",
        "generated_at_jst": now.isoformat(timespec="seconds")
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(draft, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(f"PASS: {draft['id']} written as review draft; nothing published")

if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError, KeyError, json.JSONDecodeError) as error:
        sys.exit(str(error))
