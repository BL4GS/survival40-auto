"""Small fail-closed client for the official Meta Threads Graph API.

Imported by staged publishing tools only. The scheduled draft workflow never
imports this module and never reads any Threads credential.
"""
import json
import urllib.error
import urllib.parse
import urllib.request

HOST = "https://graph.threads.net"


class ThreadsApiError(RuntimeError):
    pass


class MetaThreadsClient:
    def __init__(self, token):
        if not token or len(token.strip()) < 12:
            raise ValueError("A valid account-authorized token is required")
        self._token = token

    def _call(self, method, endpoint, params=None):
        if not endpoint.startswith("/") or "//" in endpoint:
            raise ValueError("Invalid API path")
        encoded = urllib.parse.urlencode(params or {}).encode("utf-8")
        url = HOST + endpoint
        if method == "GET":
            if encoded:
                url += "?" + encoded.decode("ascii")
            body = None
        elif method == "POST":
            body = encoded
        else:
            raise ValueError("Unsupported method")
        req = urllib.request.Request(
            url, data=body, method=method, headers={
                "Authorization": "Bearer " + self._token,
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "Survival40-Threads/0.1",
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=25) as response:
                result = json.load(response)
        except urllib.error.HTTPError as exc:
            # Meta can report HTTP 400 for several distinct causes. Record only
            # vetted integer codes and the fixed endpoint stage for triage;
            # never log raw Meta response, post text, IDs, request headers or token.
            stage = {
                "/me/threads": ("auto_publish_text" if (params or {}).get("auto_publish_text") == "true"
                                else "create_text_container"),
                "/me/threads_publish": "publish_container",
                "/me": "profile_check",
            }.get(endpoint, "other_endpoint")
            details = []
            try:
                body = json.loads(exc.read(4096).decode("utf-8"))
                meta_error = body.get("error") if isinstance(body, dict) else None
                if isinstance(meta_error, dict):
                    for field in ("code", "error_subcode"):
                        number = meta_error.get(field)
                        if type(number) is int and 0 <= number <= 999999999:
                            details.append(field + "=" + str(number))
                    transient = meta_error.get("is_transient")
                    if type(transient) is bool:
                        details.append("transient=" + str(transient).lower())
            except (ValueError, TypeError, AttributeError, UnicodeError, OSError):
                pass
            suffix = (" " + " ".join(details)) if details else ""
            raise ThreadsApiError(
                "Meta API returned HTTP " + str(exc.code) +
                " at " + stage + suffix
            ) from None
        except (urllib.error.URLError, TimeoutError):
            # Do not automatically retry ambiguous publish requests.
            raise ThreadsApiError("Meta API connection failed; manual reconciliation required") from None
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ThreadsApiError("Invalid JSON from Meta API") from None
        if not isinstance(result, dict):
            raise ThreadsApiError("Unexpected API response")
        return result

    def verify_account(self, expected_id, expected_username="survival40_jp"):
        if not expected_id or not expected_username:
            raise ValueError("Expected Threads user id and username are required")
        profile = self._call("GET", "/me", {"fields": "id,username"})
        if (str(profile.get("id")) != str(expected_id) or
                str(profile.get("username", "")).casefold() != expected_username.lstrip("@").casefold()):
            raise ThreadsApiError("Connected Threads account does not match Survival40")
        return {"id": str(profile["id"]), "username": profile["username"]}


    def publish_text(self, text):
        """Publish a TEXT post with one official Meta API request.

        Avoids the two-stage propagation race (code=24/subcode=4279009)
        seen Oct 14 and Oct 15. The caller MUST reserve its durable slot
        before calling this method. No automatic retry under any exception.
        """
        if not isinstance(text, str) or not 1 <= len(text) <= 500:
            raise ValueError("Invalid text length")
        result = self._call("POST", "/me/threads", {
            "media_type": "TEXT", "text": text, "auto_publish_text": "true",
        })
        post_id = result.get("id")
        if not isinstance(post_id, str) or not post_id.isdigit():
            raise ThreadsApiError("Auto-publish response has no post id; reconcile before retry")
        return post_id

    def create_text_container(self, text):
        if not isinstance(text, str) or not 1 <= len(text) <= 500:
            raise ValueError("Invalid text length")
        # Explicitly disable one-step auto-publication.
        result = self._call("POST", "/me/threads", {
            "media_type": "TEXT", "text": text, "auto_publish_text": "false"
        })
        container_id = result.get("id")
        if not isinstance(container_id, str) or not container_id.isdigit():
            raise ThreadsApiError("Meta did not return a valid container id")
        return container_id

    def publish_container(self, container_id):
        if not isinstance(container_id, str) or not container_id.isdigit():
            raise ValueError("Invalid container id")
        result = self._call("POST", "/me/threads_publish", {"creation_id": container_id})
        post_id = result.get("id")
        if not isinstance(post_id, str) or not post_id.isdigit():
            raise ThreadsApiError("Publish response had no post id; reconcile before retry")
        return post_id
