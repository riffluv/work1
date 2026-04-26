# 返信システム 変更ログ

更新日: 2026-04-23

## 目的

- どの変更で何が良くなったかを、後から追えるようにする
- `なんとなく良くなった / 悪くなった` で終わらせず、変更と評価結果を結びつける
- 返信生成本体を壊さずに、改善だけを積み上げる

## 使い方

- 1変更につき 1ブロックだけ追加する
- 長文で書かず、`何を変えたか / なぜ変えたか / 何で確認したか` だけ残す
- `reply-only / common / delivery-only` を必ず付ける
- batch 監査や実案件で改善確認できたら、`確認` 行に追記する

## 記録テンプレート

```text
### YYYY-MM-DD / CHG-XXX
- 分類:
- レイヤ:
- 変更:
- きっかけ:
- 想定効果:
- 確認:
- メモ:
```

---

### 2026-04-23 / CHG-001
- 分類: `reply-only`
- レイヤ: judgment / wording
- 変更: 価格・条件確認が主質問の時は、同意前に次工程へ勝手に進めないようにした
- きっかけ: `割引できますか` に対して、同意前に `症状を送ってください` へ進み、押し売り感が出た
- 想定効果: 主質問直答が強くなり、`ちゃんと話を聞いていない` 印象を減らす
- 確認: bugfix 返信学習 batch の B06 系で改善確認
- メモ: `その前提でもよろしければ、今回も対応できます。` のように止める形を採用

### 2026-04-23 / CHG-002
- 分類: `common`
- レイヤ: service page / reply policy
- 変更: bugfix-15000 を「原因だけ分かったら納品」ではなく、「修正済みファイル返却まで進められないなら正式納品へ進めない」方針に揃えた
- きっかけ: ココナラの承諾実務上、buyer は `修正まで込みで15,000円` と受け取りやすく、原因だけで課金すると事故りやすいと判断
- 想定効果: `直してもらえないのにお金だけ取られるのでは` という不安を減らす
- 確認: bugfix-15000.live.txt FAQ 修正済み / 返信ルールも同方向へ修正済み
- メモ: 調査のみ課金の思想は今の bugfix 商品では採らない

### 2026-04-23 / CHG-003
- 分類: `reply-only`
- レイヤ: scope judge
- 変更: `同じ原因` だけでなく、`同じ原因でも修正が重い` を内部判定に追加した
- きっかけ: 同じ原因でも大規模リファクタリングや広い変更が必要な場合、基本料金内に抱え込むと事故る
- 想定効果: `same_cause_light / same_cause_but_heavy / different_cause_likely / undecidable` の4分岐で、追加相談へ自然に切れる
- 確認: scope-judge skill と reply judgment flow に反映済み
- メモ: system は保守的、人間が必要なら緩める方針

### 2026-04-23 / CHG-004
- 分類: `reply-only`
- レイヤ: buyer wording
- 変更: `本番 / プレビュー / ローカル` のような技術語で環境確認しないようにした
- きっかけ: buyer が `previewって何？` で止まりやすく、入力欄と返信の両方で迷いを増やしていた
- 想定効果: 初手のラリーを減らし、相談しやすさを上げる
- 確認: bugfix-15000.live.txt の入力項目を `どこで起きているか（公開中のサイトだけか、自分のPCでも起きるか など）` に変更済み
- メモ: preview 系は必要なら2往復目で聞く

### 2026-04-23 / CHG-005
- 分類: `reply-only`
- レイヤ: review layer
- 変更: 監査ラベル `nonanswer / redundant_ask / premature_progress / hidden_rule / oversell / ai_tone` と採点軸を review batch に追加した
- きっかけ: xhigh の助言で、生成を賢くするより先に、ズレ方を分類して止める方が安全と判断
- 想定効果: 返信本体を壊さずに、悪化を見つけやすくする
- 確認: bugfix / handoff の返信監査 batch に追加済み
- メモ: 生成本体・renderer は触らない

### 2026-04-23 / CHG-006
- 分類: `reply-only`
- レイヤ: evaluation
- 変更: 最小 fixed bench を追加した
- きっかけ: 変更後に何が悪化したかを、毎回同じカテゴリで見たい
- 想定効果: `urgent_prequote / price_anxiety / unresolved_risk / purchased_extra_scope / secret_handling / direct_push_or_external_share` を固定観測できる
- 確認: `ops/tests/regression/reply-fixed-bench.yaml` 追加済み
- メモ: stop condition は `nonanswer / hidden_rule / redundant_ask / premature_progress`

### 2026-04-23 / CHG-007
- 分類: `reply-only`
- レイヤ: renderer sync
- 変更: prequote の buyer 向け環境確認を `公開中のサイトだけか / 自分のPCでも起きるか` に揃え、価格・調査・別料金不安への直答を renderer 実装へ反映した。あわせて `quote_sent` の自己反映サポートで購入促しを自動付与しないようにした
- きっかけ: service page / change log では直っていたのに、renderer 側に古い wording と closing が残り、batch で `ai_tone / premature_progress` が再発した
- 想定効果: B01 系の buyer wording drift、B02 系の価格不安回答の分かりにくさ、B04 系の不要な購入促しを減らす
- 確認: `scripts/render-prequote-estimate-initial.py --case-id STK-002/STK-003` と `scripts/render-quote-sent-followup.py --case-id GMN-020` で改善確認
- メモ: 骨格は維持し、renderer の wording / closing だけを最小修正

### 2026-04-23 / CHG-008
- 分類: `reply-only`
- レイヤ: wording trim
- 変更: 明示質問に答え切ったあと、聞かれていない `別原因の場合` `追加料金の仕組み` を自動で足さない方針に寄せた
- きっかけ: B02 系の価格不安回答で、主質問への回答後に未質問の別原因説明を足し、少し重くなる再発が見えた
- 想定効果: 主質問に答えたら止める精度が上がり、price / refund 系の文面が短くなる
- 確認: `scripts/render-prequote-estimate-initial.py --case-id STK-003` と batch-01 B02 で短縮確認
- メモ: 必要になった時だけ別原因説明を足す

