#!/usr/bin/env python3
"""Survival40 Threads: draft-only four daily slots with Gemini free tier.

There is intentionally NO Threads publication code or token handling here.
"""
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parents[2]
CONFIG = ROOT / "threads" / "editorial.json"
OUTPUT = ROOT / "threads-output" / "draft.json"
JST = ZoneInfo("Asia/Tokyo")
SLOTS = ("morning", "midday", "afternoon", "evening")
SLOT_HOURS = {"morning": 8, "midday": 12, "afternoon": 16, "evening": 20}

def choose_slot(now, requested="auto"):
    if requested in SLOTS:
        return requested
    if requested != "auto":
        raise ValueError("Invalid slot")
    # A late Actions start never creates a stale greeting.
    for slot, hour in SLOT_HOURS.items():
        if now.hour == hour and now.minute <= 59:
            return slot
    return None

def select_theme(today, slot, themes):
    seed = f"{today.isoformat()}:{slot}".encode()
    index = int(hashlib.sha256(seed).hexdigest()[:8], 16) % len(themes)
    return themes[index]

def select_editorial_topic(today, slot, groups, policy):
    """Flexible persona-first topic selection; only minor small-talk has a hard cap.

    Topics stay within a closed allowlist, while the balance between grooming,
    exercise and daily life is deliberately *not* a weekly quota. A deterministic
    hash gives stable preview output and weekly limits without persisted state.
    """
    if slot not in SLOTS:
        raise ValueError("Unknown posting slot")
    categories = ("grooming", "movement", "daily_routine", "small_talk")
    if set(groups) != set(categories) or not isinstance(policy, dict):
        raise ValueError("Unknown topic group")
    weights = policy.get("soft_weights")
    max_asides = policy.get("max_small_talk_per_14_slots")
    if (not isinstance(weights, dict) or set(weights) != set(categories)
            or any(type(weights[k]) is not int or weights[k] <= 0 for k in categories)
            or type(max_asides) is not int or not 0 <= max_asides <= 2):
        raise ValueError("Invalid persona-first topic policy")
    for items in groups.values():
        if not isinstance(items, list) or not items or not all(
                isinstance(x, str) and x.strip() for x in items):
            raise ValueError("Invalid topic allowlist")

    def weighted_pick(slot_index, salt, candidate_groups):
        total = sum(weights[k] for k in candidate_groups)
        week = today.isocalendar()
        seed = f"persona-first-v1:{week.year}:{week.week}:{slot_index}:{salt}"
        ticket = int(hashlib.sha256(seed.encode()).hexdigest()[:12], 16) % total
        for k in candidate_groups:
            if ticket < weights[k]:
                return k
            ticket -= weights[k]
        raise AssertionError("Topic selection exhausted")

    # Preserve the old deterministic 08/20 choices; separate 12/16 indices.
    slot_index = (
        today.weekday() * 2 + (0 if slot == "morning" else 1)
        if slot in ("morning", "evening")
        else 14 + today.weekday() * 2 + (0 if slot == "midday" else 1)
    )
    topic_group = weighted_pick(slot_index, "usual", categories)
    earlier_asides = sum(
        weighted_pick(i, "usual", categories) == "small_talk"
        for i in range(slot_index)
    )
    if topic_group == "small_talk" and earlier_asides >= max_asides:
        topic_group = weighted_pick(slot_index, "non-small", categories[:-1])

    morning_only = ("朝", "外出前")
    evening_only = ("夜", "帰宅後", "寝る前")
    eligible = [
        x for x in groups[topic_group]
        if slot not in ("evening", "afternoon") or not any(k in x for k in morning_only)
        if slot not in ("morning", "midday", "afternoon") or not any(k in x for k in evening_only)
    ]
    if not eligible:
        raise ValueError("No eligible topics for selected time")
    if slot in ("midday", "afternoon"):
        # Keep new daytime topics distinct from already-selected earlier slots.
        earlier = ("morning",) if slot == "midday" else ("morning", "midday")
        used = {select_editorial_topic(today, prev, groups, policy)["theme"]
                for prev in earlier}
        remaining = [theme for theme in eligible if theme not in used]
        if remaining:
            eligible = remaining
    return {"topic_group": topic_group,
            "theme": select_theme(today, slot, eligible)}


