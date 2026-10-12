<?php
/** Simulated WordPress hooks/options REST test for the staged editorial inbox. */
error_reporting(E_ALL);
define('ABSPATH', '/tmp/');
$GLOBALS['s40_options'] = [];
$GLOBALS['s40_routes'] = [];
$GLOBALS['s40_mock_titles'] = [
    1 => '40代男性の朝のスキンケアの基本を考える',
    2 => '40代男性の生活習慣と筋力維持の基礎',
];
$GLOBALS['s40_authorized'] = false;

function add_action(...$args) { return true; }
function add_filter(...$args) { return true; }
function add_shortcode(...$args) { return true; }
function register_activation_hook(...$args) { return true; }
function register_deactivation_hook(...$args) { return true; }
function current_user_can($cap) { return $cap === 'manage_options' && $GLOBALS['s40_authorized']; }
function get_option($key, $default=false) { return $GLOBALS['s40_options'][$key] ?? $default; }
function add_option($key, $value, $deprecated='', $autoload=false) {
    if (array_key_exists($key, $GLOBALS['s40_options'])) return false;
    $GLOBALS['s40_options'][$key] = $value;
    return true;
}
function update_option($key, $value, $autoload=false) {
    $old = $GLOBALS['s40_options'][$key] ?? null;
    if ($old === $value) return false;
    $GLOBALS['s40_options'][$key] = $value;
    return true;
}
function delete_option($key) { unset($GLOBALS['s40_options'][$key]); return true; }
function current_time($type) { return '2026-10-12 15:00:00'; }
function sanitize_text_field($value) { return trim(strip_tags((string)$value)); }
function sanitize_textarea_field($value) { return trim(strip_tags((string)$value)); }
function wp_strip_all_tags($value) { return strip_tags((string)$value); }
function get_posts($args) { return array_keys($GLOBALS['s40_mock_titles']); }
function get_the_title($id) { return $GLOBALS['s40_mock_titles'][$id] ?? ''; }
function register_rest_route($namespace, $route, $handlers) {
    $GLOBALS['s40_routes'][$namespace.$route] = $handlers;
    return true;
}
class WP_REST_Server {
    const READABLE = 'GET';
    const CREATABLE = 'POST';
}
class WP_REST_Response {
    public $data;
    public $status;
    public function __construct($data, $status=200) {
        $this->data = $data;
        $this->status = $status;
    }
}
class WP_Error {
    private $code;
    private $message;
    private $data;
    public function __construct($code, $message, $data=[]) {
        $this->code=$code; $this->message=$message; $this->data=$data;
    }
    public function get_error_code() { return $this->code; }
}
class S40_Request {
    private $body;
    private $params;
    public function __construct($params, $body_override=null) {
        $this->params=$params;
        $this->body=$body_override ?? json_encode($params, JSON_UNESCAPED_UNICODE);
    }
    public function get_body() { return $this->body; }
    public function get_json_params() { return $this->params; }
}
function s40_check($bool, $label) {
    if (!$bool) throw new RuntimeException('FAIL: '.$label);
    echo "PASS: $label\n";
}

$path = getenv('S40_CANDIDATE_PHP') ?: 'survival40-auto/survival40-auto.php';
require $path;
$plugin = new Survival40_Auto();
$plugin->s40_register_editorial_plan_routes();
$route=$GLOBALS['s40_routes']['survival40/v1/editorial-plans'] ?? null;
s40_check(is_array($route) && count($route) === 2, 'endpoint registered with read and write handlers');
s40_check($route[1]['methods'] === 'POST', 'POST route uses WordPress core REST authentication');
s40_check($plugin->s40_editorial_plan_permission(null) === false, 'anonymous callers denied');
$GLOBALS['s40_authorized'] = true;
s40_check($plugin->s40_editorial_plan_permission(null) === true, 'administrator may connect');