### 2026-04-23 / CHG-009
- 分類: `reply-only`
- レイヤ: service grounding
- 変更: bugfix の service facts / prequote guide / generic skill を service page 正本に揃え、handoff private lane の外向け文面からサービス名・価格・購入導線を外した
- きっかけ: service page では `修正済みファイル返却まで進める前提` `buyer 向け環境確認` `handoff 非公開` が固まっていたのに、返信系の一部に旧ルールが残っていた
- 想定効果: service page と reply system の認識ズレ、purchased の料金事故、private handoff の外向け露出を減らす
- 確認: active facts / renderer / skill refs の spot check と `render-post-purchase-quick.py` / handoff custom reply の文面確認で反映確認
- メモ: 骨格は触らず、正本との差分だけ同期

### 2026-04-23 / CHG-010
- 分類: `reply-only`
- レイヤ: skill design
- 変更: `skill は Codex の思考を置き換えず、正本の取り出し口 / guardrail に留める` 方針を、reply 系 skill 正本へ明文化した
- きっかけ: skill を増やしても Codex 本体の reasoning を邪魔しない運用を、口頭方針ではなく workspace 内の明示ルールにしておきたかった
- 想定効果: 長い固定文脈や template 群で思考を潰す再発を減らし、`router / prequote / reply` の責務分離を維持しやすくする
- 確認: `coconala-intake-router-ja` / `coconala-prequote-ops-ja` / `coconala-reply-ja` / `coconala-reply-bugfix-ja` に共通 guard を追加
- メモ: 新しい知識層を増やすのではなく、必要時だけ正本を引く薄い skill を維持する

### 2026-04-23 / CHG-011
- 分類: `common`
- レイヤ: regression
- 変更: `service_pack_fidelity` ケースを専用 checker で実行し、通常 reply runner からは regression_seed を既定で外すようにした
- きっかけ: fidelity ケース資産は存在していたが、通常 reply runner は `state` 付き会話ケース前提のため、全部 `skip_out_of_scope_state` になっていた
- 想定効果: service-pack の contract 参照切れを自動検知でき、通常 reply 回帰の skip ノイズも減る
- 確認: `scripts/check-service-pack-fidelity.py` を追加し、full regression へ接続
- メモ: まずは `expected_contract_refs` の実在監視を最小実装とし、意味レベルの監査は後続で厚くする

### 2026-04-23 / CHG-012
- 分類: `common`
- レイヤ: regression wiring
- 変更: `service_pack_fidelity` checker は fidelity source だけを拾うようにし、seed / eval / holdout / edge / renderer_seed の suite では非対象 source を自動スキップするようにした
- きっかけ: full regression に接続した直後、role suites でも fidelity checker が通常 stock / fixture を読み込もうとして誤爆していた
- 想定効果: `service_pack_fidelity` 監視を追加しても、既存 role suite の経路を壊さずに共存できる
- 確認: `scripts/check-service-pack-fidelity.py --role seed` が `[OK] no service-pack fidelity sources selected`、`scripts/check-coconala-reply-full-regression.py --role seed` で `service_pack_fidelity_status: OK`
- メモ: fidelity 監視は `regression_seed` を主入口にし、通常 suite には副作用を持ち込まない

### 2026-04-23 / CHG-013
- 分類: `reply-only`
- レイヤ: renderer / validator alignment
- 変更: prequote の primary 直答を secondary の promoted line に押し流されないように戻し、refund/discount/after-close の opening wording を current rules に揃えた。あわせて、public bugfix 向け role suite では private handoff case を out-of-scope skip として扱うよう整理した
- きっかけ: `#RE` の smoke test 後、public bugfix lane の direct answer 欠落と action_first drift が見え、さらに handoff private case が generic bugfix validator に混ざって suite を赤くしていた
- 想定効果: bugfix の `15,000円で進められるか / 調べるだけでよいか / どちらから入るか` の直答が前に出て、after-close / quote_sent の wording drift も減る。role suite では public lane の欠陥だけを先に見やすくなる
- 確認: `scripts/check-coconala-reply-role-suites.py --save-report` が `[OK]`、`runtime/regression/coconala-reply/suites/latest.txt` を green 更新
- メモ: handoff private は無効化ではなく、generic bugfix regression から切り離した。service page / service-pack 側の fidelity は別で維持する

### 2026-04-24 / CHG-014
- 分類: `reply-only`
- レイヤ: hard no / next action
- 変更: `本番反映はしない / 直接操作はしない` のような hard no の直後に、`できます` `整理して返します` だけで閉じず、相手がどの段階で止まっているかを1点だけ聞く方針を追加した
- きっかけ: delivered の `本番に反映してもらえませんか` に対し、`このトークルーム内で整理して返せます` で止めると、相手に再説明の負担が戻り、少し距離が出る違和感が見えた
- 想定効果: hard no のあとでも buyer が次の1歩を踏みやすくなり、`できることの宣言` だけで終わる再発を減らせる
- 確認: bugfix 返信学習 batch の delivered ケースで、`今どの段階で止まっているか` を1点聞く形へ修正
- メモ: `hard no -> 代替可能です` ではなく、`hard no -> どこで止まっているか -> そこに合わせた案内` を基本形にする

