"""Deterministic topic spacing for Shiori's four everyday Threads slots.

The source topic is still drawn from the editorial allowlist. This layer only
replaces recently overused topics *within the same group*. It never touches
article introductions, Meta APIs or the durable publication ledger.
"""
import datetime as dt
import hashlib

from .compose import SLOT_HOURS, SLOTS, select_editorial_topic

FIRST_SLOT = dt.date(2026, 10, 13)
# A family means a recognizable setting/object, not an arbitrary shared word.
FAMILIES = (
    "着替え", "洗面台", "ヨガマット", "日焼け止め", "洗顔",
    "スキンケア", "筋トレ", "タオル", "ハンカチ", "ポケット",
    "歯ブラシ", "シャンプー", "保湿", "靴", "レシート",
    "睡眠", "朝食", "寝具", "スマホ", "日用品",
)
COOLDOWN_EXACT_SLOTS = 12   # same exact topic no more than once in ~3 days
COOLDOWN_FAMILY_SLOTS = 8   # similar objects/scenes spaced ~2 days


def family_set(theme):
    return frozenset(x for x in FAMILIES if x in theme)


def _is_time_eligible(theme, slot):
    # Keep the established morning-vs-night guardrail from compose.py.
    if slot in ("evening", "afternoon") and any(w in theme for w in ("朝", "外出前")):
        return False
    if slot in ("morning", "midday", "afternoon") and any(w in theme for w in ("夜", "帰宅後", "寝る前")):
        return False
    return True


def _pick(base, choices, previous, date, slot, allow_preferred_out_of_daypart=False):
    group, requested = base["topic_group"], base["theme"]
    if requested not in choices:
        raise ValueError("Topic not in the approved group")
    if not all(isinstance(x, str) and x for x in choices):
        raise ValueError("Unexpected topic options")
    eligible = [x for x in choices if _is_time_eligible(x, slot)]
    if requested not in eligible:
        # Topic discovery may supply a verified allowlisted signal that is
        # seasonally relevant despite wording such as "朝食" in an evening slot.
        # Preserve previously approved signal behavior for that one target.
        if allow_preferred_out_of_daypart:
            eligible.append(requested)
        else:
            raise ValueError("Selected topic is ineligible for this daypart")
    if not eligible:
        raise ValueError("No topics eligible for this daypart")

    # Prefer entirely fresh themes within the 12-slot window; then avoid
    # sharing a distinctive object/scene within 8 slots. If no safe
    # alternative exists, select the least repetitive eligible option.
    recent_exact = [item[1] for item in previous[-COOLDOWN_EXACT_SLOTS:]]
    recent_family = [
        family_set(item[1]) for item in previous[-COOLDOWN_FAMILY_SLOTS:]
    ]
    def cost(candidate):
        occurrences = recent_exact.count(candidate)
        family = family_set(candidate)
        overlaps = sum(bool(family & old) for old in recent_family)
        # Penalize identical topic most, then recognizable same setting.
        return (occurrences, overlaps)

    scored = {c: cost(c) for c in eligible}
    best = min(scored.values())
    finalists = [c for c in eligible if scored[c] == best]
    if requested in finalists:
        chosen = requested
    else:
        # All alternatives remain in the same approved group and time of day.
        key = f"shiori-variety-v1:{date.isoformat()}:{slot}:{group}"
        digest = hashlib.sha256(key.encode("utf-8")).digest()
        chosen = finalists[int.from_bytes(digest[:8], "big") % len(finalists)]
    return {"topic_group": group, "theme": chosen}


def select_diverse_topic(now, slot, config, preferred=None):
    """A deterministic bounded-memory replay; no private data or network writes.

    Reproducing the preceding editorial selections gives consistent output for
    retries/fallbacks without storing or disclosing actual Threads post text.
    """
    if slot not in SLOTS or not isinstance(now, dt.datetime):
        raise ValueError("Invalid scheduled slot")
    groups = config["topic_groups"]
    policy = config["editorial_limits"]
    if preferred is not None:
        if (not isinstance(preferred, dict)
                or set(preferred) != {"theme", "topic_group"}
                or preferred["theme"] not in groups.get(preferred["topic_group"], [])):
            raise ValueError("Unapproved external topic")
    # Replay from a fixed launch epoch. A moving seven-day cutoff caused
    # previous days to be recalculated differently at the boundary.
    start = FIRST_SLOT
    history = []
    current_day = start
    while current_day <= now.date():
        for candidate_slot in SLOTS:
            if current_day == now.date() and SLOT_HOURS[candidate_slot] > SLOT_HOURS[slot]:
                break
            base = select_editorial_topic(current_day, candidate_slot, groups, policy)
            if current_day == now.date() and candidate_slot == slot and preferred is not None:
                base = preferred
            is_verified_signal = (
                preferred is not None
                and current_day == now.date() and candidate_slot == slot
            )
            chosen = _pick(
                base, groups[base["topic_group"]], history, current_day,
                candidate_slot, allow_preferred_out_of_daypart=is_verified_signal
            )
            history.append((base["topic_group"], chosen["theme"]))
            if len(history) > COOLDOWN_EXACT_SLOTS:
                del history[:-COOLDOWN_EXACT_SLOTS]
            if current_day == now.date() and candidate_slot == slot:
                return chosen
        current_day += dt.timedelta(days=1)
    raise ValueError("Could not select an approved topic")
