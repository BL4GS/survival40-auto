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

def select_shape(today, slot):
    """Rotate editorial formats without adding fake personal anecdotes."""
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
    theme = select_theme(now.date(), slot, config["themes"])
    shape = select_shape(now.date(), slot)
    tone_mode = select_tone_mode(now.date(), slot)
    weekday = ("月", "火", "水", "木", "金", "土", "日")[now.weekday()]
    prompt = json.dumps({
        "date_jst": now.date().isoformat(), "weekday": weekday,
        "slot": slot, "theme": theme, "shape": shape,
        "voice": config["voice"], "tone_mode": tone_mode,
        "tone_mode_instructions": (
            "自然な『です・ます』口調を維持する。砕けた語尾、笑、くだけたツッコミを意図的に挿入しない。"
            if tone_mode == "polite" else
            "基本は丁寧語。場面に自然に合う場合のみ、ごく短いラフな一言や控えめなユーモアを許可する。"
            "自然でなければ丁寧語のままでよい。『笑』や砕けた語尾を入れる必要はない。"
        ),
        "shape_notes": {
            "short_observation": "身近なものを一つ取り上げ、そのことだけを素直に述べる。教訓なし。",
            "small_detail": "具体的な道具や行動の話から逸れない。個人の実体験を創作しない。",
            "quiet_remark": "一文〜二文で十分。言いたいことが薄ければ飾らず短く終える。",
            "light_question": "実際に聞いてみたくなる平易な疑問だけを一つ。無理に作らない。"
        }[shape],
        "approved_clarity_examples": [
            "詰め替え用のスキンケアをどの段階で買い足すか、案外迷うことがあります。ストックが一つあると安心ですが、収納の場所も少し気になるところです。",
            "タオルの柔らかさが変わるタイミングって、なんとなく使っていると見逃しやすいものですね。みなさんはどういう基準で新しくしているんでしょう。",
            "新しいものを探す前に、今引き出しの奥にあるものを使えるかどうか眺めてみるのも悪くないです。案外、必要なものは一通り揃っていたりします。"
        ],
        "quality_notes": [
            "上の3つは読者が分かりやすいと評価した文章。トーンと分かりやすさの参考であり、文章・語尾・構造をコピーしない",
            "具体的な対象が何か、どう感じたかが読みながらすぐ伝わる文章にする",
            "一投稿一話題。途中で無関係な連絡事項や心理分析に話を飛ばさない",
            "前後に論理的なつながりのない理由や結論を作らない。意味のない想像を追加しない",
            "特別な意味がない日用品の話を、深そうに見せる比喩や抽象語で飾らない",
            "『朝の空気が静かになる』『視界に入る情報量』『小さな余白』のような分かりにくい表現は禁止",
            "生活の中の感覚を必要以上に文学的・ポエム風・啓蒙系にしない",
            "朝の投稿が突然夜の話になるなど、時間帯と中心テーマが不自然にずれないようにする",
            "下書きを書いた後、読んですぐ理解できない箇所は平易な表現に書き換える。言うことが薄ければ短く終える"
        ],
        "guidelines": [
            "日本語40〜100字程度を目安。短く自然なら一文でもよい。最大240字",
            "基本は『です・ます』の自然な丁寧語。敬語の堅さは不要だが、最初から友達口調にはしない",
            "tone_mode の指示を守り、毎回ラフな言葉を入れない",
            "『笑』やツッコミ、句点を抜く演出を定型化しない。語尾をわざと砕けさせない",
            "冒頭の挨拶は任意。『おはようございます』『お疲れ様です』を毎回繰り返さない",
            "40代男性の日常を見下さず、指導者ではなく程よい距離感の案内役として書く",
            "AIやシステム、投稿テスト、運用中、連携といった舞台裏の話題は出さない",
            "根拠のない季節の状況、今日の天気、祝日、時事・地域イベントには触れない",
            "実際に経験したかのような一人称の仕事・家族・買い物・使用感を創作しない",
            "健康効果を断定しない。記事や商品の宣伝、ハッシュタグ、リンクは不要",
            "努力・癒し・自分磨きなどの説教、無理な励まし、毎回の問いかけやまとめを避ける",
            "書き出し、リズム、長さを変える。啓蒙系の独白ではなく、実写アイコンの人物が自然に話す文章"
        ]
    }, ensure_ascii=False)
    return {"prompt": prompt, "theme": theme, "shape": shape, "tone_mode": tone_mode}


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
            "It is fine to stop after a single observation; do not force a moral, "
            "summary, instruction, question, or call to action. Avoid corporate or "
            "AI-assistant expressions and inspirational clichés. "
            "Never impersonate genuine personal experiences, family, work, purchases, "
            "or firsthand product tests. No unverified health effects, statistics, "
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
    theme, shape, tone_mode = instruction["theme"], instruction["shape"], instruction["tone_mode"]
    prompt = instruction["prompt"]
    post = validate_post(gemini_generate(prompt, key), slot, config["max_characters"])
    draft = {
        "id": f"{now.date().isoformat()}-{slot}", "date_jst": now.date().isoformat(),
        "slot": slot, "account": config["account"], "theme": theme, "shape": shape,
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
