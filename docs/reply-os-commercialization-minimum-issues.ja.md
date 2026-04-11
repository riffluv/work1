# 返信OS 商品化前の最低論点一覧

更新日: 2026-04-11

## 目的

- `AI返信OS / 顧客対応運用設計` を外販できる状態にする前に、最低限つぶすべき論点を明文化する
- 単なる日本語調整ではなく、商品としての再現性・安全性・説明可能性を担保する
- `bugfix-15000` / `handoff-25000` の実運用で得た知見を、商品化前の完成条件へつなげる

## 前提

- ここでいう「商品化」は、テンプレ販売や prompt 販売ではなく、導入型の上位商品を指す
- 対象は `reply-only` の改善だけでなく、`service understanding / platform knowledge / state / scope / lane 分離` を含む
- ただし現時点で最優先なのは、購入前返信の事故を止める `reply layer` の安定化である

## 現時点の評価

- 土台: 強い
- 商品としての核: ある
- そのまま高単価外販できる完成度: まだ一段ある

理由:
- routing / state / scope / service facts / lane 分離は既に強い
- 一方で、`主質問からズレた情報の差し込み` `古い基準例との競合` `QA分類の未整備` が残っている
- したがって、今の段階は `弱いからやることが多い` ではなく、`強いから最後の制御層を整える段階` と見る

## 優先順位

### P0
- これが残っていると、商品として売る前に事故る可能性が高い

### P1
- P0 の次に必要。商品説明や再現性に効く

### P2
- 商品の完成度や運用効率を上げるが、直近で未実装でも致命傷ではない

## P0: 最低限つぶす論点

### 1. 主質問ファーストの徹底

現象:
- 相手が聞いていない価格・別原因リスク・範囲説明を先頭へ差し込む
- 「正しい情報」ではあるが、主質問から焦点がずれる

なぜ危険か:
- `ちゃんと読んで返している感じ` が消える
- AI感・テンプレ感の大きな原因になる
- 高単価商品として見ると、応答設計が甘く見える

現状:
- `answer contract`
- `primary_question_id`
- `frontload_*_when_not_asked`
までは入った

完了条件:
- 5件バッチで `主質問以外の価格差し込み` が再発しない
- `お願いできますか` 系のケースで、先頭2文が対応可否へ揃う
- self-check だけで大半を止められる

### 2. prequote の約束範囲の固定

現象:
- 購入前なのに、購入後に始めるべき調査・確認・切り分けを先取りしたように読めることがある
- `見ます / 確認します / 進めます` が未受領段階で混ざる

なぜ危険か:
- buyer の期待値が上がりすぎる
- 無料で見すぎる事故と、約束しすぎる事故が起きる

現状:
- [`coconala-prequote-commitment-policy.ja.md`](/home/hr-hm/Project/work/docs/coconala-prequote-commitment-policy.ja.md) を作成済み
- `ZIP 非依存 / 購入後着手 / 15,000円でどこまで見るか` は固定済み

完了条件:
- prequote 返信で phase 漏れが再発しない
- `購入前にこちらで見ておきます` 型の文が出ない
- ZIP をこちらから標準要求しない運用が安定する

### 3. 意味接続の破綻防止

現象:
- 受け止め句と価格・件数・範囲判定を同じ文でつなぐ
- 因果がないのに、読点接続で因果のように読ませてしまう

なぜ危険か:
- 日本語としての違和感が強い
- AI感の中でもかなり目立つ
- buyer からすると `テンプレをつないだだけ` に見えやすい

現状:
- `ng-expressions`
- `self-check`
- `japanese-chat-natural`
には反映済み

完了条件:
- バッチ監査で `意味接続が変` の指摘が再発しない
- 新しい崩れが出ても `NG / self-check` へ戻せる形になっている

### 4. 古い良い例 / 契約テストとの競合除去

現象:
- 正本では禁止した旧パターンが、gold reply や test asset に残る
- 後から再び「良い例」として参照され、学習源になる

なぜ危険か:
- ルールを強化しても、下流で元に戻る
- 商品として見たときに再現性が弱い

現状:
- `gold replies`
- `prequote contract test`
の一部は掃除済み

完了条件:
- `正本 / 良い例 / 契約テスト` の3層で、主質問より先に価格を出す旧例が残っていない
- overlap 整理の手順が `reply-quality/README.ja.md` に固定されている

## P1: 次に必要な論点

### 5. forbidden_moves の運用精度

現象:
- ルールとしては入っていても、どの場面で何を禁止するかの付与精度がまだ粗い

必要なこと:
- route / state / certainty / user_intent に応じて、どの forbidden_moves を立てるかを安定化する

完了条件:
- `frontload_price_when_not_asked`
- `frontload_branching_risk_when_not_asked`
- `frontload_scope_explanation_when_not_asked`
の付与が、明らかにズレない

現状:
- [`reply-quality/forbidden-moves-matrix.ja.md`](/home/hr-hm/Project/work/docs/reply-quality/forbidden-moves-matrix.ja.md) を正本として追加済み
- `intake-router` と `output-schema` に、`forbidden_moves` を `state / reply_skeleton / burden_owner / primary question` から選ぶ前提を反映済み

