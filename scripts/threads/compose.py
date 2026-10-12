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
                 "小さな一歩を", "自分のペースで頑張", "今日も一日頑張りましたね")
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
            "Start in different ways; greetings are optional, and never use forced cheer. "
            "Use an ordinary concrete detail rather than abstract life advice. "
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
    theme = select_theme(now.date(), slot, config["themes"])
    weekday = ("月", "火", "水", "木", "金", "土", "日")[now.weekday()]
    shape = select_shape(now.date(), slot)
    prompt = json.dumps({
        "date_jst": now.date().isoformat(), "weekday": weekday,
        "slot": slot, "theme": theme, "shape": shape,
        "shape_notes": {
            "short_observation": "生活の中のちょっとした気づき。結論や教訓なし。",
            "small_detail": "ひとつの具体的な場面・行動に寄せる。想像上の個人体験は語らない。",
            "quiet_remark": "短い独り言に近い一文〜二文。挨拶や締めの定型文は不要。",
            "light_question": "答えを強要しない軽い疑問。質問を作るためだけの文章にしない。"
        }[shape],
        "guidelines": [
            "日本語18〜160字を目安。短く自然なら一文でもよい。最大240字",
            "冒頭の挨拶は任意。『おはようございます』『お疲れ様です』を毎回繰り返さない",
            "40代男性の日常を見下さず、指導者ではなく横から見ている案内役として書く",
            "AIやシステム、投稿テスト、運用中、連携といった舞台裏の話題は出さない",
            "根拠のない季節の状況、今日の天気、祝日、時事・地域イベントには触れない",
            "実際に経験したかのような一人称の仕事・家族・買い物・使用感を創作しない",
            "健康効果を断定しない。記事や商品の宣伝、ハッシュタグ、リンクは不要",
            "努力・癒し・自分磨きなどの説教、無理な励まし、毎回の問いかけやまとめを避ける",
            "書き出し、文章のリズム、長さを変える。広告コピーではなく個人の自然なつぶやき"
        ]
    }, ensure_ascii=False)
    post = validate_post(gemini_generate(prompt, key), slot, config["max_characters"])
    draft = {
        "id": f"{now.date().isoformat()}-{slot}", "date_jst": now.date().isoformat(),
        "slot": slot, "account": config["account"], "theme": theme, "shape": shape,
        "text": post, "publish": False, "status": "review_draft_only",
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
