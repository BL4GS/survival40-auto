"""Credential-free regression tests for committed OG/Instagram/Pinterest PNGs."""
import struct
import tempfile
import unittest
from pathlib import Path

from scripts.social import check_local_og_assets as mod


def fake_png(width, height):
    return (mod.PNG_SIGNATURE + b"\x00\x00\x00\rIHDR"
            + struct.pack(">II", width, height))


class LocalOGAssetsTests(unittest.TestCase):
    def test_valid_and_invalid_ihdr(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "test.png"
            self.assertIsNone(mod.png_size(path))
            path.write_bytes(fake_png(1200, 630))
            self.assertEqual(mod.png_size(path), (1200, 630))
            for invalid in (b"", b"not a png", fake_png(0, 630),
                            fake_png(50001, 630)):
                path.write_bytes(invalid)
                with self.assertRaises(ValueError):
                    mod.png_size(path)

    def test_fixed_scope_and_missing_assets_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            result = mod.audit(temp)
        self.assertEqual([row["article_id"] for row in result["items"]],
                         [387, 389, 438, 596])
        self.assertTrue(result["read_only"])
        self.assertTrue(result["local_repository_assets_only"])
        self.assertFalse(result["live_og_image_verified"])
        self.assertFalse(result["public_image_http_retrieval_verified"])
        self.assertFalse(result["google_discover_appearance_verified"])
        self.assertTrue(all(
            asset["status"] == "ABSENT"
            for row in result["items"] for asset in row["assets"].values()
        ))

    def test_article_596_actual_committed_assets(self):
        # These are GitHub repository blobs, not live WordPress OG declarations.
        rows = mod.audit()["items"]
        row = next(row for row in rows if row["article_id"] == 596)
        self.assertEqual((row["assets"]["og"]["width"],
                          row["assets"]["og"]["height"]), (1200, 630))
        self.assertEqual(row["assets"]["og"]["status"], "WIDTH_GE_1200")
        self.assertEqual((row["assets"]["instagram"]["width"],
                          row["assets"]["instagram"]["height"]), (1080, 1350))
        self.assertEqual(row["assets"]["instagram"]["status"], "WIDTH_LT_1200")
        self.assertEqual((row["assets"]["pinterest"]["width"],
                          row["assets"]["pinterest"]["height"]), (1000, 1500))


if __name__ == "__main__":
    unittest.main()
