<?php
/** Exercise protected queue research reservation and safe completion. */
function sanitize_title($s) { return strtolower(preg_replace('/\s+/u', '-', (string)$s)); }
function is_wp_error($obj) { return $obj instanceof WP_Error; }
function sanitize_key($s) { return preg_replace('/[^a-z0-9_]/', '', (string)$s); }
require __DIR__.'/test_editorial_intake_next.php';

$claim = new ReflectionMethod('Survival40_Auto', 's40_editorial_queue_claim');
$finish = new ReflectionMethod('Survival40_Auto', 's40_editorial_queue_finish');
$queued = $claim->invoke($plugin);
s40_check(is_array($queued) && !empty($queued['_s40_editorial_queue']), 'queue plan enters research stage');
s40_check($queued['allow_amazon'] === 0 && $queued['allow_a8'] === 0, 'imported plan cannot enable affiliate injection');
s40_check($queued['ymyl'] === 1, 'hair category retains required YMYL caution');
s40_check($queued['title'] === $plan['plugin_planner_input']['title'], 'original validated title passed to WP research');
s40_check($GLOBALS['s40_options']['s40_editorial_plan_queue_v1'][$queued['_s40_queued_topic_id']]['status'] === 'processing_research', 'queue plan reserved before Gemini calls');

$finish->invoke($plugin, $queued['_s40_queued_topic_id'], [
    'status'=>'draft','post_id'=>417,'review_score'=>90
]);
$entry = $GLOBALS['s40_options']['s40_editorial_plan_queue_v1'][$queued['_s40_queued_topic_id']];
s40_check($entry['status'] === 'draft_created_after_review' && $entry['post_id']===417, 'completed draft tracked in queue');
s40_check($claim->invoke($plugin) === null, 'completed plan is not claimed twice');

$failure_id='s40-bbbbbbbbbbbbbbbbbbbb';
$second=$entry;
$second['title']='40代男性の朝の水分補給を続けるための見直し方';
$second['category']='食事・栄養';
$second['status']='awaiting_independent_research';
unset($second['post_id']);
$GLOBALS['s40_options']['s40_editorial_plan_queue_v1'][$failure_id]=$second;
$next = $claim->invoke($plugin);
s40_check($next['_s40_queued_topic_id'] === $failure_id, 'next queued plan independently claimed');
$finish->invoke($plugin, $failure_id, new WP_Error('s40_queue_quality_hold', 'Research insufficient'));
$failed = $GLOBALS['s40_options']['s40_editorial_plan_queue_v1'][$failure_id];
s40_check($failed['status']==='held_after_research_failure', 'low-quality or failed research held without draft');
s40_check($claim->invoke($plugin)===null, 'failed research is not blindly retried');
echo "PASS: future queue consumer safe reservation, draft outcome and failure reconciliation.\n";
