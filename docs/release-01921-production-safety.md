# Survival40 v0.19.21 — production safety and release gate

Status: **BLOCKED FOR PRODUCTION** pending real-site checks. Last audited 2026-10-11. The 0.19.21 candidate and reviewed release-build workflow succeeded in GitHub Actions; this does not establish successful operation on survival40.com.

## Immutable goals
Read [PROJECT_VISION.md](../PROJECT_VISION.md). Reader-first autonomous article publishing; optional zero-ad articles; guide 栞さん; only eligible, content-relevant ads; no routine owner intervention.

## Verified in isolated CI
- Staged 0.19.21 PHP and navigator assets packaged as a single plugin folder.
- Isolated WordPress tests cover update activation, protected draft, initial ad switch OFF, approved-banner behavior and PHP syntax.
- GitHub Actions staging run 38063197248 and release-review run 38063459198 completed successfully.
- The release workflow now requires an explicit manual confirmation to overwrite the public 'latest' asset. A normal push must never publish it.
- The staged updater diagnosis is passive; the staging workflow explicitly guards against restoring the old self-update hooks.

## Not yet demonstrated
1. ConoHa or other host backup is recent, restorable, and covers both WordPress DB and wp-content (including plugin, uploads, theme and related settings).
2. A tested rollback plan exists (previous known-good ZIP + DB snapshot), with site access and appropriate credentials held by the owner.
3. Real-site frontend rendering of 栞さん/navigation and article pages, including mobile, has passed.
4. Actual public GitHub Release / Update URI delivery and WordPress automatic update in this hosting configuration has passed.
5. Live published/draft post count, content integrity, taxonomies, related links and advertisement state are captured and compared before/after.
6. Confirmation of the version installed in WP Admin; repository version.txt and GitHub release do not prove the deployed site version.
7. No inaccessible or expired affiliate program/offer is enabled; keep banner switch OFF until separate business-policy checks.
8. No accidental article publication occurs during the update.

## Before first production rollout (owner/authorized administrator)
- Confirm a current **offsite full backup**. Record backup timestamp, tested restore method, and last known-good release asset.
- Read-only snapshot: installed plugin version and active state; sample articles and screenshots; publish/draft counts and IDs; permalink navigation; public home page; 栞さん image/position; plugin automation settings; all affiliate switches.
- Prefer a host-provided staging clone or maintenance window. Test the actual **public distribution path** without changing live WordPress; compare ZIP member SHA-256 values against the CI reviewed candidate, not ZIP container hashes.
- Validate GitHub release update metadata and download behavior for WordPress.
- Hold a rollback path ready. Do not assume WordPress plugin rollback restores post database data.
- Require explicit owner approval before first public 0.19.21 publication and before enabling advertising; the release workflow has manual confirmation but no runtime verification of backups.

## After approved rollout
- Verify admin loads, plugin stays active and installed version changes to 0.19.21.
- Verify public home, a published article and 栞さん on desktop/mobile; original post metadata, categories and content unchanged.
- Check draft states and unchanged count; inspect PHP/error and update-audit logs.
- Verify ads remain globally OFF initially. Turn on only after verified permitted campaigns and accurate disclosures.
- Confirm no duplicate publication, orphaned scheduled events or broken images; check again after one normal cron cycle.
- If failed, deactivate automatic update route, restore previous plugin folder/ZIP, restore database only if necessary using a reviewed plan, and verify front-end integrity.

## Release invariants
- Never equate GitHub Actions SUCCESS with real-site backup, visual correctness, or production deployment.
- Never auto-approve ad programs or apply advertisements to all articles. Reader usefulness comes first.
- Never upgrade the public 'latest' release merely because files on main were edited.
- Keep publication OFF while production safety prerequisites are unresolved.

## Evidence links
- [Staging](https://github.com/BL4GS/survival40-auto/actions/runs/38063197248)
- [Review build](https://github.com/BL4GS/survival40-auto/actions/runs/38063459198)
