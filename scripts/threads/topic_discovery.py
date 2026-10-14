"""Small, consented Threads public-topic research for Shiori; no social interactions.

Uses ONLY Meta's official keyword_search endpoint. Never stores individual
Threads content, usernames, IDs, timestamps or account-specific profiles.
An absent/unapproved search scope fails closed; unrelated Shiori posts continue.
"""
import base64
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import urllib.error
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

JST = ZoneInfo("Asia/Tokyo")
ROOT = pathlib.Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "threads-output" / "topic-research.json"
API = "https://graph.threads.net/v1.0/keyword_search"
STATE_REPO = "BL4GS/survival40-auto"
STATE_BRANCH = "state/threads-ledger"
STATE_PATH = "threads-research/latest.json"

# Every suggested angle is already in the approved Survival40 editorial allowlist.
KEYWORDS = (
    ("sun", "日焼け止め", "grooming", "外出前に日焼け止めを忘れにくい置き場所"),
    ("skin", "スキンケア", "grooming", "スキンケアのストックをどこまで置いておくか"),
    ("hair", "頭皮", "grooming", "髪を乾かす道具をどこに置いておくか"),
    ("movement", "筋トレ", "movement", "無理して運動する日と休む日の切り替え"),
    ("sleep", "睡眠", "daily_routine", "寝る前にスマホをどこに置くか"),
    ("breakfast", "朝食", "daily_routine", "朝食の定番メニューを決めておくこと"),
)
MAX_SEARCHES = len(KEYWORDS)
MIN_INDEPENDENT_POSTS = 3
MAX_STORED_POSTS = 0


class ResearchUnavailable(RuntimeError):
    pass


