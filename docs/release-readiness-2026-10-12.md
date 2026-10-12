# Survival40 — 2026-10-12 update readiness

## What has actually been observed
- The owner opened ConoHa WING's **Backup** screen on 2026-10-12.
- Latest listed backup: **2026-10-11**; Web / Mail / DB were each marked **リストア可** for 2026-10-08 through 2026-10-11.
- The on-screen restore history was empty. This verifies **availability in ConoHa's panel**, not a successful restoration, an off-host backup copy, or even the specific files in the backup.
- The repository's public `version.txt` and GitHub Release remain **0.19.20**. Owner WordPress Admin screenshots on 2026-10-12 confirm **installed Survival40 Auto v0.19.20**, plugin **active** (the available action is 無効化), WordPress **plugin auto-update enabled** (自動更新有効), plugin panel **local v0.19.20 / remote v0.19.20**, last recorded self-update success **2026-10-09 23:43:03**, and **article automation OFF**. These are observed screen values, not proof of future update success.
- The v0.19.21 reviewed candidate was built and isolated checks passed. The separate v0.19.22 candidate passed isolated WordPress install and protected REST inbox tests. **Neither is installed at survival40.com.**
- Public REST read occasionally returned HTTP 507 in a CI job; other CI jobs read 23 public articles successfully. This does not prove disk fullness or downtime.

## Public-site preflight
The new script `production_preflight/baseline.py` reads only public WordPress article JSON and a few same-origin pages. It stores the public article IDs, URL, title and HTML SHA-256 hashes as a comparison baseline; no full article bodies are copied. The baseline is a GitHub Actions artifact, retained 30 days. A public source error halts it. **This tool never updates WordPress.**

## Still required before a GitHub Release update
1. **Partially completed:** WordPress confirms plugin v0.19.20, active and plugin auto-update enabled. Recheck pending-update status immediately before any actual release.
2. WP Admin → Posts: record published/draft/pending/scheduled article counts. Public REST cannot read nonpublic posts.
3. **Partially completed:** article automation is OFF. Record all affiliate/ad controls from the rest of the Survival40 Auto settings screen without changing them.
4. Confirm the ConoHa backup covers **survival40.com**, both site files and DB; preserve an independent backup/rollback copy. Confirm the concrete restoration procedure with ConoHa or in a staging clone; don't restore production just to test.
5. Confirm the previous known-good `survival40-auto.zip` and rollback method are accessible.
6. Review public-site baseline result and inspect homepage/article/Navigator on mobile.
7. The first actual release should only be triggered after these checks; `version.txt` advances after the ZIP is verified, which can trigger automatic WP plugin upgrades. Live update must be followed by immediate checks.

## Release invariants
- No public GitHub Release change or version.txt bump until prerequisites are recorded.
- Do not equate 'リストア可' with proven restorability.
- Never turn on advertisements to satisfy an update test; zero-ad articles are correct.
- Protect existing posts, drafts, Shiori assets and layout. Stop/revert the rollout on unexpected changes.
