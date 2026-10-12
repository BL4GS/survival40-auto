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
2. **Confirmed 2026-10-12 WordPress post list:** All (excluding trash) **39**, Published **23**, Draft **16**, Trash **56**. The status links displayed no separate Scheduled/Pending categories; this does not independently prove that no such statuses exist. Capture the totals again immediately after the first plugin update.
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

## Confirmed known-good plugin rollback (2026-10-12)
- The public GitHub release v0.19.20 ZIP was fetched without any release modifications; its archive CRC, plugin PHP 0.19.20 version markers, and navigator image were checked.
- Read-only GitHub Actions run: https://github.com/BL4GS/survival40-auto/actions/runs/38210856074 ; rollback artifact: https://github.com/BL4GS/survival40-auto/actions/runs/38210856074/artifacts/11728854452 (90-day retention).
- The old ZIP is available independently of the mutable public GitHub Release `latest`; a copy and SHA-256 checksum were also verified. This is **plugin file recovery only**, not a full WordPress database recovery.
- Installed plugin remains 0.19.20, active; WordPress plugin auto-update is enabled; article automation is OFF as observed in owner screenshots dated 2026-10-12.

## Official ConoHa recovery procedure — verified from support documents
- ConoHa's 'リストア可' refers to the ability to **restore backup data** from its snapshots. For Web data, ConoHa places recovered data under `/home/cXXXXXXXX/backup_data_web`, which must then be moved to the live Web document root using its file manager or FTP; choosing a restore date alone does not automatically roll back all live WordPress files.
- For database restore, ConoHa creates a recovered database named with the restore date. Its official procedure involves carefully changing the database used by the site in `wp-config.php`; this should be a controlled recovery operation, NOT undertaken as a routine plugin update step.
- ConoHa says Web/mail restored files may be deleted after **24 hours**, and restoring 5+ times within a week may cause restrictions.
- Sources: https://support.conoha.jp/w/restorebackup/ ; https://support.conoha.jp/w/recovery-web/ ; https://support.conoha.jp/w/recovery-db/.
- No restoration was executed by ChatGPT. The safest default on a plugin-only failure is to restore the **prior plugin folder** from the archived v0.19.20 ZIP, rather than overwrite the whole WordPress database and lose newer articles or configuration.

## Still open
- **Observed posts: 39 current (23 published, 16 draft), 56 trashed.** Confirm pending/scheduled status in full Admin if applicable. Still need current advertising switches in plugin settings.
- Capture a reversible site-level rollback approach suitable for the actual ConoHa account; an **off-host** DB and wp-content backup or isolated restore rehearsal is not yet verified.
- Do not publish v0.19.21 or update version.txt until final production readiness has been validated and monitoring/recovery access is available.