# Survival40 public-site audit (READ ONLY)

This is an automated **observation/reporting tool**, not a WordPress updater or a quality-certification service.

## Why it exists
The project aims to operate autonomously while preserving reader trust, existing content and the established Shiori experience. The public site must be monitored without asking the owner to check all articles every day.

## What it checks
- Reads up to 90 **publicly published** articles from the public WordPress REST endpoint `/index.php?rest_route=%2Fwp%2Fv2%2Fposts` (the standard `/wp-json/wp/v2/posts` returned HTTP 403 during an earlier probe).
- Evaluates missing/unsafe permalinks, duplicate titles, very short article text, image-alt gaps, possible unconditional health claims and optional internal-link suggestions.
- Probes the homepage and up to 6 published post URLs using bounded **read-only GETs**; a 403/429 is reported as possibly blocked, not automatically diagnosed as a broken page.
- Saves machine-readable `audit.json` and readable `audit.md` as GitHub Actions artifacts for 14 days.

## Invariants
- **No authentication** to WordPress, Meta or third-party services.
- **No editing or automatic deletion**, publication, plugin installation, or changes to ad switches.
- **Zero-ad articles are valid**, and do not trigger missing-affiliate warnings.
- Static thresholds are editorial *review signals*, not scientific or SEO assessments.
- Public data is untrusted: the audit never executes embedded content, follows third-party links, or executes generated instructions.

## Schedule and scope
- Scheduled 04:10 JST daily **only after this reviewed PR is merged**. GitHub Actions schedules are best-effort.
- `workflow_dispatch` permits authorized manual review. Pull requests execute regression tests and safe public probes; none deploy.
- A successful automated check does **not** prove installed plugin version, host backups, self-update mechanism or private dashboard health; see `docs/release-01921-production-safety.md`.

## How to interpret results
- `warning`: something concrete may need human/automated editorial validation.
- `review`: safety wording worth verifying with a stronger factual-evidence checker.
- `info`: optional UX/editorial improvement or observation, possibly fully intentional.

Do not automatically replace posts, inject ads, or change WordPress based on this report. Only a separately validated, evidence-backed update path may safely apply corrections.
