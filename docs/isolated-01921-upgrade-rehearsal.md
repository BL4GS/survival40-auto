# Survival40 v0.19.21 exact upgrade rehearsal — 2026-10-12

## What passed
- GitHub Actions run: https://github.com/BL4GS/survival40-auto/actions/runs/38216906095
- Rebuilt the **exact** proposed 0.19.21 candidate from the currently reviewed release workflow, including its existing PHP patches and original four Shiori assets.
- Installed the actual public 0.19.20 GitHub Release ZIP in disposable localhost WordPress + SQLite.
- Seeded **23 entirely synthetic published posts + 16 synthetic drafts** to match the live *counts* (not live article data).
- Set safe test conditions: `auto_enabled=0`, `auto_publish_general=0`, affiliate disclosure `1`, source display `1`, absent frontend affiliate gate treated as OFF, and WordPress plugin auto-update enrollment ON with core cron auto-upgrades disabled in the isolated runner.
- Verified plugin upgrade **0.19.20 → 0.19.21** succeeded and all synthetic post ID/status/title/content hashes and selected safety controls matched byte-for-byte.
- Verified rollback **0.19.21 → 0.19.20** succeeded, plugin remained active, and the exact same post/settings snapshot matched.

## What this does NOT prove
- It does **not** install anything on `survival40.com` or access its real DB.
- It does **not** prove ConoHa automatic backup Web/DB restoration.
- It does **not** test WordPress' automatic background updater scheduling and network behavior; the plugin ZIP upgrades used WP-CLI `plugin install --force`.
- It does **not** prove site-specific integrations, hosting PHP settings, outbound Gemini calls, frontend Shiori layout, plugins from the real site, cache/WAF behavior, or all 56 trashed posts.
- The 23/16 articles were simulated and no actual private user content was copied into CI.

## Release decision
Public release is still gated by the reviewed release workflow's independent Web+DB recovery proof, live site baseline and responsible real-time monitoring. The owner is currently working, so **do not invoke release dispatch**. The public `version.txt` remains `0.19.20` until a guarded production window.

## Post-release verification
After a separately authorized live update, compare all 23 public article IDs/titles/URLs/content hashes using `Survival40 Pre/Post Upgrade Article Integrity (READ ONLY)` against baseline run `38210094227`; use WPVibe authenticated reads to verify the 16 drafts, plugin version, activation, and advertising/automation OFF states. Inspect public site on mobile. On any anomaly, halt, preserve diagnostics and use the archived 0.19.20 ZIP for a **plugin-only** rollback if appropriate; do not restore the whole DB casually.
