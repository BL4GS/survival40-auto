"""Offline, read-only A8 outcome CSV summarizer for an exact registered site.

Neither CSV rows nor order identifiers are sent to any service or returned.
The report period and column definitions must be verified on A8 separately.
"""
import argparse
import csv
import io
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path


class A8CsvError(ValueError):
    pass


_STATUSES = {"未確定": "pending", "確定": "confirmed", "キャンセル": "cancelled"}


def decode_csv(data):
    if data.startswith((b"PK\x03\x04", b"\xd0\xcf\x11\xe0")):
        raise A8CsvError("Excel or binary file is not CSV")
    for encoding in ("utf-8-sig", "cp932"):
        try:
            text = data.decode(encoding)
            if "\x00" in text:
                raise A8CsvError("Binary file is not CSV")
            return text, encoding
        except UnicodeDecodeError:
            continue
    raise A8CsvError("Cannot decode CSV as UTF-8 or CP932")


def parse_yen(value):
    if not isinstance(value, str):
        raise A8CsvError("Missing monetary amount")
    cleaned = value.strip().replace(",", "").replace("￥", "").replace("¥", "")
    if cleaned.endswith("円"):
        cleaned = cleaned[:-1]
    if not cleaned or cleaned in ("-", "－"):
        raise A8CsvError("Blank or unreported monetary amount")
    try:
        amount = Decimal(cleaned)
    except InvalidOperation:
        raise A8CsvError("Invalid monetary amount") from None
    if not amount.is_finite() or amount < 0 or amount != amount.to_integral_value():
        raise A8CsvError("Expected nonnegative whole-yen amount")
    return amount


def summarize_outcomes(data, *, exact_site, site_field="サイト名",
                       status_field="ステータス種別", reward_field="成果報酬額"):
    """Summarize one occurrence-detail snapshot. Never add overlapping exports."""
    if not isinstance(data, bytes) or not data:
        raise A8CsvError("Expected nonempty CSV bytes")
    if not isinstance(exact_site, str) or not exact_site or exact_site.strip() != exact_site:
        raise A8CsvError("Provide exact, nonblank registered site name")
    fields = [site_field, status_field, reward_field]
    if any(not isinstance(f, str) or not f for f in fields) or len(set(fields)) != 3:
        raise A8CsvError("Site, status and reward columns must be distinct")
    text, encoding = decode_csv(data)
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if not reader.fieldnames:
        raise A8CsvError("CSV has no header")
    columns = [name.strip() if isinstance(name, str) else name for name in reader.fieldnames]
    if None in columns or len(columns) != len(set(columns)):
        raise A8CsvError("Duplicate or malformed column headers")
    header = dict(zip(columns, reader.fieldnames))
    for name in fields:
        if name not in header:
            raise A8CsvError(f"Required column missing: {name}; explicitly map actual headers")
    counts = {v: 0 for v in _STATUSES.values()}
    amounts = {v: Decimal(0) for v in _STATUSES.values()}
    selected = 0
    ignored = 0
    for line_no, row in enumerate(reader, start=2):
        if None in row or any(row.get(header[f]) is None for f in fields):
            raise A8CsvError(f"Malformed CSV row at line {line_no}")
        if row[header[site_field]].strip() != exact_site:
            ignored += 1
            continue
        status = row[header[status_field]].strip()
        if status not in _STATUSES:
            raise A8CsvError(f"Unrecognized outcome status at line {line_no}")
        money = parse_yen(row[header[reward_field]])
        key = _STATUSES[status]
        counts[key] += 1
        amounts[key] += money
        selected += 1
    if selected == 0 and ignored:
        raise A8CsvError("No exact site rows: check the registered site label")
    return {
        "site_scope": "exact_match",
        "selected_outcome_rows": selected,
        "other_site_rows_ignored": ignored,
        "status_counts": counts,
        "reported_reward_yen_by_status": {k: int(v) for k, v in amounts.items()},
        "confirmed_reward_yen_in_export": int(amounts["confirmed"]),
        "source": "a8_occurrence_detail_csv",
        "encoding_read": encoding,
        "limitations": [
            "CSV is an outcome-detail snapshot, not a click or impression report.",
            "CSV alone does not prove report window or selected filtering settings.",
            "Do not sum overlapping snapshots or confirmation-detail exports.",
            "Rows are outcomes, not distinct buyers or confirmed bank payments.",
            "Validate the chosen monetary column against A8's report definition.",
            "Zero rows means only that this export contains no matching outcome rows.",
        ],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--site", required=True, help="exact A8 registered site name")
    parser.add_argument("--site-field", default="サイト名")
    parser.add_argument("--status-field", default="ステータス種別")
    parser.add_argument("--reward-field", default="成果報酬額")
    args = parser.parse_args(argv)
    result = summarize_outcomes(
        args.csv.read_bytes(), exact_site=args.site,
        site_field=args.site_field, status_field=args.status_field,
        reward_field=args.reward_field,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
