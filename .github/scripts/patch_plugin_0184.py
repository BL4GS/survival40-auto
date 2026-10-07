from pathlib import Path
import re

php = Path("survival40-auto/survival40-auto.php")
text = php.read_text(encoding="utf-8")

def replace_once(old, new, label):
    global text
    if old not in text:
        raise SystemExit(f"patch anchor not found: {label}")
    text = text.replace(old, new, 1)

replace_once(" * Version: 0.18.0\n", " * Version: 0.18.4\n * Update URI: https://github.com/BL4GS/survival40-auto\n", "header version")
replace_once("    const VERSION = '0.18.0';", "    const VERSION = '0.18.4';", "const version")
replace_once(
    "    const GITHUB_VERSION_URL = 'https://api.github.com/repos/BL4GS/survival40-auto/contents/version.txt?ref=main';\n"
    "    const GITHUB_PACKAGE_URL = 'https://api.github.com/repos/BL4GS/survival40-auto/releases/assets/latest';",
    "    const GITHUB_VERSION_URL = 'https://raw.githubusercontent.com/BL4GS/survival40-auto/main/version.txt';\n"
    "    const GITHUB_PACKAGE_URL = 'https://github.com/BL4GS/survival40-auto/releases/download/latest/survival40-auto.zip';",
    "github constants"
)
replace_once(
    "        add_filter('pre_set_site_transient_update_plugins', [$this, 'github_update_check']);\n"
    "        add_filter('plugins_api', [$this, 'github_plugin_info'], 20, 3);",
    "        add_filter('pre_set_site_transient_update_plugins', [$this, 'github_update_check']);\n"
    "        add_filter('site_transient_update_plugins', [$this, 'github_update_check']);\n"
    "        add_filter('update_plugins_github.com', [$this, 'github_update_uri'], 10, 4);\n"
    "        add_filter('plugins_api', [$this, 'github_plugin_info'], 20, 3);\n"
    "        add_action('admin_init', [$this, 'github_force_refresh_once']);",
    "updater hooks"
)
replace_once("<h1>Survival40 Auto v0.18.0</h1>", "<h1>Survival40 Auto v0.18.4</h1>", "admin heading")
replace_once(
    "                現在: v<?php echo esc_html(self::VERSION); ?> ／ リモート: <?php echo esc_html($this->github_remote_version() ?: '未取得'); ?><br>\n"
    "                自動運転: <?php echo !empty($s['auto_enabled']) ? 'ON' : 'OFF'; ?>",
    "                現在: v<?php echo esc_html(self::VERSION); ?> ／ リモート: <?php echo esc_html($this->github_remote_version() ?: '未取得'); ?><br>\n"
    "                更新方式: WordPress Update URI + GitHub Release<br>\n"
    "                自動運転: <?php echo !empty($s['auto_enabled']) ? 'ON' : 'OFF'; ?>",
    "admin updater status"
)
replace_once(
    """                <form method="post" action="<?php echo esc_url(admin_url('admin-post.php')); ?>" style="margin:12px 0 26px;">
                    <input type="hidden" name="action" value="survival40_run_auto_once">
                    <?php wp_nonce_field(self::NONCE, '_s40nonce'); ?>
                    <?php submit_button('自動運転を今すぐ1回テスト', 'secondary', 'submit', false); ?>
                    <p class="description">既存タイトルを避けて次の1記事を企画→生成→安全判定→内部リンク→Amazon検索リンクまで自動処理します。</p>
                </form>""",
    """                <?php
                $s40_test_url = wp_nonce_url(
                    admin_url('admin-post.php?action=survival40_run_auto_once'),
                    self::NONCE,
                    '_s40nonce'
                );
                ?>
                <div style="margin:12px 0 26px;">
                    <a href="<?php echo esc_url($s40_test_url); ?>" class="button button-secondary">自動運転を今すぐ1回テスト</a>
                    <p class="description">既存タイトルを避けて次の1記事を企画→生成→安全判定→内部リンク→Amazon検索リンクまで自動処理します。</p>
                </div>""",
    "test button"
)

pattern = re.compile(r"""    private function github_remote_version\(\) \{.*?
    private function github_release_asset_url\(\) \{.*?
    \}
""", re.S)
m = pattern.search(text)
if not m:
    raise SystemExit("patch anchor not found: updater methods")
new_methods = """    private function github_remote_version() {
        $cached = get_transient('survival40_github_remote_version');
        if ($cached) return $cached;

        $res = wp_remote_get(self::GITHUB_VERSION_URL, [
            'headers' => ['User-Agent' => 'Survival40-Auto/' . self::VERSION],
            'timeout' => 20,
            'redirection' => 5,
        ]);
        if (is_wp_error($res)) return '';
        if (wp_remote_retrieve_response_code($res) !== 200) return '';

        $version = trim(wp_remote_retrieve_body($res));
        if (!preg_match('/^\\d+\\.\\d+\\.\\d+$/', $version)) return '';

        set_transient('survival40_github_remote_version', $version, 5 * MINUTE_IN_SECONDS);
        return $version;
    }

    private function github_release_asset_url() {
        return self::GITHUB_PACKAGE_URL;
    }

    public function github_force_refresh_once() {
        $key = 'survival40_updater_refresh_' . self::VERSION;
        if (get_option($key)) return;
        delete_site_transient('update_plugins');
        delete_transient('survival40_github_remote_version');
        update_option($key, 1, false);
    }

    public function github_update_uri($update, $plugin_data, $plugin_file, $locales) {
        if ($plugin_file !== plugin_basename(__FILE__)) return $update;

        $remote = $this->github_remote_version();
        if (!$remote || !version_compare($remote, self::VERSION, '>')) {
            return false;
        }

        return [
            'id' => 'https://github.com/' . self::GITHUB_REPO,
            'slug' => 'survival40-auto',
            'version' => $remote,
            'url' => 'https://github.com/' . self::GITHUB_REPO,
            'package' => self::GITHUB_PACKAGE_URL,
            'tested' => get_bloginfo('version'),
            'requires_php' => '7.4',
            'autoupdate' => false,
        ];
    }
"""
text = text[:m.start()] + new_methods + text[m.end():]

replace_once(
    """    public function github_update_check($transient) {
        if (empty($transient->checked)) return $transient;

        $plugin_file = plugin_basename(__FILE__);
        $remote = $this->github_remote_version();
        if (!$remote || !version_compare($remote, self::VERSION, '>')) return $transient;

        $package = $this->github_release_asset_url();
""",
    """    public function github_update_check($transient) {
        if (!is_object($transient)) $transient = new stdClass();
        if (!isset($transient->response) || !is_array($transient->response)) $transient->response = [];
        if (!isset($transient->no_update) || !is_array($transient->no_update)) $transient->no_update = [];

        $plugin_file = plugin_basename(__FILE__);
        $remote = $this->github_remote_version();
        if (!$remote) return $transient;

        if (!version_compare($remote, self::VERSION, '>')) {
            $obj = new stdClass();
            $obj->slug = 'survival40-auto';
            $obj->plugin = $plugin_file;
            $obj->new_version = self::VERSION;
            $obj->url = 'https://github.com/' . self::GITHUB_REPO;
            $obj->package = '';
            $transient->no_update[$plugin_file] = $obj;
            return $transient;
        }

        $package = $this->github_release_asset_url();
""",
    "update transient"
)

php.write_text(text, encoding="utf-8")

