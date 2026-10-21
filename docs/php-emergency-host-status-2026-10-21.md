# PHP emergency response checkpoint — 2026-10-21 (JST)

**Status: BOTH PRODUCTION HOST PATCH STATES UNVERIFIED. No changes authorized.**

This is a source-controlled read-only incident checklist, not evidence of a patched server.

## Confirmed upstream release

On 2026-10-21 the PHP project published emergency security releases for two critical remote-code-execution vulnerabilities (CVE-2026-109618 and CVE-2026-109619; CVSS v4.0 9.2 each). Official upstream fixed releases:

| PHP branch | Fixed upstream release |
| --- | --- |
| 8.2 | 8.2.35 |
| 8.3 | 8.3.36 |
| 8.4 | 8.4.27 |
| 8.5 | 8.5.12 |

The PHP project no longer supports 8.1 and earlier. A hosting vendor may have its own backported patches; do not infer either safety or exposure from an older-looking version string alone. A WordPress core/plugin update does **not** update the server's PHP interpreter.

Sources:
- https://www.php.net/archive/2026.php#2026-10-21-1
- https://www.php.net/archive/2026.php
- https://wordpress.org/documentation/article/site-health-screen/

## Confirmed ConoHa WING maintenance, not patch confirmation

ConoHa WING announced emergency maintenance for **2026-10-21 19:00 through 2026-10-22 10:00 JST**, with possible temporary service interruptions. Its notice says only **system maintenance**; it does not explicitly confirm PHP patches, versions, or whether an owner must act.

Official notice: https://www.conoha.jp/wing/news/?ap=2015054897

Do not interpret the maintenance announcement or a normally loading homepage as proof that the emergency PHP fix is installed.

## Site-by-site evidence required

| Site | Running PHP version | ConoHa vendor patch evidence | Status |
| --- | --- | --- | --- |
| Survival40 | Not verified | Not verified | Unknown; check promptly |
| DiGlife | Not verified | Not verified | Unknown; check promptly |

Read-only check per site: WordPress admin > Tools > Site Health > Info > Server > PHP version. Capture the full patch version and the check time, without sharing login credentials. Confirm with ConoHa whether the selected PHP branch has received the October 21 emergency fix (including any vendor backport) and whether user action is required. If the dashboard is unavailable during maintenance, retry later or contact ConoHa support.

## Decision gate

1. **PHP 8.2–8.5 below the upstream fixed version:** treat as *not verified patched*; request ConoHa's exact deployment/backport status and upgrade guidance urgently. Do not label safe.
2. **At or above the fixed upstream version:** check the actual running runtime and ConoHa confirmation; this is a strong positive indicator, not a forensic guarantee.
3. **PHP 8.1 or older:** upstream unsupported; request a supported migration or written vendor backport confirmation urgently.
4. **Unusual vendor version strings or unlisted branches:** classification unknown until the hosting vendor explains its patch status.
5. **Maintenance or access errors:** do not assume compromise or successful patching. Recheck after the window and escalate prolonged failure.

Before any authorized production PHP switch, confirm a recent recoverable offsite full backup, plugin/theme compatibility, and a rollback plan. Do not change PHP, WordPress, plugins, database, public articles, advertisements, or SNS settings as part of this read-only checkpoint. PHP runtime patching is a hosting responsibility or an explicitly approved admin action; this GitHub repository cannot patch the running ConoHa service.

## Other ongoing work

Keep Discover OG image checks, Pinterest RSS transport audits, and Shiori/Threads safeguards read-only or staging-only while the host status remains unresolved. A passing GitHub Actions run does not establish WordPress host security or Discover/Pinterest/Threads actual delivery.

Next checkpoint: record both actual PHP versions and ConoHa's explicit response after the emergency maintenance, then update this document with verified evidence and dates.
