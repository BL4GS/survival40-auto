"""Staging-only WordPress updater diagnostics; observational, no updates triggered."""
from pathlib import Path
p=Path("survival40-auto/survival40-auto.php")
s=p.read_text(encoding="utf-8")
hook="        add_action('admin_menu', [$this, 's40_affiliate_ledger_menu']);"
assert s.count(hook)==1
s=s.replace(hook,hook+"""
        add_action('upgrader_process_complete', [$this, 's40_update_audit_after_upgrade'], 20, 2);
        add_action('admin_init', [$this, 's40_update_audit_admin_check'], 50);""",1)
anchor="    public function s40_affiliate_ledger_menu() {"
assert s.count(anchor)==1
method=r'''    // Persist bounded, non-sensitive status observations only.
    private function s40_update_audit_record($reason, $details=[]) {
        $log = get_option('s40_update_audit_v1', []);
        if (!is_array($log)) $log = [];
        $log[] = [
            'time'=>current_time('mysql'),
            'reason'=>sanitize_key($reason),
            'version'=>self::VERSION,
            'details'=>$details,
        ];
        update_option('s40_update_audit_v1', array_slice($log, -20), false);
    }

    public function s40_update_audit_after_upgrade($upgrader, $hook_extra) {
        if (($hook_extra['type'] ?? '') !== 'plugin' || ($hook_extra['action'] ?? '') !== 'update') return;
        $plugin = plugin_basename(__FILE__);
        $plugins = isset($hook_extra['plugins']) && is_array($hook_extra['plugins'])
            ? $hook_extra['plugins'] : [$hook_extra['plugin'] ?? ''];
        if (!in_array($plugin, $plugins, true)) return;
        $active = (array)get_option('active_plugins', []);
        $this->s40_update_audit_record('upgrader_complete', [
            'active_option'=>in_array($plugin, $active, true),
            'target_plugin'=>$plugin,
        ]);
    }

    public function s40_update_audit_admin_check() {
        if (!current_user_can('manage_options')) return;
        $plugin = plugin_basename(__FILE__);
        $active = (array)get_option('active_plugins', []);
        $last = get_option('s40_update_audit_last_state', []);
        $current = ['version'=>self::VERSION, 'active_option'=>in_array($plugin, $active, true)];
        if ($last !== $current) {
            $this->s40_update_audit_record('admin_state_changed', $current);
            update_option('s40_update_audit_last_state', $current, false);
        }
    }

'''
s=s.replace(anchor,method+anchor,1)
p.write_text(s,encoding="utf-8")
print("staged bounded update diagnostic log; no updater calls or activation changes")