def select_persona_angle(today, slot, angles):
    """Optional emotional lens, not a writing template or a biographical fact."""
    if not isinstance(angles, list) or not angles or not all(
            isinstance(x, str) and x.strip() for x in angles):
        raise ValueError("Missing persona-angle options")
    seed = f"shiori-character-v1:{today.isoformat()}:{slot}".encode()
    index = int(hashlib.sha256(seed).hexdigest()[:12], 16) % len(angles)
    return angles[index]


def select_shape(today, slot):
    """Rotate conversational formats; small fictional daily incidents are allowed."""
    options = ("short_observation", "small_detail", "quiet_remark", "conversation_opening")
    digest = hashlib.sha256(f"style:{today.isoformat()}:{slot}".encode()).digest()
    return options[int.from_bytes(digest[:4], "big") % len(options)]


def select_tone_mode(today, slot):
    """Permit a rare casual aside without mandating one or creating a calendar pattern."""
    if slot not in SLOTS:
        raise ValueError("Unknown posting slot")
    # The new daytime slots use a calm tone by default; 08/20 are unchanged.
    if slot in ("midday", "afternoon"):
        return "polite"
    index = today.toordinal() * 2 + (0 if slot == "morning" else 1)
    def candidate(n):
        digest = hashlib.sha256(f"shiori-voice-v1:{n}".encode()).digest()
        return int.from_bytes(digest[:4], "big") % 100 < 22
    if candidate(index) and not any(candidate(index - i) for i in (1, 2)):
        return "relaxed_allowed"
    return "polite"


