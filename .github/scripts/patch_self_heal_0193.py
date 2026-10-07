from pathlib import Path
p=Path('survival40-auto/survival40-auto.php')
s=p.read_text(encoding='utf-8')
s=s.replace(' * Version: 0.19.2\\n',' * Version: 0.19.3\\n',1)
s=s.replace("    const VERSION = '0.19.2';","    const VERSION = '0.19.3';",1)
s=s.replace('<h1>Survival40 Auto v0.19.2</h1>','<h1>Survival40 Auto v0.19.3</h1>',1)
p.write_text(s,encoding='utf-8')

old="""        $review = $this->review_generated_article($p, $html, $research);\n        if (($review['verdict'] ?? 'revise') !== 'pass') {\n            $rewritten = $this->rewrite_from_review($p, $html, $research, $review);\n            if (!is_wp_error($rewritten)) {\n                $html = $rewritten;\n                $review = $this->review_generated_article($p, $html, $research);\n            }\n        }\n\n        $warnings = $this->safety_scan($html);"""
new="""        $review = $this->review_generated_article($p, $html, $research);\n        $review_repairs = 0;\n        for ($repair = 0; $repair < 3 && (($review['verdict'] ?? 'revise') !== 'pass'); $repair++) {\n            $rewritten = $this->rewrite_from_review($p, $html, $research, $review);\n            if (is_wp_error($rewritten)) break;\n            $html = $rewritten;\n            $review = $this->review_generated_article($p, $html, $research);\n            $review_repairs++;\n        }\n\n        $warnings = $this->safety_scan($html);"""
if old not in s: raise SystemExit('review loop anchor not found')
s=s.replace(old,new,1)
s=s.replace("'_survival40_review_issues'=>implode(' / ', $review['issues'] ?? []),","'_survival40_review_issues'=>implode(' / ', $review['issues'] ?? []),\n                '_survival40_review_repairs'=>intval($review_repairs),",1)
s=s.replace("'review_verdict'=>$review['verdict'] ?? 'revise', 'review_score'=>intval($review['score'] ?? 0),","'review_verdict'=>$review['verdict'] ?? 'revise', 'review_score'=>intval($review['score'] ?? 0),\n            'review_repairs'=>intval($review_repairs), 'review_issues'=>array_values(array_slice($review['issues'] ?? [],0,5)),",1)
p.write_text(s,encoding='utf-8')