### 2026-04-24 / CHG-015
- 分類: `reply-only`
- レイヤ: prequote / scope anxiety
- 変更: `同一原因か / 2件分か / 購入前に知りたい` が主質問の時は、`ご購入後は〜を確認します` を先頭へ置かず、まず `この時点で2件分と決まっているわけではない` `同じ原因なら1件` `別原因でも自動加算しない` を返す方針を追加した
- きっかけ: B02 系で、buyer は `購入前に2件分になるか知りたい` と聞いているのに、返信が `ご購入後は...` から入り、主質問への直答が弱くなっていた
- 想定効果: 価格不安と scope 不安への直答が前に出て、`とりあえず購入してから判断されるのでは` という不信を減らせる
- 確認: bugfix 返信学習 batch の B02 を `購入前の結論 -> 別原因でも自動加算しない` の順へ修正
- メモ: 購入後に確認する事実は残してよいが、購入前の不安回答より前に出さない

### 2026-04-24 / CHG-016
- 分類: `reply-only`
- レイヤ: closed / recurrence boundary
- 変更: closed 後の再発相談で、`同じ原因なら基本料金内` を初手で言い切らず、まず `前回の修正とつながる再発か / 新しい原因か` を見て、続き扱いか新しいご依頼かを先に返す方針を追加した
- きっかけ: B06 系で、closed 後なのに `同じ原因なら基本料金内で対応します` と返すと、無料継続対応を約束したように読める drift が出た
- 想定効果: クローズ後の料金・継続対応境界がぶれにくくなり、再発相談での hidden rule を減らせる
- 確認: bugfix 返信学習 batch の closed ケースを `再発か新原因かの確認 -> 続き扱いか新規依頼かを返す` 形へ修正
- メモ: closed 後は、売り手側で後から吸収する余地を残しても、最初の返信では無料保証の含みを出さない

### 2026-04-24 / CHG-017
- 分類: `reply-only`
- レイヤ: complaint / multi-symptom handling
- 変更: 複数症状をすでに書いている相談では、相手へ再選別を返しすぎず、こちらで仮の起点を1つ置いて `つながっているか` を続ける方針を追加した。あわせて、納品後の `修正ファイルがない / 期待と違う` には `認識のずれ` より先に送付漏れや不足の確認へ寄せるようにした
- きっかけ: B02 系で buyer が2点を書いているのに `一番困っている方を1つだけ` と返すと少し redundant_ask に見え、B05 系では `認識のずれ` が buyer 側の誤解へ寄って見える危険があった
- 想定効果: prequote の複数症状相談で会話が前に進みやすくなり、納品後クレームでも buyer の誤解扱いに見える drift を減らせる
- 確認: bugfix 返信学習 batch の B02/B05 を `こちらで仮の起点を置く` / `送付漏れ・返却不能の確認` へ修正
- メモ: どちらも返信文側の運用改善であり、common へは広げない

### 2026-04-24 / CHG-018
- 分類: `reply-only`
- レイヤ: prequote / evidence request
- 変更: prequote で進め方を添える時は `ご購入後は` の連発を避け、`進める場合は` などへ散らす方針を追加した。あわせて、Stripe 画面のスクショ依頼では必要に応じて機密情報を隠してよいことを添えるようにした
- きっかけ: B01〜B03 で service facts 自体は正しいのに `ご購入後は` が続くと少し premature_progress 寄りに見え、B05 では Stripe 画面スクショ依頼に機密情報注意があるとより安全だと判断した
- 想定効果: prequote の購入前返信が購入前提に見えにくくなり、UI案内時のスクショ依頼でも安全性を一言添えやすくなる
- 確認: bugfix 返信学習 batch の B01〜B03 を `進める場合は` へ修正し、B05 に `機密情報が見える場合は隠したうえで` を追加
- メモ: 料金・scope ルールの変更ではなく、購入前の温度感と安全な依頼文への調整

### 2026-04-24 / CHG-019
- 分類: `reply-only`
- レイヤ: buyer wording / prequote
- 変更: buyer 向けの確認系説明で `同じ原因の範囲` が重く見える場面では、`つながっている内容` や `原因が見つかった場合` に翻訳する方針を追加した
- きっかけ: B02 系で service facts 自体は正しくても、`同じ原因の範囲で...` が内部判定語っぽく見え、reviewer に繰り返し拾われた
- 想定効果: service facts を崩さずに、buyer 向けの見積り説明が入りやすくなる
- 確認: bugfix 返信学習 batch の B02 を `原因が見つかった場合は...` に修正
- メモ: facts は維持しつつ、外向け wording だけを軽くする

### 2026-04-24 / CHG-020
- 分類: `reply-only`
- レイヤ: boundary wording / prevention answer
- 変更: 価格を聞かれていない境界判定では `15,000円の範囲で進められるか` を前に出さず、`このサービスで対応できるか` を優先するようにした。あわせて、再発予防の質問では `再発しにくい形` のような保証っぽい言い方を避け、`今回確認できた原因については修正済み` を起点に短く返す方針を追加した
- きっかけ: B01 で価格未質問なのに `15,000円の範囲` が前に出て少し内部寄りに見え、B06 では `再発しにくい形` が保証っぽく読める懸念が出た
- 想定効果: 境界判定が価格説明に引っ張られにくくなり、予防説明でも過剰な保証感を減らせる
- 確認: bugfix 返信学習 batch の B01 を `このサービスで対応できるか` に修正し、B06 を `今回確認できた原因については修正済み` へ変更
- メモ: facts を変えず、buyer 向けの言い回しだけを締める

### 2026-04-24 / CHG-021
- 分類: `reply-only`
- レイヤ: price direct answer / non-stripe boundary
- 変更: `追加でいくらかかりますか` と金額を明示して聞かれた時は、`自動で発生しません` だけで止めず、追加1件の金額を先に返すようにした。あわせて、Stripe以外の決済名が出た時は、決済サービス自体ではなく `Webhook後のサイト側処理 / DB更新` のように、こちらが見る範囲を先に限定して返す方針を追加した
- きっかけ: B04 で追加料金の金額質問に数字を返さず nonanswer 気味になり、B03 では Square 側まで対象に見える余地が残った
- 想定効果: 追加費用不安への直答が強くなり、非Stripe案件でも service boundary を広げすぎない
- 確認: bugfix 返信学習 batch の B03/B04 を reviewer 指摘に沿って修正
- メモ: facts を変えず、buyer が誤読しやすい境界だけを締める

