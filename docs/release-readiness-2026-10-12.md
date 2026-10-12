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
## Read-only after-update public article integrity comparator
- PR #16 https://github.com/BL4GS/survival40-auto/pull/16 merged 2026-10-12, offline regression tests passed.
- Manual GitHub Action **Survival40 Pre/Post Upgrade Article Integrity (READ ONLY)** downloads the pre-upgrade snapshot artifact from run **38210094227**, rescans public WordPress articles, and checks article ID, title, URL and content hash changes.
- A difference causes the verification workflow to fail, while preserving a comparison artifact for troubleshooting. No WordPress writes or release actions occur.
- PR regression tests do not perform public API requests, reducing the chance of repeat HTTP 507 host limits.
- This comparison does not verify private/draft posts (16 observed), WP plugin activation, advertising state or actual backup restore; confirm each separately before release.
## Connected WPVibe authenticated read (2026-10-12)
- WordPress site connected at https://www.survival40.com using user-approved one-click authorization. WPVibe `site_info` authenticated read succeeded.
- Current installed and active Survival40 Auto is **0.19.20**; active site theme Twenty Twenty-Five **1.4**.
- Authenticated WordPress REST GET `/wp/v2/posts?per_page=100&status=publish,draft,pending,future,private&context=edit` returned exactly **39** posts: 23 published, 16 drafts. Separate future query returned **0**.
- Core WordPress REST settings request returned only the site title, not plugin-specific affiliate/ad or automation switches.
- Site-side WPVibe (Vibe AI) plugin is **not installed**. The current WPVibe connection supports authenticated WordPress core REST and abilities read; native WP-CLI/options and file inspection are unavailable until that plugin is separately installed and authorized.
- **No writes** to the live site, plugin updates, ads, posts or theme were made through this integration. Do not mistake account-side WPVibe authorization for approval to install a new plugin.
## WPVibe plugin installed and read-only admin settings verified (2026-10-12)
- Owner explicitly authorized adding the **Vibe AI / WPVibe plugin**. WordPress REST installation returned plugin `vibe-ai/vibe-ai` **active, v1.20.3**; WPVibe `site_info` after installation confirms WordPress authenticated administrator access and WP-CLI availability.
- Native WP-CLI list confirms Survival40 Auto **active 0.19.20** and WPVibe **active 1.20.3**. No other plugin update was executed.
- Read-only `option pluck survival40_auto_settings` checks (individual non-secret keys only): `auto_enabled=0`, `auto_publish_general=0`, `auto_interval=daily`, `affiliate_notice=1`, `show_sources=1`, `model=gemini-3.5-flash-lite`. No Gemini API key, tokens, or private identifiers were read out or stored.
- `s40_affiliate_frontend_enabled` option was **not present** (WP-CLI exit code 1); staged 0.19.21 code defaults this gate to `no`. Its absence cannot by itself prove every individual legacy article has no embedded affiliate links. The `affiliate_notice=1` setting controls disclosure, not whether an advertisement is inserted.
- `auto_max_per_run` key was not present in the stored array; the v0.19.20 PHP defaults to 1. No WordPress options were modified.
- Authenticated WordPress REST inventory confirms 23 published / 16 drafts / 0 scheduled, as previously observed.
- These findings improve the upgrade baseline but **do not attest to a successful ConoHa database restore or independent off-host backup**. Actual public release still needs recovery verification.

## Safe GitHub release hard gates and isolated plugin rollback (2026-10-12)
- Release safety PR #17 (https://github.com/BL4GS/survival40-auto/pull/17) merged after all contract tests passed. Public v0.19.21 release now requires exact four manual dispatch confirmations: release intention, separately tested Web+DB restore, live baseline/ad checks, and a person available to monitor and roll back production. A PR build or branch push cannot publish a new plugin ZIP or bump version.txt.
- The manual release additionally downloads and verifies the existing v0.19.20 plugin release ZIP, archives it for 90 days, and **only then** permits any public release mutation. Asset re-download and byte comparison precede version.txt bump. The workflow no longer cancels an in-flight release run when another is submitted.
- Isolated rollback rehearsal PR #18 (https://github.com/BL4GS/survival40-auto/pull/18) merged after GitHub Actions run https://github.com/BL4GS/survival40-auto/actions/runs/38214978009 succeeded.
- That test installed v0.19.22 RC in a disposable WordPress/SQLite site, generated a research-only queue brief, rolled back to the actual existing GitHub Release v0.19.20 ZIP via WP-CLI plugin installer, then reinstalled v0.19.22 RC. Article status/title/IDs and editorial plan queue remained byte-equivalent at each stage. This is evidence of **plugin-only rollback on an isolated WordPress test**, NOT ConoHa backup restore and NOT a production update.
- The backup restore assertion must be based on **real verification**, not simply entering confirmation strings. When the owner is working and unable to monitor production, DO NOT trigger public release.

## Mobile display/SEO baseline (read-only, 2026-10-12)
- WPVibe PageSpeed/Lighthouse checked the public homepage on mobile: performance **92**, accessibility **95**, best-practices **100**, SEO **92**. Lab LCP **2.9s**, CLS **0**; no CrUX field data, so this is a diagnostic snapshot, not proof of field performance.
- The bare domain redirects to canonical **https://www.survival40.com/**, matching WordPress home/siteurl and AIOSEO canonical. Lab reported a ~780ms redirect opportunity; no domain change was made.
- Live HTML contains **no homepage meta description**, although AIOSEO 5.0.3 is active. A separate accessibility issue flags color contrast; no styles changed. Improvement tracked in https://github.com/BL4GS/survival40-auto/issues/19 .
- Static WordPress homepage is page **471**. The suggested meta description must be reviewed and set through AIOSEO when convenient, not injected during the production upgrade.
- Inspection used public read-only HTML and PageSpeed API only; no site data changed.
