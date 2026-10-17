"""Synthetic, offline A8 CSV checks; no real transactions are stored."""
import csv
import io
import unittest

from scripts.analytics.a8_csv_audit import (
    A8CsvError, decode_csv, parse_yen, summarize_outcomes,
)

SITE = "40代からの生存戦略"
ROWS = [
    {"サイト名": SITE, "ステータス種別": "未確定", "成果報酬額": "1,500", "注文ID": "private-order-1"},
    {"サイト名": SITE, "ステータス種別": "確定", "成果報酬額": "500", "注文ID": "private-order-2"},
    {"サイト名": SITE, "ステータス種別": "キャンセル", "成果報酬額": "350", "注文ID": "private-order-3"},
    {"サイト名": "別のサイト", "ステータス種別": "確定", "成果報酬額": "99999", "注文ID": "private-order-4"},
]


def fixture(rows, encoding="utf-8-sig", fields=None):
    buffer = io.StringIO()
    fields = fields or ["サイト名", "ステータス種別", "成果報酬額", "注文ID"]
    writer = csv.DictWriter(buffer, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode(encoding)


class A8CsvTest(unittest.TestCase):
    def test_site_only_and_statuses(self):
        result = summarize_outcomes(fixture(ROWS), exact_site=SITE)
        self.assertEqual(result["selected_outcome_rows"], 3)
        self.assertEqual(result["other_site_rows_ignored"], 1)
        self.assertEqual(result["status_counts"],
                         {"pending": 1, "confirmed": 1, "cancelled": 1})
        self.assertEqual(result["reported_reward_yen_by_status"],
                         {"pending": 1500, "confirmed": 500, "cancelled": 350})
        self.assertEqual(result["confirmed_reward_yen_in_export"], 500)
        self.assertNotIn("private-order", str(result))

    def test_cp932_supported(self):
        result = summarize_outcomes(fixture(ROWS, "cp932"), exact_site=SITE)
        self.assertEqual(result["encoding_read"], "cp932")

    def test_no_site_column_rejected(self):
        data = fixture([{"ステータス種別": "確定", "成果報酬額": "10"}],
                       fields=["ステータス種別", "成果報酬額"])
        with self.assertRaises(A8CsvError):
            summarize_outcomes(data, exact_site=SITE)

    def test_custom_mapping(self):
        data = fixture([{"登録サイト": SITE, "状態": "確定", "報酬": "100"}],
                       fields=["登録サイト", "状態", "報酬"])
        result = summarize_outcomes(data, exact_site=SITE, site_field="登録サイト",
                                    status_field="状態", reward_field="報酬")
        self.assertEqual(result["confirmed_reward_yen_in_export"], 100)

    def test_other_site_only_rejected(self):
        with self.assertRaises(A8CsvError):
            summarize_outcomes(fixture(ROWS[3:]), exact_site=SITE)

    def test_empty_export_is_not_unknown(self):
        result = summarize_outcomes(fixture([]), exact_site=SITE)
        self.assertEqual(result["selected_outcome_rows"], 0)

    def test_unknown_status_rejected(self):
        row = dict(ROWS[0], **{"ステータス種別": "不明"})
        with self.assertRaises(A8CsvError):
            summarize_outcomes(fixture([row]), exact_site=SITE)

    def test_duplicate_headers_rejected(self):
        data = "サイト名,サイト名,ステータス種別,成果報酬額\n".encode()
        with self.assertRaises(A8CsvError):
            summarize_outcomes(data, exact_site=SITE)

    def test_invalid_amounts_rejected(self):
        for amount in ("-10", "-", "1.5", "", "unknown", "NaN", "Infinity"):
            with self.subTest(amount=amount), self.assertRaises(A8CsvError):
                parse_yen(amount)

    def test_yen_formats(self):
        for value in ("￥1,500", "¥1500", "1500円", "1,500"):
            with self.subTest(value=value):
                self.assertEqual(parse_yen(value), 1500)

    def test_excess_columns_rejected(self):
        data = (f"サイト名,ステータス種別,成果報酬額\n{SITE},確定,10,extra\n").encode()
        with self.assertRaises(A8CsvError):
            summarize_outcomes(data, exact_site=SITE)

    def test_excel_xlsx_rejected(self):
        with self.assertRaises(A8CsvError):
            decode_csv(b"PK\x03\x04hello")

    def test_excel_xls_rejected(self):
        with self.assertRaises(A8CsvError):
            decode_csv(b"\xd0\xcf\x11\xe0test")

    def test_empty_bytes_rejected(self):
        with self.assertRaises(A8CsvError):
            summarize_outcomes(b"", exact_site=SITE)

    def test_blank_site_rejected(self):
        with self.assertRaises(A8CsvError):
            summarize_outcomes(fixture(ROWS), exact_site="")

    def test_case_sensitive_site(self):
        with self.assertRaises(A8CsvError):
            summarize_outcomes(fixture(ROWS), exact_site=SITE+"x")

    def test_other_site_bad_status_not_used(self):
        row = dict(ROWS[3], **{"ステータス種別": "unexpected"})
        result = summarize_outcomes(fixture(ROWS[:3]+[row]), exact_site=SITE)
        self.assertEqual(result["selected_outcome_rows"], 3)