### 2026-04-24 / CHG-022
- 分類: `reply-only`
- レイヤ: prequote / check-only boundary
- 変更: まだ不具合が起きていない `確認だけ` 相談には、そのまま `可能です` と受けず、確認専用サービスのように見せない方針を追加した。気になる箇所が1つある場合だけ、不具合修正として扱えるかを購入前に見立てる形へ寄せる。あわせて、prequote では `確認します` より `見立てます` `対応できるかをお返しします` を優先するようにした
- きっかけ: B02 で `まだ不具合は起きていない確認だけ` をそのまま受ける文面になり、公開中 bugfix-15000 の範囲が確認専用サービスまで広がって見えた
- 想定効果: 公開中 bugfix の守備範囲を崩さずに、購入前の確認依頼も自然に受け止めやすくなる
- 確認: bugfix 返信学習 batch の B02 を reviewer 指摘に沿って修正
- メモ: 価格や facts は変えず、受け方だけを締める

### 2026-04-25 / CHG-023
- 分類: `reply-only`
- レイヤ: #RE review loop / learning log
- 変更: `#RE` の batch 冒頭に `batch_manifest` を置く方針を追加し、reviewer prompt に `直す単位 / 再発根拠 / 既存rule hit / 戻し先候補` の4項目だけを追加した。あわせて learning log に `rule に戻さなかった理由` を残せる欄を追加した
- きっかけ: ChatGPT Pro の `#RE 学習ループ監査4-25` で、必須修正と rule 化を混同しないための最小メタデータが有効と判断した
- 想定効果: `#RE` が添削会やモグラたたきへ寄らず、case fix / 再発 / 好み差 / 却下を後から追いやすくなる
- 確認: bugfix 返信学習 batch に `batch_manifest` を追加し、Codex xhigh / Claude 監査プロンプトへ学習判定4項目を追加
- メモ: 生成本体・rule・renderer・validator は触らない。骨格変更ではなく監査と記録の精度だけを上げる

### 2026-04-25 / CHG-024
- 分類: `reply-only`
- レイヤ: #RE / question-type observation
- 変更: Pro 監査結果を受け、次の #RE で見る buyer 質問タイプと batch_manifest 案を `question-type-batch-plan-20260425.ja.md` に分離して記録した。README の `#RE` には、必要に応じて `主質問タイプ` と `最初に答えるべき問い` を観察ラベルとして添える方針だけを追記した
- きっかけ: batch-03 で、buyer が価格・納期・対象・保証などのサービス仕様を聞いているのに、汎用不具合テンプレへ流れる nonanswer が出た
- 想定効果: 次の Codex でも、質問タイプ判定を狭く検査する #RE を再開できる。質問タイプ router や renderer 刷新に飛ばず、観察から進められる
- 確認: まだ運用メモ段階。次回 `RE-2026-04-25-bugfix-04-question-type-spec` で検証する
- メモ: 生成本体・rule・renderer・validator は未変更。`一息で言う` は引き続き reviewer_prompt 観点に留める

### 2026-04-25 / CHG-025
- 分類: `reply-only`
- レイヤ: prequote / service spec question
- 変更: `prequote-compression-rules.ja.md` に、価格固定・復旧時間・原因不明時の料金/返金・保証・対象可否・コード/設定のようなサービス仕様質問では、汎用不具合確認テンプレートへ流さず仕様上いま答えられる事実を先に返す方針を追加した
- きっかけ: `RE-2026-04-25-bugfix-04-question-type-spec` r0 で、batch-02/03 と同型の `question_type_miss` が再発した
- 想定効果: buyer が不具合の中身ではなく価格・納期・保証・返金などを聞いている時に、`まず確認します -> 15,000円 -> 確認します` の汎用テンプレへ逃げる崩れを減らす
- 確認: batch r1 で B01/B02/B04/B05/B06 を最小修正。生成本体・renderer・validator は未変更
- メモ: 大規模な質問タイプ router は作らない。次 batch で副作用を確認する

### 2026-04-25 / CHG-026
- 分類: `reply-only`
- レイヤ: external research lane / #RE observation
- 変更: Deep Research の `日本語実務返信品質の外部調査報告4-25` を、`external-research-observation-plan-20260425.ja.md` として観察候補へ分離した。README からも参照できるようにした
- きっかけ: 外部調査で、現行骨格は大きく再設計せず、`#RE` の観察候補を増やして再発だけ戻す方針が補強された
- 想定効果: 次セッションでも、外部調査の知見を忘れず、`bugfix-05-boundary-secure-share` や `bugfix-06-poststate-aftercare` の archetype へ使える
- 確認: rule / renderer / validator には未反映。外部調査レーンのメモとして保存
- メモ: 外部調査結果をそのまま正本 rule にしない。まず #RE で再発確認する

### 2026-04-25 / CHG-027
- 分類: `common`
- レイヤ: service state / source-of-truth guard
- 変更: Pro のサービス状態監査を受け、`public:false` service の外向け出力禁止、`service-registry.yaml` の `public/source_of_truth` 優先、handoff ready の内部専用ヘッダー、gold の参照資格方針を最小補強した
- きっかけ: handoff-25000.ready.txt が外向け文面として完成しているため、public:false ガードを踏み外すと価格・導線が混ざるリスクがあると判定された
- 想定効果: Codex の自由な文章判断を保ちつつ、公開状態・価格・範囲・正式納品 gate の上書き事故を減らす
- 確認: service-registry / self-check core / service-pack source-of-truth / runtime interface / gold README / handoff ready header を更新。renderer / validator / 生成本体は未変更
- メモ: 広い再設計ではなく、既存骨格へのガード文追加に留める

