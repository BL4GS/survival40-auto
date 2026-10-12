"""Future-release patch: research-only WordPress editorial inbox consumer.

Applied AFTER patch_planner_failclosed_next.py and patch_editorial_intake_next.py.
Not invoked by current 0.19.21 release. Queued plans MUST remain draft-only
even when the site's general auto-publish option is enabled.
"""
from pathlib import Path

TARGET = Path("survival40-auto/survival40-auto.php")
METHOD_ANCHOR = "    private function auto_existing_titles($limit = 120) {"
CYCLE_START = "    public function run_automation_cycle() {"
CYCLE_END = "    private function category_id($name) {"
PLAN_LINE = "            $plan = $this->plan_next_article();"
RESULT_LINE = "            $result = $this->generate_planned_article($plan);"
DONE_LINE = "            $done[] = $result;"
STATUS_LINE = "if (empty($p['ymyl']) && empty($warnings) && $research_ok && $review_ok && !empty($s['auto_publish_general'])) $status = 'publish';"
CATEGORY_LINE = "        $cat = $this->category_id($p['category']);\n        $source_meta = [];"

METHODS = r'''    // Future inbox consumer: claim at most one unresearched plan per cycle.
    // Existing WordPress planning remains the fallback when inbox is empty.
    private function s40_editorial_queue_claim() {
        $queue = get_option('s40_editorial_plan_queue_v1', []);
        if (!is_array($queue) || !$queue) return null;
        if (!add_option('s40_editorial_ingest_lock_v1', time(), '', false)) {
            return new WP_Error('s40_editorial_busy', '企画キューは処理中です。');
        }
        try {
            // Freshly verify all live WordPress titles, including nonpublic posts.
            $titles = $this->auto_existing_titles(200);
            $categories = $this->auto_category_map();
            foreach ($queue as $id=>$item) {
                if (($item['status'] ?? '') !== 'awaiting_independent_research') continue;
                $title = (string)($item['title'] ?? '');
                $category = (string)($item['category'] ?? '');
                if (!preg_match('/^s40-[a-f0-9]{20}$/D', (string)$id)
                    || !isset($categories[$category]) || !$title) {
                    $queue[$id]['status'] = 'blocked_invalid_plan';
                    update_option('s40_editorial_plan_queue_v1', $queue, false);
                    continue;
                }
                $normalized = $this->normalize_title_key($title);
                $already_exists = false;
                foreach ($titles as $old) {
                    $prior = $this->normalize_title_key($old);
                    if ($normalized === $prior) { $already_exists = true; break; }
                    if (mb_strlen($normalized) >= 10 && mb_strlen($prior) >= 10) {
                        similar_text($normalized, $prior, $pct);
                        if ($pct >= 84.0) { $already_exists = true; break; }
                    }
                }
                if ($already_exists) {
                    $queue[$id]['status'] = 'blocked_duplicate_post';
                    update_option('s40_editorial_plan_queue_v1', $queue, false);
                    continue;
                }

                $cfg = $categories[$category];
                $source_group = $cfg['source_group'];
                if ($category === '40代の不調') {
                    if (preg_match('/(調光レンズ|フォトクロミック|可視光調光)/u', $title))
                        $source_group = 'photochromic';
                    elseif (preg_match('/(ドライアイ|目の乾燥|眼の乾燥)/u', $title))
                        $source_group = 'dryeye';
                    elseif (preg_match('/(目|眼|視力|老視|老眼|眼精疲労|眼鏡)/u', $title))
                        $source_group = 'eye';
                }
                $queue[$id]['status'] = 'processing_research';
                $queue[$id]['started_at'] = current_time('mysql');
                if (!update_option('s40_editorial_plan_queue_v1', $queue, false)) {
                    return new WP_Error('s40_queue_write_failed', '企画の処理状態を保存できませんでした。');
                }
                return [
                    'title'=>$title,
                    'slug'=>sanitize_title($title),
                    'keyword'=>$item['keyword'],
                    'category'=>$category,
                    'excerpt'=>$item['excerpt'],
                    'seo_title'=>$item['seo_title'],
                    'amazon_candidate'=>'',
                    'allow_amazon'=>0,
                    'allow_a8'=>0,
                    'source_group'=>$source_group,
                    'ymyl'=>!empty($cfg['ymyl']) || !empty($item['ymyl']) ? 1 : 0,
                    'planner_reason'=>'事前企画キューから取得。根拠調査と審査を必須とする。',
                    '_s40_editorial_queue'=>1,
                    '_s40_queued_topic_id'=>$id,
                ];
            }
            return null;
        } finally {
            delete_option('s40_editorial_ingest_lock_v1');
        }
    }

    private function s40_editorial_queue_finish($id, $result) {
        // A failed completion keeps the row in "processing_research", which
        // blocks auto-retry until the uncertain WordPress state is checked.
        if (!add_option('s40_editorial_ingest_lock_v1', time(), '', false)) return;
        try {
            $queue = get_option('s40_editorial_plan_queue_v1', []);
            if (!is_array($queue) || !isset($queue[$id])
                || ($queue[$id]['status'] ?? '') !== 'processing_research') return;
            if (is_wp_error($result)) {
                $queue[$id]['status'] = 'held_after_research_failure';
                $queue[$id]['failure_code'] = sanitize_key($result->get_error_code());
            } elseif (is_array($result) && ($result['status'] ?? '') === 'draft') {
                $queue[$id]['status'] = 'draft_created_after_review';
                $queue[$id]['post_id'] = intval($result['post_id'] ?? 0);
            } else {
                $queue[$id]['status'] = 'held_unexpected_result';
            }
            $queue[$id]['finished_at'] = current_time('mysql');
            update_option('s40_editorial_plan_queue_v1', $queue, false);
        } finally {
            delete_option('s40_editorial_ingest_lock_v1');
        }
    }

'''


