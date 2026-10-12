#!/usr/bin/env python3
"""Map vetted concept proposals to the existing Survival40 WP planner contract.

This is deliberately a NON-EXECUTABLE editorial handoff: it has no WordPress
credentials, no posting client, and does not bypass article research/review.
"""
import hashlib
import json
import pathlib
import re
import sys
import unicodedata
from editorial_intelligence.plan import is_similar
from site_audit.audit import fetch_posts, plain

BASE = pathlib.Path(__file__).resolve().parents[1]
SOURCE = BASE / "editorial-output" / "topics.json"
DEST = BASE / "editorial-output" / "wp-plan-handoff.json"

# Verified against v0.19.21 release-review PHP auto_category_map().
CATEGORY = {
    "肌・老け見え": {"group": "skin", "ymyl": False},
    "髪・頭皮": {"group": "aga", "ymyl": True},
    "ニオイ・清潔感": {"group": "general", "ymyl": False},
    "口・歯": {"group": "oral", "ymyl": True},
    "疲労・睡眠": {"group": "sleep", "ymyl": True},
    "体型・筋力": {"group": "fitness", "ymyl": False},
    "食事・栄養": {"group": "nutrition", "ymyl": True},
    "40代の不調": {"group": "general", "ymyl": True},
}
# Order matters only for deterministic output; ambiguous results are held.
SUBJECTS = (
    ("40代の不調", r"ドライアイ|老眼|老視|眼精疲労|視力|目の疲れ|目の乾燥|眼鏡|メガネ|腰痛|関節痛|頭痛|肩こり|痛み"),
    ("髪・頭皮", r"白髪|頭皮|抜け毛|薄毛|育毛|髪|シャンプー|ヘアカラー|染毛"),
    ("口・歯", r"歯磨き|歯周|虫歯|口臭|口腔|デンタル|歯ブラシ|歯間"),
    ("ニオイ・清潔感", r"体臭|汗臭|加齢臭|デオドラント|脇汗|清潔感|ニオイ"),
    ("疲労・睡眠", r"睡眠|寝付き|寝つき|不眠|夜更かし|寝不足|眠り|寝室"),
    ("食事・栄養", r"食事|栄養|朝食|水分補給|飲料|カフェイン|コーヒー|お酒|アルコール|プロテイン|食物繊維"),
    ("体型・筋力", r"筋トレ|筋力|筋肉|ストレッチ|運動|スクワット|体幹|体型|ウォーキング"),
    ("肌・老け見え", r"スキンケア|化粧水|乳液|保湿|乾燥肌|敏感肌|肌荒れ|日焼け止め|紫外線|洗顔|シミ"),
)
EXCLUDE = re.compile(r"診断法|治療法|治す方法|完治|処方|市販薬|薬の飲み方|糖尿病|高血圧|がんを|うつ病")
CONCEPT_FIELDS = ("title", "category", "reader_problem", "reader_takeaway",
                  "research_questions", "advertising_policy", "status")


class HandoffError(ValueError):
    pass


def classify(title):
    """Fail closed if title clearly spans different WP editor sections."""
    matched = [name for name, expr in SUBJECTS if re.search(expr, title)]
    if not matched:
        return None, "unrecognized_subject"
    # Eyes/pain override incidental eye-wear/skin words; still conservatively YMYL.
    if "40代の不調" in matched and len(matched) == 2:
        other = next(x for x in matched if x != "40代の不調")
        if other in ("体型・筋力", "肌・老け見え"):
            return "40代の不調", "health_caution_priority"
    if len(matched) > 1:
        return None, "multi_subject_review_required"
    return matched[0], "unambiguous_subject"