### 2026-04-25 / CHG-028
- 分類: `reply-only`
- レイヤ: skill reference / latest #RE bridge
- 変更: `coconala-reply-bugfix-ja` に、最新 #RE メモと self-check core / prequote compression / learning-log への参照導線を追加した。外部調査メモは rule ではなく stock / archetype / reviewer 観点として扱うことも明記した
- きっかけ: Pro や外部調査の知見を落とし込んだ後でも、古い skill 本体だけを読んで返信すると最新 guard を読み落とす懸念が出た
- 想定効果: 次セッションや監査時に、skill が古いテンプレ本体として誤用されず、最新正本へ自然に辿れる
- 確認: skill 本体へ大量ルール移植はせず、参照導線だけを追加。renderer / validator / 生成本体は未変更
- メモ: 骨格変更ではない。`#RE` 観察メモを通常返信 rule と混同しないための案内

### 2026-04-25 / CHG-029
- 分類: `reply-only`
- レイヤ: renderer fixed phrase / validator vocabulary
- 変更: `quote_sent` の返金・原因不明固定文を、`調査と切り分けの作業分として15,000円は発生` から、`原因を特定できず修正方針にもつながらない状態のまま15,000円の正式納品として進めない / 返金は断定しない` に置き換えた。あわせて、購入後の直接 push / 本番反映の境界文を `前提にしていません` から `行っていません` + 修正済みファイル・差分・適用手順の代替提示へ寄せ、closed 後の再依頼は新しい見積り提案前提の表現へ締めた
- きっかけ: #R / #RE の script 経由で古い固定文が発火し、最新の返金・安全境界・closed 状態 guard とズレる可能性が見つかった
- 想定効果: current rules で batch を作る時に、旧テンプレ由来の `返金/原因不明` `直接push` `本番反映` `closed後の継続` のノイズが混ざりにくくなる
- 確認: `check-rendered-quote-sent-followup.py` / `check-rendered-post-purchase-quick.py` / `check-rendered-closed-followup.py` の対象ケースを通し、`check-coconala-reply-role-suites.py --save-report` が全 role OK
- メモ: renderer の構造や層は増やしていない。固定文と validator 語彙を最新正本へ合わせた最小補修

### 2026-04-25 / CHG-030
- 分類: `reply-only`
- レイヤ: renderer / validator boundary regression
- 変更: `STK-063` の本番管理画面ログイン情報・直接作業依頼を専用境界ケースとして検出し、`直接作業できない / ログイン情報を送らない / 修正済みファイルと反映手順で返す` へ固定した。あわせて、quote_sent の Vercel デプロイ手順質問と purchased の Vercel 手順不安を、Yes/No と画面操作/コマンド分離で返すようにし、closed 後の再依頼から `今の公開範囲` を除いた
- きっかけ: `RE-2026-04-25-bugfix-07-script-boundary-regression` r0 で、古い固定文は消えた一方、B02/B04/B05 が過去 batch と同型の nonanswer / boundary_miss / missing_safe_alternative で止まった。特に B05 は同一 stock で2回再発した
- 想定効果: 本番ログイン情報・直接操作・本番反映手順の境界質問で、汎用の `確認します` へ逃げず、安全代替まで一息で返せる
- 確認: `STK-045` / `STK-051` / `STK-052` / `STK-063` / `STK-091` / `QST-004` の targeted render + lint が OK。`check-coconala-reply-role-suites.py --save-report` も全 role OK
- メモ: 骨格変更ではなく、再発証拠のある境界ケースだけを renderer / validator に戻した

### 2026-04-25 / CHG-031
- 分類: `reply-only`
- レイヤ: refund gate / closed wording validator
- 変更: quote_sent の失敗時料金説明に、原因特定だけでなく `修正済みファイルの返却まで進められない場合` も正式納品へ進めない gate として入れた。closed follow-up では `形になります` を validator で検出し、再依頼価格文を `前回とは別の不具合として新規で見る場合は、基本は15,000円です` へ置き換えた
- きっかけ: batch-07 r1 の Codex 再監査で、B01 の失敗時料金説明に修正済みファイル返却 gate が抜け、B06 に既知NGの `形になります` が残っていると指摘された
- 想定効果: 返金不安への回答で `原因だけ分かれば納品` と誤読されにくくなり、closed 後の再依頼文から内部的・機械的な routing 表現が減る
- 確認: `QST-004` / `STK-091` の targeted render + lint が OK。`check-coconala-reply-role-suites.py --save-report` も全 role OK
- メモ: 新規 rule 追加ではなく、既存 facts / ban 表現の未反映を renderer と validator に同期した

### 2026-04-25 / CHG-032
- 分類: `reply-only`
- レイヤ: quote_sent reaction / validator
- 変更: `risk_refund_question` の冒頭反応で、buyer の `了解` への謝意よりも失敗時料金不安の受け止めを優先し、`直らなかった場合の扱いについてですね。` を返すようにした。あわせて quote_sent validator で `ご了解` を検出するようにした
- きっかけ: `QST-004` の `15,000円でのご了解、ありがとうございます。` が不自然で、renderer から再発する可能性があると分かった
- 想定効果: 返金・失敗時料金不安の場面で、価格了承への反応が先に出て buyer の主不安からずれることを防ぐ
- 確認: `QST-004` の targeted render + lint が OK。`check-coconala-reply-role-suites.py --save-report` も全 role OK。`os-check.sh` も OK
- メモ: `了解` という入力語を全面禁止しない。`ご了解ありがとうございます` 系の不自然な外向け反応だけを止める