def transform(source):
    if source.count(METHOD_ANCHOR) != 1 or source.count(CYCLE_START) != 1 or source.count(CYCLE_END) != 1:
        raise ValueError("Unknown WordPress source structure")
    if "s40_editorial_queue_claim" in source:
        raise ValueError("Queue consumer is already installed")
    if "s40_editorial_plan_ingest" not in source or "s40_plan_unavailable" not in source:
        raise ValueError("Apply prior intake and failclosed patches first")
    first, tail = source.split(CYCLE_START, 1)
    cycle, after = tail.split(CYCLE_END, 1)
    if cycle.count(PLAN_LINE) != 1 or cycle.count(RESULT_LINE) != 1 or cycle.count(DONE_LINE) != 1:
        raise ValueError("Automation cycle changed; refuse patch")
    cycle = cycle.replace(
        PLAN_LINE,
        "            $plan = $this->s40_editorial_queue_claim();\n"
        "            if ($plan === null) $plan = $this->plan_next_article();",
        1,
    )
    cycle = cycle.replace(
        RESULT_LINE,
        RESULT_LINE
        + "\n            if (!empty($plan['_s40_queued_topic_id'])) "
        "$this->s40_editorial_queue_finish($plan['_s40_queued_topic_id'], $result);",
        1,
    )
    cycle = cycle.replace(
        DONE_LINE,
        DONE_LINE + "\n            if (!empty($plan['_s40_editorial_queue'])) break; // one queue plan/cycle",
        1,
    )
    source = first + CYCLE_START + cycle + CYCLE_END + after
    if source.count(STATUS_LINE) != 1 or source.count(CATEGORY_LINE) != 1:
        raise ValueError("Article creation guards changed")
    # Never publish an externally imported proposal directly, even if site's
    # general non-YMYL auto-publish flag is on.
    source = source.replace(
        STATUS_LINE,
        STATUS_LINE.replace("&& !empty($s['auto_publish_general'])",
                            "&& !empty($s['auto_publish_general']) && empty($p['_s40_editorial_queue'])"),
        1,
    )
    quality_gate = """        if (!empty($p['_s40_editorial_queue']) && (!$research_ok || !$review_ok || !empty($warnings))) {
            // Never fill WordPress with unchecked or unsupported queued articles.
            return new WP_Error('s40_queue_quality_hold',
                '企画の直接的な根拠と編集審査が揃わず、下書き作成を保留しました。');
        }

"""
    source = source.replace(CATEGORY_LINE, quality_gate + CATEGORY_LINE, 1)
    source = source.replace(METHOD_ANCHOR, METHODS + METHOD_ANCHOR, 1)
    return source


def main():
    before = TARGET.read_text(encoding="utf-8")
    after = transform(before)
    TARGET.write_text(after, encoding="utf-8")
    print("STAGED: queued brief -> existing research/review -> draft only; no auto publication")


if __name__ == "__main__":
    main()
