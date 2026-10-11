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

def validate_post(text, slot, max_chars):
    if not isinstance(text, str):
        raise ValueError("Text is not a string")
    text = text.strip()
    if not 28 <= len(text) <= max_chars:
        raise ValueError("Out-of-range text length")
    if slot == "morning" and not text.startswith("おはようございます"):
        raise ValueError("Morning greeting missing")
    if slot == "evening" and not (text.startswith("お疲れ様です") or text.startswith("今日も一日お疲れ様")):
        raise ValueError("Evening greeting missing")
    forbidden = ("http://", "https://", "survival40.com", "PR案件", "絶対に治る",
                 "必ず治る", "確実に治る", "今すぐ購入", "購入はこちら", "今日の祝日は",
                 "本日が祝日", "今日は祝日", "今日は国民の祝日")
    if any(word in text for word in forbidden):
        raise ValueError("Unverified claim or promotion")
    if text.count("？") + text.count("?") > 1:
        raise ValueError("Too many questions")
    if re.search(r"[#＃][\w\-]+", text):
        raise ValueError("No hashtags in regular greetings")
    return text

def gemini_generate(prompt, key, model="gemini-3.5-flash-lite"):
    payload = {
        "systemInstruction": {"parts": [{"text": (
            "You are writing a Japanese Threads greeting on behalf of the fictional "
            "Survival40 guide 栞さん. Gentle, natural, grounded, no superiority, "
            "no personal lived-experience claims, no affiliate links or products. "
            "Never claim a holiday, current news, weather, temperature or health "
            "effect without verified evidence in input. Respond ONLY JSON with "
            'one property "text". Avoid repetitive corporate phrasing.'
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
    salutation = "おはようございます！" if slot == "morning" else "お疲れ様です！"
    weekday = ("月", "火", "水", "木", "金", "土", "日")[now.weekday()]
    prompt = json.dumps({
        "date_jst": now.date().isoformat(), "weekday": weekday,
        "slot": slot, "opening": salutation, "theme": theme,
        "guidelines": [
            "文字数60〜180文字程度、最大300文字",
            "一日の挨拶が主役。宣伝もリンクも不要",
            "季節への軽い言及は可能。ただし事実未確認の祝日、天気、時事ニュース、イベント名は言わない",
            "栞さんは40代男性の生活を否定せず、指導者ではなく案内役",
            "架空の本人の実体験や健康効果を断定しない",
            "夜は自然な労いを優先。問いかけは任意で最大1つ"
        ]
    }, ensure_ascii=False)
    post = validate_post(gemini_generate(prompt, key), slot, config["max_characters"])
    draft = {
        "id": f"{now.date().isoformat()}-{slot}", "date_jst": now.date().isoformat(),
        "slot": slot, "account": config["account"], "theme": theme,
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
