"""Fix AIOSEO persistence for the existing autonomous article generator.

Applied after 0.19.20 and staged affiliate patches, before version promotion.
Fail closed if source anchors drift. Does NOT edit existing posts or ads.
"""
from pathlib import Path

path = Path("survival40-auto/survival40-auto.php")
source = path.read_text(encoding="utf-8")

old_call = "        $this->sync_aioseo_rest($post_id, $p);"
assert source.count(old_call) == 1, "expected exactly one auto-article SEO sync call"

anchor = "    private function generate_planned_article($p) {"
assert source.count(anchor) == 1, "auto generation method anchor changed"

helper = r'''    // AIOSEO v4/v5 stores its SEO fields in aioseo_posts, not WP postmeta.
    // The existing REST sync can fail during unattended WP-Cron generation.
    // Use AIOSEO's own model; preserve anything already edited by a human.
    private function s40_sync_aioseo_native($post_id, $plan) {
        $post_id = (int) $post_id;
        if ($post_id <= 0 || !is_array($plan)) return false;

        $title = sanitize_text_field((string) ($plan['seo_title'] ?? $plan['title'] ?? ''));
        $description = sanitize_text_field(wp_strip_all_tags((string) ($plan['excerpt'] ?? '')));
        if (function_exists('mb_substr')) {
            $description = mb_substr($description, 0, 155, 'UTF-8');
        }
        if ($title === '' || $description === '') {
            update_post_meta($post_id, '_survival40_seo_sync_status', 'missing_plan_data');
            return false;
        }

        $model_class = '\\AIOSEO\\Plugin\\Common\\Models\\Post';
        if (!class_exists($model_class) || !method_exists($model_class, 'getPost')) {
            update_post_meta($post_id, '_survival40_seo_sync_status', 'aioseo_unavailable');
            return false;
        }
        try {
            $meta = $model_class::getPost($post_id);
            if (!is_object($meta) || !method_exists($meta, 'save')) {
                update_post_meta($post_id, '_survival40_seo_sync_status', 'model_unavailable');
                return false;
            }
            $changed = false;
            if (trim((string) ($meta->title ?? '')) === '') {
                $meta->title = $title;
                $changed = true;
            }
            if (trim((string) ($meta->description ?? '')) === '') {
                $meta->description = $description;
                $changed = true;
            }
            if ($changed && $meta->save() === false) {
                update_post_meta($post_id, '_survival40_seo_sync_status', 'save_failed');
                return false;
            }
            // A shortcode, explicit canonical, social fields and existing SEO
            // are deliberately left untouched.
            update_post_meta($post_id, '_survival40_seo_sync_status', $changed ? 'saved' : 'already_set');
            return true;
        } catch (\Throwable $error) {
            // Do not expose stack traces, credentials or article data in post meta.
            update_post_meta($post_id, '_survival40_seo_sync_status', 'exception');
            return false;
        }
    }

'''

source = source.replace(anchor, helper + anchor, 1)
source = source.replace(old_call, "        $this->s40_sync_aioseo_native($post_id, $p);", 1)

# category_id() is already the generator's category selector.
# Never silently publish an article as Uncategorized on lookup failure.
old_category = "        $cat = $this->category_id($p['category']);"
generation_start = source.index(anchor)
generation_end = source.index("    public function handle_run_auto_once()", generation_start)
section = source[generation_start:generation_end]
assert section.count(old_category) == 1, "planned-article category assignment changed"
new_category = r'''        $cat = $this->category_id($p['category']);
        if (!$cat && !empty($p['category'])) {
            $matching_category = get_term_by('name', sanitize_text_field($p['category']), 'category');
            if ($matching_category && !is_wp_error($matching_category)) {
                $cat = (int) $matching_category->term_id;
            }
        }
        if (!$cat) {
            return new WP_Error('s40_category_not_found', '予定カテゴリが存在しないため自動公開を停止しました。');
        }'''
section = section.replace(old_category, new_category, 1)
source = source[:generation_start] + section + source[generation_end:]

assert source.count("private function s40_sync_aioseo_native(") == 1
assert source.count(old_call) == 0
assert source.count("s40_category_not_found") == 1
path.write_text(source, encoding="utf-8")
print("Staged AIOSEO native sync and missing-category fail-closed guard.")
