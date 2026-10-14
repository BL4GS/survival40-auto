"""Review-only sample generation for Shiori. Never calls the Threads API."""
import datetime as dt
import json
import os
import pathlib
import sys
from zoneinfo import ZoneInfo

from .compose import CONFIG, JST, ROOT, build_prompt, gemini_generate, select_tone_mode, validate_post

OUTPUT = ROOT / "threads-output" / "shiori-samples.json"


def select_examples(start_date):
    """Six typical polite samples and two deliberately sampled rare-allowance cases.

    This preview is STRATIFIED to make the occasional-tone cases easy to judge.
    It is NOT a prediction of how often the real automated schedule will use them.
    """
    candidates = []
    for day_offset in range(45):
        day = start_date + dt.timedelta(days=day_offset)
        for slot in ("morning", "evening"):
            candidates.append((day, slot, select_tone_mode(day, slot)))
    normal = [t for t in candidates if t[2] == "polite"]
    rare = [t for t in candidates if t[2] == "relaxed_allowed"]
    if len(rare) < 2 or len(normal) < 18:
        raise RuntimeError("Insufficient evaluation samples")
    # Spread typical examples across topics, slots, and days.
    selected = [normal[i] for i in (0, 3, 6, 9, 12, 15)] + rare[:2]
    selected.sort(key=lambda item: (item[0], item[1]))
    return selected


def main():
    token = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not token:
        raise RuntimeError("Gemini secret missing; no samples produced")
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    now = dt.datetime.now(JST)
    examples = select_examples(now.date())
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    bundle = {
        "generated_at_jst": now.isoformat(timespec="seconds"),
        "mode": "draft_preview_only",
        "posting_enabled": False,
        "selection": "stratified: 6 polite and 2 relaxed-allowed slots for comparison; not actual scheduling frequency",
        "review_criteria": config["editorial_review"]["questions"],
        "examples": [],
    }
    for day, slot, tone_mode in examples:
        simulated_time = dt.datetime.combine(
            day, dt.time(8 if slot == "morning" else 20), tzinfo=JST
        )
        instruction = build_prompt(simulated_time, slot, config)
        item = {
            "day_jst": day.isoformat(),
            "slot": slot,
            "theme": instruction["theme"],
            "topic_group": instruction["topic_group"],
            "persona_angle": instruction["persona_angle"],
            "tone_mode": tone_mode,
            "valid": False,
        }
        try:
            result = gemini_generate(instruction["prompt"], token)
            item["text"] = result
            try:
                validate_post(result, slot, config["max_characters"])
                item["valid"] = True
            except ValueError as exc:
                item["rejection_reason"] = str(exc)
        except (RuntimeError, ValueError, KeyError, json.JSONDecodeError) as exc:
            item["generation_error"] = str(exc)
        bundle["examples"].append(item)
        # Always preserve partial output, including nonconforming generations.
        OUTPUT.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Sample {len(bundle['examples'])}/8: {tone_mode}, valid={item['valid']}")
        if "generation_error" in item:
            print("Gemini was unavailable; stopping without fallback or retries.")
            break
    print("Draft preview saved. No Threads credential was read or post published.")
    if not bundle["examples"] or any("generation_error" in x for x in bundle["examples"]):
        raise RuntimeError("Some previews could not be generated; inspect the partial artifact")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError, KeyError) as exc:
        sys.exit(str(exc))