$plan = [
    'topic_id'=>'s40-abcdef0123456789abcd',
    'stage'=>'needs_independent_source_research',
    'plugin_planner_input'=>[
        'title'=>'40代男性の白髪染めシャンプーの仕組みと続けるための注意点',
        'keyword'=>'白髪染めシャンプー 仕組み 注意点',
        'category'=>'髪・頭皮',
        'seo_title'=>'白髪染めシャンプーの仕組みと注意点を40代男性向けに解説',
        'excerpt'=>'髪を染める仕組みと日々気をつけたい点を解説します。成分表示や製品の注意点などを理解するための基本を整理して紹介する記事の企画です。',
        'amazon_query'=>''
    ],
    'editorial'=>[
        'sources_checked'=>false,
        'verified_sources'=>0,
        'advertising_policy'=>'none',
        'requires_ymyl_gate'=>true,
        'research_questions'=>[
            '白髪染めシャンプーの染色の仕組みを一次情報で説明できるか',
            'メーカーの説明書から使用上の注意点を確認できるか',
        ]
    ],
    'safety'=>[
        'publish_authorized'=>false,
        'no_affiliate_assigned'=>true,
        'requires_existing_wordpress_quality_gates'=>true,
        'must_recheck_all_wordpress_posts_including_drafts'=>true
    ],
];
$report = [
    'schema'=>'survival40.wp_plan_handoff.v1',
    'ready_to_publish'=>false, 'wp_posts_written'=>0, 'threads_posts_written'=>0,
    'plans'=>[$plan]
];
$response=$plugin->s40_editorial_plan_ingest(new S40_Request($report));
s40_check($response instanceof WP_REST_Response && $response->status===202, 'accepted staging queue only');
s40_check($response->data['accepted']===1 && $response->data['wp_posts_created']===0, 'one valid idea, zero posts created');
$state=$plugin->s40_editorial_plan_status(null);
s40_check($state->data['count']===1 && $state->data['publication_enabled']===false, 'stored but not publishable');
$copy=$plugin->s40_editorial_plan_ingest(new S40_Request($report));
s40_check($copy->data['duplicate']===1 && $copy->data['accepted']===0, 'replayed delivery is idempotent');
s40_check(!array_key_exists('s40_editorial_ingest_lock_v1', $GLOBALS['s40_options']), 'writer lock always released');

$bad=$report;
$bad['ready_to_publish']=true;
$rejected=$plugin->s40_editorial_plan_ingest(new S40_Request($bad));
s40_check($rejected instanceof WP_Error && $rejected->get_error_code()==='s40_bad_plan_schema', 'publication-ready payload refused');

$bad=$report;
$bad['plans'][0]['topic_id']='s40-0123456789abcdef0123';
$bad['plans'][0]['plugin_planner_input']['category']='カスタム悪意カテゴリ';
$held=$plugin->s40_editorial_plan_ingest(new S40_Request($bad));
s40_check($held->data['accepted']===0 && $held->data['held'][0]['reason']==='invalid_topic_fields', 'invalid category held');

$bad=$report;
$bad['plans'][0]['topic_id']='s40-00112233445566778899';
$bad['plans'][0]['plugin_planner_input']['title']='40代男性の朝のスキンケアの基本を考える';
$held=$plugin->s40_editorial_plan_ingest(new S40_Request($bad));
s40_check($held->data['accepted']===0 && $held->data['held'][0]['reason']==='existing_wordpress_post', 'existing WP draft/published title held');

$bad=$report;
$bad['plans'][0]['topic_id']='s40-112233445566778899aa';
$bad['plans'][0]['editorial']['sources_checked']=true;
$held=$plugin->s40_editorial_plan_ingest(new S40_Request($bad));
s40_check($held->data['accepted']===0 && $held->data['held'][0]['reason']==='unsafe_unresearched_state', 'unsupported research verification refused');

$huge=$plugin->s40_editorial_plan_ingest(new S40_Request($report, str_repeat('x', 50001)));
s40_check($huge instanceof WP_Error && $huge->get_error_code()==='s40_payload_large', 'oversize payload rejected');

s40_check($plugin->s40_editorial_plan_status(null)->data['count']===1, 'only original safe plan retained');
echo "PASS: WP stub integration, no posts/ads/site publishing hooks used.\n";
