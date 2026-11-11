"""Pure offline checks. All observations are synthetic."""
import copy
import unittest

from scripts.analytics.funnel_audit import AuditInputError, audit_funnel


EXAMPLE = {
    "ga4": {"start_date": "2026-10-01", "end_date": "2026-10-12", "source_medium": [
        {"key": "(direct) / (none)", "sessions": 4},
        {"key": "l.threads.com / referral", "sessions": 2},
        {"key": "pinterest.lightning.force.com / referral", "sessions": 3},
        {"key": "m.facebook.com / referral", "sessions": 1},
    ]},
    "a8": {"start_date": "2026-10-01", "end_date": "2026-10-13", "site_filtered": True,
           "impressions": 20, "clicks": 5, "results": 0},
}


class FunnelAuditTest(unittest.TestCase):
    def test_pinterest_lookalike_is_unclassified(self):
        result = audit_funnel(EXAMPLE)
        self.assertEqual(result["ga4"]["source_groups"]["unclassified_source"], 3)
        self.assertNotIn("pinterest", result["ga4"]["source_groups"])

    def test_totals_are_not_mistaken_for_conversions(self):
        result = audit_funnel(EXAMPLE)
        self.assertEqual(result["ga4"]["sessions_in_supplied_rows"], 10)
        self.assertEqual(result["affiliate"]["ctr_percent"], 25.0)
        self.assertEqual(result["affiliate"]["state"], "zero_recorded_results")
        self.assertIsNone(result["cross_system_conversion_rate"])
        self.assertFalse(result["periods_match"])

    def test_even_matching_periods_do_not_prove_attribution(self):
        sample = copy.deepcopy(EXAMPLE)
        sample["a8"]["end_date"] = "2026-10-12"
        sample["a8"]["results"] = 1
        result = audit_funnel(sample)
        self.assertTrue(result["periods_match"])
        self.assertIsNone(result["cross_system_conversion_rate"])
        self.assertEqual(result["affiliate"]["state"], "recorded_results")

    def test_unfiltered_a8_cannot_be_attributed_to_site(self):
        sample = copy.deepcopy(EXAMPLE)
        sample["a8"]["site_filtered"] = False
        result = audit_funnel(sample)
        self.assertFalse(result["scope_match"])
        self.assertTrue(any("not site-filtered" in w for w in result["warnings"]))

    def test_a8_not_supplied_is_not_zero(self):
        result = audit_funnel({"ga4": EXAMPLE["ga4"]})
        self.assertEqual(result["affiliate"]["state"], "not_supplied")

    def test_zero_impressions_and_positive_clicks(self):
        sample = copy.deepcopy(EXAMPLE)
        sample["a8"]["impressions"] = 0
        sample["a8"]["clicks"] = 1
        result = audit_funnel(sample)
        self.assertIsNone(result["affiliate"]["ctr_percent"])
        self.assertTrue(any("zero impressions" in w for w in result["warnings"]))

    def test_ctr_can_exceed_one_hundred(self):
        sample = copy.deepcopy(EXAMPLE)
        sample["a8"]["clicks"] = 22
        result = audit_funnel(sample)
        self.assertEqual(result["affiliate"]["ctr_percent"], 110)
        self.assertTrue(any("exceed impressions" in w for w in result["warnings"]))

    def test_bad_counts_rejected(self):
        for value in (-1, True, 2.0, "2", None):
            sample = copy.deepcopy(EXAMPLE)
            sample["a8"]["clicks"] = value
            with self.subTest(value=value), self.assertRaises(AuditInputError):
                audit_funnel(sample)

    def test_bad_window_rejected(self):
        sample = copy.deepcopy(EXAMPLE)
        sample["ga4"]["end_date"] = "2026-09-30"
        with self.assertRaises(AuditInputError):
            audit_funnel(sample)

    def test_duplicate_sources_rejected(self):
        sample = copy.deepcopy(EXAMPLE)
        sample["ga4"]["source_medium"].append({"key": "m.facebook.com / referral", "sessions": 4})
        with self.assertRaises(AuditInputError):
            audit_funnel(sample)

    def test_google_organic_is_not_mislabeled_as_referral(self):
        sample = copy.deepcopy(EXAMPLE)
        sample["ga4"]["source_medium"].append({"key": "google / organic", "sessions": 7})
        result = audit_funnel(sample)
        self.assertEqual(result["ga4"]["source_groups"]["organic_search"], 7)
        self.assertNotIn("unclassified_referral", result["ga4"]["source_groups"])

    def test_partial_ga4_rows_warn(self):
        sample = copy.deepcopy(EXAMPLE)
        sample["ga4"]["truncated"] = True
        self.assertTrue(any("truncated" in w for w in audit_funnel(sample)["warnings"]))

    def test_approved_pinterest_host_recognized(self):
        sample = copy.deepcopy(EXAMPLE)
        sample["ga4"]["source_medium"].append({"key": "www.pinterest.com / referral", "sessions": 1})
        self.assertEqual(audit_funnel(sample)["ga4"]["source_groups"]["pinterest"], 1)

    def test_missing_site_scope_rejected(self):
        sample = copy.deepcopy(EXAMPLE)
        del sample["a8"]["site_filtered"]
        with self.assertRaises(AuditInputError):
            audit_funnel(sample)


if __name__ == "__main__":
    unittest.main()