### 2026-04-25 / CHG-033
- 分類: `reply-only`
- レイヤ: quote_sent fixed phrase / validator vocabulary
- 変更: quote_sent renderer に残っていた `形になります` 系の固定文を、`選んで進めてください` `切り分けます` `ご相談します` など主語と行動が見える表現へ置き換えた。あわせて quote_sent validator で `形になります` を検出するようにした
- きっかけ: 固定文が Codex の自然判断を邪魔する可能性を調べたところ、既知NGの `形になります` が quote_sent 側に複数残っていた
- 想定効果: quote_sent のサービス仕様・返金・支払い方法・範囲切り分けで、事務的な固定語尾が発火して bot 感が出ることを減らす
- 確認: `QST-004` の targeted render + lint が OK。`check-coconala-reply-role-suites.py --save-report` も全 role OK。`os-check.sh` も OK。`scripts/render-*.py` に `形になります` が残っていないことを確認
- メモ: 価格・範囲・禁止事項の facts は変えない。語尾と受け止めの固定文だけを最小補修する

### 2026-04-25 / CHG-034
- 分類: `reply-only`
- レイヤ: purchased/delivered/closed renderer / validator
- 変更: purchased の追加範囲相談で `の件の件` が出ないよう topic 抽出を修正し、validator に助詞重複検出を追加した。delivered の副作用疑いでは、相手文にない `Webhookの受信` を補完しないようにし、closed の別イベント相談では `メッセージ上で確認 -> 実作業が必要なら見積り提案/新規依頼` を出すようにした。closed 返金要求では `お約束する形` を禁止し、返金可否断定不可と取引状況確認へ寄せた
- きっかけ: `RE-2026-04-25-bugfix-08-confirmation-stamp-r0` で、`確認しました` 系の固定反応に加えて `の件の件`、未提示対象名の補完、closed 後導線不足、返金表現の既知NGが確認された
- 想定効果: purchased / delivered / closed の実務返信で、固定反応が buyer の主張を上書きしたり、closed 後の進め方を曖昧にしたりする事故を減らす
- 確認: `TRK-002` / `SCP-003` / `DLV-002` / `DLV-004` / `CLS-003` / `EMO-004` の targeted render + lint が OK。`check-coconala-reply-role-suites.py --save-report` も全 role OK。`os-check.sh` も OK
- メモ: `確認しました` を全面禁止しない。文脈を壊す固定反応と、明確な文法バグだけを止める

### 2026-04-25 / CHG-035
- 分類: `reply-only`
- レイヤ: delivered renderer / validator
- 変更: delivered の将来不安・保証確認ケースに残っていた `保証を先にお約束する形ではありませんが` を、固定保証期間を約束していないことが分かる表現へ置き換えた。あわせて delivered validator でも `形になります` / `お約束する形` を検出するようにした
- きっかけ: fixed phrase 探索で、batch-08 外の delivered renderer に既知NGの `お約束する形` が1箇所残っていることが分かった
- 想定効果: 納品後の将来不安・保証確認で、事務的な固定語尾が buyer の不安対応を邪魔することを防ぐ
- 確認: delivered 将来不安ケースの targeted render + lint が OK。`check-coconala-reply-role-suites.py --save-report` も全 role OK
- メモ: 将来仕様変更や固定保証期間の facts は変えない。既知NGの語尾だけを最小補修する

### 2026-04-25 / CHG-036
- 分類: `reply-only`
- レイヤ: purchased/delivered renderer / batch r2
- 変更: purchased の追加範囲相談で、追加料金を直接聞かれていない場合でも `同じ原因なら見る` だけで閉じず、別原因時は追加対応が必要か先に相談する一文を戻した。delivered の副作用疑いでは、buyer の `修正いただいた箇所` をそのまま返さず、出品者側の主語として `修正した箇所` に整えた
- きっかけ: `RE-2026-04-25-bugfix-08-confirmation-stamp-r1` の Codex 再監査で、B01 の別原因時の扱い落ちと、B03 の主語違和感が必須修正になった
- 想定効果: 購入後の追加範囲相談で scope 不安を残しにくくし、納品後の副作用疑いで buyer 文の敬語を機械的にコピーして出品者側の主語が崩れることを防ぐ
- 確認: `TRK-002` / `SCP-003` / `DLV-002` の targeted render + lint が OK。`check-coconala-reply-role-suites.py --save-report` も全 role OK
- メモ: 新規 rule 化はしない。B01/B03 の実送信リスクだけを r2 と renderer に最小同期した

### 2026-04-25 / CHG-037
- 分類: `reply-only`
- レイヤ: platform phase contract / closed refund
- 変更: closed 後の返金要求について、`取引状況に沿って確認します` だけで曖昧に閉じず、旧トークルームが閉じていること、返金可否やキャンセル手続きをこの場で断定できないこと、まずメッセージ上で前回修正との関係を見ることを明示する方針にした。`Gold Reply 20` から、ココナラ取引の返金と依頼者サービス側の Stripe 返金を混同する `Stripe 管理画面` 文を削除した
- きっかけ: #AR でココナラ公式ヘルプを確認した結果、closed 後は旧トークルームでメッセージ/ファイル投稿/おひねりができず、取引中へ戻すことや承諾取消もできないため、返金要求への `取引状況に沿って` が buyer には曖昧すぎると判断した
- 想定効果: closed 後の返金・再発不満で、seller が返金手続きまで曖昧に引き受けるように見えたり、逆にはぐらかして見えたりする事故を減らす
- 確認: `EMO-004` / `CLS-003` の targeted render + lint が OK。`check-coconala-reply-role-suites.py --save-report` も全 role OK
- メモ: ココナラ取引の返金判断は断定しない。まず前回修正との関係を確認し、作業が必要なら見積り提案または新規依頼へ戻す

