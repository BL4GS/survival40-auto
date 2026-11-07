"""Stage a timing-only fix for Survival40 Auto's mobile Shiori narrator.

Apply after plugin version 0.19.20 is reconstructed, before subsequent version bump.
DOES NOT publish releases, change ads, posts, WordPress or WAF.
"""
from pathlib import Path

SOURCE = Path("survival40-auto/survival40-auto.php")
OLD = "? Math.min(window.innerHeight*.45,350)"
NEW = "? Math.min(window.innerHeight*.72,580)"


def apply(source: str) -> str:
    """Move mobile heading trigger from mid-screen to the bottom-third of view.

    A 844px-tall phone changes at ~580px rather than ~350px from viewport top.
    Higher threshold = earlier transition during downward scrolling. Desktop
    threshold, JS messages/states, topic detection, scroll handler are unchanged.
    """
    if source.count(OLD) != 1:
        raise ValueError("Expected exactly one existing mobile switch threshold")
    if source.count("var switchLine=mobile.matches") != 1:
        raise ValueError("Expected single Shiori switchLine variable")
    if source.count("getBoundingClientRect().top <= switchLine") != 1:
        raise ValueError("Expected single Shiori heading threshold use")
    return source.replace(OLD, NEW, 1)


if __name__ == "__main__":
    current = SOURCE.read_text(encoding="utf-8")
    updated = apply(current)
    assert current != updated
    SOURCE.write_text(updated, encoding="utf-8")
    print("PASS: Shiori mobile only H2 switch at 72% viewport / max 580px")
