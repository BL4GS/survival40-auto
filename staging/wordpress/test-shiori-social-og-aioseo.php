<?php
/** Offline contract for disabled-by-default AIOSEO social tags. */
define('ABSPATH', dirname(__DIR__, 2) . '/');
$GLOBALS['filters'] = array();
$GLOBALS['active_id'] = 516;
$GLOBALS['active_type'] = true;
$GLOBALS['active_status'] = 'publish';
$GLOBALS['active_permalink'] = 'https://www.survival40.com/women-men-grooming-impression-survey/';

function add_filter($hook, $callback, $priority = 10, $args = 1) {
    $GLOBALS['filters'][$hook] = $callback;
}
function is_singular($type) {
    return $type === 'post' && $GLOBALS['active_type'];
}
function get_queried_object_id() {
    return $GLOBALS['active_id'];
}
function get_post_status($id) {
    return $GLOBALS['active_status'];
}
function get_permalink($id) {
    return $GLOBALS['active_permalink'];
}
function check($condition, $message) {
    if (!$condition) {
        fwrite(STDERR, 'FAIL: ' . $message . PHP_EOL);
        exit(1);
    }
}

if (($argv[1] ?? '') === 'enabled') {
    define('SURVIVAL40_OG_STAGING_ENABLED', true);
}
require __DIR__ . '/shiori-social-og-aioseo.php';

if (($argv[1] ?? '') !== 'enabled') {
    check(count($GLOBALS['filters']) === 0, 'No hook should register without explicit opt-in');
    echo "PASS: prototype disabled by default\n";
    exit(0);
}
check(count($GLOBALS['filters']) === 2, 'Only AIOSEO official filters registered');
$fb = $GLOBALS['filters']['aioseo_facebook_tags'];
$tw = $GLOBALS['filters']['aioseo_twitter_tags'];
$base = array('og:title' => 'Original AIOSEO title', 'og:description' => 'Keep this unchanged');
$image = 'https://raw.githubusercontent.com/BL4GS/survival40-auto/main/assets/social/og/516.png';
$result = $fb($base);
check($result['og:image'] === $image, 'Article #516 gets exact original image');
check($result['og:image:width'] === '1200' && $result['og:image:height'] === '630',
      'Original image dimensions retained');
check($result['og:title'] === $base['og:title'], 'Existing social title untouched');
$twitter = $tw(array('twitter:title' => 'Keep Twitter title'));
check($twitter['twitter:image'] === $image, 'Exact Twitter original image');
check($twitter['twitter:card'] === 'summary_large_image', 'Card type is large');
$ownerImage = array('og:image' => 'https://www.survival40.com/media/owner-picked.jpg');
check($fb($ownerImage) === $ownerImage, 'Owner social image never overwritten');
$twitterOwner = array('twitter:image' => 'https://www.survival40.com/own-card.jpg');
check($tw($twitterOwner) === $twitterOwner, 'Owner Twitter image never overwritten');
check($fb('unexpected') === 'unexpected', 'Unexpected tag representation preserved');

$GLOBALS['active_type'] = false;
check($fb($base) === $base, 'Non-post pages unchanged');
$GLOBALS['active_type'] = true;
$GLOBALS['active_status'] = 'draft';
check($fb($base) === $base, 'Drafts unchanged');
$GLOBALS['active_status'] = 'publish';
$GLOBALS['active_id'] = 777;
check($fb($base) === $base, 'Non-allowlisted published posts unchanged');

$GLOBALS['active_id'] = 512;
$GLOBALS['active_permalink'] = 'https://www.survival40.com/40s-eye-strain-massage-breaks/';
check($fb($base)['og:image'] ===
      'https://raw.githubusercontent.com/BL4GS/survival40-auto/main/assets/social/og/512.png',
      'Article #512 gets its own image');
$GLOBALS['active_permalink'] = 'https://www.survival40.com/another-article/';
check($fb($base) === $base, 'ID and permalink mismatch must stop injection');
echo "PASS: staging-only AIOSEO native social tag behavior, no site changes\n";