def build_prompt(now, slot, config, topic_signal=None):
    """One canonical prompt for daily drafts and evaluation previews."""
    if slot not in SLOTS:
        raise ValueError("Unknown posting slot")
    editorial = select_editorial_topic(
        now.date(), slot, config["topic_groups"],
        config["editorial_limits"]
    )
    persona_angle = select_persona_angle(
        now.date(), slot, config["character"]["everyday_angles"]
    )
    theme, topic_group = editorial["theme"], editorial["topic_group"]
    # An optional signal only chooses a PRE-APPROVED theme from the same
    # static topic groups. Never include third-party Threads text/usernames.
    if topic_signal is not None:
        if (not isinstance(topic_signal, dict)
                or set(topic_signal) != {"theme", "topic_group"}
                or topic_signal["theme"] not in config["topic_groups"].get(
                    topic_signal["topic_group"], [])):
            raise ValueError("Untrusted topic signal")
        theme, topic_group = topic_signal["theme"], topic_signal["topic_group"]
    shape = select_shape(now.date(), slot)
    tone_mode = select_tone_mode(now.date(), slot)
    weekday = ("月", "火", "水", "木", "金", "土", "日")[now.weekday()]
    prompt = json.dumps({
        "post_kind": "everyday_chat",
        "date_jst": now.date().isoformat(), "weekday": weekday,
        "slot": slot, "daypart": {"morning": "朝", "midday": "昼", "afternoon": "午後", "evening": "夜"}[slot],
        "theme": theme, "shape": shape, "topic_group": topic_group,
        "persona_angle": persona_angle,
        "character": config["character"],
        "editorial_goal": "宣伝しないことだけをゴールにしない。身近な場面の具体的な気づき・迷い・小さな行動から栞さんの人柄を見せ、『また読みたい』と思える一言にする。教訓や商品誘導は不要",
        "conversation_policy": config["editorial_modes"]["everyday_chat"]["conversation_policy"],
        "voice": config["voice"], "tone_mode": tone_mode,
        "topic_guardrail": (
            "これは少数枠だけ許可された、身の回りの持ち物や小さな家事の雑談です。"
            "主題を変えて政治、芸能、ニュース、ゲーム、恋愛、ビジネス、買い物レビューなどへ広げない。"
            "結論や教訓は不要。ただし状況・小さな出来事・その人らしい反応を具体的に書き、内容のない雰囲気だけで終わらない。" 
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
            "conversation_opening": "相手の経験を自然に聞きたくなるなら、その話題について短く問いかけてよい。質問は必須ではなく、独り言で終えてもよい。"
        }[shape],
        "editorial_priority": [
            "これは毎日の雑談下書き。役立つ情報を教える記事紹介とは役割が違う",
            "投稿ごとに人柄が少し見えることを目的にする。言葉の主語は栞さんであり、運営者やブログではない",
            "指定されたpersona_angleは感情や人柄のヒント。演じる義務ではなく自然に合うときだけ使う",
            "商品名・誘導文・有益な結論を入れるために日常の話を歪めない",
            "ひとりの人物が身近な物事について普通に話している雰囲気を優先する。雰囲気だけの作文にはせず、固有の物・手間・行動・失敗のどれかを見せる",
            "読者が最初に見る投稿でも、何の話か一読で分かる",
            "話題は再登場して構わない。ただし表現や問いかけを毎回同じ型にしない",
            "大きな教訓はいらない。ただしどうでもよさそうな話でも、細部や反応に栞さんらしさがあり、読み手が情景を思い浮かべられるようにする",
            "事実を教える、改善策を勧める、自己啓発の結論を出すことを目的にしない",
            "短く素直に話せるなら一文で止める。説明を足して文字数を稼がない。とはいえ『迷った・気がする・面白い』という評価語だけで終えず何が起きたかを示す",
            "話題について本当に他の人にも聞きたいときは質問で終えてよい。読者が自分の経験を気軽に返信できる問いは歓迎",
            "質問は毎回不要。独り言や小さな失敗談はそのまま終えてよい。会話を無理やり取りにいかない",
            "質問するなら直前の出来事と自然につながること。無関係な質問や反応稼ぎの二択、連続した問いかけを付け足さない",
            "栞さんは物語上の人物。ありそうな日常の小さな体験は一人称で創作してよい。出来事を語ることで人柄を感じさせる",
            "毎回体験談にする必要はない。感想だけ、疑問だけ、ちょっと情けない失敗だけでもよい",
            "人物の継続設定になる仕事・家族・住居・年齢・交友関係を勝手に作らない",
            "抽象的な比喩、読者心理の憶測、意味の通らない因果関係を使わない",
            "朝・昼・午後・夜の枠に話題が合うようにするが、今日何かをしたとは捏造しない"
        ],
        "guidelines": [
            "日本語25〜100字程度。短く自然なら一文でもよい。最大240字",
            "基本は『です・ます』の自然な丁寧語。敬語の堅さは不要だが、最初から友達口調にはしない",
            "tone_mode の指示を守り、毎回ラフな言葉を入れない",
            "『笑』やツッコミ、句点を抜く演出を定型化しない。語尾をわざと砕けさせない",
            ("8時の投稿は冒頭の「おはようございます。」を後処理で付けるため、本文中に重複して書かない"
             if slot == "morning" else
             "12時・16時・20時は挨拶を固定しない。朝の挨拶を使い回さない"),
            "40代男性の日常を見下さず、指導者ではなく程よい距離感の案内役として書く",
            "AIやシステム、投稿テスト、運用中、連携といった舞台裏の話題は出さない",
            "根拠のない季節の状況、今日の天気、祝日、時事・地域イベントには触れない",
            "身近な家事・持ち物・動作の小さな一人称エピソードは創作してよい。ただし本人の職歴、家族構成、実在の商品購入歴は勝手に設定しない",
            "ブランド商品の使用レビュー・アフィリエイト上の体験談・美容や健康の効果など、事実に基づくべき証言は捏造しない",
            "健康効果を断定しない。これは通常の雑談であり、記事紹介や商品宣伝を混ぜない",
            "努力・癒し・自分磨きなどの説教、無理な励まし、義務的な問いかけやまとめを避ける",
            "書き出し、リズム、長さを変える。啓蒙系の独白ではなく、実写アイコンの人物が自然に話す文章",
            "出来事と感想が一読で分かり、栞さんの性格が少し伝わるかを優先。『何について話し、何が印象に残るか』を自分で確かめ、空疎なら書き直す。短ければ短いままでよい"
        ]
    }, ensure_ascii=False)
    return {"prompt": prompt, "theme": theme, "topic_group": topic_group,
            "persona_angle": persona_angle, "shape": shape, "tone_mode": tone_mode}


