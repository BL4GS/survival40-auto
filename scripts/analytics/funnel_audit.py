"""Read-only audit of Survival40 GA4 and A8 aggregate observations.

No account access, tracking changes or publishing. Overall totals cannot
establish individual visitor-to-affiliate attribution.
"""
import argparse
import datetime as dt
import json
from collections import defaultdict
from pathlib import Path


class AuditInputError(ValueError):
    pass


def _window(source, label):
    if not isinstance(source, dict):
        raise AuditInputError(f"{label} must be an object")
    try:
        start = dt.date.fromisoformat(source["start_date"])
        end = dt.date.fromisoformat(source["end_date"])
    except (KeyError, TypeError, ValueError):
        raise AuditInputError(f"{label} requires ISO calendar dates") from None
    if start > end:
        raise AuditInputError(f"{label} start_date follows end_date")
    return (start.isoformat(), end.isoformat())


def _count(value, label):
    if type(value) is not int or value < 0:
        raise AuditInputError(f"{label} must be a nonnegative integer")
    return value


def _source_group(source_medium):
    """Explicit host allowlists; never use brand-name substring heuristics."""
    source = source_medium.strip().lower().split(" / ", 1)[0]
    if source in ("l.threads.com", "threads.net", "www.threads.net", "threads.com", "www.threads.com"):
        return "threads"
    if source in ("facebook.com", "m.facebook.com", "l.facebook.com", "www.facebook.com", "lm.facebook.com"):
        return "facebook"
    if source in ("instagram.com", "www.instagram.com", "l.instagram.com"):
        return "instagram"
    if source in ("pinterest.com", "www.pinterest.com", "pin.it"):
        return "pinterest"
    if source == "(direct)":
        return "direct_or_unattributed"
    if source_medium.strip().lower() in ("google / organic", "bing / organic", "yahoo / organic", "duckduckgo / organic"):
        return "organic_search"
    return "unclassified_source"


def audit_funnel(payload):
    """Compute evidence-based aggregates; never infer a cross-system conversion."""
    if not isinstance(payload, dict) or "ga4" not in payload:
        raise AuditInputError("Expected a ga4 object")
    ga4 = payload["ga4"]
    ga4_window = _window(ga4, "ga4")
    rows = ga4.get("source_medium")
    if not isinstance(rows, list):
        raise AuditInputError("ga4.source_medium must be a list")
    seen = set()
    traffic = defaultdict(int)
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise AuditInputError(f"ga4 row {index} must be an object")
        label = row.get("key")
        if not isinstance(label, str) or not label.strip():
            raise AuditInputError(f"ga4 row {index} has no sourceMedium key")
        if label in seen:
            raise AuditInputError("Repeated sourceMedium row; aggregate before auditing")
        seen.add(label)
        traffic[_source_group(label)] += _count(row.get("sessions"), "sessions")
    total = sum(traffic.values())
    warnings = ["GA4 sessions are not unique people; direct traffic has unknown origin.",
                "Social referrals do not establish an affiliate purchase or causal attribution."]
    if ga4.get("truncated") is True:
        warnings.append("GA4 row list is truncated: observed sessions exclude omitted rows.")
    elif ga4.get("truncated") is not False:
        warnings.append("GA4 row completeness was not provided; sums may omit rows.")
    result = {"ga4": {"window": list(ga4_window), "sessions_in_supplied_rows": total,
                      "source_groups": dict(sorted(traffic.items()))},
              "affiliate": {"state": "not_supplied"},
              "periods_match": None, "scope_match": None,
              "cross_system_conversion_rate": None, "warnings": warnings}
    if "a8" not in payload:
        warnings.append("A8 data unavailable: affiliate outcomes cannot be evaluated.")
        return result

    a8 = payload["a8"]
    a8_window = _window(a8, "a8")
    impressions = _count(a8.get("impressions"), "a8.impressions")
    clicks = _count(a8.get("clicks"), "a8.clicks")
    outcomes = _count(a8.get("results"), "a8.results")
    if type(a8.get("site_filtered")) is not bool:
        raise AuditInputError("a8.site_filtered must be a boolean")
    if clicks < outcomes:
        warnings.append("A8 outcomes exceed clicks; check report definitions and time lags.")
    if impressions == 0 and clicks > 0:
        warnings.append("A8 clicks despite zero impressions; check reporting measurement.")
    if impressions and clicks > impressions:
        warnings.append("A8 clicks exceed impressions: CTR can exceed 100%; do not infer unique people.")
    result["affiliate"] = {
        "state": "recorded_results" if outcomes else "zero_recorded_results",
        "window": list(a8_window), "impressions": impressions, "clicks": clicks,
        "results": outcomes,
        "ctr_percent": round(clicks / impressions * 100, 2) if impressions else None,
        "site_filtered": a8["site_filtered"],
    }
    result["periods_match"] = a8_window == ga4_window
    result["scope_match"] = a8["site_filtered"]
    if not result["periods_match"]:
        warnings.append("GA4 and A8 date ranges differ: counts are not directly comparable.")
    if not result["scope_match"]:
        warnings.append("A8 report is not site-filtered: cannot assign clicks to Survival40.")
    warnings.append("A8 clicks can include repeat clicks, test traffic or automated requests; classification is unknown.")
    warnings.append("A8 result counts are not GA4 keyEvents or confirmed payouts.")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="local JSON with aggregate GA4/A8 metrics")
    args = parser.parse_args(argv)
    data = json.loads(args.input.read_text(encoding="utf-8"))
    print(json.dumps(audit_funnel(data), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
