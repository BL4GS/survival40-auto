# Threads article source: verified integration notes (2026-10-11)

Scope: Threads review draft generation only. No API publishing and no WordPress modification.

## GitHub Actions network probe
- Repo workflow run: https://github.com/BL4GS/survival40-auto/actions/runs/38142180455
- Main site GET: HTTP 200.
- WordPress RSS GET at /feed/: HTTP 200.
- WordPress REST GET /wp-json/: HTTP 200.
- Pretty REST posts GET /wp-json/wp/v2/posts: **HTTP 403**.
- Equivalent query-route GET /index.php?rest_route=%2Fwp%2Fv2%2Fposts: **HTTP 200**.
- The restricted query-route **with published-post filters** returned **23 articles**. No article from the previous 24 hours qualified at probe time.
- 14 isolated tests passed, including URL safety, published-only selection, and fallback on HTTP 403.

The staged extractor \`scripts/threads/articles.py\` tries the pretty REST endpoint, then the query-route on 403/404, and rejects off-domain links, non-published status and short/incomplete source text.

## Required next gates
- PR #3 remains a draft and has not been merged to main.
- Workflow only drafts on explicit workflow_dispatch after merge; pull requests run tests and source connectivity probes but never call Gemini or Meta.
- Before an unattended article-promotion schedule, add a persistent per-article-id ledger so restarts and retries cannot re-promote the same article; establish volume limits and optional non-commercial article preference.
- Before *any* live post, obtain account-authorized Threads API credentials, verify exact @survival40_jp identity, reconcile uncertain failures, and perform a single explicitly approved test.
- Do not infer that public WordPress reads equal permission to change or publish WordPress content.
- Existing main WordPress articles and plugin version are untouched.
