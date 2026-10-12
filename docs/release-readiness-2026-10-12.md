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

## Exact 0.19.21 isolated upgrade/revert passed (2026-10-12)
- GitHub Actions https://github.com/BL4GS/survival40-auto/actions/runs/38216906095 succeeded. PR #20 https://github.com/BL4GS/survival40-auto/pull/20 was merged into main.
- Reconstructed the exact staged 0.19.21 candidate, installed the published 0.19.20 ZIP into disposable WordPress+SQLite, and generated **synthetic** article inventory matching live counts (23 published / 16 draft) with automation/publication OFF.
- Installed v0.19.21 using WP-CLI, verified plugin version/active state and article ID, title, status, body hashes and selected safety settings unchanged; reinstalled public v0.19.20 ZIP and independently verified the same counts/options again.
- This is **NOT a verified ConoHa Web/DB restore**, nor a live WordPress automatic-updater test. No production Release or version.txt was changed.
- New operational recovery playbook, grounded in ConoHa support docs: [docs/conoha-production-recovery-playbook.md](conoha-production-recovery-playbook.md). Prioritize plugin-only recovery; do not casually restore DB for a plugin-only error.

## ConoHa WEB backup extraction performed (2026-10-12 18:23 JST)
- The owner directly operated ConoHa WING control panel. ConoHa displayed **「リストアが完了しました。」** for backup type **Web**, source date **2026-10-11**, extraction completed **2026-10-12 18:23:11 JST**. Displayed output folder: `/home/c5108478/backup_data_web`.
- This is **verified Web backup extraction by ConoHa into a recovery folder**, NOT a verification of the extracted WordPress files, plugin contents, full-site restoration, or database restorability. No production web files have been manually replaced. Extraction folder content still requires a read-only check; ConoHa reports recovery files may be automatically deleted after approximately 24 hours.
- Production WordPress **after this ConoHa Web extraction**, independently queried using authenticated WPVibe reads: **23 published / 16 drafts**, Survival40 Auto **0.19.20 ACTIVE**, `survival40_auto_settings.auto_enabled=0`, `auto_publish_general=0`. No publication or auto-generation was enabled.
- ConoHa database restore **has not been run/tested**, therefore the combined WEB+DB recovery gate for a guarded real release **remains unsatisfied**. Do not attest `WEB-DB-RESTORE-VERIFIED` until a safe DB copy is created and independently inspected with no production configuration/database cutover.

## ConoHa restored Survival40 plugin file check (2026-10-12 18:33 JST)
- Owner opened `backup_data_web/public_html/survival40.com/wp-content/plugins/survival40-auto/` in the ConoHa recovery directory and visually confirmed `survival40-auto.php`, `README.txt` and `assets/navigator/` are present. Inside the navigator directory, screenshot shows `normal.webp` and `summary.webp`; directory reports **4 items, 18 KB**, but filenames of the other two are not visible in that screenshot.
- Separately inspected the previously archived **public v0.19.20 rollback ZIP** (GitHub Action run `38210856074`, artifact `11728854452`): it does include all **four** navigator assets `normal.webp`, `summary.webp`, `explain.webp`, `caution.webp`, plus `survival40-auto.php` and `README.txt`. Four image file sizes sum approximately 18 KB. This proves the ZIP contains all four, **not** that the restored folder contains all four until independently listed.
- Owner has NOT overwritten active site files. Database restoration/test remains outstanding. Keep public release gate closed.

## ConoHa isolated DB backup restore completed (2026-10-12 19:10 JST)
- The owner restored the **2026-10-11 backup of the Survival40 database** using the ConoHa control panel at **2026-10-12 19:10:03 JST**. Screenshot explicitly says **「リストアが完了しました。」**, type **DB**, and reports a **new timestamp-suffixed database name** distinct from the live WordPress DB. The exact database names/host credentials are deliberately not recorded here.
- The owner did **not** change WordPress's connected database or replace live files. Separately queried the actual production WordPress afterwards, read-only: **23 published and 16 drafts**, active Survival40 Auto **v0.19.20**, **auto_enabled=0** and **auto_publish_general=0**.
- Combined ConoHa **Web files and DB backup extraction/creation have now been demonstrated by the hosting provider's control panel**, but the new DB's recovered tables and saved rows have **not yet been independently inspected**, nor has a separate staging WordPress successfully booted from the Web+DB restored assets. Do not falsely claim a complete end-to-end site restore.
- **Remaining for release gate:** verify the timestamp-suffixed restored DB exists and contains expected WordPress table structure/records using read-only access, confirm no accidental live DB cutover; assess whether an isolated end-to-end smoke test is practical. Keep release workflow's manual restore and monitoring attestations untriggered until verified. No publication/autoupdate activation yet.

## Release watch and isolated DB verification boundary (2026-10-12 evening)
- Production follow-up monitoring is now implemented in PR #26 (merged): https://github.com/BL4GS/survival40-auto/pull/26 . A read-only GitHub Actions workflow can run three bounded public probes after an explicitly authorized update and stop on article fingerprint changes, missing homepage article links or Shiori UI, unavailable navigator images, or HTTP errors. Offline regression tests passed. No release was triggered.
- The operator's restored database now shows approximately 35 MB used, while the original database shows approximately 49 MB. The difference is not explained. Presence and reported capacity do not prove recovered WordPress rows or an end-to-end bootable restoration.
- Official ConoHa support documents note that external database connections are not available. Its database user selector displayed indistinguishable short tags for original/restored DB. Do not guess. Exact restored-database access/verification remains tracked by https://github.com/BL4GS/survival40-auto/issues/27 .
- Public Release v0.19.21 is still held. A successful read-only public watch **does not certify** plugin version, 16 private drafts, ad/automation settings or actual database restore integrity; these need independent validation.