### 2026-04-25 / CHG-038
- 分類: `reply-only`
- レイヤ: platform phase contract / DeepResearch review
- 変更: DeepResearch の phase contract レビューを受け、`platform-contract.yaml` に内部 state の写像を明記した。`quote_sent` は見積り提案済みだが入金完了前、`purchased` は入金完了後のトークルーム open、`delivered` は正式な納品後・クローズ前、`closed` は完了としてクローズ済みで `cancelled` とは分ける。あわせて、`delivered` で差し戻し可否を一般化しないこと、`closed` 後は確認材料の受領と実作業を分けることを追加した
- きっかけ: DeepResearch が、#AR メモの骨子は公式仕様と整合する一方、phase 名が公式用語ではなく内部写像であること、`quote_sent` / `delivered` / `closed` の言い切りに補正が必要だと指摘した
- 想定効果: 見積り提案後を取引開始済みと誤認したり、正式納品後を closed と混同したり、closed 後のメッセージ確認を実作業受領へ滑らせたりする事故を減らす
- 確認: `platform-contract.yaml` の YAML 読み込み OK。`./scripts/os-check.sh` OK。`check-coconala-reply-role-suites.py --save-report` は全 role OK
- メモ: phase を増やさない。電話相談・定期購入・支払い方法別返金 timing は phase contract 本体に入れない

### 2026-04-25 / CHG-039
- 分類: `reply-only`
- レイヤ: platform phase contract / Pro final audit
- 変更: Pro 最終監査を受け、`closed_talkroom_locked` を公式事実に限定し、`実作業なら見積り提案または新規依頼へ戻す` は operational guidance 側へ分離した。`delivery` は phase ではなく mode として扱い、`mode: delivery` + `when: pre_formal_delivery` に分けた。closed 後返金では、前回補足で済む確認か実作業が必要な新規導線かを切り分ける着地を追加し、quote_sent では入金前に実作業を開始しないことを明示した
- きっかけ: Pro が、platform-contract は正本投入可だが、official/operational の混在、delivery mode/state 混線、closed 返金の最終着地不足、quote_sent の作業開始曖昧さを最小補正すべきと指摘した
- 想定効果: 公式事実と運用判断を分けたまま、buyer には「結局どうなるか」が見える返信に寄せる。closed 後に旧トークルーム内キャンセルやおひねり、見積り前実作業へ滑る事故を減らす
- 確認: `platform-contract.yaml` の YAML 読み込み OK。`./scripts/os-check.sh` OK。`check-coconala-reply-role-suites.py --save-report` は全 role OK（eval の既存 projection warning `CMP-002` 1件のみ）
- メモ: ファイル受領を全面禁止しない。確認材料の受領と、修正・差し替えファイル作成・成果物返却を分ける

### 2026-04-26 / CHG-040
- 分類: `reply-only`
- レイヤ: reviewer prompt / phase answer gap
- 変更: Codex / Claude の監査プロンプトに `phase_answer_gap` を追加した。文面が安全でも、`quote_sent / delivered / closed` などの phase で buyer が次に取れる行動、不可な操作、代替導線、次アクションのどれかが抜けている場合に拾う監査ラベルとして扱う
- きっかけ: `RE-2026-04-26-bugfix-09-phase-contract-edge` で、`確認します` と安全に返していても、入金前作業開始・承諾後・差し戻し・closed 後おひねりなどで buyer が「結局どうすればよいか」迷うケースが出た
- 想定効果: 生成側を重くせず、外部 reviewer が「安全だが導線が見えない」返信を検知しやすくする。検知した再発だけを gold / validator / rule へ戻す
- 確認: prompt / markdown のみ更新。生成 renderer / validator は未変更
- メモ: `phase_answer_gap` は生成 rule ではなく監査レンズ。毎回説明を足す目的では使わない

### 2026-04-26 / CHG-041
- 分類: `reply-only`
- レイヤ: gold / learning-log / phase contract edge
- 変更: `RE-2026-04-26-bugfix-09-phase-contract-edge-r2` が Codex / Claude の両方で採用可になったため、`quote_sent` 入金前作業開始、`delivered` 承諾前後、`delivered` 差し戻し、`closed` おひねり追加修正の4型を `Gold Reply 22` として保存した。あわせて learning-log に `phase_answer_gap` の検知結果と、renderer / validator へ即反映しない理由を記録した
- きっかけ: r0 では phase 上の不可・代替・次導線が抜けていたが、r2 では buyer が次に取れる行動まで見える形に改善し、両 reviewer で通過した
- 想定効果: 今後の #RE で、`確認します` だけでは足りない phase edge を検知した時に、説明過多にせず不可・代替・次導線の置き方を参照できる
- 確認: markdown / learning-log のみ更新。`./scripts/os-check.sh` OK
- メモ: `Gold Reply 22` はテンプレートではなく近いケースのアンカー。validator / renderer 本体への反映は同型再発を見てから判断する

### 2026-04-26 / CHG-042
- 分類: `reply-only`
- レイヤ: reviewer prompt / discovery label
- 変更: Codex / Claude の監査プロンプト、監査 batch、failure taxonomy に `unnamed_discomfort` を追加した。既存ラベルにまだ当てはまらないが、実務返信として buyer が詰まりそう・逃げに見えそう・商売上弱そうな違和感を、最大1〜2件だけ観察できる reviewer 専用ラベルとして扱う
- きっかけ: `phase_answer_gap` の発見後、ユーザー監査から「まだ名前がついていない違和感を、ノイズを抑えて拾う枠」が必要だと分かった
- 想定効果: 生成側を重くせず、Codex / Claude の自由な監査能力で新しい崩れの兆候を拾いやすくする。単発の好み差は必須修正にせず、再発してから名前付け・gold・validator・rule 返却を検討する
- 確認: prompt / markdown のみ更新。生成 renderer / validator は未変更
- メモ: `unnamed_discomfort` は rule ではなく発見用レンズ。実務リスクを説明できない指摘や好み差は採用しない

