from pathlib import Path
import re

p = Path("survival40-auto/survival40-auto.php")
s = p.read_text(encoding="utf-8")

# 0.19.6: unattended updates + eliminate the permanent Japanese FAQ 79-point trap.
target = "0.19.6"
s, n1 = re.subn(r"(?m)^(\s*\*\s*Version:\s*)\d+\.\d+\.\d+\s*$", lambda m: m.group(1) + target, s, count=1)
s, n2 = re.subn(r"(?m)^(\s*const\s+VERSION\s*=\s*')[^']+(';\s*)$", lambda m: m.group(1) + target + m.group(2), s, count=1)
s, n3 = re.subn(r"Survival40 Auto v\d+\.\d+\.\d+", "Survival40 Auto v" + target, s, count=1)
if n1 != 1 or n2 != 1 or n3 != 1:
    raise SystemExit("version surfaces not patched")

# Japanese FAQ headings normally end with a full-width question mark.
# 0.19.1 only recognized ASCII "?", so valid Japanese FAQs could be permanently
# flagged by deterministic checks and therefore capped at 79 points.
old = r"/<h3\b[^>]*>\s*(?:Q[\.\d\s]*)?([^<]*\?)\s*<\/h3>\s*(.*?)(?=<h[23]\b|$)/isu"
new = r"/<h3\b[^>]*>\s*(?:Q[\.\d\s]*)?([^<]*[?？])\s*<\/h3>\s*(.*?)(?=<h[23]\b|$)/isu"
if old not in s:
    raise SystemExit("FAQ regex anchor not found")
s = s.replace(old, new, 1)

# Let WordPress install Survival40 Auto updates without requiring the user to
# press the update button. Other plugins keep their existing update policy.
hook = "        add_action('admin_init', [$this, 'github_force_refresh_once']);"
if hook not in s:
    raise SystemExit("updater hook anchor not found")
s = s.replace(
    hook,
    hook + "\n        add_filter('auto_update_plugin', [$this, 'github_auto_update'], 10, 2);",
    1,
)

anchor = "    public function github_update_uri($update, $plugin_data, $plugin_file, $locales) {"
if anchor not in s:
    raise SystemExit("github_update_uri anchor not found")
method = """    public function github_auto_update($update, $item) {
        $plugin_file = plugin_basename(__FILE__);
        $item_plugin = is_object($item) ? ($item->plugin ?? '') : '';
        $item_slug = is_object($item) ? ($item->slug ?? '') : '';

        if ($item_plugin === $plugin_file || $item_slug === 'survival40-auto') {
            return true;
        }
        return $update;
    }

"""
s = s.replace(anchor, method + anchor, 1)

# Also advertise the policy in the custom Update URI payload.
s = s.replace("'autoupdate' => false,", "'autoupdate' => true,", 1)

# Give self-healing a little more room, but only when each rewrite produces a
# reviewable article. The deterministic issues are already merged into review['issues']
# and therefore passed to rewrite_from_review().
s = s.replace(
    "for ($repair = 0; $repair < 3 && (($review['verdict'] ?? 'revise') !== 'pass'); $repair++) {",
    "for ($repair = 0; $repair < 5 && (($review['verdict'] ?? 'revise') !== 'pass'); $repair++) {",
    1,
)

p.write_text(s, encoding="utf-8")
print("patched to 0.19.6")
