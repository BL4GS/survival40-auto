"""Staging-only v0.19.22+ PHP patch: authenticated, read-only-to-content plan inbox.

DO NOT wire this patch into the v0.19.21 release flow. No WP posts, ad
switches, auto-publish behavior, or existing admin screens are changed.
"""
from pathlib import Path

TARGET = Path("survival40-auto/survival40-auto.php")

CONSTRUCTOR_ANCHOR = "        add_action('survival40_auto_cron', [$this, 'run_automation_cycle']);"
REST_REGISTRATION = """        // Future-version editorial intake: authenticated inbox only; no post creation.
        add_action('rest_api_init', [$this, 's40_register_editorial_plan_routes']);
"""

METHOD_ANCHOR = "    private function auto_existing_titles($limit = 120) {"

METHODS = r'''    // Editorial inbox: only administrator-authorized WordPress REST requests.
    // Works with WordPress Application Passwords or existing authenticated admin.
    public function s40_register_editorial_plan_routes() {
        register_rest_route('survival40/v1', '/editorial-plans', [
            [
                'methods' => WP_REST_Server::READABLE,
                'callback' => [$this, 's40_editorial_plan_status'],
                'permission_callback' => [$this, 's40_editorial_plan_permission'],
            ],
            [
                'methods' => WP_REST_Server::CREATABLE,
                'callback' => [$this, 's40_editorial_plan_ingest'],
                'permission_callback' => [$this, 's40_editorial_plan_permission'],
            ],
        ]);
    }

    public function s40_editorial_plan_permission($request) {
        return current_user_can('manage_options');
    }

    public function s40_editorial_plan_status($request) {
        $queue = get_option('s40_editorial_plan_queue_v1', []);
        if (!is_array($queue)) $queue = [];
        return new WP_REST_Response([
            'schema' => 'survival40.wp_plan_queue.v1',
            'count' => count($queue),
            'capacity' => 30,
            'items' => array_map(function($item) {
                return [
                    'topic_id' => $item['topic_id'],
                    'title' => $item['title'],
                    'category' => $item['category'],
                    'status' => $item['status'],
                ];
            }, array_values($queue)),
            'wp_posts_created' => 0,
            'publication_enabled' => false,
        ], 200);
    }

    public function s40_editorial_plan_ingest($request) {
        if (strlen($request->get_body()) > 50000) {
            return new WP_Error('s40_payload_large', 'Plan payload exceeds size limit', ['status'=>413]);
        }
        $document = $request->get_json_params();
        if (!is_array($document)
            || ($document['schema'] ?? '') !== 'survival40.wp_plan_handoff.v1'
            || ($document['ready_to_publish'] ?? null) !== false
            || ($document['wp_posts_written'] ?? null) !== 0
            || ($document['threads_posts_written'] ?? null) !== 0
            || !isset($document['plans']) || !is_array($document['plans'])
            || count($document['plans']) > 5) {
            return new WP_Error('s40_bad_plan_schema', 'Only unresearched planning handoffs accepted', ['status'=>400]);
        }

        // Atomic option creation is a conservative single-writer guard: concurrent
        // deliveries refuse to race on the WordPress option-based queue.
        if (!add_option('s40_editorial_ingest_lock_v1', time(), '', false)) {
            return new WP_Error('s40_ingest_busy', 'Editorial inbox is busy; retry later', ['status'=>409]);
        }
        try {
            $queue = get_option('s40_editorial_plan_queue_v1', []);
            if (!is_array($queue) || count($queue) > 30) {
                return new WP_Error('s40_bad_queue', 'Editorial inbox state invalid', ['status'=>409]);
            }
            $map = $this->auto_category_map();
            $existing_titles = $this->auto_existing_titles(200);
            $accepted = [];
            $held = [];
            $duplicate = 0;
            foreach ($document['plans'] as $index=>$proposal) {
                $reason = '';
                if (!is_array($proposal)) {
                    $reason = 'invalid_object';
                } elseif (!preg_match('/^s40-[a-f0-9]{20}$/D', (string)($proposal['topic_id'] ?? ''))) {
                    $reason = 'invalid_topic_id';
                } elseif (($proposal['stage'] ?? '') !== 'needs_independent_source_research'
                    || ($proposal['safety']['publish_authorized'] ?? null) !== false
                    || ($proposal['safety']['no_affiliate_assigned'] ?? null) !== true
                    || ($proposal['safety']['requires_existing_wordpress_quality_gates'] ?? null) !== true
                    || ($proposal['safety']['must_recheck_all_wordpress_posts_including_drafts'] ?? null) !== true
                    || ($proposal['editorial']['sources_checked'] ?? null) !== false
                    || ($proposal['editorial']['verified_sources'] ?? null) !== 0
                    || ($proposal['plugin_planner_input']['amazon_query'] ?? null) !== '') {
                    $reason = 'unsafe_unresearched_state';
                } else {
                    $plan = $proposal['plugin_planner_input'] ?? [];
                    $topic_id = (string)$proposal['topic_id'];
                    $title = sanitize_text_field($plan['title'] ?? '');
                    $category = sanitize_text_field($plan['category'] ?? '');
                    $keyword = sanitize_text_field($plan['keyword'] ?? '');
                    $excerpt = sanitize_textarea_field($plan['excerpt'] ?? '');
                    $seo_title = sanitize_text_field($plan['seo_title'] ?? '');
                    $questions = $proposal['editorial']['research_questions'] ?? [];
                    if (!isset($map[$category]) || mb_strlen($title) < 18 || mb_strlen($title) > 90
                        || mb_strlen($keyword) < 4 || mb_strlen($keyword) > 90
                        || mb_strlen($excerpt) < 30 || mb_strlen($excerpt) > 160
                        || mb_strlen($seo_title) < 10 || mb_strlen($seo_title) > 90
                        || !is_array($questions) || count($questions) < 2 || count($questions) > 4) {
                        $reason = 'invalid_topic_fields';
                    } elseif (isset($queue[$topic_id]) || isset($accepted[$topic_id])) {
                        $duplicate++;
                        continue;
                    } elseif (count($queue) + count($accepted) >= 30) {
                        $reason = 'queue_full';
                    } else {
                        $valid_questions = [];
                        foreach ($questions as $q) {
                            if (!is_string($q) || mb_strlen($q) < 12 || mb_strlen($q) > 200) {
                                $reason = 'invalid_research_question';
                                break;
                            }
                            $valid_questions[] = sanitize_textarea_field($q);
                        }
                        $normalized = $this->normalize_title_key($title);
                        if (!$reason) foreach ($existing_titles as $old) {
                            $prior = $this->normalize_title_key($old);
                            if ($normalized === $prior) {
                                $reason = 'existing_wordpress_post';
                                break;
                            }
                            // Additional conservative check for near duplicate headlines.
                            if (mb_strlen($normalized) >= 10 && mb_strlen($prior) >= 10) {
                                similar_text($normalized, $prior, $pct);
                                if ($pct >= 84.0) {
                                    $reason = 'similar_wordpress_post';
                                    break;
                                }
                            }
                        }
                        if (!$reason) foreach (array_merge($queue, $accepted) as $other) {
                            if ($this->normalize_title_key($other['title']) === $normalized) {
                                $reason = 'duplicate_queue_title';
                                break;
                            }
                        }
                        if (!$reason) {
                            $accepted[$topic_id] = [
                                'topic_id' => $topic_id,
                                'title' => $title,
                                'category' => $category,
                                'keyword' => $keyword,
                                'excerpt' => $excerpt,
                                'seo_title' => $seo_title,
                                'research_questions' => $valid_questions,
                                'advertising_policy' => ($proposal['editorial']['advertising_policy'] ?? '') === 'optional'
                                    ? 'optional' : 'none',
                                'status' => 'awaiting_independent_research',
                                'ymyl' => !empty($map[$category]['ymyl'])
                                    || !empty($proposal['editorial']['requires_ymyl_gate']),
                                'received_at' => current_time('mysql'),
                            ];
                        }
                    }
                }
                if ($reason) $held[] = ['index'=>intval($index), 'reason'=>$reason];
            }
            if ($accepted) {
                $updated = update_option('s40_editorial_plan_queue_v1',
                    array_merge($queue, $accepted), false);
                if (!$updated) {
                    return new WP_Error('s40_queue_write_failed', 'Editorial inbox could not be saved', ['status'=>503]);
                }
            }
            return new WP_REST_Response([
                'accepted' => count($accepted),
                'duplicate' => $duplicate,
                'held' => $held,
                'queue_count' => count($queue) + count($accepted),
                'wp_posts_created' => 0,
                'ready_to_publish' => false,
            ], 202);
        } finally {
            delete_option('s40_editorial_ingest_lock_v1');
        }
    }

'''


def transform(source):
    if source.count(CONSTRUCTOR_ANCHOR) != 1 or source.count(METHOD_ANCHOR) != 1:
        raise ValueError("Unexpected plugin structure; fail closed")
    if "s40_register_editorial_plan_routes" in source or "s40_editorial_plan_ingest" in source:
        raise ValueError("Editorial inbox already installed; refuse to patch twice")
    result = source.replace(CONSTRUCTOR_ANCHOR, REST_REGISTRATION + CONSTRUCTOR_ANCHOR, 1)
    result = result.replace(METHOD_ANCHOR, METHODS + METHOD_ANCHOR, 1)
    return result


def main():
    before = TARGET.read_text(encoding="utf-8")
    after = transform(before)
    TARGET.write_text(after, encoding="utf-8")
    print("STAGED: administrator-only REST inbox, queue storage only; no posts published.")


if __name__ == "__main__":
    main()
