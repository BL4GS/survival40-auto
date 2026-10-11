"""Durable at-most-once reservation via a dedicated GitHub ledger branch.

The reservation is written BEFORE any Meta API side effect. A failed/ambiguous
attempt stays reserved and must be reconciled manually, never auto-retried.
No scheduled workflow currently invokes this module.
"""
import base64
import json
import re
import urllib.error
import urllib.parse
import urllib.request


class LedgerError(RuntimeError):
    pass


class GithubLedger:
    def __init__(self, repository, branch, token):
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
            raise ValueError("Invalid GitHub repository")
        if not re.fullmatch(r"[A-Za-z0-9_./-]+", branch) or not branch.startswith("state/"):
            raise ValueError("Use a dedicated state/ branch")
        if not token:
            raise ValueError("GitHub write token required")
        self.repository = repository
        self.branch = branch
        self.token = token

    @staticmethod
    def filename(key):
        match = re.fullmatch(r"(20[0-9]{2})-([01][0-9])-([0-3][0-9])-(morning|evening)", key)
        if not match:
            raise ValueError("Invalid local-date slot id")
        return f"threads-ledger/{match[1]}/{match[2]}/{key}.json"

    def _call(self, method, path, payload=None):
        quoted_path = urllib.parse.quote(path, safe="/")
        url = f"https://api.github.com/repos/{self.repository}/contents/{quoted_path}"
        if method == "GET":
            url += "?" + urllib.parse.urlencode({"ref": self.branch})
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers={
            "Authorization": "Bearer " + self.token,
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        })
        try:
            with urllib.request.urlopen(req, timeout=25) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if exc.code == 404 and method == "GET":
                return None
            if exc.code == 422 and method == "PUT":
                # 422 may mean existing file OR branch not found; reconcile using GET.
                if self._call("GET", path) is not None:
                    return {"already_reserved": True}
            raise LedgerError(f"GitHub ledger {method} rejected (HTTP {exc.code}); no post") from None
        except (urllib.error.URLError, TimeoutError):
            raise LedgerError("GitHub ledger unavailable; no post") from None

    @staticmethod
    def _payload(body, message, branch, sha=None):
        payload = {
            "message": message, "branch": branch,
            "content": base64.b64encode(
                (json.dumps(body, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
            ).decode("ascii")
        }
        if sha:
            payload["sha"] = sha
        return payload

    def reserve(self, slot_id, account_id, text_digest):
        if not account_id or not re.fullmatch(r"[a-f0-9]{64}", text_digest):
            raise ValueError("Missing account id or text sha256")
        path = self.filename(slot_id)
        # Explicit read allows a clear duplicate result; absence is not enough
        # without the GitHub create-without-sha race guard below.
        if self._call("GET", path) is not None:
            return False
        body = {
            "id": slot_id,
            "account_id": str(account_id),
            "text_sha256": text_digest,
            "status": "reserved",
            "manual_reconciliation_required_if_interrupted": True,
        }
        result = self._call("PUT", path, self._payload(
            body, "Reserve Threads publication " + slot_id, self.branch))
        if result.get("already_reserved"):
            return False
        if not isinstance(result, dict) or "content" not in result:
            raise LedgerError("Reservation acknowledgment missing; do not publish")
        return True

    def mark_published(self, slot_id, post_id):
        if not re.fullmatch(r"[0-9]+", str(post_id)):
            raise ValueError("Invalid Threads post id")
        path = self.filename(slot_id)
        previous = self._call("GET", path)
        if not previous or "sha" not in previous or "content" not in previous:
            raise LedgerError("Reservation missing; manual reconciliation required")
        try:
            metadata = json.loads(base64.b64decode(previous["content"]).decode("utf-8"))
        except (ValueError, KeyError, UnicodeDecodeError, json.JSONDecodeError):
            raise LedgerError("Ledger entry corrupted; manual reconciliation required") from None
        if metadata.get("id") != slot_id or metadata.get("status") != "reserved":
            raise LedgerError("Reservation mismatch; manual reconciliation required")
        metadata["status"] = "published"
        metadata["threads_post_id"] = str(post_id)
        result = self._call("PUT", path, self._payload(
            metadata, "Record Threads publication " + slot_id, self.branch, previous["sha"]))
        if not result or "content" not in result:
            raise LedgerError("Ledger update uncertain; manual reconciliation required")
