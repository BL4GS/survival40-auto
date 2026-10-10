<?php
// Read-only isolated behavior checks. No WordPress installation or publication.
error_reporting(E_ALL);
$source = file_get_contents('survival40-auto/survival40-auto.php');
function method_from_source($source, $name) {
    $start = strpos($source, "    private function " . $name . "(");
    if ($start === false) throw new RuntimeException("Missing method ".$name);
    $end = strpos($source, "\n    }", $start);
    if ($end === false) throw new RuntimeException("Missing method end ".$name);
    return substr($source, $start, $end + 6 - $start);
}
$one = method_from_source($source, 's40_affiliate_infer_topic');
$two = method_from_source($source, 's40_affiliate_eligible_for_post');
eval('class S40_Test_Harness {' . $one . "\n" . $two . ' public function topic($p){return $this->s40_affiliate_infer_topic($p);} public function eligible($i,$r){return $this->s40_affiliate_eligible_for_post($i,$r);} }');
$GLOBALS['s40_test_meta'] = [];
function get_post_meta($id, $key, $single = false) { return $GLOBALS['s40_test_meta'][$id][$key] ?? ''; }
function post_for_test($title) {return (object)['post_type'=>'post','post_title'=>$title];}
function check_result($actual, $expected, $label) {
    if ($actual !== $expected) throw new RuntimeException($label.': expected '.var_export($expected,true).' got '.var_export($actual,true));
    echo "PASS ".$label."\n";
}
$h = new S40_Test_Harness();
check_result($h->topic(post_for_test('40代のプロテインの飲み方')), 'protein', 'protein topic');
check_result($h->topic(post_for_test('エアコンクリーニングの選び方')), 'cleaning', 'cleaning topic');
check_result($h->topic(post_for_test('プロテインとシャンプーの話')), '', 'conflicting topics rejected');
check_result($h->topic(post_for_test('休日の日記')), '', 'unrelated article rejected');
$row = ['id'=>'s00000026776002','status'=>'approved'];
check_result($h->eligible(1, $row), false, 'default disallows ads');
$GLOBALS['s40_test_meta'][1] = [
    '_s40_affiliate_reviewed'=>'yes',
    '_s40_affiliate_reviewed_program_id'=>'s00000026776002',
    '_s40_affiliate_conditions_verified'=>'yes',
    '_s40_affiliate_item_code'=>'ringconn-gen2'
];
check_result($h->eligible(1, $row), true, 'reviewed exact item is permitted');
$GLOBALS['s40_test_meta'][1]['_s40_affiliate_item_code']='ringconn-gen1';
check_result($h->eligible(1, $row), false, 'wrong product generation rejected');
check_result($h->eligible(1, ['id'=>'s00000022947002','status'=>'approved']), false, 'unverified campaign rejected');
echo "Behavior tests completed.\n";
