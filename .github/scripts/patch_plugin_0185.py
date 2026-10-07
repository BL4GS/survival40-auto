from pathlib import Path
import re

php = Path("survival40-auto/survival40-auto.php")
text = php.read_text(encoding="utf-8")

def replace_once(old, new, label):
    global text
    if old not in text:
        raise SystemExit(f"patch anchor not found: {label}")
    text = text.replace(old, new, 1)

replace_once(" * Version: 0.18.0\n", " * Version: 0.18.5\n * Update URI: https://github.com/BL4GS/survival40-auto\n", "header version")
replace_once("    const VERSION = '0.18.0';", "    const VERSION = '0.18.5';", "const version")
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
replace_once("<h1>Survival40 Auto v0.18.0</h1>", "<h1>Survival40 Auto v0.18.5</h1>", "admin heading")
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

# 0.18.5 editorial quality rules.
planner_old = '            . "目的は検索流入とAmazon/A8への自然な導線です。煽り、医療断定、既存記事との重複は禁止。\\n\\n"'
planner_new = '''            . "目的は検索流入とAmazon/A8への自然な導線です。煽り、医療断定、既存記事との重複は禁止。\\n"
            . "タイトルは28〜42文字程度。日本語として自然で、同じ意味の語を重ねない。\\n"
            . "単なる一般論ではなく、読者が何を確認し、どう選ぶかが明確になる企画を優先する。\\n"
            . "医療・健康に近い俗称や断定的表現は避け、必要なら正式な概念を併記する。\\n\\n"'''
if planner_old in text:
    text = text.replace(planner_old, planner_new, 1)

body_old = '        . "- H2/H3で論理的に構造化する。\\n"'
body_new = '''        . "- H2は3〜5個に絞り、記事タイトルの言い換えをH2で繰り返さない。\\n"
        . "- H3は具体的な選び方・確認ポイントに使う。\\n"
        . "- 抽象論を続けず、各節に読者が実際に確認できる基準・表示・行動を1つ以上入れる。\\n"
        . "- 根拠のない優先順位や万能論を作らない。\\n"
        . "- 医療・健康に関わる主張は参考資料の範囲を超えない。資料にない因果関係は書かない。\\n"
        . "- 目・視力・眼精疲労・ドライアイ等の話題では、化粧品の一般論と眼科領域を混同しない。\\n"
        . "- 『スマホ老眼』のような俗称を病名のように扱わない。\\n"
        . "- 目元化粧品は製品表示の使用部位・使用回数・注意事項を優先し、全製品共通の使い方を断定しない。\\n"
        . "- 性別による肌質差や成分効果を、根拠資料がないまま一般化しない。\\n"
        . "- サプリメントは食事の代替ではないこと、過剰摂取や成分重複に注意することを明記する。\\n"'''
if body_old in text:
    text = text.replace(body_old, body_new, 1)

# Make Amazon CTA readable on mobile.
cta_old = '''            . '<p style="margin:0;"><a href="' . esc_url($url) . '" target="_blank" rel="nofollow sponsored noopener">' . esc_html($label) . '</a></p>' '''
cta_new = '''            . '<p style="margin:0;"><a style="font-size:16px !important;line-height:1.5 !important;font-weight:700 !important;display:inline-block !important;" href="' . esc_url($url) . '" target="_blank" rel="nofollow sponsored noopener">' . esc_html($label) . '</a></p>' '''
if cta_old in text:
    text = text.replace(cta_old, cta_new, 1)

# Mark eye-related themes as YMYL and use the skin/medical safety gate.
route_old = '''        $cfg = $map[$data['category']];
        return ['''
route_new = '''        $cfg = $map[$data['category']];
        $eye_text = $title . ' ' . sanitize_text_field($data['keyword']);
        if (preg_match('/(目|眼|視力|老視|老眼|眼精疲労|ドライアイ|アイケア)/u', $eye_text)) {
            $cfg['source_group'] = 'skin';
            $cfg['ymyl'] = 1;
        }
        return ['''
if route_old in text:
    text = text.replace(route_old, route_new, 1)

php.write_text(text, encoding="utf-8")
print("patched to 0.18.5")
