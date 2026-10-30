#!/usr/bin/env python3
"""Read-only lint for accidentally double-escaped HTML in WordPress draft bodies.

Accepts a local JSON export (WordPress REST `content.raw` or `{ "html": ... }`).
No WordPress access, credentials, publishing, or automatic repairs.
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Deliberately narrow: only patterns that strongly suggest serialized HTML
# was pasted into an HTML field without unescaping. Normal prose is ignored.
_ESCAPED_NEWLINE_BEFORE_TAG = re.compile(
    r"\\n(?=\s*</?(?:h[1-6]|p|ul|ol|li|div|section|blockquote|a)\b)", re.I
)
_ESCAPED_ATTRIBUTE_QUOTE = re.compile(
    r"\b(?:href|src|class|id|style|title|alt)=\\\"", re.I
)
_CODE_SPAN = re.compile(r"<(pre|code)\b[^>]*>.*?</\1\s*>", re.I | re.S)


def extract_raw_html(payload):
    """Return the raw post body, never the WordPress rendered HTML field."""
    if not isinstance(payload, dict):
        raise ValueError("Expected a JSON object")
    value = payload.get("html")
    if not isinstance(value, str):
        content = payload.get("content")
        value = content.get("raw") if isinstance(content, dict) else content
    if not isinstance(value, str):
        raise ValueError("Expected html string or content.raw string")
    return value


def lint_html(raw_html):
    """Report narrow double-escape indicators with offsets, not article text."""
    if not isinstance(raw_html, str):
        raise TypeError("raw_html must be a string")
    # Mask literal code examples so sample markup is not treated as article HTML.
    masked = _CODE_SPAN.sub(lambda match: " " * len(match.group()), raw_html)
    findings = []
    for code, pattern in (
        ("literal_backslash_n_before_html_tag", _ESCAPED_NEWLINE_BEFORE_TAG),
        ("literal_backslash_quote_in_html_attribute", _ESCAPED_ATTRIBUTE_QUOTE),
    ):
        for match in pattern.finditer(masked):
            findings.append({"code": code, "offset": match.start()})
    return sorted(findings, key=lambda finding: finding["offset"])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("json_file", help="Local WordPress REST JSON export; '-' for stdin")
    args = parser.parse_args(argv)
    try:
        raw = sys.stdin.read() if args.json_file == "-" else Path(args.json_file).read_text(encoding="utf-8")
        payload = json.loads(raw)
        findings = lint_html(extract_raw_html(payload))
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps({"ok": not findings, "findings": findings}, ensure_ascii=False))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
