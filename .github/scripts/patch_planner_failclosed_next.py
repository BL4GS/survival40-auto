"""Proposed NEXT-release patch ONLY: remove fabricated skincare fallback.

Do NOT call this from the v0.19.21 release workflow. It is intentionally
staged for a later reviewed release after live backup and updater verification.
"""
from pathlib import Path
import re

TARGET = Path("survival40-auto/survival40-auto.php")

def transform(source):
    anchor = r"""        if (!is_array($data)) {
            $fallback_title = '40代男性のスキンケア基本｜老け見えを防ぐ最低限の習慣';"""
    if source.count(anchor) != 1:
        raise ValueError("Expected exactly one known skincare fallback in reviewed plugin")
    expression = re.compile(
        r"        if \(!is_array\(\$data\)\) \{\n"
        r"            \$fallback_title = '40代男性のスキンケア基本｜老け見えを防ぐ最低限の習慣';\n"
        r".*?\n"
        r"        \}\n\n"
        r"        \$title = sanitize_text_field\(\$data\['title'\]\);",
        re.S,
    )
    replacement = """        if (!is_array($data)) {
            // Never invent a repeatable product-based article when planning fails.
            // Existing callers log the WP_Error and halt this automatic cycle.
            return new WP_Error(
                's40_plan_unavailable',
                '根拠のある記事企画を取得できず、自動生成を停止しました。次回のサイクルで再試行します。'
            );
        }

        $title = sanitize_text_field($data['title']);"""
    new, count = expression.subn(lambda _: replacement, source, count=1)
    if count != 1:
        raise ValueError("Reviewed planner block changed; patch refused")
    if "'amazon_query' => 'メンズ オールインワン 保湿'" in new:
        raise ValueError("Unsafe fallback still present after patch")
    return new


def main():
    before = TARGET.read_text(encoding="utf-8")
    after = transform(before)
    TARGET.write_text(after, encoding="utf-8")
    print("STAGED: planner now fails closed on unusable Gemini JSON. No other code patched.")


if __name__ == "__main__":
    main()