### 6. QA分類の固定

現象:
- 今は指摘は鋭いが、失敗会話の分類軸がまだ散発的

必要な分類:
- 主質問ズレ
- 余計情報差し込み
- phase 漏れ
- 内部語漏れ
- 意味接続破綻
- テンプレ臭
- 温度感ズレ

完了条件:
- 5件バッチの監査結果を、上の分類で戻せる
- 新しい崩れが `どの層の問題か` で整理できる

現状:
- [`reply-quality/failure-taxonomy.ja.md`](/home/hr-hm/Project/work/docs/reply-quality/failure-taxonomy.ja.md) を正本として追加済み
- 今後は 5件バッチ監査の指摘を、まずこの分類へ落としてから反映判断する

### 7. route / state / service ごとの guidance scoping

現象:
- ルールは増えてきたが、適用範囲が広いままのものがある
- 一部の guidance が、別 route や別 state にまで漏れるリスクがある

必要なこと:
- `service / profile / message`
- `prequote / purchased / delivery`
- `bugfix / handoff / boundary`
ごとの適用域をより明示する

完了条件:
- 「このルールはどこにだけ効くか」を説明できる
- route 混同、phase 混同の再発率が下がる

現状:
- [`reply-quality/guidance-scoping.ja.md`](/home/hr-hm/Project/work/docs/reply-quality/guidance-scoping.ja.md) を正本として追加済み
- 今後は、監査で出た改善を採用する前に `reply-only / route / state / service` の4軸で適用域を切る

### 8. prequote の説明量制御

現象:
- 正しいことは書いているが、説明を盛りすぎて buyer を疲れさせる
- `主質問への答え` と `誤解防止` と `サービス説明` を1通に詰め込みすぎる

なぜ危険か:
- `仕事できない感` や迷いを生む
- 購入前の返信で読む負担が増え、購入率にも影響する
- AI感より前に、商談として重く見える

必要なこと:
- prequote では `1通1主論点`
- 理由は1つ、次アクションは1つ
- 主質問より前にサービス説明や境界説明を広げない

現状:
- [`reply-quality/prequote-compression-rules.ja.md`](/home/hr-hm/Project/work/docs/reply-quality/prequote-compression-rules.ja.md) を正本として追加済み
- `coconala-prequote-ops-ja` と `self-check` に最小接続済み

完了条件:
- 5件バッチで `説明が長い / 結局何を言いたいか分からない` の指摘が再発しにくい
- 価格質問や価値質問で、説明より先に主回答が立つ
## P2: 商品完成度を上げる論点

### 9. 商品説明に使える QA 指標

必要な指標例:
- 主質問へ直答できた率
- 不要情報差し込み率
- phase 破綻率
- human 修正率
- 5件バッチ再監査での合格率

価値:
- 商品説明で `なんとなく良い` ではなく、改善成果を示せる

### 10. 実案件ベースの curated set 拡充

必要なこと:
- gold replies を増やしすぎず、主要場面ごとに代表例を積む
- `温度感の良い例` と `骨格の良い例` を分けて扱う

価値:
- 商品化後の導入でも、相手別の調整がしやすくなる

### 11. 外販用の導入単位の固定

現状の候補:
- 1サービス分
- purchased memory
- 複数サービス対応
- case切替
- delivery 導線

必要なこと:
- 本体とオプションの切り分けを最終確定する
- 「どこまで入ると使える完成品か」を明示する

## いまやらないこと

- 重い自動評価基盤の構築
- 監査項目の過剰な細分化
- 外部AIの一般論を一括で rules に落とすこと
- 文章の微差だけを追う大規模な自然化ルール追加

理由:
- 今の段階では、骨格制御のほうが費用対効果が高い
- 一般論の一括導入はノイズになりやすい

## 現時点での結論

商品化前に最低限つぶすべき中心論点は、次の4本である。

1. 主質問ファースト
2. prequote の約束範囲固定
3. 意味接続の破綻防止
4. 古い良い例 / 契約テストとの競合除去

この4本が安定すれば、返信OSは `高単価商品としての土台` にかなり近づく。

## 参照

- [`coconala-prequote-commitment-policy.ja.md`](/home/hr-hm/Project/work/docs/coconala-prequote-commitment-policy.ja.md)
- [`coconala-reply-self-check.ja.md`](/home/hr-hm/Project/work/docs/coconala-reply-self-check.ja.md)
- [`reply-quality/README.ja.md`](/home/hr-hm/Project/work/docs/reply-quality/README.ja.md)
- [`reply-quality/forbidden-moves-matrix.ja.md`](/home/hr-hm/Project/work/docs/reply-quality/forbidden-moves-matrix.ja.md)
- [`reply-quality/failure-taxonomy.ja.md`](/home/hr-hm/Project/work/docs/reply-quality/failure-taxonomy.ja.md)
- [`reply-quality/guidance-scoping.ja.md`](/home/hr-hm/Project/work/docs/reply-quality/guidance-scoping.ja.md)
- [`次期サービス候補 README.ja.md`](/home/hr-hm/Project/work/サービスページ/次期サービス候補/README.ja.md)
