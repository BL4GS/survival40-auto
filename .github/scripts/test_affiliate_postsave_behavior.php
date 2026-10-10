<?php
// Execute real staged save callback against WordPress-compatible mocks, no database.
error_reporting(E_ALL);
$source=file_get_contents('survival40-auto/survival40-auto.php');
function extract_callback($source,$name) {
  $needle="    public function ".$name."(";
  $start=strpos($source,$needle);
  if($start===false) throw new RuntimeException("Missing ".$name);
  $end=strpos($source,"\n    }",$start);
  if($end===false) throw new RuntimeException("Unterminated ".$name);
  return substr($source,$start,$end+6-$start);
}
$GLOBALS['meta']=[];
$GLOBALS['writes']=[];
function wp_is_post_revision($id){return false;}
function wp_is_post_autosave($id){return false;}
function get_post_meta($id,$key,$single=true){return $GLOBALS['meta'][$id][$key]??'';}
function update_post_meta($id,$key,$val){$GLOBALS['writes'][]=['update',$id,$key];$GLOBALS['meta'][$id][$key]=$val;}
function delete_post_meta($id,$key){$GLOBALS['writes'][]=['delete',$id,$key];unset($GLOBALS['meta'][$id][$key]);}
$callback=extract_callback($source,'s40_affiliate_on_post_saved');
eval('class TestSaveCallback {'.$callback.'
 private function s40_affiliate_infer_topic($post){return strpos($post->post_title,"プロテイン")!==false?"protein":"";}
 private function s40_affiliate_prepare_review($id,$topic){return ["suggested_ads"=>[["id"=>"s00000021719001"]]];}
}');
function ok($condition,$message){if(!$condition)throw new RuntimeException($message);echo "PASS ".$message."\n";}
$test=new TestSaveCallback();
$post=(object)['post_type'=>'post','post_status'=>'draft','post_title'=>'プロテインの飲み方','post_content'=>'ORIGINAL'];
$test->s40_affiliate_on_post_saved(4,$post,false);
ok(($GLOBALS['meta'][4]['_s40_affiliate_proposed_ids']??null)===['s00000021719001'],'proposal saved from inferred topic');
ok($post->post_status==='draft'&&$post->post_content==='ORIGINAL','post status/content unchanged');
$GLOBALS['writes']=[];
$GLOBALS['meta'][4]['_s40_affiliate_disabled']='1';
$test->s40_affiliate_on_post_saved(4,$post,true);
ok(!isset($GLOBALS['meta'][4]['_s40_affiliate_proposed_ids']),'disabled post clears proposals');
ok(count($GLOBALS['writes'])===1&&$GLOBALS['writes'][0][0]==='delete','disabled post writes only proposal deletion');
$GLOBALS['writes']=[];
$other=(object)['post_type'=>'page','post_status'=>'publish','post_title'=>'プロテイン','post_content'=>'PAGE'];
$test->s40_affiliate_on_post_saved(5,$other,false);
ok(count($GLOBALS['writes'])===0,'page remains untouched');
echo "Post-save behavior checks completed.\n";
