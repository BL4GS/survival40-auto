import hashlib
import unittest
import urllib.error
from unittest.mock import patch
from scripts.threads.ledger import GithubLedger, LedgerError


class GithubLedgerTests(unittest.TestCase):
    def setUp(self):
        self.ledger = GithubLedger("BL4GS/survival40-auto", "state/threads-ledger", "TEST_GITHUB_TOKEN")
        self.digest = hashlib.sha256("hi".encode()).hexdigest()

    def test_path(self):
        self.assertEqual(self.ledger.filename("2026-10-11-evening"),
                         "threads-ledger/2026/10/2026-10-11-evening.json")
        for invalid in ("../foo", "2026-10-11-article", "2026-10-11-evening/../oops"):
            with self.assertRaises(ValueError):
                self.ledger.filename(invalid)

    def test_existing_reservation_skips(self):
        with patch.object(self.ledger, "_call", return_value={"sha": "abc"}) as call:
            self.assertFalse(self.ledger.reserve("2026-10-11-evening", "123", self.digest))
            call.assert_called_once()

    def test_reserve_before_publish(self):
        with patch.object(self.ledger, "_call", side_effect=[None, {"content": {"sha": "123"}}]) as call:
            self.assertTrue(self.ledger.reserve("2026-10-11-evening", "123", self.digest))
            self.assertEqual(call.call_args_list[0].args[0], "GET")
            self.assertEqual(call.call_args_list[1].args[0], "PUT")
            self.assertNotIn("TEST_GITHUB_TOKEN", str(call.call_args_list))

    def test_ambiguous_reservation_does_not_publish(self):
        with patch.object(self.ledger, "_call", side_effect=[None, LedgerError("GitHub unavailable")]):
            with self.assertRaises(LedgerError):
                self.ledger.reserve("2026-10-11-morning", "123", self.digest)

    def test_wrong_branch_rejected(self):
        with self.assertRaises(ValueError):
            GithubLedger("BL4GS/survival40-auto", "main", "TEST_GITHUB_TOKEN")


if __name__ == "__main__":
    unittest.main()
