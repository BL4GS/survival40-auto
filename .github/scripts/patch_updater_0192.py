from pathlib import Path

php = Path("survival40-auto/survival40-auto.php")
text = php.read_text(encoding="utf-8")

text = text.replace(" * Version: 0.19.1\n", " * Version: 0.19.2\n", 1)
text = text.replace("    const VERSION = '0.19.1';", "    const VERSION = '0.19.2';", 1)
text = text.replace("<h1>Survival40 Auto v0.19.1</h1>", "<h1>Survival40 Auto v0.19.2</h1>", 1)

old = """    private function github_remote_version() {
        $cached = get_transient('survival40_github_remote_version');
        if ($cached) return $cached;

        $res = wp_remote_get(self::GITHUB_VERSION_URL, [
            'headers' => ['User-Agent' => 'Survival40-Auto/' . self::VERSION],
            'timeout' => 20,
            'redirection' => 5,
        ]);"""
new = """    private function github_remote_version() {
        $cached = get_transient('survival40_github_remote_version');
        if ($cached) return $cached;

        $check_url = add_query_arg([
            'plugin_version' => self::VERSION,
            'cache_bust' => floor(time() / 300),
        ], self::GITHUB_VERSION_URL);

        $res = wp_remote_get($check_url, [
            'headers' => [
                'User-Agent' => 'Survival40-Auto/' . self::VERSION,
                'Cache-Control' => 'no-cache',
            ],
            'timeout' => 20,
            'redirection' => 5,
        ]);"""
if old not in text:
    raise SystemExit("github_remote_version anchor not found")
text = text.replace(old,new,1)

old2 = """    public function github_force_refresh_once() {
        $key = 'survival40_updater_refresh_' . self::VERSION;
        if (get_option($key)) return;
        delete_site_transient('update_plugins');
        delete_transient('survival40_github_remote_version');
        update_option($key, 1, false);
    }"""
new2 = """    public function github_force_refresh_once() {
        // Refresh update metadata periodically while an administrator is using wp-admin.
        // This avoids WordPress keeping an old "latest version" in update_plugins for hours.
        $last = intval(get_option('survival40_updater_last_refresh', 0));
        if ($last && (time() - $last) < 300) return;

        delete_site_transient('update_plugins');
        delete_transient('survival40_github_remote_version');
        if (function_exists('wp_clean_plugins_cache')) wp_clean_plugins_cache(true);
        update_option('survival40_updater_last_refresh', time(), false);
    }"""
if old2 not in text:
    raise SystemExit("github_force_refresh_once anchor not found")
text = text.replace(old2,new2,1)

# Keep remote version cache short so releases appear promptly.
text = text.replace(
    "set_transient('survival40_github_remote_version', $version, 5 * MINUTE_IN_SECONDS);",
    "set_transient('survival40_github_remote_version', $version, 2 * MINUTE_IN_SECONDS);",
    1
)

php.write_text(text, encoding="utf-8")
print("patched to 0.19.2")
