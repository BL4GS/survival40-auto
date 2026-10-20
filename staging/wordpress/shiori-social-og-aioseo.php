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

/**
 * The currently emitted social image on some articles is our *own*
 * portrait 1080x1350 PNG. In staging ONLY, a precisely matching original
 * portrait may be switched to the previously verified 1200x630 card.
 * Any other image or inconsistent associated metadata is left untouched.
 */
function survival40_staging_portrait_card() {
    $image = survival40_staging_verified_social_card();
    if ($image === null) {
        return null;
    }
    $id = (int) get_queried_object_id();
    return 'https://raw.githubusercontent.com/BL4GS/survival40-auto/main/assets/instagram/auto/' . $id . '.png';
}

function survival40_staging_empty_tag($tags, $key) {
    return !isset($tags[$key]) || $tags[$key] === '';
}

add_filter('aioseo_facebook_tags', function ($tags) {
    if (!is_array($tags)) {
        return $tags;
    }
    $image = survival40_staging_verified_social_card();
    $old = survival40_staging_portrait_card();
    if ($image === null || $old === null) {
        return $tags;
    }
    $hasImage = !survival40_staging_empty_tag($tags, 'og:image');
    if ($hasImage && (!is_string($tags['og:image']) || $tags['og:image'] !== $old)) {
        return $tags; // Existing owner-selected image wins.
    }
    // Preserve an unrelated secure URL, alternate image metadata, or owner
    // dimensions. Do not create contradictory tags during a test rollout.
    if (!survival40_staging_empty_tag($tags, 'og:image:secure_url')
        && $tags['og:image:secure_url'] !== $old) {
        return $tags;
    }
    if ($hasImage) {
        foreach (array('og:image:width' => 1080, 'og:image:height' => 1350) as $key => $size) {
            if (!survival40_staging_empty_tag($tags, $key)
                && (string) $tags[$key] !== (string) $size) {
                return $tags;
            }
        }
    } elseif (!survival40_staging_empty_tag($tags, 'og:image:width')
              || !survival40_staging_empty_tag($tags, 'og:image:height')) {
        return $tags;
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
    $old = survival40_staging_portrait_card();
    if ($image === null || $old === null) {
        return $tags;
    }
    // Existing arbitrary social images, including owner-selected images,
    // cannot be replaced. A conflicting Twitter src also blocks the change.
    foreach (array('twitter:image', 'twitter:image:src') as $key) {
        if (!survival40_staging_empty_tag($tags, $key)
            && (!is_string($tags[$key]) || $tags[$key] !== $old)) {
            return $tags;
        }
    }
    $tags['twitter:image'] = $image;
    if (array_key_exists('twitter:image:src', $tags)) {
        $tags['twitter:image:src'] = $image;
    }
    if (empty($tags['twitter:card'])) {
        $tags['twitter:card'] = 'summary_large_image';
    }
    return $tags;
}, 10, 1);