def validate_post(text, slot, max_chars):
    if slot not in SLOTS:
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
            "Write from the perspective of Shiori as a consistent character "
            "the reader can get to know and like over many posts. "
            "Prioritize genuine personality, reactions, quirks, and relatable "
            "small moments over content marketing, informational value, or SEO. "
            "Give a reader a reason to remember this person or recognize their "
            "own small friction. Not every post needs a practical takeaway. "
            "A character-angle hint is optional, never a formula. "
            "This is a casual everyday post, NOT an article promotion or advice column. "
            "No requirement for lessons, useful tips, improvement plans, or conclusions. "
            "An ordinary trivial observation or a mildly embarrassing, "
            "relatable everyday incident is an acceptable complete post only when "
            "it contains a memorable concrete action, friction, choice, or reaction. "
            "Vague mood, mere indecision, or saying something is interesting is not "
            "a sufficient post by itself. "
            "Allow topics to repeat over time, but not canned phrasing. "
            "Do not imitate previous sample posts or repeat their sentence structures. "
            "Stay tightly within the assigned theme and topic group; avoid "
            "unrelated entertainment, news, politics, or broad lifestyle chatter. "
            "A genuine short question about the just-described experience can "
            "invite friendly replies; allow that when it flows naturally, but "
            "do not end every post with a question or tack on generic engagement bait. "
            "Many posts should simply stop with an observation, feeling, or mishap. "
            "Do not force a moral, summary, instruction, or call to action. "
            "Avoid corporate or "
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
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {"text": {"type": "STRING"}},
                "required": ["text"]
            },
            "maxOutputTokens": 800
        }
    }
    request = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"x-goog-api-key": key, "Content-Type": "application/json"},
        method="POST",
    )
    # A malformed structured-model response should not waste the entire preview.
    # Retry only that *formatting* failure once. Never retry 429, auth/network
    # problems, or use a paid-model fallback; never publish malformed text.
    for attempt in range(2):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                data = json.load(response)
        except urllib.error.HTTPError as error:
            # Only 503 is retried once. This is draft generation before ANY
            # ledger reservation or Threads publication call. Never retry a
            # 429, permission failure, network uncertainty or a Meta request.
            if error.code == 503 and attempt == 0:
                time.sleep(2)
                continue
            raise RuntimeError(f"Gemini unavailable (HTTP {error.code}); draft skipped") from None
        except (urllib.error.URLError, TimeoutError) as error:
            raise RuntimeError(f"Gemini connection error: {type(error).__name__}") from None
        except json.JSONDecodeError:
            if attempt == 0:
                continue
            raise RuntimeError("Gemini response envelope was malformed twice; draft skipped") from None

        output = "".join(
            part.get("text", "")
            for candidate in data.get("candidates", [])
            for part in candidate.get("content", {}).get("parts", [])
            if isinstance(part, dict)
        )
        try:
            post = json.loads(output)["text"]
            if isinstance(post, str) and post.strip():
                return post
        except (json.JSONDecodeError, KeyError, TypeError):
            pass
        if attempt == 0:
            continue
    raise RuntimeError("Gemini returned malformed post JSON twice; draft skipped")


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
        "topic_group": topic_group, "persona_angle": instruction["persona_angle"],
        "shape": shape, "tone_mode": tone_mode, "text": post, "publish": False, "status": "review_draft_only",
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
