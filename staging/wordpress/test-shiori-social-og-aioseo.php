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

// Current public articles may already have the original portrait from an
// earlier rollout. Replace ONLY exact same-article original art in staging.
$portrait = 'https://raw.githubusercontent.com/BL4GS/survival40-auto/main/assets/instagram/auto/516.png';
$portraitTags = array(
    'og:image' => $portrait,
    'og:image:secure_url' => $portrait,
    'og:image:width' => '1080',
    'og:image:height' => '1350',
    'og:title' => 'AIOSEO original title',
    'og:description' => 'AIOSEO original description',
);
$updated = $fb($portraitTags);
check($updated['og:image'] === $image
    && $updated['og:image:secure_url'] === $image
    && $updated['og:image:width'] === '1200'
    && $updated['og:image:height'] === '630',
    'Exact old portrait card switches to 1200x630 in staging');
check($updated['og:title'] === $portraitTags['og:title']
    && $updated['og:description'] === $portraitTags['og:description'],
    'Other AIOSEO metadata must survive the image switch unchanged');
$twPortrait = array(
    'twitter:image' => $portrait,
    'twitter:image:src' => $portrait,
    'twitter:card' => 'summary_large_image',
    'twitter:description' => 'Preserve this',
);
$twUpdated = $tw($twPortrait);
check($twUpdated['twitter:image'] === $image
    && $twUpdated['twitter:image:src'] === $image
    && $twUpdated['twitter:description'] === 'Preserve this',
    'Exact portrait Twitter card switches without changing other metadata');

// Protect any distinct social image or contradictory metadata, including
// possible owner choices unknown to this prototype.
$portraitTags['og:image'] = 'https://www.survival40.com/owner-cover.jpg';
check($fb($portraitTags) === $portraitTags, 'Owner-selected image wins even with old dimensions');
$portraitTags['og:image'] = $portrait;
$portraitTags['og:image:secure_url'] = 'https://www.survival40.com/custom-secure.jpg';
check($fb($portraitTags) === $portraitTags, 'Conflicting secure image blocks replacement');
$portraitTags['og:image:secure_url'] = $portrait;
$portraitTags['og:image:width'] = '1920';
check($fb($portraitTags) === $portraitTags, 'Conflicting custom width blocks replacement');
$portraitTags['og:image:width'] = '1080';
$portraitTags['og:image:height'] = '1440';
check($fb($portraitTags) === $portraitTags, 'Conflicting custom height blocks replacement');
check($fb(array('og:image:width' => '777')) === array('og:image:width' => '777'),
      'Unmatched dimensions without an image remain unchanged');
$otherTwitter = array(
    'twitter:image' => $portrait,
    'twitter:image:src' => 'https://www.survival40.com/owner-image.jpg',
);
check($tw($otherTwitter) === $otherTwitter, 'Conflicting Twitter src blocks replacement');
$twitterCardOwner = array('twitter:image' => $portrait, 'twitter:card' => 'summary');
$twitterResult = $tw($twitterCardOwner);
check($twitterResult['twitter:card'] === 'summary', 'Existing Twitter card setting preserved');
check($twitterResult['twitter:image'] === $image, 'Image switches without card preference mutation');

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
