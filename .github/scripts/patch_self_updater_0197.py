from pathlib import Path
import re

p=Path("survival40-auto/survival40-auto.php")
s=p.read_text(encoding="utf-8")

# Add a dedicated self-update cron hook alongside the existing updater hooks.
hook="        add_action('admin_init', [$this, 'github_force_refresh_once']);"
if hook not in s:
    raise SystemExit("admin_init updater hook not found")
if "survival40_self_update_event" not in s:
    s=s.replace(
        hook,
        hook + "\n        add_action('admin_init', [$this, 'github_schedule_self_update']);"
             + "\n        add_action('survival40_self_update_event', [$this, 'github_run_self_update']);",
        1
    )

anchor="    public function github_update_uri($update, $plugin_data, $plugin_file, $locales) {"
if anchor not in s:
    raise SystemExit("github_update_uri anchor not found")

methods=r'''    public function github_schedule_self_update() {
        if (!is_admin() || wp_doing_ajax()) return;
        if (!current_user_can('update_plugins')) return;

        $remote = $this->github_remote_version();
        if (!$remote || !version_compare($remote, self::VERSION, '>')) return;

        // Avoid repeatedly queuing the same update on every admin request.
        $lock_key = 'survival40_self_update_scheduled_' . $remote;
        if (get_transient($lock_key)) return;

        set_transient($lock_key, 1, 10 * MINUTE_IN_SECONDS);

        // Do not depend on WP-Cron. Run the upgrader after the current admin
        // response has finished rendering, so a normal wp-admin reload is enough
        // to trigger the update even when loopback cron is disabled or delayed.
        add_action('shutdown', [$this, 'github_run_self_update'], 999);
    }

    public function github_run_self_update() {
        $remote = $this->github_remote_version();
        if (!$remote || !version_compare($remote, self::VERSION, '>')) return;

        require_once ABSPATH . 'wp-admin/includes/class-wp-upgrader.php';
        require_once ABSPATH . 'wp-admin/includes/plugin.php';

        // Rebuild update metadata so Plugin_Upgrader sees our GitHub package.
        delete_site_transient('update_plugins');
        delete_transient('survival40_github_remote_version');
        wp_update_plugins();

        $plugin_file = plugin_basename(__FILE__);
        $updates = get_site_transient('update_plugins');
        if (!is_object($updates) || empty($updates->response[$plugin_file])) return;

        $skin = new Automatic_Upgrader_Skin();
        $upgrader = new Plugin_Upgrader($skin);
        $result = $upgrader->upgrade($plugin_file);

        if (is_wp_error($result) || $result === false) {
            delete_transient('survival40_self_update_scheduled_' . $remote);
            update_option(
                'survival40_self_update_last_error',
                is_wp_error($result) ? $result->get_error_message() : 'Plugin_Upgrader returned false',
                false
            );
            return;
        }

        update_option('survival40_self_update_last_success', current_time('mysql'), false);
        delete_transient('survival40_self_update_scheduled_' . $remote);
    }

'''
if "public function github_schedule_self_update()" not in s:
    s=s.replace(anchor,methods+anchor,1)

# Surface updater state on the plugin page for diagnosis without needing server access.
status_anchor='''                更新方式: WordPress Update URI + GitHub Release<br>
                自動運転: <?php echo !empty($s['auto_enabled']) ? 'ON' : 'OFF'; ?>'''
status_new='''                更新方式: WordPress Update URI + GitHub Release + 自己更新<br>
                <?php
                $s40_update_ok = get_option('survival40_self_update_last_success', '');
                $s40_update_err = get_option('survival40_self_update_last_error', '');
                ?>
                自己更新: <?php echo $s40_update_err ? '直近エラー: ' . esc_html($s40_update_err) : ($s40_update_ok ? '最終成功 ' . esc_html($s40_update_ok) : '待機中'); ?><br>
                自動運転: <?php echo !empty($s['auto_enabled']) ? 'ON' : 'OFF'; ?>'''
if status_anchor in s:
    s=s.replace(status_anchor,status_new,1)

p.write_text(s,encoding="utf-8")
print("self updater added")