def _json_request(url, token, *, method="GET", payload=None, timeout=15):
    if not token:
        raise ResearchUnavailable("Missing consented API token")
    # Auth in header, NEVER log token-bearing URLs, HTTP bodies or token headers.
    req = urllib.request.Request(
        url, data=(json.dumps(payload).encode() if payload is not None else None),
        method=method, headers={"Authorization": "Bearer " + token,
                                "Accept": "application/json",
                                "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            return json.load(res)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError) as exc:
        # Strip token, user data and response contents out of errors/artifacts.
        raise ResearchUnavailable("Provider or ledger access unavailable") from None


def _meta_search(keyword, token):
    params = urllib.parse.urlencode({
        "q": keyword, "search_type": "RECENT", "search_mode": "KEYWORD",
        "fields": "id,text,username,permalink,timestamp",
        "limit": 12,
    })
    value = _json_request(API + "?" + params, token)
    if not isinstance(value, dict) or not isinstance(value.get("data"), list):
        raise ResearchUnavailable("Unexpected search response structure")
    return value["data"]


def _valid_public_result(row, keyword, now):
    if not isinstance(row, dict):
        return None
    author = row.get("username")
    text = row.get("text")
    link = row.get("permalink")
    stamp = row.get("timestamp")
    if not all(isinstance(x, str) for x in (author, text, link, stamp)):
        return None
    author = author.strip().lstrip("@").lower()
    if not author or author == "survival40_jp":
        return None  # A token without approved public search may show only itself.
    if (not re.fullmatch(r"[a-z0-9._]{2,30}", author)
            or keyword not in text or not 12 <= len(text) <= 500
            or any(t in text.lower() for t in ("pr案件", "アフィリエイト", "プレゼント企画",
                "フォロバ", "案件募集", "激安", "今すぐ購入", "www.", "http://", "https://"))):
        return None
    u = urllib.parse.urlsplit(link)
    if u.scheme != "https" or u.hostname not in ("www.threads.net", "threads.net"):
        return None
    try:
        posted = dt.datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if posted.tzinfo is None:
        return None
    age = now.astimezone(dt.timezone.utc) - posted.astimezone(dt.timezone.utc)
    if not dt.timedelta(0) <= age <= dt.timedelta(hours=72):
        return None
    # Short lived in RAM only; no social identifiers or post text in saved state.
    return author, str(row.get("id") or link)


def summarize(now, search_data):
    """Aggregate only broad allowed topics; untrusted public content is discarded."""
    if now.tzinfo is None or now.utcoffset() != dt.timedelta(hours=9):
        raise ValueError("Expected timezone-aware JST")
    if set(search_data) != {x[0] for x in KEYWORDS}:
        raise ResearchUnavailable("Missing keyword results")
    scored = []
    for topic_id, keyword, group, theme in KEYWORDS:
        found = set()
        authors = set()
        for row in search_data[topic_id][:12]:
            match = _valid_public_result(row, keyword, now)
            if match is None:
                continue
            author, unique_id = match
            authors.add(author)
            found.add(unique_id)
        if len(found) >= MIN_INDEPENDENT_POSTS and len(authors) >= MIN_INDEPENDENT_POSTS:
            scored.append((len(authors), len(found), topic_id, group, theme))
    if not scored:
        return None  # Missing permission or insufficient public signal.
    scored.sort(key=lambda x: (-x[0], -x[1], x[2]))
    _, count, topic, group, theme = scored[0]
    return {"schema_version": 1, "date_jst": now.date().isoformat(),
            "topic_id": topic, "topic_group": group, "theme": theme,
            "evidence": "aggregated_official_public_keyword_search",
            "signal_strength": "3+" if count >= 3 else "insufficient"}


def _github_path():
    return ("https://api.github.com/repos/" + STATE_REPO
            + "/contents/" + STATE_PATH)


def write_sanitized_signal(signal, token):
    """One known state path, no social content. Existing state is SHA-protected."""
    if signal is None or not validate_signal(signal):
        raise ValueError("Invalid aggregated hint")
    url = _github_path()
    read_url = url + "?" + urllib.parse.urlencode({"ref": STATE_BRANCH})
    sha = None
    try:
        existing = _json_request(read_url, token)
        sha = existing.get("sha")
        if not isinstance(sha, str):
            raise ResearchUnavailable("Unexpected state format")
    except ResearchUnavailable:
        # Only a verified 404 may create; do not overwrite on transient errors.
        req = urllib.request.Request(read_url, headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json"})
        try:
            urllib.request.urlopen(req, timeout=12).close()
            raise ResearchUnavailable("Unexpected state result")
        except urllib.error.HTTPError as ex:
            if ex.code != 404:
                raise ResearchUnavailable("GitHub state unavailable") from None
        except (urllib.error.URLError, TimeoutError):
            raise ResearchUnavailable("GitHub state unavailable") from None
    body = {"message": "Update anonymized Shiori topic signal",
            "branch": STATE_BRANCH,
            "content": base64.b64encode((json.dumps(signal, ensure_ascii=False, sort_keys=True)+"\n").encode()).decode()}
    if sha:
        body["sha"] = sha
    result = _json_request(url, token, method="PUT", payload=body, timeout=20)
    if not isinstance(result, dict) or "content" not in result:
        raise ResearchUnavailable("State write not acknowledged")


def validate_signal(obj):
    if not isinstance(obj, dict) or obj.get("schema_version") != 1:
        return False
    matching = [x for x in KEYWORDS if x[0] == obj.get("topic_id")
                and x[2] == obj.get("topic_group") and x[3] == obj.get("theme")]
    if len(matching) != 1 or obj.get("signal_strength") != "3+":
        return False
    if obj.get("evidence") != "aggregated_official_public_keyword_search":
        return False
    if set(obj) != {"schema_version","date_jst","topic_id","topic_group","theme","evidence","signal_strength"}:
        return False
    try:
        return dt.date.fromisoformat(obj["date_jst"]).isoformat() == obj["date_jst"]
    except (TypeError, ValueError):
        return False


def choose_safe_signal(now, signal, config, slot):
    """At most two ordinary 20:00 posts/week; articles and morning unaffected."""
    if (slot != "evening" or now.weekday() not in (1, 4)
            or not validate_signal(signal)):
        return None
    day = dt.date.fromisoformat(signal["date_jst"])
    if not (dt.timedelta(0) <= now.date() - day <= dt.timedelta(days=1)):
        return None
    if signal["theme"] not in config["topic_groups"].get(signal["topic_group"], []):
        return None
    return {"theme": signal["theme"], "topic_group": signal["topic_group"]}


def read_safe_signal(now, token, config, slot):
    if slot != "evening" or now.weekday() not in (1, 4) or not token:
        return None
    try:
        info = _json_request(_github_path()+"?"+urllib.parse.urlencode({"ref": STATE_BRANCH}), token)
        value = json.loads(base64.b64decode(info["content"]).decode("utf-8"))
        return choose_safe_signal(now, value, config, slot)
    except (ResearchUnavailable, ValueError, TypeError, KeyError, UnicodeError, OverflowError):
        return None


def main():
    now = dt.datetime.now(JST)
    result = {"date_jst": now.date().isoformat(),
              "state": "not_run_or_unavailable", "search_count_limit": MAX_SEARCHES,
              "individual_user_data_stored": False, "likes_or_replies_sent": False}
    try:
        meta_token = os.environ.get("THREADS_ACCESS_TOKEN", "")
        github_token = os.environ.get("GITHUB_TOKEN", "")
        if not meta_token or not github_token:
            result["state"] = "credentials_missing"
        else:
            found = {topic: _meta_search(keyword, meta_token)
                     for topic, keyword, _group, _theme in KEYWORDS}
            hint = summarize(now, found)
            if hint is None:
                result["state"] = "public_search_unavailable_or_insufficient"
            else:
                write_sanitized_signal(hint, github_token)
                result["state"] = "aggregate_saved"
                result["topic_id"] = hint["topic_id"]
    except ResearchUnavailable:
        result["state"] = "search_permission_or_provider_unavailable"
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print("THREADS_RESEARCH: " + result["state"])


if __name__ == "__main__":
    main()
