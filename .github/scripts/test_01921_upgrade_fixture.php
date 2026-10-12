<?php
/**
 * ISOLATED WordPress fixture only (WP-CLI eval-file).
 * Synthetic posts and settings; never execute on survival40.com.
 */
if (!defined('ABSPATH')) { throw new RuntimeException('WP-CLI WordPress required'); }
if (getenv('S40_ISOLATED_REHEARSAL') !== 'ephemeral-only') {
    throw new RuntimeException('Not an approved disposable rehearsal instance');
}
if (strpos(site_url(), 'localhost') === false) {
    throw new RuntimeException('Refusing to run fixture on non-local WordPress');
}
$mode = getenv('S40_REHEARSAL_PHASE');
global $wpdb;
if ($mode === 'seed') {
    $old_posts = $wpdb->get_col("SELECT ID FROM {$wpdb->posts} WHERE post_type = 'post'");
    foreach ($old_posts as $old_id) {
        wp_delete_post((int)$old_id, true); // isolated test site only
    }
    for ($i = 1; $i <= 39; $i++) {
        $status = $i <= 23 ? 'publish' : 'draft';
        $id = wp_insert_post([
            'post_type' => 'post',
            'post_status' => $status,
            'post_author' => 1,
            'post_title' => sprintf('Survival40 isolated %s test %02d',
                $status, $i),
            'post_content' => '<p>Isolated release safety test only: ' .
                $i . '</p>',
        ], true);
        if (is_wp_error($id) || !$id) {
            throw new RuntimeException('Could not seed isolated post ' . $i);
        }
    }
    $settings = get_option('survival40_auto_settings', []);
    if (!is_array($settings)) { $settings = []; }
    $settings['auto_enabled'] = 0;
    $settings['auto_publish_general'] = 0;
    $settings['affiliate_notice'] = 1;
    $settings['show_sources'] = 1;
    $settings['auto_interval'] = 'daily';
    update_option('survival40_auto_settings', $settings, false);
    // Matches actual live production where the frontend ad gate was absent.
    delete_option('s40_affiliate_frontend_enabled');
    update_option('auto_update_plugins',
        ['survival40-auto/survival40-auto.php'], false);
    echo "PASS: generated 23 published and 16 draft synthetic posts\n";
    exit;
}
if ($mode !== 'snapshot') {
    throw new RuntimeException('Unknown rehearsal phase');
}
$posts = $wpdb->get_results(
    "SELECT ID, post_title, post_status, post_content FROM {$wpdb->posts}
     WHERE post_type='post' AND post_status IN ('publish','draft')
     ORDER BY ID ASC",
    ARRAY_A
);
$counts = ['publish' => 0, 'draft' => 0];
$rows = [];
foreach ($posts as $row) {
    if (!array_key_exists($row['post_status'], $counts)) {
        throw new RuntimeException('Unexpected post status');
    }
    $counts[$row['post_status']]++;
    $rows[] = [
        'id' => (int)$row['ID'],
        'status' => $row['post_status'],
        'title' => $row['post_title'],
        'content_sha256' => hash('sha256', $row['post_content']),
    ];
}
if ($counts !== ['publish' => 23, 'draft' => 16]) {
    throw new RuntimeException('Synthetic article inventory changed');
}
$settings = get_option('survival40_auto_settings', []);
if (!is_array($settings)
    || (string)($settings['auto_enabled'] ?? '') !== '0'
    || (string)($settings['auto_publish_general'] ?? '') !== '0'
    || (string)($settings['affiliate_notice'] ?? '') !== '1'
    || (string)($settings['show_sources'] ?? '') !== '1'
    || ($settings['auto_interval'] ?? '') !== 'daily') {
    throw new RuntimeException('Editorial/ad controls changed');
}
if (get_option('s40_affiliate_frontend_enabled', 'no') !== 'no') {
    throw new RuntimeException('Frontend advertising became enabled');
}
$updaters = get_option('auto_update_plugins', []);
if (!is_array($updaters)
    || !in_array('survival40-auto/survival40-auto.php', $updaters, true)) {
    throw new RuntimeException('Plugin auto-update enrollment changed');
}
echo wp_json_encode([
    'counts' => $counts,
    'posts' => $rows,
    'settings' => [
        'auto_enabled' => (string)$settings['auto_enabled'],
        'auto_publish_general' => (string)$settings['auto_publish_general'],
        'affiliate_notice' => (string)$settings['affiliate_notice'],
        'show_sources' => (string)$settings['show_sources'],
        'auto_interval' => $settings['auto_interval'],
    ],
    'frontend_ads' => get_option('s40_affiliate_frontend_enabled', 'no'),
    'auto_update_plugins' => $updaters,
], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) . "\n";
