"""Offline tests only. Never fetch live credentials or call Meta."""
import datetime as dt
import unittest
from scripts.threads.token_preflight import (
    TokenPreflightError, validate_debug_response, validate_profile,
    EXPECTED_APP_ID, MIN_REMAINING_SECONDS,
)


class TokenPreflightTests(unittest.TestCase):
    def setUp(self):
        self.now = 1_800_000_000
        self.user_id = "123456789"
        self.valid = {
            "data": {
                "is_valid": True,
                "user_id": self.user_id,
                "app_id": EXPECTED_APP_ID,
                "scopes": ["threads_basic", "threads_content_publish"],
                "expires_at": self.now + 20 * 86400,
                "data_access_expires_at": self.now + 30 * 86400,
            }
        }

    def test_valid(self):
        self.assertIsInstance(validate_debug_response(
            self.valid, self.user_id, self.now), dt.datetime)

    def test_wrong_account(self):
        with self.assertRaises(TokenPreflightError):
            validate_profile({"id": "other", "username": "survival40_jp"}, self.user_id)
        with self.assertRaises(TokenPreflightError):
            validate_profile({"id": self.user_id, "username": "other"}, self.user_id)

    def test_missing_publish_scope(self):
        self.valid["data"]["scopes"] = ["threads_basic"]
        with self.assertRaises(TokenPreflightError):
            validate_debug_response(self.valid, self.user_id, self.now)

    def test_unknown_or_expired_lifetime(self):
        for value in (None, 0, self.now - 1, self.now + MIN_REMAINING_SECONDS):
            with self.subTest(value=value):
                self.valid["data"]["expires_at"] = value
                with self.assertRaises(TokenPreflightError):
                    validate_debug_response(self.valid, self.user_id, self.now)

    def test_invalid_debugger_response(self):
        for body in ({}, {"data": []}, {"data": {"is_valid": False}}):
            with self.subTest(body=body):
                with self.assertRaises(TokenPreflightError):
                    validate_debug_response(body, self.user_id, self.now)

    def test_debugger_identity_and_app_mismatch(self):
        for field, wrong in (("user_id", "222"), ("app_id", "123")):
            with self.subTest(field=field):
                sample = {"data": dict(self.valid["data"])}
                sample["data"][field] = wrong
                with self.assertRaises(TokenPreflightError):
                    validate_debug_response(sample, self.user_id, self.now)

    def test_data_access_expiry(self):
        self.valid["data"]["data_access_expires_at"] = self.now + 1
        with self.assertRaises(TokenPreflightError):
            validate_debug_response(self.valid, self.user_id, self.now)

    def test_no_bypass_without_scopes(self):
        self.valid["data"].pop("scopes")
        with self.assertRaises(TokenPreflightError):
            validate_debug_response(self.valid, self.user_id, self.now)


if __name__ == "__main__":
    unittest.main()
