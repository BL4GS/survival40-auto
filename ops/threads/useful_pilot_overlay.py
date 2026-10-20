"""No-publisher, one-for-one Shiori helpful-post trial overlay.

Executed *after* the existing immutable-Shiori-generator creates its safe
everyday fallback, *before* the existing, independently guarded publisher.
Four Thursday 16:00 JST posts only, never extra slots and never article links.
The source is a separately pinned and reviewed GitHub checkout.
"""
import datetime as dt
import importlib.util
import json
from pathlib import Path
from zoneinfo import ZoneInfo

ACCOUNT = "@survival40_jp"
START = dt.date(2026, 10, 22)
END = dt.date(2026, 11, 12)
JST = ZoneInfo("Asia/Tokyo")


def eligible(now, draft):
    if (not isinstance(now, dt.datetime) or now.tzinfo is None
            or now.utcoffset() != dt.timedelta(hours=9)
            or not isinstance(draft, dict)):
        return False
    day = now.date()
    if (not START <= day <= END or day.weekday() != 3
            or now.hour != 16
            or draft.get("slot") != "afternoon"
            or draft.get("kind") != "everyday"
            or draft.get("date_jst") != day.isoformat()
            or draft.get("id") != day.isoformat() + "-afternoon"
            or draft.get("account") != ACCOUNT
            or draft.get("article_id") is not None
            or draft.get("article_url") is not None
            or draft.get("article_title") is not None
            or draft.get("publish") is not False
            or draft.get("status") != "prepared_for_separate_publish_gate"):
        return False
    # A generated draft from today, not an old/other-account message.
    try:
        generated = dt.datetime.fromisoformat(draft["generated_at_jst"])
    except (TypeError, ValueError, KeyError):
        return False
    if (generated.tzinfo is None
            or generated.utcoffset() != dt.timedelta(hours=9)
            or not 0 <= (now - generated).total_seconds() <= 600):
        return False
    return True


def choose_helpful(now, approved_root):
    """Require exact reviewed RSS excerpts/IDs, otherwise no replacement."""
    root = Path(approved_root).resolve()
    helper_file = root / "scripts/threads/useful_preview.py"
    if not helper_file.is_file():
        raise ValueError("Missing approved helpful text/source validator")
    spec = importlib.util.spec_from_file_location("approved_helpful_only", helper_file)
    if spec is None or spec.loader is None:
        raise ValueError("Unusable approved helpful validator")
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    entries = helper.verified_articles(root / "pinterest/survival40-pins.xml")
    candidates = helper.make_previews(entries)
    # Four approved, distinct pieces of source-backed copy. Missing an entry
    # means ordinary Shiori continues, rather than shifting topics.
    expected_ids = (608, 610, 616, 617)
    if [p["source_post_id"] for p in candidates] != list(expected_ids):
        raise ValueError("Approval inventory changed")
    pilot_week = (now.date() - START).days // 7
    if not 0 <= pilot_week < len(candidates):
        raise ValueError("Outside approved four-post campaign")
    selected = candidates[pilot_week]
    if (selected.get("status") != "REVIEW_PREVIEW_ONLY"
            or selected.get("publish") is not False
            or selected.get("account") != ACCOUNT
            or selected.get("source_url") != entries[selected["source_post_id"]]["url"]
            or selected.get("requires_live_post_recheck") is not True):
        raise ValueError("Changed approved helper metadata")
    return selected


def apply(draft_path, approved_root, now, validate_post):
    """Only mutates one pre-existing draft on a 4-date pilot; never posts."""
    path = Path(draft_path)
    draft = json.loads(path.read_text(encoding="utf-8"))
    if not eligible(now, draft):
        return "SKIPPED_NOT_APPROVED_SLOT"
    try:
        selected = choose_helpful(now, approved_root)
        reviewed_text = validate_post(selected["text"], "afternoon", 300)
        if reviewed_text != selected["text"]:
            raise ValueError("Reviewed wording mutated")
    except (ValueError, OSError, UnicodeError, KeyError, TypeError,
            ImportError, AttributeError):
        # Source/wording drift: preserve vetted Gemini everyday draft as-is.
        return "SKIPPED_SOURCE_INVALID_ORDINARY_PRESERVED"
    updated = dict(draft)
    updated["text"] = reviewed_text
    updated["helpful_source_post_id"] = selected["source_post_id"]
    updated["helpful_source_url"] = selected["source_url"]
    updated["helpful_overlay_kind"] = "one_slot_grounded_pilot"
    encoded = json.dumps(updated, ensure_ascii=False, indent=2) + "\n"
    path.write_text(encoded, encoding="utf-8")
    return "PREPARED_ONE_FOR_ONE_HELPFUL_POST_NO_PUBLISH"


def main():
    # Main action deliberately has NO Meta credentials and NO API client.
    from scripts.threads.compose import OUTPUT, validate_post
    root = Path(__file__).resolve().parents[2]
    now = dt.datetime.now(JST)
    status = apply(OUTPUT, root, now, validate_post)
    print(status)


if __name__ == "__main__":
    main()
