# PHP critical advisories — read-only incident review (2026-10-27 JST)

Status: **guidance only; no server logs inspected, no compromise determination, no PHP or WordPress changes**. Scope: Survival40 (`survival40.com`) and DiGlife (`diglife.online`). Keep this review separate from WordPress production deployment and from the existing editorial PRs.

## Verified vendor/advisory facts

- PHP announced CVE-2026-109618 and CVE-2026-109619 on **2026-10-21**; fixed upstream releases are **8.2.35 / 8.3.36 / 8.4.27 / 8.5.12**. A prior upstream version string by itself is not evidence of an unpatched vendor-backport build.
- ConoHa WING's **2026-10-22 20:45 JST final notice** says its security patch was applied to *all offered PHP versions* without changing version strings, explicitly including displayed **8.4.26**, and that customers need not change PHP versions for these two issues.
- **2026-10-29 22:02 JST authenticated read-only site_info:** Survival40 and DiGlife both report **PHP 8.4.26** (WordPress 7.1.4). These are application-reported version strings, **not independent verification of the server binary or backported patch**. ConoHa's all-offered-version backport announcement is the relevant host-side evidence for the original two CVEs.
- **JPCERT/CC updated its alert on 2026-10-26**: public exploit claims and reports of attempted exploitation are increasing; exploitability depends on runtime conditions. JPCERT recommends both patching and investigating possible compromise. This does **not** establish an attack against either site.
- **2026-10-29 escalation (JPCERT/CC updated alert):** investigators reported traces suggesting successful exploitation against **specific versions of a firewall appliance**, with version-tailored PHP exploit chaining and a Linux kernel privilege escalation; some vendors also reported observed attacks. This is **not a report that generic WordPress or ConoHa WING instances were compromised**. Nevertheless, prioritize **historical log review and evidence preservation** for both sites despite the host's 10/22 patch completion; a patched site can still require review for the pre-patch window. The latest advisory does not invalidate ConoHa's completed backport statement. **Neither site's access/error/WAF logs nor compromise indicators were read in this check.**
- PHP's **2026-10-23** follow-up on **CVE-2026-115560** concerns the *unusual conjunction* of configured `session.serialize_handler=php_binary` or `php_serialize`, runtime `ini_set()` switch to `php` before `session_start()`, and enabled session upload progress. PHP recommends `session.upload_progress.enabled=0` until a later fix **for affected deployments**. Neither site's runtime/application conditions nor ConoHa's handling of this *additional* CVE have been verified. **Do not infer that ConoHa's 10/22 final notice covers a 10/23 advisory.**

## 2026-11-05 22:00 JST checkpoint — security status (read-only)

- **Authenticated WordPress connection metadata checked again on both sites:** Survival40 and DiGlife each report **WordPress 7.1.4 / PHP 8.4.26**. This does not independently attest to PHP binary patch bytes, historical compromise, or PHP session configuration. No configuration was changed.
- **WordPress core:** WordPress released **7.1.4 on 2026-10-28** as a security release. JPCERT/CC's **2026-11-05 weekly report** references CVE-2026-119977 (an actively exploited WordPress core upgrade-window issue) and points to 7.1.4. Both sites report the fixed WordPress version; no core upgrade was initiated. Confirming that this exact build is deployed is limited to authenticated WordPress-reported metadata.
- **PHP CVE-2026-109618/109619:** The PHP project's fixed upstream 8.4 release is 8.4.27; **ConoHa WING's 2026-10-22 20:45 JST notice explicitly covers displayed 8.4.26 with a backport**, so a lower displayed version alone does not justify changing PHP. This host notice is not independent binary attestation or a retroactive incident investigation.
- **Additional conditional CVE-2026-115560:** PHP's 2026-10-23 advisory requires an unusual combination: configured serializer `php_binary`/`php_serialize`, runtime switch to `php` before `session_start()`, and enabled session upload progress. **Neither site's combined conditions nor ConoHa's treatment of this later issue have been established.** If the host confirms the combination, ask ConoHa to evaluate PHP's `session.upload_progress.enabled=0` mitigation and safe worker restart. No automatic server changes.
- **Historical compromise review still outstanding:** ConoHa's backport completed on Oct 22, but no authenticated access/error/WAF logs for the preceding window were reviewed. JPCERT's Oct 29 update is a reason to preserve and inspect available logs, not evidence that either site was attacked.
- **Operational boundaries:** No GitHub release, production deployment, PHP/WordPress/plugin/theme/DB changes, ad modifications, article edits or SNS posts. CI checks on this document cannot verify production safety.

Sources: [WordPress 7.1.4 security release](https://wordpress.org/news/2026/10/wordpress-7-1-4/); [JPCERT/CC weekly report 2026-11-05](https://www.jpcert.or.jp/wr/2026/wr261105.html); [PHP October 2026 security and session advisories](https://www.php.net/archive/2026.php); [ConoHa WING patch completion](https://www.conoha.jp/wing/news/?ap=2015054909); [JPCERT/CC PHP advisory, updated 2026-10-29](https://www.jpcert.or.jp/at/2026/at260033.html).

## Owner/operator review — READ ONLY, both sites separately

1. In the ConoHa WING control panel select the correct domain, then **WING → サイト管理 → アクセス解析 → ログ**. View or download the existing access/error logs without changing their retention settings. ConoHa says the on-screen view is limited (access: last 100 lines; errors: last 300 lines); lack of findings in the panel is **not** a full historical review.
2. For the period **before 2026-10-22 20:45 JST** and after, examine available logs for JPCERT indicators: anomalous `PHPSESSID` response cookies; suspicious `multipart/form-data` requests; contemporaneous memory-limit/HTTP 500 errors; unusual PHP worker crashes/restarts. These are *triage clues*, not a standalone proof of exploitation, and logging may not capture every indicator.
3. Optionally inspect **サイト管理 → サイトセキュリティ → WAF → ログ** for blocked requests. Do not change WAF rules, exclusions, logging, or server configuration during this review.
4. Compare any suspicious timeframe with the existing WordPress user list, file integrity and known publishing history **only using existing authorized read-only access**. Do not publish logs, cookies, user details, server paths or credentials into GitHub issues/PRs. Escalate credible anomalies to ConoHa support/security response for evidence preservation and a scoped incident review.
5. If the owner or host can verify the CVE-2026-115560 configuration conjunction, seek a host-specific mitigation/patch answer. **Do not automatically change php.ini, restart workers, switch PHP versions, modify plugins or update WordPress.** The 10/21 two-CVE backport and the later conditional issue are different decisions.

## Release and editorial guardrails

- No change to `PROJECT_VISION.md`, `docs/release-01921-production-safety.md`, `docs/organic-distribution-rollout-2026-10-21.md`, workflow schedules, SNS identity/posting ledger, RSS/OG metadata, articles, affiliate links or WordPress.
- Keep unverified observations marked as unverified. Passing GitHub Actions or public page GETs does not prove a host binary is patched or a site is uncompromised.
- Rollback if merged: revert the documentation-only PR merge commit; no runtime effect. Existing editorial/Threads PRs remain separate.

## Primary references

- PHP security release: https://www.php.net/archive/2026.php#2026-10-21-5
- PHP follow-up: https://www.php.net/archive/2026.php#2026-10-23-1
- JPCERT/CC alert (updated 2026-10-29): https://www.jpcert.or.jp/at/2026/at260033.html
- ConoHa WING final report: https://www.conoha.jp/wing/news/?ap=2015054909
- ConoHa WING log viewing guide: https://support.conoha.jp/w/checklogs/
- ConoHa WING WAF log viewing guide: https://support.conoha.jp/w/waf/
