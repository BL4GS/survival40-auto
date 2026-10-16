<?php
/**
 * Survival40 AIOSEO original Shiori social image proof of concept.
 *
 * STAGING ONLY. NOT INSTALLED OR ENABLED ON WORDPRESS.
 *
 * Requires an EXPLICIT per-environment enable flag defined before loading:
 *   define('SURVIVAL40_OG_STAGING_ENABLED', true);
 *
 * This prototype is deliberately limited to two already-verified public articles.
 * NEVER generalize image URLs to arbitrary articles or enable on production
 * without staging preview, rollback, and full SEO/meta compatibility checks.
 */
if (!defined('ABSPATH')) {
    exit;
}
if (!defined('SURVIVAL40_OG_STAGING_ENABLED') || SURVIVAL40_OG_STAGING_ENABLED !== true) {
    return;
}

/**
 * Output an image URL only for an exact, previously verified permalink.
 * No GET/HEAD request and no modification of the post, theme or database.
 */
function survival40_staging_verified_social_card() {
    if (!function_exists('is_singular') || !is_singular('post')) {
        return null;
    }
    $id = (int) get_queried_object_id();
    $verified = array(
        512 => array(
            'permalink' => 'https://www.survival40.com/40s-eye-strain-massage-breaks/',
            'image' => 'https://raw.githubusercontent.com/BL4GS/survival40-auto/main/assets/social/og/512.png',
        ),
        516 => array(
            'permalink' => 'https://www.survival40.com/women-men-grooming-impression-survey/',
            'image' => 'https://raw.githubusercontent.com/BL4GS/survival40-auto/main/assets/social/og/516.png',
        ),
    );
    if (!isset($verified[$id]) || get_post_status($id) !== 'publish') {
        return null;
    }
    $article = $verified[$id];
    if (get_permalink($id) !== $article['permalink']) {
        return null;
    }
    return $article['image'];
}

add_filter('aioseo_facebook_tags', function ($tags) {
    if (!is_array($tags)) {
        return $tags;
    }
    $image = survival40_staging_verified_social_card();
    if ($image === null || !empty($tags['og:image'])) {
        return $tags; // Owner's manually selected AIOSEO social image wins.
    }
    $tags['og:image'] = $image;
    $tags['og:image:secure_url'] = $image;
    $tags['og:image:width'] = '1200';
    $tags['og:image:height'] = '630';
    return $tags;
}, 10, 1);

add_filter('aioseo_twitter_tags', function ($tags) {
    if (!is_array($tags)) {
        return $tags;
    }
    $image = survival40_staging_verified_social_card();
    if ($image === null || !empty($tags['twitter:image'])) {
        return $tags;
    }
    $tags['twitter:image'] = $image;
    if (empty($tags['twitter:card'])) {
        $tags['twitter:card'] = 'summary_large_image';
    }
    return $tags;
}, 10, 1);
