# Threads Meta OAuth onboarding checklist — Survival40

**Stage:** preparation only, not enabled. Do not paste tokens, secrets or authorization codes into ChatGPT, PRs, tickets, source files or screenshots.

## Human authorization required (account owner)
1. Sign in at [Meta for Developers](https://developers.facebook.com/apps/) with an account authorized to configure a Meta developer app.
2. Create or select a Meta app that supports the **Threads API** use case. Check the app's current setup requirements and any tester/role restrictions. Select **only necessary Threads scopes**, at minimum \`threads_basic\` and \`threads_content_publish\`.
3. Configure a secure HTTPS OAuth redirect URI belonging to an owner-controlled callback service. The value used to exchange the code must match the authorized redirect URI exactly. A secure authorization-code + state/CSRF verification flow must be reviewed before any account login.
4. From the **correct @survival40_jp Threads account**, approve the explicit Meta authorization request. Review the granted scopes and account ID; do not authorize the owner's personal account by mistake.
5. Exchange the authorization code for a **Threads user** access token, then exchange for a long-lived token per Meta's instructions. App access tokens are **not** interchangeable with authorized Threads user tokens.
6. Store the resulting long-lived token **only** in GitHub Actions Secrets of the correct repository; record the expected Threads user ID using restricted configuration. Use secret names \`THREADS_ACCESS_TOKEN\` and \`THREADS_USER_ID\` when publication orchestration is built. Never print access-token values in logs/artifacts.
7. Implement and test long-lived token refresh, revocation/expiry handling and failure alerts before unattended operation. Refresh *before* expiry, not after. A refresh job must fail closed on errors and must not expose credentials.
8. With the correct account and permissions verified, run **one explicitly approved** live text post. Confirm the actual result on Threads before enabling the morning/evening schedule.
9. Use a persistent account+JST-date+slot or article-id key to make API publication effectively at-most-once. In any uncertain network outcome, STOP and require reconciliation; never blindly retry a possibly successful post.
10. Keep \`THREADS_PUBLISH_ENABLED\` explicitly **false** until Meta OAuth, token renewal, idempotency, account identity and one-post review are complete.

## Confirmed requirements / API references
- Official Meta-maintained Postman collection: https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api
- Authorized scopes and exchanging refreshable tokens: \`threads_basic\`, \`threads_content_publish\`, \`/oauth/access_token\`, \`/access_token\`, \`/refresh_access_token\`.
- Official publishing uses \`POST /me/threads\` to create a text container (with \`auto_publish_text=false\` for staged publishing), followed by \`POST /me/threads_publish\` with its container \`creation_id\`.
- Read Meta's current rules and rate limits before production; app/permission review rules depend on Meta account role and visibility.

## Status in repository
- \`scripts/threads/meta_api.py\` implements a *test-only staged* client for identity check and explicit two-step text publishing, not OAuth. It is not called from production actions.
- \`scripts/threads/ledger.py\` is a draft GitHub-ledger reservation primitive, not an enabled deployment or guarantee of exact-once semantics.
- PR #2 is draft: https://github.com/BL4GS/survival40-auto/pull/2
- Existing scheduled greeting workflow generates **review drafts only**, not posts.
- WordPress, site publishing and affiliate rules remain untouched.
