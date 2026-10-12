<?php
/** Real isolated WordPress REST smoke test. Never run against production. */
if (!defined('ABSPATH')) throw new RuntimeException('Must run via WP-CLI in isolated WP');
$path='/survival40/v1/editorial-plans';
$before=get_posts(['post_type'=>'post','post_status'=>'any','numberposts'=>-1,'fields'=>'ids']);

wp_set_current_user(0);
$anon=rest_do_request(new WP_REST_Request('GET',$path));
if ($anon->get_status() < 400) throw new RuntimeException('Unauthenticated WP REST request was accepted');

wp_set_current_user(1);
$authorized=rest_do_request(new WP_REST_Request('GET',$path));
if ($authorized->get_status()!==200) throw new RuntimeException('Admin cannot read editorial inbox');

$idea=[
 'topic_id'=>'s40-aabbccddeeff00112233',
 'stage'=>'needs_independent_source_research',
 'plugin_planner_input'=>[
   'title'=>'40代男性の白髪染めシャンプーの仕組みと使う前に見直したい注意点',
   'keyword'=>'白髪染めシャンプー 仕組み 注意点',
   'category'=>'髪・頭皮',
   'excerpt'=>'白髪染めシャンプーの仕組みを理解し、使う前に成分表示や製品の使用上の注意を調べてから選ぶための情報を整理した記事の企画です。',
   'seo_title'=>'40代の白髪染めシャンプーの仕組みと注意点を分かりやすく紹介',
   'amazon_query'=>'',
 ],
 'editorial'=>[
   'sources_checked'=>false,'verified_sources'=>0,'advertising_policy'=>'none',
   'requires_ymyl_gate'=>true,
   'research_questions'=>[
       '使用方法と染色の仕組みをメーカー公式情報によって確認できるか',
       '使用上の注意点と成分上の制約を一次資料に照らして説明できるか',
   ],
 ],
 'safety'=>[
   'publish_authorized'=>false,
   'no_affiliate_assigned'=>true,
   'requires_existing_wordpress_quality_gates'=>true,
   'must_recheck_all_wordpress_posts_including_drafts'=>true,
 ]
];
$document=[
 'schema'=>'survival40.wp_plan_handoff.v1',
 'ready_to_publish'=>false,'wp_posts_written'=>0,'threads_posts_written'=>0,
 'plans'=>[$idea]
];
$request=new WP_REST_Request('POST',$path);
$request->set_header('Content-Type','application/json');
$request->set_body(wp_json_encode($document));
$result=rest_do_request($request);
if ($result->get_status()!==202) throw new RuntimeException('Admin POST rejected: HTTP '.$result->get_status().' '.wp_json_encode($result->get_data()));
$body=$result->get_data();
if (($body['accepted']??null)!==1 || ($body['wp_posts_created']??null)!==0) throw new RuntimeException('Unexpected intake acknowledgement');
$repeat=rest_do_request($request);
if (($repeat->get_data()['duplicate']??null)!==1) throw new RuntimeException('Duplicate request was not idempotent');
$after=get_posts(['post_type'=>'post','post_status'=>'any','numberposts'=>-1,'fields'=>'ids']);
if ($after!==$before) throw new RuntimeException('Article count/IDs changed by research-only intake');
if (get_option('s40_affiliate_frontend_enabled','no')!=='no') throw new RuntimeException('Ads enabled unexpectedly');
$state=rest_do_request(new WP_REST_Request('GET',$path));
if (($state->get_data()['count']??null)!==1) throw new RuntimeException('Inbox plan not persisted');
echo "PASS: real WordPress REST permission, intake, replay and zero article/ad mutations\n";