### 2026-04-26 / CHG-043
- 分類: `reply-only`
- レイヤ: closed renderer / validator / gold
- 変更: `RE-2026-04-26-bugfix-10-closed-materials-work-boundary-r1` が Codex / Claude の両方で採用可になったため、closed 後の確認材料と実作業境界を最小分岐として戻した。closed renderer に、確認材料送付、ZIP修正返却、外部共有、大容量ファイル、秘密情報送付、無料/追加料金不安、見積り前原因確認の分岐を追加した。closed validator には generic fallback、外部共有、秘密値、ZIP修正返却、見積り前原因調査、無料/追加料金不安の検出を追加した。あわせて `Gold Reply 23` と learning-log に採用型を保存した
- きっかけ: r0 で closed 6件すべてが `今回のご相談がどの種類かを見てから案内します` の同一 generic fallback になり、buyer の主質問へ答えられなかった
- 想定効果: closed 後に、確認材料として見ることと、修正・差し替えファイル作成・成果物返却などの実作業を混ぜる事故を減らす。外部共有や秘密値送付へ逃がさず、buyer が次に送る材料や見積り導線を把握しやすくする
- 確認: `closed-materials-work-boundary-bugfix10.yaml` の unified render + lint が OK。`check-rendered-closed-followup.py` も OK。generic fallback guard が holdout の第三者指摘・技術質問 follow-up 3件も拾ったため、closed renderer に最小分岐を追加して全 role suite OK
- メモ: closed 後のファイル受領を全面禁止しない。確認材料の受領と実作業を分けるだけに留める

### 2026-04-26 / CHG-044
- 分類: `reply-only`
- レイヤ: platform contract / service facts / closed angry free-support wording
- 変更: ココナラ公式のカテゴリ最低サービス価格を受け、`bugfix-15000` のカテゴリ最低価格を service facts に追加した。platform contract には、closed 後の実作業は0円作業を前提にせず、こちら起因の可能性がある場合でもココナラ上で進められる新しい取引導線と費用を先に相談する、という guidance を追加した。B05 の無料対応不満型は `15,000円をいただく前提では進めません` から `通常料金をいただく前提では進めません` に変更し、実作業が必要な場合は `ココナラ上で進められる形と費用の有無` を先に相談する文面へ寄せた
- きっかけ: ユーザー監査で、closed 後に実作業が必要な場合、たとえこちら起因でも0円では取引できず、カテゴリ最低価格制約があるのではないかと指摘された
- 想定効果: closed 後の不満対応で、無料実作業を約束したように見える事故と、いきなり通常料金を請求するように見える事故の両方を避ける
- 確認: `closed-materials-work-boundary-bugfix10.yaml` の unified render + lint OK。`check-rendered-closed-followup.py` OK。全 role suite OK
- メモ: 外向けには最低金額を先出ししない。実際の提案金額は画面上の制約とサービスカテゴリを確認してから決める

### 2026-04-26 / CHG-045
- 分類: `reply-only`
- レイヤ: closed free-support wording / reviewer prompt / presentation
- 変更: Pro 監査を受け、closed 後の無料対応不満型 B05 をさらに自然化した。`同じ原因なら通常料金前提では進めない` を、無料約束に読ませにくい `確認しないまま、通常料金の新規依頼として進めることはしません` へ寄せ、`ココナラ上で進められる形と費用の有無` を `作業に入る前に、ココナラ上でどう進めるかと費用が発生するか` へ変更した。closed renderer の時刻コミットは分単位の bot 感を避けるため15分単位に丸める。監査ラベルには `transaction_model_gap` を追加した
- きっかけ: Pro が、今回の「ツギハギ感は transaction model 欠落として出る」という仮説を支持しつつ、writer 常駐ルールを増やすのではなく reviewer レンズと局所文面の微調整に留めるべきと指摘した
- 想定効果: closed 後の怒り気味 buyer に対して、無料約束にも通常料金請求にも見せず、確認材料・実作業・費用相談の順序をより自然に出せる。時刻の分単位表示による bot 感も減らす
- 確認: B05 targeted render + lint、`check-rendered-closed-followup.py`、全 role suite、`os-check.sh` OK
- メモ: `transaction_model_gap` は writer rule ではなく reviewer 専用。validator に入れるのは deterministic な事故だけに限定する

### 2026-04-26 / CHG-046
- 分類: `reply-only`
- レイヤ: gold / validator / transaction model gap
- 変更: `RE-2026-04-26-bugfix-11-transaction-model-gap-r2` で、取引構造の曖昧さを検証した。r0 では quote_sent の入金前コード/ログ確認、purchased の追加症状と別料金不安、delivered の承諾前後、closed の購入なし修正助言と次回相談導線で generic fallback や nonanswer が出た。r2 で B06 の見積り表現重複を圧縮し、B02/B05/B06 の3型を `Gold Reply 24` として保存した。quote_sent validator には入金前の材料要求 guard、purchased validator には追加症状の別料金不安 guard を追加した
- きっかけ: Codex / Claude の再監査で、文面の自然さだけでなく、支払い・作業開始・見積り提案・購入の順番が一本につながっていないと buyer が迷うことが確認された
- 想定効果: local lint が OK でも、入金前作業開始や追加料金不安への nonanswer を止めやすくする。closed 後の「文章で直し方だけ教えて」はファイル返却なしでも実作業寄りとして扱う
- 確認: `TMG-001` / `TMG-002` targeted lint が新 guard で NG になることを確認。全 role suite OK（eval の既存 projection warning `CMP-002` 1件のみ）
- メモ: `transaction_model_gap` は引き続き reviewer レンズ。validator へ戻すのは、入金前材料要求や別料金不安のように文字列条件で安定検出できるものだけにする