def inspect_idea(idea, published, seen_ids):
    if not isinstance(idea, dict) or any(x not in idea for x in CONCEPT_FIELDS):
        return None, "missing_required_fields"
    if idea.get("status") != "concept_only_not_researched":
        return None, "incorrect_concept_status"
    title = idea["title"]
    if not isinstance(title, str) or not 18 <= len(title.strip()) <= 90:
        return None, "invalid_title"
    if EXCLUDE.search(title):
        return None, "medical_treatment_topic_not_auto_eligible"
    if is_similar(title, published):
        return None, "similar_to_current_published_article"
    original_category = idea.get("category")
    if original_category not in ("skin", "body", "daily"):
        return None, "invalid_concept_category"
    if idea["advertising_policy"] not in ("none", "optional"):
        return None, "invalid_ad_policy"
    research = idea["research_questions"]
    if not isinstance(research, list) or not 2 <= len(research) <= 4 or not all(
        isinstance(q, str) and 12 <= len(q) <= 200 for q in research
    ):
        return None, "missing_research_brief"
    category, rationale = classify(title)
    if category is None:
        return None, rationale
    # Broad buckets are hints, never override exact WordPress subject classes.
    if original_category == "skin" and category not in ("肌・老け見え", "40代の不調"):
        return None, "category_conflict"
    if original_category == "body" and category not in (
        "体型・筋力", "疲労・睡眠", "食事・栄養", "40代の不調"
    ):
        return None, "category_conflict"
    checksum = hashlib.sha256(
        (unicodedata.normalize("NFKC", title).casefold() + "|" + category).encode("utf-8")
    ).hexdigest()[:20]
    if checksum in seen_ids:
        return None, "duplicate_idea_in_queue"
    seen_ids.add(checksum)
    # A search keyword candidate, not verified search-volume/SEO data.
    keyword = re.sub(r"[|｜:：!！?？、。]", " ", title).strip()[:90]
    reader_problem = idea["reader_problem"]
    takeaway = idea["reader_takeaway"]
    if not isinstance(reader_problem, str) or not isinstance(takeaway, str) or not reader_problem.strip() or not takeaway.strip():
        return None, "missing_reader_value"
    excerpt = (takeaway.strip() + " " + reader_problem.strip())[:120]
    if len(excerpt) < 30:
        return None, "short_excerpt"
    return {
        "topic_id": "s40-" + checksum,
        "stage": "needs_independent_source_research",
        "plugin_planner_input": {
            "title": title.strip(),
            "keyword": keyword,
            "category": category,
            "excerpt": excerpt,
            "seo_title": title.strip()[:90],
            "amazon_query": "",  # No unchecked affiliate links/products.
            "reason": "週次企画からの候補。根拠調査・校閲前のため公開不可。",
        },
        "editorial": {
            "original_bucket": original_category,
            "mapped_category_reason": rationale,
            "research_questions": research,
            "source_group_hint": CATEGORY[category]["group"],
            "requires_ymyl_gate": CATEGORY[category]["ymyl"],
            "advertising_policy": idea["advertising_policy"],
            "verified_search_demand": False,
            "verified_sources": 0,
            "sources_checked": False,
        },
        "safety": {
            "publish_authorized": False,
            "can_enter_research_stage": True,
            "must_recheck_all_wordpress_posts_including_drafts": True,
            "no_affiliate_assigned": True,
            "requires_existing_wordpress_quality_gates": True,
        },
    }, None


def build_handoff(report, published_titles):
    if not isinstance(report, dict):
        raise HandoffError("Invalid concepts report")
    if report.get("automatically_published") is not False or report.get("source_validation") != "not_done_yet":
        raise HandoffError("Concepts lack the required nonpublished/unresearched markers")
    ideas = report.get("ideas")
    if not isinstance(ideas, list) or len(ideas) > 8:
        raise HandoffError("Invalid concepts list")
    accepted, held, seen = [], [], set()
    for i, candidate in enumerate(ideas):
        entry, error = inspect_idea(candidate, published_titles, seen)
        if error:
            held.append({"index": i, "reason": error})
        else:
            accepted.append(entry)
    return {
        "schema": "survival40.wp_plan_handoff.v1",
        "source_date_jst": report.get("date_jst"),
        "published_article_title_count": len(published_titles),
        "plans": accepted,
        "held": held,
        "wp_posts_written": 0,
        "threads_posts_written": 0,
        "ready_to_publish": False,
        "disclaimer": "Concept handoff only. Not a verified WordPress post/draft/publication request.",
    }


def main():
    report = json.loads(SOURCE.read_text(encoding="utf-8"))
    posts, _ = fetch_posts()
    titles = [plain(p.get("title", {}).get("rendered", ""))
              for p in posts if isinstance(p, dict) and p.get("status") == "publish"]
    if not titles:
        raise HandoffError("No current published titles; fail closed")
    handoff = build_handoff(report, titles)
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(handoff, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: {len(handoff['plans'])} research-stage handoffs, "
          f"{len(handoff['held'])} held; 0 WordPress mutations")


if __name__ == "__main__":
    try:
        main()
    except (HandoffError, ValueError, OSError, json.JSONDecodeError) as exc:
        sys.exit("SKIP: " + str(exc))
