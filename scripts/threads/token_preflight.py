"""Manual, read-only verification of the saved Threads token and its permissions.

Never print a credential, HTTP request URL, raw API response, or exception body.
Does not refresh tokens or create/publish Threads containers.
"""
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

HOST = "https://graph.threads.net"
EXPECTED_USERNAME = "survival40_jp"
EXPECTED_APP_ID = "996264916835561"
REQUIRED_SCOPES = {"threads_basic", "threads_content_publish"}
MIN_REMAINING_SECONDS = 7 * 86400


class TokenPreflightError(RuntimeError):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise TokenPreflightError("Unexpected redirect; no action taken")


def safe_get(endpoint, token, params=None):
    query = urllib.parse.urlencode(params or {})
    url = HOST + endpoint + ("?" + query if query else "")
    request = urllib.request.Request(
        url, method="GET",
        headers={"Authorization": "Bearer " + token, "Accept": "application/json"},
    )
    try:
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=20) as response:
            if response.status != 200:
                raise TokenPreflightError("Meta did not return HTTP 200")
            raw = response.read(32769)
            if len(raw) > 32768:
                raise TokenPreflightError("Meta response exceeds size limit")
            decoded = json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise TokenPreflightError("Meta request failed (HTTP %s)" % exc.code) from None
    except (urllib.error.URLError, TimeoutError, UnicodeError, ValueError):
        raise TokenPreflightError("Meta connection or response failed") from None
    if not isinstance(decoded, dict):
        raise TokenPreflightError("Unexpected Meta response structure")
    return decoded


def validate_profile(profile, expected_id):
    if (str(profile.get("id", "")) != expected_id
            or str(profile.get("username", "")).lstrip("@").casefold() != EXPECTED_USERNAME):
        raise TokenPreflightError("Threads account is not the expected @survival40_jp")


def validate_debug_response(response, expected_id, now_epoch):
    data = response.get("data")
    if not isinstance(data, dict):
        raise TokenPreflightError("Token debugger data was not returned")
    if data.get("is_valid") is not True:
        raise TokenPreflightError("Threads token is invalid or not confirmed valid")
    scopes = data.get("scopes")
    if not isinstance(scopes, list) or any(not isinstance(s, str) for s in scopes):
        raise TokenPreflightError("Token debugger did not return scopes")
    if not REQUIRED_SCOPES.issubset(set(scopes)):
        raise TokenPreflightError("Required Threads publishing scopes were not granted")
    expires_at = data.get("expires_at")
    if type(expires_at) is not int or expires_at <= now_epoch + MIN_REMAINING_SECONDS:
        raise TokenPreflightError("Token expiry missing or too near for safe publishing")
    for field in ("user_id", "app_id"):
        value = data.get(field)
        if value is not None:
            expected = expected_id if field == "user_id" else EXPECTED_APP_ID
            if str(value) != expected:
                raise TokenPreflightError("Token debugger " + field + " mismatch")
    data_expiry = data.get("data_access_expires_at")
    if data_expiry is not None and (type(data_expiry) is not int
                                    or data_expiry <= now_epoch + MIN_REMAINING_SECONDS):
        raise TokenPreflightError("Token data-access expiry missing or too near")
    return dt.datetime.fromtimestamp(expires_at, tz=dt.timezone.utc)


def main():
    token = os.getenv("THREADS_ACCESS_TOKEN", "").strip()
    expected_id = os.getenv("THREADS_USER_ID", "").strip()
    if len(token) < 12 or not re.fullmatch(r"[0-9]{1,30}", expected_id):
        raise TokenPreflightError("Required GitHub Secrets are absent or invalid")

    profile = safe_get("/me", token, {"fields": "id,username"})
    validate_profile(profile, expected_id)
    # Official Meta Threads /debug_token requires input_token as a query parameter.
    # HTTPS only; never print URL, request, token, or response contents.
    debug = safe_get("/debug_token", token, {"input_token": token})
    expiry = validate_debug_response(debug, expected_id, int(dt.datetime.now(dt.timezone.utc).timestamp()))
    print("PASS: @survival40_jp, publishing scopes, and token expiry verified.")
    print("Token expires (UTC): " + expiry.strftime("%Y-%m-%d %H:%M"))
    print("No post created, no secrets printed, no token refresh performed.")
    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as output:
            output.write("## Threads token readiness: PASS\n\n")
            output.write("- Correct account: **@survival40_jp**\n")
            output.write("- Required scopes: **verified**\n")
            output.write("- Expiration (UTC): **" + expiry.strftime("%Y-%m-%d %H:%M") + "**\n")
            output.write("- **GET only; no Threads post created.**\n")


if __name__ == "__main__":
    try:
        main()
    except TokenPreflightError as exc:
        sys.exit("FAIL: " + str(exc) + ". Nothing posted.")
