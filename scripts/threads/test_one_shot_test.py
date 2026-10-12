"""Offline, secret-free one-shot publishing safety tests."""
import sys
import types
import unittest
from unittest.mock import MagicMock, patch

from scripts.threads.one_shot_test import (
    CONFIRM_PHRASE, TEST_KEY, TEST_TEXT, REPOSITORY,
    assert_approval, live_publish,
)
from scripts.threads.ledger import GithubLedger, LedgerError


class OneShotTests(unittest.TestCase):
    def setUp(self):
        self.env = {
            "THREADS_TEST_PUBLISH_ENABLED": "true",
            "THREADS_TEST_ACK": CONFIRM_PHRASE,
            "GITHUB_ACTOR": "BL4GS",
            "GITHUB_REF": "refs/heads/main",
            "GITHUB_REPOSITORY": REPOSITORY,
            "GITHUB_EVENT_NAME": "workflow_dispatch",
            "THREADS_ACCESS_TOKEN": "FAKE_API_TOKEN_FOR_UNIT_TESTS",
            "THREADS_USER_ID": "123",
            "GITHUB_TOKEN": "FAKE_GH_TOKEN_FOR_UNIT_TESTS",
        }

    def test_locked_by_default_and_rejects_every_wrong_gate(self):
        for key in ("THREADS_TEST_PUBLISH_ENABLED", "THREADS_TEST_ACK",
                    "GITHUB_ACTOR", "GITHUB_REF",
                    "GITHUB_REPOSITORY", "GITHUB_EVENT_NAME"):
            with self.subTest(key=key):
                wrong = dict(self.env)
                wrong.pop(key)
                with self.assertRaises(ValueError):
                    assert_approval(wrong)

    def test_disabled_never_calls_meta_or_ledger(self):
        with patch("scripts.threads.one_shot_test.MetaThreadsClient") as client:
            with patch("scripts.threads.one_shot_test.GithubLedger") as ledger:
                with self.assertRaises(ValueError):
                    live_publish({})
                client.assert_not_called()
                ledger.assert_not_called()

    def test_unique_permanent_test_key(self):
        self.assertEqual(GithubLedger.filename(TEST_KEY),
                         "threads-ledger/tests/test-20261013-v1.json")
        with self.assertRaises(ValueError):
            GithubLedger.filename("../test-20261013-v1")

    def run_with_fake_token_preflight(self, reserved):
        fake = types.ModuleType("scripts.threads.token_preflight")
        events = []
        fake.safe_get = lambda path, token, params: (
            events.append("get:" + path) or
            ({"id": "123", "username": "survival40_jp"} if path == "/me"
             else {"data": {"is_valid": True}})
        )
        fake.validate_profile = lambda *args: events.append("validate_profile")
        fake.validate_debug_response = lambda *args: events.append("validate_debug")
        with patch.dict(sys.modules, {"scripts.threads.token_preflight": fake}):
            with patch("scripts.threads.one_shot_test.MetaThreadsClient") as client:
                with patch("scripts.threads.one_shot_test.GithubLedger") as ledger:
                    client.return_value.verify_account.side_effect = (
                        lambda *_: events.append("client.verify_account"))
                    ledger.return_value.reserve.side_effect = (
                        lambda *_: events.append("reserve") or reserved)
                    client.return_value.create_text_container.side_effect = (
                        lambda *_: events.append("container") or "1234")
                    client.return_value.publish_container.side_effect = (
                        lambda *_: events.append("publish") or "5678")
                    ledger.return_value.mark_published.side_effect = (
                        lambda *_: events.append("record"))
                    if reserved:
                        live_publish(self.env)
                    else:
                        with self.assertRaises(LedgerError):
                            live_publish(self.env)
                    return events, client, ledger

    def test_ledger_precedes_every_meta_post(self):
        events, client, ledger = self.run_with_fake_token_preflight(True)
        self.assertEqual(events, [
            "get:/me", "validate_profile", "get:/debug_token",
            "validate_debug", "client.verify_account",
            "reserve", "container", "publish", "record",
        ])
        client.return_value.create_text_container.assert_called_once_with(TEST_TEXT)
        ledger.return_value.reserve.assert_called_once()

    def test_already_reserved_never_posts(self):
        events, client, ledger = self.run_with_fake_token_preflight(False)
        self.assertEqual(events[-1], "reserve")
        client.return_value.create_text_container.assert_not_called()
        client.return_value.publish_container.assert_not_called()


if __name__ == "__main__":
    unittest.main()
