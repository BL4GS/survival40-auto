from pathlib import Path
import re
p=Path("survival40-auto/survival40-auto.php")
s=p.read_text(encoding="utf-8")
hook="        add_action('wp_footer', [$this, 'survival40_brand_separation'], 90);"
assert s.count(hook)==1
s=s.replace(hook,hook+"\n        add_action('admin_menu', [$this, 's40_affiliate_ledger_menu']);\n        add_action('admin_post_s40_save_affiliate_ledger', [$this, 's40_affiliate_ledger_save']);",1)
anchor="    public function survival40_brand_separation() {"
assert s.count(anchor)==1
method=r'''    private function s40_affiliate_seed() {
        return [
            ['id'=>'s00000014286004','name'=>'NULL オールインワンジェル','category'=>'スキンケア','reward'=>'購入1,000円','status'=>'approved','notes'=>'対象商品はオールインワンジェルのみ'],
            ['id'=>'ultora','name'=>'ULTORA プロテイン','category'=>'筋トレ・栄養','reward'=>'購入10%（要再確認）','status'=>'approved','notes'=>'プログラムIDは未確認'],
            ['id'=>'s0000007191012','name'=>'プレミアムブラックシャンプー','category'=>'ヘアケア','reward'=>'税抜購入額15%','status'=>'approved','notes'=>'プログラムIDは過去情報・要照合'],
            ['id'=>'s00000016652002','name'=>'マイまくら','category'=>'睡眠','reward'=>'購入15%','status'=>'approved','notes'=>'医療機器表現と広告掲載URLを確認'],
            ['id'=>'s00000020317006','name'=>'HOLO BELL プロテクト保湿UV','category'=>'紫外線対策','reward'=>'新規購入1,000円','status'=>'approved','notes'=>'商品紹介文必須・広告掲載URL提出'],
            ['id'=>'s00000014443001','name'=>'AUEN','category'=>'ファッション','reward'=>'購入15%','status'=>'approved','notes'=>'画像転載とブランド表記に制限'],
            ['id'=>'s00000018173002','name'=>'SIX-CHANGE','category'=>'筋トレ用品','reward'=>'初回購入3,500円','status'=>'approved','notes'=>'LP掲載商品だけ・誇張表現禁止'],
            ['id'=>'s00000017106008','name'=>'ボディセンス','category'=>'身だしなみ','reward'=>'初回購入4,500円','status'=>'approved','notes'=>'LP掲載商品だけ・フェロモン効能を断定しない'],
            ['id'=>'s00000024389001','name'=>'MPNプロテイン','category'=>'筋トレ・栄養','reward'=>'税抜購入額5%（一般）','status'=>'approved','notes'=>'商品別成果条件・人物画像使用不可'],
            ['id'=>'s00000022516001','name'=>'cacom公式ショップ','category'=>'寝具','reward'=>'購入7%','status'=>'approved','notes'=>'本人申込不可'],
            ['id'=>'s00000023792001','name'=>'Meals 宅配弁当','category'=>'食生活','reward'=>'新規購入3,000円','status'=>'approved','notes'=>'広告掲載URL提出・誇張表現禁止'],
            ['id'=>'s00000019450001','name'=>'ミートガイ','category'=>'季節・BBQ','reward'=>'通常5%・トライアル10%','status'=>'approved','notes'=>'過去に読者購入実績あり'],
            ['id'=>'aono','name'=>'マンダム aono','category'=>'スキンケア','reward'=>'新規購入2,000円（要確認）','status'=>'pending','notes'=>'審査待ち・プログラムID未確認'],
            ['id'=>'holobell-body','name'=>'HOLO BELL ボディソープ','category'=>'ボディケア','reward'=>'新規購入1,000円（要確認）','status'=>'pending','notes'=>'審査待ち・プログラムID未確認'],
            ['id'=>'regina-homme','name'=>'レジーナクリニックオム','category'=>'医療脱毛','reward'=>'来院10,000円（要確認）','status'=>'pending','notes'=>'審査待ち・医療広告規制に注意'],
            ['id'=>'mens-rize','name'=>'メンズリゼ','category'=>'医療脱毛','reward'=>'来院12,000円（要確認）','status'=>'pending','notes'=>'審査待ち・医療広告規制に注意'],
        ];
    }

    private function s40_affiliate_ledger_get() {
        $saved = get_option('s40_affiliate_ledger_v1', []);
        if (!is_array($saved)) $saved = [];
        $rows = [];
        foreach ($this->s40_affiliate_seed() as $seed) {
            $id = $seed['id'];
            $extra = isset($saved[$id]) && is_array($saved[$id]) ? $saved[$id] : [];
            $rows[$id] = array_merge($seed, [
                'url' => isset($extra['url']) ? (string)$extra['url'] : '',
                'status' => in_array($extra['status'] ?? '', ['approved','pending','inactive'], true) ? $extra['status'] : $seed['status'],
                'notes' => isset($extra['notes']) ? (string)$extra['notes'] : $seed['notes'],
            ]);
        }
        return $rows;
    }

    public function s40_affiliate_ledger_menu() {
        add_submenu_page('options-general.php','Survival40 広告台帳','Survival40 広告台帳','manage_options','s40-affiliate-ledger',[$this,'s40_affiliate_ledger_screen']);
    }

    public function s40_affiliate_ledger_save() {
        if (!current_user_can('manage_options')) wp_die('権限がありません');
        check_admin_referer('s40_affiliate_ledger_save');
        $incoming = isset($_POST['ledger']) && is_array($_POST['ledger']) ? wp_unslash($_POST['ledger']) : [];
        $rows = $this->s40_affiliate_ledger_get();
        $saved = [];
        foreach ($rows as $id=>$row) {
            $field = isset($incoming[$id]) && is_array($incoming[$id]) ? $incoming[$id] : [];
            $url = isset($field['url']) ? trim((string)$field['url']) : '';
            if ($url !== '' && (!wp_http_validate_url($url) || !str_starts_with($url,'https://'))) {
                wp_die('無効な広告URLが含まれています。HTTPSのURLだけを入力してください。');
            }
            $status = isset($field['status']) && in_array($field['status'],['approved','pending','inactive'],true) ? $field['status'] : $row['status'];
            $saved[$id] = ['url'=>esc_url_raw($url),'status'=>$status,'notes'=>sanitize_textarea_field($field['notes'] ?? '')];
        }
        update_option('s40_affiliate_ledger_v1',$saved,false);
        wp_safe_redirect(add_query_arg(['page'=>'s40-affiliate-ledger','saved'=>1],admin_url('options-general.php')));
        exit;
    }

    public function s40_affiliate_ledger_screen() {
        if (!current_user_can('manage_options')) return;
        $rows = $this->s40_affiliate_ledger_get();
        ?>
        <div class="wrap"><h1>Survival40 A8広告台帳</h1>
        <p>提携案件を管理するための非公開台帳です。広告URLを保存しても記事に自動掲載されません。広告URLはA8で作成した計測用リンクを、改変せず入力してください。</p>
        <?php if(isset($_GET['saved'])): ?><div class="notice notice-success"><p>台帳を保存しました。</p></div><?php endif; ?>
        <form method="post" action="<?php echo esc_url(admin_url('admin-post.php')); ?>">
          <input type="hidden" name="action" value="s40_save_affiliate_ledger"/>
          <?php wp_nonce_field('s40_affiliate_ledger_save'); ?>
          <table class="widefat striped"><thead><tr><th>プログラム／ジャンル</th><th>成果報酬</th><th>状態</th><th>広告URL（HTTPS）</th><th>掲載条件・メモ</th></tr></thead><tbody>
          <?php foreach($rows as $id=>$row): ?>
          <tr><td><strong><?php echo esc_html($row['name']); ?></strong><br><code><?php echo esc_html($id); ?></code><br><?php echo esc_html($row['category']); ?></td>
          <td><?php echo esc_html($row['reward']); ?></td>
          <td><select name="ledger[<?php echo esc_attr($id); ?>][status]">
          <?php foreach(['approved'=>'提携済み','pending'=>'審査待ち','inactive'=>'停止・見送り'] as $v=>$label): ?>
          <option value="<?php echo esc_attr($v); ?>" <?php selected($row['status'],$v); ?>><?php echo esc_html($label); ?></option>
          <?php endforeach; ?></select></td>
          <td><input type="url" style="width:100%;min-width:220px" name="ledger[<?php echo esc_attr($id); ?>][url]" placeholder="https://px.a8.net/..." value="<?php echo esc_attr($row['url']); ?>"/></td>
          <td><textarea rows="3" style="width:100%;min-width:230px" name="ledger[<?php echo esc_attr($id); ?>][notes]"><?php echo esc_textarea($row['notes']); ?></textarea></td></tr>
          <?php endforeach; ?>
          </tbody></table>
          <?php submit_button('広告台帳を保存'); ?>
        </form></div>
        <?php
    }

'''
s=s.replace(anchor,method+anchor,1)
s,a=re.subn(r"(?m)^(\s*\*\s*Version:\s*)0\.19\.17\s*$",r"\g<1>0.19.18",s,count=1)
s,b=re.subn(r"(?m)^(\s*const\s+VERSION\s*=\s*')0\.19\.17(';\s*)$",r"\g<1>0.19.18\2",s,count=1)
s,c=re.subn(r"<h1>Survival40 Auto v0\.19\.17</h1>","<h1>Survival40 Auto v0.19.18</h1>",s,count=1)
assert a==b==c==1
p.write_text(s,encoding="utf-8")
print("added A8 affiliate admin ledger, 16 seeded programs, no auto placement")
