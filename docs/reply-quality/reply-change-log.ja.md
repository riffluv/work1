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

### 2026-04-26 / CHG-047
- 分類: `reply-only`
- レイヤ: shelf / gold / taxonomy / learning-log
- 変更: batch-12〜17 の棚卸しを行い、戻し先を `validator 候補 / gold / reviewer_prompt / case_fix` に分類した。新規に `Gold Reply 25` と棚卸しメモ、learning-log を追加し、failure taxonomy に `template_quote_drift` と `cancel_word_misroute` を追加した
- きっかけ: batch-17 までで、丸引用 + `とのことでした`、delivered 汎用 fallback、購入前の対処法要求、quote_sent の追加料金/キャンセル不安、技術的キャンセル語の誤分類が再発パターンとして固まった
- 想定効果: 次の修正で、全部を writer rule にせず、再発性が高く deterministic に検出できる事故だけ validator 化できる。gold は4型に絞り、参照ノイズを増やしすぎない
- 確認: markdown / learning-log のみ更新。validator 実装は未実施
- メモ: 次に validator 実装するなら、優先順は `template_quote_drift` -> `delivered_generic_fallback` -> `cancel_word_misroute` -> `prequote solution extraction` -> `quote_sent fee/cancel anxiety`

### 2026-04-26 / CHG-048
- 分類: `reply-only`
- レイヤ: validator / minimal renderer / pre-shelf regression
- 変更: CHG-047 の棚卸しを受け、V1 `template_quote_drift`、V2 `delivered_generic_fallback`、V3 `prequote solution extraction`、V4 `cancel_word_misroute` を validator に戻した。targeted sentry で残った `キャンセルフロー` 誤分類、delivered 承諾後不安、delivered 月次確認要求、購入前の対処法要求は、既存 renderer に最小分岐だけ追加した
- きっかけ: batch-12〜17 で、丸引用、delivered 汎用 fallback、購入前の具体修正手順要求、技術的キャンセル語の誤分類が r0 で再発した。batch-17 r1/r2 で採用可の文面が固まったため、deterministic に検出できるものだけ恒久反映した
- 想定効果: reviewer に出す前の r0 で、読んでいないように見える丸引用、承諾/承諾後/月次サポートへの汎用 fallback、購入前の直し方だけ要求、Stripe の技術的キャンセル語の誤分類を止めやすくする
- 確認: targeted fixture `pre-shelf-validator-bugfix12-17.yaml` OK。`python3 scripts/check-coconala-reply-role-suites.py --save-report` 全 role OK（eval の既存 projection warning `CMP-002` 1件のみ）。`./scripts/os-check.sh` OK
- メモ: V5 `quote_sent` 追加料金/キャンセル不安は今回は gold 優先で維持。次の #RE で同型再発したら validator 化を検討する

### 2026-04-26 / CHG-049
- 分類: `reply-only`
- レイヤ: quote_sent renderer / validator / gold / completion gate
- 変更: batch-17 B01 のユーザー監査を受け、V5 `quote_sent` 追加料金/キャンセル不安を `completion_gate_gap` として格上げした。`extra_fee_fear` renderer に、購入前なら無理に支払いボタンを押さなくてよいこと、別原因が複数でも自動増額しないこと、15,000円内で修正完了できない場合は先へ進まず説明すること、追加/停止/キャンセル扱いは作業状況とココナラ手続きに沿って相談することを追加した。validator / Gold Reply 25 / 棚卸しメモ / learning-log / failure taxonomy も更新した
- きっかけ: `キャンセルを安請け合いしない` guard だけが働くと、予算上限のある buyer に対して未完成納品・追加費用・停止判断の導線が宙ぶらりんになることを確認した
- 想定効果: 15,000円内で完了不能な可能性が出た時に、未完成のまま正式納品へ押し込む印象と、キャンセル/返金を事前確約する印象の両方を避ける
- 非変更: キャンセル可否・返金額を事前断定する rule は追加しない。納品物本文や service facts へは反映しない

### 2026-04-26 / CHG-050
- 分類: `reply-only`
- レイヤ: quote_sent wording / completion gate
- 変更: CHG-049 の B17-01 文面から、buyer を足踏みさせる `購入前なので、迷いがあれば支払いボタンを押さなくて大丈夫` と、意味が曖昧な `追加対応として進めるか` を外した。標準文は `今回の見積もりは15,000円の範囲で進める前提`、`この金額内では修正完了まで進められないと分かった場合は止めて説明`、`勝手に料金が増えたり追加作業へ進まない`、`キャンセル扱いはココナラ上の手続きに沿って相談` に圧縮した
- きっかけ: ユーザー監査で、buyer の本音は「15,000円で対応してほしい。超えるならやめたい」であり、長い seller 都合の分岐説明は不信感を生むと分かった
- 想定効果: 予算上限のある buyer に対して、購入を止める方向へ押し戻さず、かつ未完成納品・自動追加料金・キャンセル確約の事故を避ける

### 2026-04-26 / CHG-051
- 分類: `reply-only` + service listing wording
- レイヤ: prequote renderer / validator / gold / service page copy
- 変更: 同じ `completion_gate_gap` が prequote 側にも残っていないか確認し、`追加費用が怖い`、`2件だと30,000円か`、`原因不明でも15,000円がかかるのか`、`修正範囲が広くて返金になるか`、`全部見て全部直すと予算内か`、`3本あるAPIが15,000円×3か` の6件を sentry 化した。prequote renderer に `budget_completion_gate` を追加し、validator でも自動増額なし・completion gate・同一原因/別原因・返金/キャンセル断定回避を検査するようにした。公開サービスページ FAQ と mirror の `追加対応に進むか` も、`修正完了まで進められない場合は止めて説明` へ置き換えた
- きっかけ: GMN-015 / QLT-003 / V3-003 / V3-006 / V4-020 が lint OK のまま、予算上限や返金不安に対して基本テンプレートへ流れることを確認した
- 想定効果: quote_sent だけでなく prequote の段階でも、「15,000円で見てほしい。超えるならやめたい」という buyer の本音を落とさず、未完成納品・自動追加料金・キャンセル確約を同時に避ける

### 2026-04-26 / CHG-052
- 分類: `reply-only`
- レイヤ: completion gate / internal operating model
- 変更: `completion_gate_gap` の内部判断モデルを6点に整理し、failure taxonomy、Gold Reply 25、prequote 約束ポリシー、棚卸しメモへ反映した。内容は、15,000円で修正完了まで進める前提、別原因・別フロー・重い修正では勝手に追加作業へ進まない、範囲内で完了不能なら止めて説明する、追加費用を望まない buyer に未完成納品を押し切らない、キャンセル/返金は断定せず手続きに沿って相談する、軽微なら基本料金内吸収の余地を残す、の6点
- きっかけ: ユーザー監査で、`キャンセルを安請け合いしない` だけでは返信が宙ぶらりんになり、取引実務としては「未完成納品へ押し切らない」ことが中核だと整理された
- 想定効果: 返信文に長い防御説明を増やさず、内部では completion gate を通してから buyer に必要な部分だけを短く出せる

### 2026-04-26 / CHG-053
- 分類: service listing wording
- レイヤ: bugfix-15000 public service page / completion gate
- 変更: `bugfix-15000.live.txt` と mirror の `coconala-listing-final.ja.md` で、`別原因だけ追加対応をご案内します`、`レポートにまとめます`、`キャンセルを含めてご相談します` のように、追加対応・報告のみ納品・キャンセルを誤読させやすい表現を整理した。別原因は「進める前に対応方法と費用の有無を相談」、間欠不具合は「修正方針につながれば修正まで進める / 完了できない場合は止めて必要情報を伝える」に変更した
- きっかけ: completion gate 方針が固まったことで、公開サービスページ側にも seller 視点の曖昧表現が残っていないか確認した
- 想定効果: サービスページの時点で、未完成納品・自動追加料金・返金/キャンセル保証のいずれにも誤読されにくくする

### 2026-04-26 / CHG-054
- 分類: service listing wording
- レイヤ: ChatGPT Pro audit / bugfix-15000 public service page
- 変更: ChatGPT Pro 監査結果を受け、FAQ の `原因が分からないまま15,000円になることはありますか？` を `原因が分からないまま正式納品されますか？` へ差し替えた。`正式納品へ進めません` は `一方的に正式納品へ進めることはありません` に寄せ、返金/キャンセル保証ではなく作業状況に応じた個別相談であることを明記した。大幅な設計変更・別フロー・秘密値・外部連絡/外部決済・GitHub等への直接pushも公開本文で明確化し、公開ページ末尾のトークルーム回答例と将来追加候補を削除した
- きっかけ: Pro 監査で、買い手の安心に効く一方で `原因不明なら料金が発生しない` `直らなければキャンセル/返金保証` と誤読される余地、未公開サービス導線が公開文面に混ざるリスクが指摘された
- 想定効果: completion gate を保ちつつ、返金保証・キャンセル保証・未公開サービス期待・追加作業自動化の誤読を減らす

### 2026-04-26 / CHG-055
- 分類: service listing wording
- レイヤ: bugfix-15000 public service page / answer examples
- 変更: CHG-054 で削除したトークルーム回答例3件を、本番ページ用の必須欄として復元した。回答例は current completion gate / 秘密値禁止 / 追加料金自動発生なしの方針に合わせて更新し、`将来追加候補` だけは公開文面に戻さない
- きっかけ: ユーザー確認で、トークルーム回答例3件は公開ページに書き込む必要がある項目だと判明した
- 想定効果: ココナラのサービスページ項目を欠落させず、未公開サービス導線だけを除外した状態に戻す

### 2026-04-26 / CHG-056
- 分類: `reply-only`
- レイヤ: prequote renderer / validator / gold / shelf
- 変更: batch-18 B08 の監査結果を棚卸しし、`修正と整理、どちらを先に頼むべきか` への旧テンプレート回帰を `fix_vs_structure_first` として追加した。failure taxonomy / Gold Reply 25 / 棚卸しメモ / learning-log に反映し、prequote renderer には非公開 handoff 導線を出さずに「まず不具合修正から見るのが近い」と直答する最小分岐を追加した。prequote validator と active fixture `PSV-006` も追加した
- きっかけ: Codex / Claude 監査で、B08 だけが `この不具合なら15,000円で進められます` の基本テンプレートへ戻り、buyer の主質問「修正と整理どちらが先か」に答えていないと一致した
- 想定効果: 現公開状態で `整理` `コード全体` `把握` などの語が出ても、非公開サービス名や25,000円導線へ逃がさず、公開中 bugfix の範囲で主質問に答えられる
- 確認: `PSV-006` targeted lint OK。`pre-shelf-validator-bugfix12-17.yaml` unified render + lint OK。`check-rendered-prequote-estimate.py --case-id PSV-006` OK

### 2026-04-26 / CHG-057
- 分類: `reply-only`
- レイヤ: writer brief / compression rules / gold usage / batch wording
- 変更: ChatGPT Pro の設計監査を受け、長文化・ツギハギ感を `surface_overexposure` として taxonomy に追加した。`prequote-compression-rules` に post-render compression と boundary atom の `hidden / one_line / expanded_only_if_asked` を追加し、`writer-brief` には外向けに出す安全条件を主質問に必要なもの最大2個までに絞る原則を追加した。Gold 24/25 は長文テンプレートではなく、`minimal_outward` と `expanded_only_if_asked` を持つ判断 anchor として使う方針へ寄せた。batch-19 B01/B03/B08 は短縮見本へ修正した
- きっかけ: ユーザー監査と Pro 監査で、返信SYSTEMは安全境界を守れている一方、内部 lens の判断要素を本文に並べすぎると、buyer には監査項目・規約説明・契約説明のように見えると確認された
- 想定効果: `transaction_model_gap` / `completion_gate_gap` を削らず、内部では厚く見たまま、外向け本文は `直答 1〜2文 -> 必要な境界 1〜2文 -> 次アクション 1文` へ圧縮しやすくする
- 非変更: renderer / validator の大規模変更や hard fail 追加は行わない。まず docs/gold/batch の最小反映に留め、次の #RE で短縮により安全性が落ちていないか確認する

### 2026-04-26 / CHG-058
- 分類: `reply-only`
- レイヤ: prequote renderer / delivered renderer / validator allowlist / batch-20
- 変更: batch-20 r0 の Codex / Claude 監査で、B01/B02/B03/B07 が batch-19 r0 と同じ旧テンプレートへ戻ったため、case 修正ではなく renderer 未反映として最小反映した。prequote renderer に `public_structure_scope_boundary`、`no_concrete_bug_anxiety`、`multi_site_non_stripe_scope` を追加し、`fix_vs_structure_first` の検出語を `整理が先` 系へ拡張した。delivered renderer には次回の全体構成見直し相談で、今回見た範囲・全体見直しの別扱い・金額は範囲確認後に相談、を短く返す分岐を追加した
- きっかけ: `surface_overexposure` 反映後も、r0 で `この不具合なら15,000円` へ戻り、修正/整理、不具合なし相談、2サイト+非Stripe、delivered 全体見直しの主質問に答えない再発が残った
- 想定効果: public な `bugfix-15000` だけで答えるべき境界ケースを、非公開 `handoff-25000` へ逃がさず、かつ旧テンプレートへ落とさない。安全条件は必要最小限にし、completion gate は buyer の質問に必要な範囲だけ出す
- 確認: STK-081 / STK-085 / STK-079 / GMN-049 targeted unified lint OK。`python3 scripts/check-coconala-reply-role-suites.py --save-report` 全 role OK（既存 projection warning `CMP-002` 1件のみ）。`./scripts/os-check.sh` OK
- 非変更: `surface_overexposure` を hard validator 化しない。B08 closed 怒り気味対応は、r1 再監査後に batch 文面だけ短く圧縮し、renderer 変更は行わない

### 2026-04-27 / CHG-059
- 分類: `reply-only`
- レイヤ: closed renderer / closed validator / Gold Reply 23
- 変更: closed 後の無料対応不満型で、`無料で対応できるかはまだ断定できません` だけだと無料実作業の可能性に読めるため、Gold Reply 23 と closed renderer を `このメッセージ上でできるのは確認材料を見るところまで` を先に出す形へ修正した。closed validator も、無料対応・15,000円不満・納得できない系の raw では、メッセージ上の確認範囲と実作業境界の両方を検査するようにした
- きっかけ: ユーザー監査で、closed 後に実作業が必要な場合はココナラ上の新しい取引導線と費用相談が必要であり、無料対応可否だけを保留すると「作業まで無料であり得る」と誤読されると分かった
- 想定効果: 正本の `closed 後は確認材料の受領と実作業を分ける` が、gold / renderer / validator へ届き切らず再発する事故を減らす。通常料金への即誘導と無料実作業約束の両方を避ける
- 確認: `CMW-005` / `TMG-004` targeted render + closed lint OK。`python3 scripts/check-coconala-reply-role-suites.py --save-report` 全 role OK（既存 projection warning `CMP-002` 1件のみ）。`./scripts/os-check.sh` OK
- 非変更: `transaction_model_gap` は writer rule 化しない。deterministic に拾える closed 無料対応不満型の実作業境界だけを validator へ戻す

### 2026-04-27 / CHG-060
- 分類: `reply-only`
- レイヤ: bugfix skill reference / closed renderer fallback
- 変更: `coconala-reply-bugfix-ja` の style-rules に残っていた closed 後の古い導線表現を、`platform-contract.yaml` の現在モデルへ合わせた。closed 後の再発・追加対応は、機械的に `新規のご相談として` や `料金はかかります` へ寄せず、まずメッセージ上で確認材料を見る範囲と、コード修正・差し替えファイル作成・具体的な修正指示など実作業になる範囲を分ける。あわせて `generic_closed` fallback も、`今回のご相談がどの種類か` / `前回の続きとして扱えるか` の内部語をやめ、メッセージ上の確認と実作業前の相談に寄せた
- きっかけ: 正本接続棚卸しで、platform-contract / Gold / validator は更新済みでも、skill reference と generic fallback に古い closed 認識が残ると、未知ケースで transaction_model_gap が再発し得ると分かった
- 想定効果: `#R` や未分類 closed ケースで、通常料金への即誘導・無料実作業期待・内部分類語のいずれにも寄らず、確認材料と実作業の境界を保ちやすくする
- 非変更: closed 後の全ケースを hard rule 化しない。具体質問に対する直答は引き続き scenario / validator / gold で扱い、generic fallback は最後の安全網としてだけ使う

### 2026-04-27 / CHG-061
- 分類: `reply-only`
- レイヤ: external research synthesis / reviewer prompt / taxonomy / scorecard
- 変更: ChatGPT Deep Research と Gemini Deep Research の結果を、正本へ直接流し込まず、`transaction_model_gap` の下位観点として最小反映した。failure taxonomy に `transaction_clarity`、`phase_route_clarity`、`work_payment_boundary_clarity`、`buyer_not_lost`、`responsibility_over_admission_risk`、`free_support_expectation_risk`、`request_minimality` を追加し、Codex / Claude 監査プロンプトにも「該当時だけ見る補助観点」として接続した。scorecard には点数を増やさない補助監査軸を追加した
- きっかけ: 外部調査で、実務返信AIは文体だけでなく、状態管理・workflow guardrails・policy/action guardrails・QA loop として成立させる必要があると確認された。`transaction_model_gap` は既存概念と近いが、ココナラの支払い状態・作業開始条件・成果物返却導線までまとめて見る内部レンズとして有効だと整理された
- 想定効果: normal prequote を重くせず、closed / delivered / quote_sent など高リスク phase でだけ、buyer が迷子になる取引構造の欠落を監査で拾いやすくする
- 非変更: writer rule / renderer / validator の新規大規模追加は行わない。下位観点は全件採点軸ではなく、`transaction_model_gap` が疑われる時だけ使う reviewer lens とする

### 2026-04-27 / CHG-062
- 分類: `reply-only`
- レイヤ: delivered renderer / phase contract
- 変更: active fixture `PCE-005` の delivered 差し戻し/承諾不安が `generic_delivered` へ落ちていたため、`delivered_can_reject` の最小分岐を追加した。正式納品後・承諾前に、未確認箇所があるなら無理に承諾しなくてよいこと、承諾前はトークルーム内で伝えること、承諾後に同じ問題が出た場合はメッセージ上で前回修正とのつながりを確認することを返す
- きっかけ: external research 反映後の targeted lint で、role suite は通る一方、phase-contract edge fixture の `PCE-005` が `generic_delivered fallback survived` で落ちた。これは `phase_route_clarity` の接続不足として扱うべき deterministic gap だった
- 想定効果: delivered の承諾/差し戻し質問で、buyer が「承諾するしかないのか」「承諾後はどうなるのか」で迷子になる事故を減らす
- 確認: `python3 scripts/check-rendered-delivered-followup.py --fixture ops/tests/quality-cases/active/phase-contract-edge-bugfix09.yaml` OK。full role suite OK

### 2026-04-27 / CHG-063
- 分類: `reply-only`
- レイヤ: #RE batch-22 / gold候補メモ
- 変更: batch-22 `normal-phase-tmg-regression` の r1 で、普通寄り prequote と phase sentry の混在 batch が Codex / Claude の両監査で採用可になった。B01 は `Stripe支払い完了 -> プラン未反映` と `ログの場所が分からない` を拾う prequote 型、B03 は `本番Vercel / Stripe Checkout / POST 405` を一息で拾う技術症状型、B07 は closed 後の `購入なしで具体的な修正指示まではできない` 境界型として gold 候補に記録する
- きっかけ: r0 では B01/B03 が `内容ありがとうございます -> この不具合なら15,000円 -> どこで止まっているか確認` の旧テンプレートへ戻り、B07 も購入なしコード修正助言への直答が弱かった。r1 で buyer 情報拾いと closed 実作業境界を最小修正し、両監査で必須修正なしになった
- 想定効果: `transaction_model_gap` 下位観点を接続した後でも、普通の見積り相談が重くなりすぎず、buyer の具体症状を拾った自然な prequote と phase 境界の両立を確認できた
- 非変更: 今回は validator / renderer / reviewer_prompt へ新規反映しない。B01/B03 の旧テンプレート回帰が次 batch でも再発する場合だけ、prequote の `内容ありがとうございます` / generic stop-check を validator 候補として棚卸しする

### 2026-04-27 / CHG-064
- 分類: `reply-only`
- レイヤ: #RE batch-23 / gold候補メモ
- 変更: batch-23 `normal-prequote-depth` の r2 で、普通寄り prequote 4件と phase sentry 3件が採用可になった。B01 は `raw body / request.text() / stripe-signature` を拾う Webhook署名検証型、B02 は `customer.subscription.updated / DB未更新 / ダウングレード正常` を拾う情報量多め相談型、B03 は顧客対応と不具合修正を分ける型、B04 は成功率/100%保証質問への completion gate 型、B06 は purchased 進捗 + diff希望回答型、B07 は closed 後の一般的な確認手順質問型として gold 候補に記録する
- きっかけ: r0 では B01/B02/B04 が旧テンプレートへ戻り、B03 は顧客対応質問に答えず、B06 は同義反復と diff 希望落ちが出た。r1/r2 で buyer 情報拾い、業務対応と技術修正の分離、進捗現在地、closed 後の情報提供範囲を最小修正した
- 想定効果: 普通の見積り相談で具体症状を拾う力と、`transaction_model_gap` の補助観点を本文に出しすぎないバランスを確認できた。特に B03 は buyer の「顧客に何と伝えるか」と「修正をどう頼むか」を分ける gold 候補として重要
- 非変更: 今回も validator / renderer へ即時反映しない。ただし `内容ありがとうございます -> この不具合なら15,000円 -> どこで止まっているか確認` の旧テンプレート回帰は batch-21〜23 で連続しているため、次の棚卸しで prequote renderer / validator の最優先候補にする

### 2026-04-27 / CHG-065
- 分類: `reply-only`
- レイヤ: prequote renderer / validator / Gold Reply 26
- 変更: batch-21〜23 で連続再発した `内容ありがとうございます -> この不具合なら15,000円 -> どこで止まっているか確認` の旧 prequote テンプレート回帰を棚卸しした。renderer に Webhook署名検証/raw body、subscription更新DB未反映、顧客対応+不具合修正、成功率/100%保証の4つだけ最小分岐を追加し、validator には具体症状がある prequote で旧三点セットが同時に出た場合の warn を追加した。Gold Reply 26 も追加し、buyer の具体情報を1〜2個拾ってから価格・次アクションへ進む型を参照できるようにした
- きっかけ: r1/r2 の手修正では毎回採用可まで持っていける一方、r0 では同じ旧テンプレートへ戻るため、case_fix ではなく renderer / validator に戻す再発条件を満たした
- 想定効果: 普通の prequote を契約説明のように重くせず、具体症状が書かれている相談では `読んでいない感` と `bot感` を減らす。成功率質問や顧客対応混在相談を通常の不具合受付テンプレートへ流さない
- 確認: STK-014 / STK-024 / STK-032 / STK-041 の targeted render と prequote lint OK。`python3 scripts/check-coconala-reply-role-suites.py --save-report` OK（既存 projection warning `CMP-002` 1件のみ）。`./scripts/os-check.sh` OK

### 2026-04-27 / CHG-066
- 分類: `reply-only`
- レイヤ: prequote renderer / validator / purchased renderer / Gold Reply 26 / batch-24
- 変更: batch-24 r0 で、CHG-065 の4分岐外にある普通 prequote 5件が旧テンプレート三点セットへ戻ったため、近縁ケースの最小分岐を追加した。対象は、プラン変更後の未反映、本番VercelだけのCheckout POST 405、preview環境Webhookエラー、Vercel上のWebhook署名検証400、フロント問題とStripe連携不具合の混在相談。validator の concrete prequote context も同じ範囲へ拡張した。あわせて purchased 進捗確認 + diff希望で `原因の切り分け中` の同義反復が出る問題を、現在地 + diff共有可否 + 次回報告内容へ分ける最小分岐にした
- きっかけ: Codex / Claude 監査で、B01〜B05 がすべて `内容ありがとうございます -> この不具合なら15,000円 -> どこで止まっているか確認` に戻り、B06 も diff 希望へ答えず同義反復になった。これは case_fix ではなく、CHG-065 の接続範囲不足として扱うべき再発だった
- 想定効果: 専用4型だけでなく、近い普通 prequote でも buyer の具体症状を拾ってから価格・次アクションへ進める。購入後の進捗催促では、空の `確認中です` ではなく、現在地と次に返す内容を buyer に見える形にする
- 非変更: prequote 全般を大きく再設計しない。今回確認された具体症状パターンと、旧三点セットの deterministic warn に限って最小反映する

### 2026-04-27 / CHG-067
- 分類: `reply-only`
- レイヤ: #RE batch-24 / Gold Reply 27
- 変更: batch-24 `prequote-specificity-after-shelf` の r2 で、Codex 監査が採用可となったため完了扱いにした。B05 は r1 で `Next.jsならフロント側全般が対象` に見える drift があったため、`Stripe決済後の表示やNext.js/API連携に関わる不具合であれば確認できます` へ締めた。B07 は closed 後の一般的な確認方法質問として、見積り導線へ寄せすぎず一般回答を先に返す gold として `27_closed-general-check-method.ja.md` に記録した
- きっかけ: Claude は r1 で採用可だったが、Codex が B05 の scope 広げすぎと B07 の gold 候補性を指摘した。B05 は batch 内で最小修正し、B07 は単発文面修正ではなく参照 anchor として残す価値があると判断した
- 想定効果: フロント問題混在相談で bugfix-15000 の範囲を広げすぎず、Stripe/API連携との関係へ閉じられる。closed 後の一般質問では、`対応できません` や `新規見積りです` へ急がず、答えられる一般範囲を先に返せる
- 確認: batch-24 r2 を Codex 監査に出し、必須修正なし・採用可を確認。B06/B07 は軽微指摘のみで、batch 停止不要と判断
- 非変更: B06 の具体対象名追加、B07 の追加具体化は必須ではないため renderer / validator へ戻さない。B07 は gold 参照に留める

### 2026-04-27 / CHG-068
- 分類: `reply-only`
- レイヤ: prequote renderer / prequote validator / purchased renderer / closed renderer / batch-32
- 変更: Pro 棚卸し後の r0 未安定型 regression として、非Stripe scope、緊急復旧、仕様/不具合境界、返金/キャンセル、新機能追加、保証期間、closed後別プロジェクト割引要求を検証した。r0 では B01-B06 が旧テンプレ・情報不足テンプレ・service spec nonanswer へ戻ったため、prequote renderer に `non_stripe_webhook_scope`、`emergency_recovery_time`、`spec_vs_bug_boundary`、`refund_cancel_prequote`、`feature_addon_scope` を追加し、purchased renderer に `warranty_period_question` を追加した。validator には旧三点セット、非Stripe scope、緊急復旧、phase語彙、同義反復3回の guard を接続し、closed 割引要求では別プロジェクト・固定価格・コピペ不可を明示するようにした。全体スイートで追加露出した eval / holdout の具体技術症状型（引き継ぎコードの決済不具合、解約メール二重送信、coupon `resource_missing`、quantity変更時例外）も専用分岐へ戻した
- きっかけ: Codex / Claude 監査で、B01-B06 がすべて必須修正。特に `内容ありがとうございます -> この不具合なら15,000円 -> どこで止まっているか確認`、返金/キャンセル誤読、新機能追加の scope 吸収、保証期間未回答は、過去 batch で複数回再発しており case_fix では止まらないと判断した
- 想定効果: service structure question を通常の不具合受付へ流さず、buyer が聞いている「対象か」「いつ直るか」「仕様か」「返金/キャンセルはどうなるか」「同じ料金内か」「保証はあるか」に先に答える。`transaction_model_gap` を本文へ出しすぎず、必要な入口分岐として効かせる
- 確認: batch-32 7件の targeted render + lane lint OK。追加で eval / holdout の失敗ケース 9件を targeted render + lane lint OK。`python3 scripts/check-coconala-reply-role-suites.py --save-report` は seed / renderer_seed / edge / eval / holdout すべて OK。`python3 -m py_compile` OK。`git diff --check` OK
- 非変更: Pro棚卸しの全提案を一括投入しない。今回 deterministic に再発した r0 未安定型だけを renderer / validator へ最小反映し、怒り気味 buyer の温度や短文化は引き続き reviewer / gold 側で観察する

### 2026-04-28 / CHG-069
- 分類: `reply-only`
- レイヤ: #RE batch-33 / Gold Reply 34 / learning-log
- 変更: batch-33 `post-chg068-near-miss` の r1 が Codex / Claude 監査で採用可になったため、CHG-068 後の近縁ケースを棚卸しした。r0 では非Stripe scope と緊急復旧時間が初めて通過し、秘密情報対応と closed 疲弊+無料期待も安定した。一方、仕様/不具合+返金、複数症状+料金、purchased 進捗+別件+Slack では明示質問の取り落としが残ったため、Gold Reply 34 に複合質問の回収型として保存した。learning-log にも、複合質問では料金・返金・外部連絡・秘密情報・closed 後導線を落とさないことを記録した
- きっかけ: batch-33 r0 は batch-32 より改善したが、B03/B04/B06 で「技術症状だけ拾い、返金・2件料金・Slackなどの取引上危ない問いを落とす」再発が出た。r1 では全件通過し、Gold 化する価値があると判断した
- 想定効果: `transaction_model_gap` をさらに細かく、複数質問の回収順序として効かせる。特に purchased 複数話題で `進捗だけ返す`、複数症状で `2件目を無視する`、秘密情報で `接続URLを送らせる` 事故を減らす
- 非変更: 新規 renderer / validator 反映は保留。r0 で改善が見え始めているため、即 rule 追加ではなく Gold 34 と learning-log で次 batch の再発を見る

### 2026-04-28 / CHG-070
- 分類: `reply-only`
- レイヤ: Pro analysis / failure taxonomy / scorecard / writer brief / Gold Reply 34
- 変更: ChatGPT Pro の `buyer_state_ack_gap` 分析を受け、QA-07 温度感ズレの下位レンズとして最小反映した。Gold 34 の closed 疲弊+無料期待ケースは、`また同じような症状が出ているとのこと、確認しました` から、`同じような症状がまた出ていて、前回分との関係や費用面も気になる状況かと思います` へ差し替えた。failure taxonomy / scorecard notes / writer brief に、怒り・疲弊・不安・焦り・不信・困惑・遠慮・無料/返金不満などの状態シグナルを、症状や料金だけで受け流していないかを見る補助観点を追加した
- きっかけ: closed 後の再発+無料期待ケースで、transaction / phase / work boundary は正しいのに、冒頭が症状だけを `確認しました` で受けており、buyer の `もう嫌` `また払うのは納得できない` という状態シグナルが落ちていた
- 想定効果: 怒り気味・疲弊気味 buyer への返信で、謝罪や無料対応約束に寄らず、状態だけを1文受けてから主質問・取引境界・次アクションへ戻せるようにする
- 非変更: validator / renderer / hard rule には入れない。`buyer_state_ack_gap` は deterministic ではないため、当面は reviewer_prompt + gold + scorecard notes に留める。再発しても hard fail ではなく warn 候補として扱う

### 2026-04-28 / CHG-071
- 分類: `reply-only`
- レイヤ: writer brief / Gold Reply 34 / learning-log / batch-34
- 変更: `buyer_state_ack_gap` のうち、他者修正失敗や再発後の不信を受ける語彙を補強した。`次に頼む先を決めるのも不安` は抽象化されすぎて bot 的に見えるため、`今回も本当に直るのか不安に感じる状況かと思います` のように、buyer の判断不安そのものへ寄せる方針を writer brief / Gold 34 / learning-log に追加し、batch-34 B02 も差し替えた
- きっかけ: batch-34 B02 の「次に頼む先」という表現が不自然で、共感を無理に作ったように見えた。外部調査でも、クレーム/不安対応では抽象的な感情推測より、相手の具体状況を短く受ける方が自然だと確認した
- 想定効果: 不信・再発・他者修正失敗のケースで、前任批判や過剰保証に寄らず、自然な状態受けを1文で置けるようにする
- 非変更: validator / renderer / hard rule には入れない。固定文として自動挿入せず、gold / writer phrase bank の参照 anchor に留める

### 2026-04-28 / CHG-072
- 分類: `reply-only`
- レイヤ: writer brief / learning-log / batch-35
- 変更: `buyer_state_ack_gap` の状態受け後に、価格・scope・phase 導線へ急に飛ぶと貼り合わせ感が出るため、短い橋を置く方針を writer brief と learning-log に追加した。batch-35 B02 は `その点も含めて、ご購入後は現在のコードとログを改めて確認する前提で、15,000円で対応できます` へ修正した。B07 は文中の単独 `はい、このメッセージで症状を送って大丈夫です` を削り、`まずはこのメッセージで症状を送ってください` へ統合した
- きっかけ: user 監査で、状態受けと `15,000円で対応できます` がパーツを貼ったように見えること、また文脈上すでに方向を出した後の `はい` が日本語として流れを切ることが指摘された
- 想定効果: 状態受けを入れても bot 的な共感文にならず、主質問・価格・次アクションへ自然につながる。Yes/No の直答も、文章の流れを切らずに次アクションへ統合できる
- 非変更: validator / renderer / hard rule には入れない。固定文を自動挿入するのではなく、writer が状態受けと結論の接続を判断するための自然化観点に留める

### 2026-04-28 / CHG-073
- 分類: `reply-only`
- レイヤ: Pro analysis / failure taxonomy / scorecard / writer brief / reviewer prompts / Gold Reply 35 / learning-log
- 変更: ChatGPT Pro の `response_weight_mismatch` 分析を受け、buyer の文量・温度・質問数に対して返信が重すぎるかを見る補助レンズを追加した。failure taxonomy と scorecard notes には、`surface_overexposure` の近縁 warning として記録した。writer brief には、短文化で境界を削らず、主質問に必要な safety atom だけを外向けに残す原則を1行だけ追加した。Claude / Codex xhigh 監査プロンプトにも、hard fail ではなく reviewer warning として見る注意を追加した。Gold Reply 35 には、短くても安全な例、重くても必要な例、状態受けから価格へ飛ばさない例、文中の `はい` を次アクションへ統合する例を追加した
- きっかけ: batch-35 の文面で、安全境界は守れているが buyer の文量に対して返信が少し重いケース、状態受けと価格が貼り合わせに見えるケース、文中の `はい` が流れを切るケースが見えた。Pro は `response_weight_mismatch` を validator hard reject ではなく reviewer warning / gold 対比で扱うべきと判断した
- 想定効果: 安全性を落とさず、説明過多・bot感・パーツ貼り付け感を減らす。`短くする` ではなく、buyer に必要な直答・境界・次アクションだけを外向けに残す判断をしやすくする
- 非変更: validator / renderer / hard rule には入れない。文字数・文数・`はい` の有無で落とさない。closed / 返金 / 保証 / 秘密情報などの必要な安全境界を削る用途には使わない

### 2026-04-28 / CHG-074
- 分類: `reply-only`
- レイヤ: Pro analysis / failure taxonomy / scorecard / writer brief / reviewer prompts / batch-36
- 変更: ChatGPT Pro の監査レンズ布陣レビューを受け、`transaction_model_gap` の下位観点を常時7系統で見る運用から、まず `route_clarity` / `work_payment_boundary` / `buyer_not_lost` の3系統で見る運用へ圧縮した。`responsibility_over_admission_risk`、`free_support_expectation_risk`、`request_minimality` は closed / refund / anger / secrets など高リスク時だけ使う補助観点にした。`surface_overexposure` は独立 hard label ではなく `response_weight_mismatch` の原因 subtype として扱い、`response_weight_mismatch`、`buyer_state_ack_gap`、`unnamed_discomfort` は soft lens と明記した。writer brief には、未受領の材料に依存する見立て・時刻・作業予定を `届き次第` `いただけた範囲で` `確認できる範囲で` のように条件付きで書く方針を追加した。batch-36 B06 は `本日07:10までに` の時刻約束を、`いただけた範囲で、見立てを短くお返しします` へ修正した
- きっかけ: Pro は、レンズが増えたことで監査が二重採点・過剰補正に寄る危険を指摘した。特に `surface_overexposure` と `response_weight_mismatch` の重複、`unnamed_discomfort` の必須修正化、材料未受領前の時刻コミットは、現行品質を崩すノイズになり得ると判断した
- 想定効果: 監査レンズを増やしすぎず、hard fail は phase drift / 非公開サービス漏れ / 返金・無料・保証断定 / 外部共有 / 直接 push / 本番デプロイ / closed 後旧トークルーム継続など deterministic な事故に絞る。自然さ・重さ・状態受けの違和感は soft lens として扱い、Codex の判断を遮らず、必要な時だけ gold / reviewer_prompt へ戻す
- 非変更: `response_weight_mismatch`、`buyer_state_ack_gap`、`unnamed_discomfort` は validator 化しない。短文化のために安全境界を削らない。`transaction_model_gap` 自体は維持し、取引構造が崩れた時の中核レンズとして使い続ける

### 2026-04-28 / CHG-075
- 分類: `reply-only`
- レイヤ: #RE batch-37 / learning-log / connection audit
- 変更: batch-37 `lens-layout-near-miss` の r0/r1 を棚卸しした。r0 では旧三点セット、context bleed、purchased 追加症状テンプレ誤発火、新機能追加の scope 未回答、delivered 汎用 fallback、closed の浮いた `はい` が出た。一方、r1 では既存 gold に戻すだけで全7件が採用可になったため、新レンズ不足ではなく `gold / renderer / validator の接続不足` として learning-log に記録した
- きっかけ: CHG-074 のレンズ布陣整理後、batch-36 の全件 r0 通過から一転して batch-37 r0 が大きく崩れた。監査では、レンズ整理そのものよりも、renderer / writer-brief / gold の参照接続が外れて旧テンプレに戻った可能性が高いと判断された
- 想定効果: 次の構造補修で、旧三点セット hard reject、purchased の `進捗 / 追加症状 / 新機能追加` 分岐、delivered 承諾 yes/no 分岐、context bleed guard を優先できる。soft lens を増やさず、r0 初手分岐の安定化へ焦点を戻せる
- 非変更: 新しい監査レンズや hard rule は追加しない。今回の学びは「r1 で通る gold を r0 にどう接続するか」であり、`response_weight_mismatch` や `buyer_state_ack_gap` の validator 化には進めない

### 2026-04-28 / CHG-076
- 分類: `reply-only`
- レイヤ: #BR shortcut / boundary-routing shadow rehearsal
- 変更: `#BR` を `bugfix-15000 / handoff-25000` の境界ルーティング専用 shadow rehearsal として定義した。`docs/next-codex-prompt.txt` と `docs/reply-quality/README.ja.md` に保存先・公開状態・監査観点を追加し、正本メモ `boundary-routing-shadow-rehearsal.ja.md` を作成した。あわせて `サービスページ/rehearsal/boundary-routing-返信学習/返信監査_batch-01.md`、`監査プロンプト_codex-xhigh.md`、`監査プロンプト_claude.md`、`ops/tests/quality-cases/active/boundary-routing-shadow-br01.yaml` を準備した
- きっかけ: `bugfix-15000` で十分に返信OSが育ってきたため、将来 `handoff-25000` を公開した時の `修正 / 整理 / 混在 / 価格分離 / scope 外` のルーティングを先に鍛える必要が出た
- 想定効果: 通常の `#RE` を壊さず、dual-service 状態の boundary case を別レーンで検査できる。`handoff-25000 public:false` の間は live 返信に名称・価格・購入導線を漏らさず、future-dual simulation としてだけ route 判定を鍛えられる
- 確認: `#BR` 定義・保存先・fixture を追加。`service-registry.yaml` の公開状態は未変更
- 非変更: `handoff-25000` を public にしない。通常の `#R` / `#RE bugfix` へ handoff の名称・25,000円・購入導線を混ぜない。今回の準備では renderer / validator は変更しない

### 2026-04-28 / CHG-077
- 分類: `reply-only`
- レイヤ: #BR batch-01 r1 / boundary route gold
- 変更: `#BR` 初回 r0 の Codex 監査を受け、`返信監査_batch-01.md` の B02〜B07 を boundary route 正解形へ手反映した。B02 は `handoff-first`、B03 は `bugfix-first`、B04 は `bugfix-first + scope boundary`、B05 は `handoff-first + flow boundary`、B06 は `handoff-first + no repair promise`、B07 は `neither / scope out` として整理した
- きっかけ: r0 では handoff-first / neither が `default_bugfix` に吸収され、`壊れていない整理相談`、`主要1フロー整理`、`整理中のバグ修正約束`、`新機能追加` がすべて bugfix 文脈へ流れた。B03/B04 では相手文にない `外注先と連絡が取れず` の context bleed も出た
- 想定効果: #BR の最初の gold として、`直したいなら bugfix-first`、`把握したいなら handoff-first`、`混在なら主目的で順番を決める`、`新機能追加は neither` を明確にできる。将来 dual-service 化した時の価格・成果物・修正約束の混線を減らす
- 確認: `返信監査_batch-01.md` を r1 手反映済みに更新し、`git diff --check` OK
- 非変更: `service-registry.yaml` の公開状態は変更しない。今回の r1 は batch 内 gold 化であり、通常 live 返信や #RE renderer には戻さない

### 2026-04-28 / CHG-078
- 分類: `reply-only`
- レイヤ: #BR batch-01 r2 / boundary route gold
- 変更: #BR batch-01 r1 の Codex再監査で必須修正なし・採用可となったため、軽微2点だけ反映した。B02 は handoff-first の購入前相談でコード一式や関係ファイル送付を強く求めず、対象フロー確認に留める文へ変更した。B06 は `整理はできる / 修正は別` と切った後に、整理として進める次アクションを1文追加した
- きっかけ: 監査で、handoff-first の購入前にファイル要求が強すぎること、handoff で修正を別扱いにした後の次アクションが薄いことが軽微指摘された
- 想定効果: 将来 dual-service 化した際、整理相談で購入前からコード一式を求めすぎず、buyer がまず対象フローを決められる。handoff で修正を約束しない場合も、buyer が次に何を送ればよいか迷子にならない
- 確認: `返信監査_batch-01.md` を r2 手反映済みに更新し、`git diff --check` OK
- 非変更: 新規 rule 化はしない。今回の2点は #BR shadow gold として保持し、通常 live / #RE へは戻さない

### 2026-04-28 / CHG-079
- 分類: `reply-only`
- レイヤ: #BR batch-01 r3 / boundary route naturalization
- 変更: user監査を受け、B02 の handoff-first 返信を自然化した。`今すぐ壊れている不具合の修正というより...` は route 判定を外向けに発表しているように見えるため、先に `できます。` と直答し、その後で `今回の目的だと、壊れている箇所を直すよりも、次の外注先が追えるように...整理する対応が合っています` へ接続する形に変更した
- きっかけ: B02 の r2 返信は boundary としては正しいが、文頭で `不具合修正というより` と分類しており、用意したパーツを貼ったように見えるという違和感があった
- 想定効果: #BR の handoff-first で、内部 route 判定をそのまま外向けに出さず、buyer の依頼への可否回答から自然に整理ルートへつなげられる
- 確認: `返信監査_batch-01.md` を r3 手反映済みに更新
- 非変更: 通常 live への handoff 解禁はしない。今回の変更は #BR shadow batch 内の自然化に留める

### 2026-04-28 / CHG-080
- 分類: `reply-only`
- レイヤ: #BR batch-01 r4 / boundary route naturalization
- 変更: B02 の冒頭で単独 `できます。` が FAQ 的に浮いていたため削除した。`この内容であれば、次の外注先が追えるように「決済完了から注文作成まで」の流れを整理する対応が合っています` へ統合し、対象フロー確認文も短くした
- きっかけ: user監査で、単独の `できます。` は日本語圏の業務文として bot 感が強いと指摘された。外部確認でも、ビジネス文では `対応可能です` や具体的な対応内容を伴う表現が一般的で、単独の可否返答は文脈内で浮きやすいと判断した
- 想定効果: handoff-first で可否に答えつつ、`はい/できます` のFAQパーツ感を減らし、相談内容から自然に整理ルートへ接続できる
- 確認: `返信監査_batch-01.md` を r4 手反映済みに更新
- 非変更: `できます` という語自体を禁止しない。単独で浮く場合だけ避ける。通常 live への handoff 解禁はしない

### 2026-04-28 / CHG-081
- 分類: `reply-only`
- レイヤ: #BR audit prompt
- 変更: #BR 監査プロンプト内の主対象を固定の `返信監査_batch-02.md` ではなく、ユーザーが添付・指定した `返信監査_batch-*.md` として扱う表現へ変更した。プロンプト本文や過去ログの batch 名と実ファイル名が食い違う場合は、実ファイルを優先し、対象名のズレを監査結果で指摘する運用にした
- きっかけ: batch-02 作成時に共有監査プロンプトを batch-02 向けへ書き換えたため、batch-01 r4 を再監査する時に対象名がズレた
- 想定効果: #BR batch を複数並行で扱っても、監査対象ファイルの取り違えを減らす。batch ごとに監査プロンプトを手で戻す必要をなくし、実ファイル優先の運用にできる
- 非変更: #BR の監査観点・service facts・future-dual simulation の前提は変更しない

### 2026-04-28 / CHG-082
- 分類: `reply-only`
- レイヤ: #BR batch file operation
- 変更: #BR の監査対象ファイルを `返信監査_batch-current.md` に固定した。メイン階層には最新 batch だけを残し、既存の `返信監査_batch-01.md` と `返信監査_batch-02.md` は `archive/` へ退避した。監査プロンプトも `返信監査_batch-current.md` を主対象に戻した
- きっかけ: 過去履歴を使って Codex 監査へ出す運用では、batch ごとにファイル名が変わると対象名の修正が手間になり、監査対象の取り違えが起きやすい
- 想定効果: #RE と同じく「毎回見るファイルは1つ」に固定できる。外部監査へ渡すファイル名が安定し、batch の増殖やプロンプト名ズレを防げる
- 非変更: `archive/` は履歴退避用であり、通常の監査対象にはしない。#BR の future-dual simulation 前提や公開状態ルールは変更しない

### 2026-04-28 / CHG-083
- 分類: `reply-only`
- レイヤ: #BR batch-current r1 / boundary route gold
- 変更: `返信監査_batch-current.md` の r0 監査を受け、B01〜B07 を boundary route 正解形へ手反映した。B01/B03/B05 は bugfix-first、B02/B04/B06 は handoff-first、B07 は neither として整理した。B05 の `外注先と連絡が取れず` の context bleed を削除し、B06 では 25,000円整理がリポジトリ全体・Stripe全処理の網羅ではなく主要1フローであることを明記した
- きっかけ: r0 では handoff-first と neither が default_bugfix に吸収され、壊れていない整理相談や新機能追加が `この不具合なら15,000円` へ流れた。B05 では相手文にない事情の context bleed も再発した
- 想定効果: #BR の dual-service 境界で、修正・整理・新機能追加を buyer の主目的に沿って分けられる。軽い変更箇所説明と正式な引き継ぎメモの境界も明確になる
- 非変更: 通常 live への handoff 解禁はしない。今回の 25,000円案内は #BR future-dual simulation 内の shadow gold として扱う

### 2026-04-28 / CHG-084
- 分類: `reply-only`
- レイヤ: #BR batch-current r2 / boundary route gold
- 変更: #BR batch-current r1 の Codex再監査で必須修正なし・採用可となったため、軽微2点だけ反映した。B04 は handoff-first の次アクションを `対象フローを「決済からユーザー権限付与まで」に絞って進めます` へ明確化した。B07 は neither 判定で `この2つの出品では対応範囲外です` を追加した
- きっかけ: 監査で、B04 は回答として正しいが次アクションが少し弱いこと、B07 は新機能追加として scope out できているが buyer が迷わないよう対応範囲外の明示があるとよいことが軽微指摘された
- 想定効果: handoff-first では可否回答後に対象フローの確定が見え、neither では bugfix / handoff のどちらにも含まれないことが明確になる
- 非変更: 新規 rule 化はしない。通常 live への handoff 解禁はしない

### 2026-04-28 / CHG-085
- 分類: `reply-only`
- レイヤ: #BR batch-current r3 / boundary route naturalization
- 変更: B02 の `今は不具合修正ではなく...整理する内容が合っています` を、`決済自体は動いていて、次の担当者へ渡す前にStripeまわりの危険箇所と関連ファイルを整理したい、という内容ですね` へ変更した
- きっかけ: user監査で、buyer はすでに整理依頼を決め打ちしているため、`合っています` と route 判定を返すのは、迷っていない相手に診断を発表しているようで不自然だと指摘された
- 想定効果: #BR の handoff-first で、buyer が迷っている場面と、すでに整理依頼をしている場面を分けられる。前者では route 提案、後者では依頼内容の自然な受けから価格・範囲・次アクションへ進める
- 非変更: `対応できます` や `対応可能です` を禁止語にはしない。今回の改善は敬語表現ではなく、buyer の依頼状態に応じて route 判定語を外向けに出すかどうかの自然化

### 2026-04-28 / CHG-086
- 分類: `reply-only`
- レイヤ: #BR route state split / boundary-route subrule
- 変更: `boundary-route` の下位判定として、`route_match_decided` / `route_mismatch_decided` / `route_uncertain` を追加した。正しい route を buyer がすでに選んでいる時は診断文を出さず依頼内容を受ける。buyer の選んだ route が主目的とズレている時は受け流さず正しい入口へ誘導する。buyer が迷っている時は主目的から順番を提案する
- きっかけ: user監査で、B02 のように buyer が整理依頼を決め打ちしている場面では `合っています` が不自然だが、明らかに症状と違う route を選んでいる場面では誘導が必要だと整理された
- 想定効果: #BR で、route 判定を外向けに出しすぎる bot 感を減らしつつ、誤った route 選択をそのまま受ける事故も防ぐ
- 非変更: 新しい大きな監査レンズは追加しない。`route_state_mismatch` は #BR の `boundary-route` 下位ラベルとして扱い、通常 live への handoff 解禁や `service-registry.yaml` の公開状態は変更しない

### 2026-04-28 / CHG-087
- 分類: `reply-only`
- レイヤ: #BR batch-current r1 / route state split gold
- 変更: BR-03 r0 の Codex監査を受け、`返信監査_batch-current.md` の B01〜B07 を r1 へ手反映した。B01/B04 は `route_match_decided / handoff-first`、B02 は `route_mismatch_decided / bugfix-first`、B03 は `route_uncertain / bugfix-first`、B05 は `bugfix-first + later handoff`、B06 は `neither / scope out`、B07 は `handoff-first + no repair promise` として整理した
- きっかけ: r0 では、buyer が正しい handoff route をすでに選んでいる B01/B04 と、新機能追加の B06、handoff に修正を吸収しそうな B07 が default bugfix へ吸収された。B02/B03/B05 も順番提示や後続整理への回答が薄かった
- 想定効果: #BR の route state split を実データで gold 化できる。`合っている時は受ける / ズレている時は誘導する / 迷っている時は順番を提案する` を、将来 dual-service 化した時の境界ルーティング資産として保持できる
- 非変更: 通常 live への handoff 解禁はしない。今回の 25,000円案内は #BR future-dual simulation 内の shadow gold として扱う

### 2026-04-28 / CHG-088
- 分類: `reply-only`
- レイヤ: #BR batch-current r2 / handoff one-flow clarity
- 変更: BR-03 r1 の Codex再監査で必須修正なし・採用可となったため、軽微3点だけ反映した。B02 は `入口が近いです` を自然化し、B03 は `15,000円内で` を `15,000円の範囲で` に変更した。B07 は handoff の説明に `対象にする流れを1つに絞って` を追加した
- きっかけ: 監査で、route 境界は通っているが、B02/B03 は語感、B07 は `Stripe連携の流れ` が広く見える点を軽微指摘された
- 想定効果: handoff-25000 の 25,000円整理が、Stripe連携全体やリポジトリ全体の網羅ではなく主要1フローであることを #BR 内でも安定して示せる
- 非変更: 新規 rule 化はしない。通常 live への handoff 解禁はしない

### 2026-04-28 / CHG-089
- 分類: `reply-only`
- レイヤ: #BR batch-current r1 / mixed-service stress gold
- 変更: BR-04 r0 の Codex監査を受け、`返信監査_batch-current.md` を r1 へ手反映した。B01/B03/B04/B05 は handoff-first 系、B02/B07 は bugfix-first 系、B06 は neither として整理した。B04 では 25,000円整理が Stripe連携全体・DB全部の網羅ではないこと、B05 では handoff 中に軽微なバグ修正を吸収しないこと、B07 では修正後の軽い変更箇所説明と正式な引き継ぎ資料を分けることを明示した
- きっかけ: r0 では handoff-first / neither の相談が default bugfix へ吸収され、B07 では相手文にない `外注先と連絡が取れず` の context bleed が出た
- 想定効果: dual-service 化した時に、`壊れていない整理`、`active defect の整理逃げ`、`不具合なしの把握相談`、`全体網羅要求`、`handoff中の修正吸収`、`新機能追加`、`bugfix内の軽い説明` をそれぞれ分けられる
- 非変更: 通常 live への handoff 解禁はしない。今回の 25,000円案内は #BR future-dual simulation 内の shadow gold として扱う

### 2026-04-28 / CHG-090
- 分類: `reply-only`
- レイヤ: #BR batch-current r2 / handoff next-action close
- 変更: BR-04 r1 の Codex再監査で必須修正なし・採用可となったため、B01/B05 の handoff-first 文末導線だけ軽微補強した。B01 は対象フローを `Stripe決済からユーザー権限付与まで` に絞ることと、コード一式は購入後でよいことを追加した。B05 はサブスク変更フローを1つに絞って整理することを最後に追加した
- きっかけ: 監査で、route / price / scope は通っているが、handoff 側の文末導線をもう少し締めると buyer が迷いにくいと指摘された
- 想定効果: handoff-first 返信で、`対象1フロー` / `購入後にコード共有` / `修正は含まない` のいずれかを自然に置き、整理依頼の次アクションを明確にする
- 非変更: 新規 rule 化はしない。通常 live への handoff 解禁はしない

### 2026-04-28 / CHG-091
- 分類: `reply-only`
- レイヤ: #BR batch-current r3 / route-mismatch no-sequential-upsell
- 変更: BR-04 B02 の user監査を受け、`まず購入履歴が作られない不具合修正から` と `整理メモが必要な場合は、修正後に別対応` を弱めた。buyer は整理メモを明確に欲しがっているのではなく、コードが読めないため route を迷っている状態なので、`今回の目的が購入履歴が作られない状態を止めたいことなら、15,000円の不具合修正で対応する内容` とし、整理メモは今回の修正に必須ではないとした
- きっかけ: `まず` が、1サービス目の後に2サービス目へ進む前提・追加購入前提に読めると user 監査で指摘された
- 想定効果: route_mismatch_decided で正しい入口へ誘導する時に、不要な後続サービス感を出さず、buyer の主目的に対して必要な入口だけを示せる
- 非変更: 新規 rule 化はしない。通常 live への handoff 解禁はしない

### 2026-04-28 / CHG-092
- 分類: `reply-only`
- レイヤ: #BR batch-current r1 / boundary route stress br05
- 変更: BR-05 r0 の Codex監査を受け、`返信監査_batch-current.md` を r1 へ手反映した。B01 は active defect のため bugfix-first、B02/B03/B04/B07 は handoff-first 系、B06 は neither、B05 は bugfix-first + light explanation boundary として整理した。B04 では2フローを同じ25,000円内でまとめないこと、B06 では返金ボタン追加を新機能追加として切ること、B07 では handoff 中の小さい修正を吸収しないことを明示した
- きっかけ: r0 では handoff-first / neither が default bugfix へ吸収され、B05 では相手文にない `外注先と連絡が取れず` の context bleed が出た
- 想定効果: #BR で、active defect の整理迷い、明確な handoff 依頼、2フロー整理、新機能追加、bugfix 内の軽い説明、handoff 中の修正吸収をより安定して切り分ける
- 非変更: 通常 live への handoff 解禁はしない。今回の 25,000円案内は #BR future-dual simulation 内の shadow gold として扱う

### 2026-04-28 / CHG-093
- 分類: `reply-only`
- レイヤ: #BR batch-current r2 / handoff close and add-flow clarity
- 変更: BR-05 r1 の Codex再監査で必須修正なし・採用可となったため、B02/B04 の文末導線だけ軽微補強した。B02 は対象フローを `決済完了から注文作成まで` に絞って進めることを追加した。B04 は2フロー両方が必要な場合、まず1フローを整理したうえで追加分として相談することを追加した
- きっかけ: route / price / scope は通っているが、handoff 側の文末導線を締めると buyer が次に選ぶ対象フローを迷いにくいと指摘された
- 想定効果: #BR の handoff-first で、`主要1フロー` と `追加フロー` の着地を短く明示し、25,000円整理が複数フロー一括に見える事故を減らす
- 非変更: 新規 rule 化はしない。通常 live への handoff 解禁はしない

### 2026-04-28 / CHG-094
- 分類: `reply-only`
- レイヤ: #BR batch-current r1 / explicit bugfix+handoff separation
- 変更: BR-06 r0 の Codex監査を受け、`返信監査_batch-current.md` を r1 へ手反映した。B01 は bugfix-first + optional handoff、B02 は handoff-first then possible bugfix、B03 はセット割圧力への price / deliverable separation、B04 は3フロー整理 + 小さい不具合の scope split、B05 は bugfix 内の軽い説明、B06 は新機能追加 scope out + 既存不具合 bugfix、B07 は正式仕様書ではなく主要1フロー引き継ぎメモとして整理した
- きっかけ: r0 では bugfix と handoff の両方を明示された相談が片方へ潰れ、B02/B04/B07 の handoff-first が default bugfix に吸収された。B03 では相手文にない `外注先と連絡が取れず` の context bleed が出た。B06 では請求書CSV出力の新機能追加を neither に落とせなかった
- 想定効果: dual-service 化した時に、buyer が両方を明示しても `順番` / `価格` / `成果物` を分けて案内できる。15,000円修正と25,000円整理を一括料金やセット割として約束せず、handoff を複数フロー・正式仕様書・修正作業へ広げない
- 非変更: 新規 rule 化はしない。通常 live への handoff 解禁はしない。今回の 25,000円案内は #BR future-dual simulation 内の shadow gold として扱う

### 2026-04-28 / CHG-095
- 分類: `reply-only`
- レイヤ: #BR batch-current r1/r2 / near-boundary route gold
- 変更: BR-07 r0 の Codex監査を受け、`返信監査_batch-current.md` を r1 へ手反映し、再監査後に B05 文末だけ軽微修正した。B01 は handoff repair boundary、B02 は cheap-route mismatch、B03 は route_match_decided handoff、B04 は bugfix + later handoff no same-day promise、B05 は Customer Portal 新機能を neither、B06 は handoff audience boundary、B07 は bugfix light explanation enough として整理した
- きっかけ: r0 では、`25,000円整理で修正も含むか`、`15,000円修正枠で整理だけ見たい`、`正式仕様書や職種別資料までほしい`、`新機能追加もメモにしたい` などの近縁境界が default bugfix へ吸収された。B03 では相手文にない `外注先と連絡が取れず` の context bleed も出た
- 想定効果: dual-service 化した時に、25,000円整理へ修正を吸収しない、15,000円修正枠で整理だけ見たい相談を bugfix にしない、正式仕様書・職種別資料・新機能追加を handoff に広げない、bugfix 内の軽い説明で足りる時は handoff を押し込まない
- 非変更: 新規 rule 化はしない。通常 live への handoff 解禁はしない。今回の 25,000円案内は #BR future-dual simulation 内の shadow gold として扱う

### 2026-04-28 / CHG-096
- 分類: `reply-only`
- レイヤ: #BR batch-current r1 / config-test-runbook boundary gold
- 変更: BR-11 r0 の Codex監査を受け、`返信監査_batch-current.md` を r1 へ手反映した。B01 は active defect sequencing、B02 は config / URL secret safety、B03 は test creation scope out、B04 は multi-flow audit の1フロー境界、B05 は bugfix + handoff no same-day promise、B06 は ops runbook scope out、B07 は route_match_decided handoff として整理した
- きっかけ: r0 では、B02/B03/B06/B07 が default_bugfix へ吸収され、B04 も不具合相談へ誤寄せされた。B05 は不具合修正側へ寄る一方で、次担当者向けメモとの成果物分離と同日約束の否定が不足した
- 想定効果: dual-service 化した時に、secret / APIキー / DB接続URL / 接続先URL の値そのものを扱わない、テスト追加・テスト仕様書・社内運用資料・復旧手順書を handoff に吸収しない、複数フローや同日一括完了を安易に約束しない境界を保持できる
- 非変更: 新規 rule 化はしない。通常 live への handoff 解禁はしない。今回の 25,000円案内は #BR future-dual simulation 内の shadow gold として扱う

### 2026-04-28 / CHG-097
- 分類: `reply-only`
- レイヤ: #BR batch-current r2 / config inventory flow close
- 変更: BR-11 の外部 Codex 監査で必須崩れなし・採用圏となったため、軽微指摘の B02 だけ反映した。`対象フローを1つに絞って進めます` を、`たとえば「決済完了から注文作成まで」のように対象フローを1つに絞って進めます` へ変更した
- きっかけ: config / env / secret 整理では、対象フローが抽象的なままだと環境変数全体の棚卸しへ広がりやすいと指摘された
- 想定効果: handoff でキー名・利用箇所・用途を扱う場合も、主要1フロー境界から外れずに案内できる
- 非変更: 新規 rule 化はしない。通常 live への handoff 解禁はしない。今回の修正は #BR batch 内の case_fix として扱う

### 2026-04-28 / CHG-098
- 分類: `reply-only`
- レイヤ: #BR batch-current r1 / work-surface and migration boundary gold
- 変更: BR-12 r0 の Codex監査を受け、`返信監査_batch-current.md` を r1 へ手反映した。B01 は bugfix + no direct push/deploy、B02 は handoff memo not GitHub PR review、B03 は monitoring retainer scope out、B04 は bugfix + schema migration boundary、B05 は multi-repo one-flow handoff、B06 は API/framework migration scope out、B07 は no-repair handoff with secret-safe settings map として整理した
- きっかけ: r0 では、B02/B05/B07 の handoff-first が default_bugfix へ吸収され、B03/B06 の neither も active defect 風の generic boundary へ流れた。B01/B04 は bugfix-first の方向は近いが、直接push・本番反映・DB設計変更/マイグレーションを切る回答が不足した
- 想定効果: dual-service 化した時に、修正対象そのものと作業場所/本番反映/外部レビュー/継続監視/移行作業を分けられる。active defect は bugfix-first に保ちつつ、直接push・本番デプロイ・DB大規模変更・継続保守を吸収しない
- 非変更: 新規 rule 化はしない。通常 live への handoff 解禁はしない。今回の 25,000円案内は #BR future-dual simulation 内の shadow gold として扱う

### 2026-04-28 / CHG-099
- 分類: `reply-only`
- レイヤ: #BR forward plan / previous Codex handoff
- 変更: 前 Codex からの引き継ぎを受け、BR13 以降の重点を `handoff に見えるが実は neither` 系へ寄せる方針を `boundary-routing-shadow-rehearsal.ja.md` に追記した。あわせて、通常 live / #RE へ戻してよい汎用境界と、shadow asset に留めるべき handoff-25000 / 25,000円 / dual-service 案内を分離して記録した
- きっかけ: BR10〜BR12 で bugfix / handoff の境界は育ってきたため、次は `どちらにも入れないものを冷たくならずに切る` 訓練が重要だと整理された
- 想定効果: 複数サービス展開時の router core として、service fit だけでなく neither 判定を安定させる。Pro 分析へ投げる時も、BR10〜BR15 の r0/r1 差分と gold をまとめて渡せる
- 非変更: 新規 renderer / validator 実装はしない。通常 live への handoff 解禁はしない

### 2026-04-28 / CHG-100
- 分類: `reply-only`
- レイヤ: #BR batch-current r2 / migration neither close
- 変更: BR-12 の外部 Codex 監査で必須崩れなし・採用圏となったため、軽微指摘の B06 だけ反映した。`既存フローを整理するだけであれば25,000円の整理候補になりますが` を、`既存フローの整理だけが目的であれば別の整理対象になりますが` へ変更した
- きっかけ: API更新・App Router移行を neither に落とした後に、25,000円整理候補を補足すると、範囲外判定後の説明が少し横へ広がると指摘された
- 想定効果: neither 判定後に別サービス候補を出しすぎず、今回の API更新・フレームワーク移行が対象外であることへ戻せる
- 非変更: 新規 rule 化はしない。通常 live への handoff 解禁はしない。今回の修正は #BR batch 内の case_fix として扱う

### 2026-04-28 / CHG-101
- 分類: `reply-only`
- レイヤ: #BR batch-current r1 / neither-heavy boundary gold
- 変更: BR-13 r0 の Codex監査を受け、`返信監査_batch-current.md` を r1 へ手反映した。B01 は customer FAQ scope out、B02 は dashboard operations manual scope out、B03 は formal spec / audience-specific docs scope out、B04 は new feature plus memo scope out、B05 は raw secret inventory scope out、B06 は full audit pressure の1フロー境界、B07 は diagnosis-only pressure、B08 は handoff repair absorption として整理した
- きっかけ: 前 Codex からの引き継ぎどおり、BR13 は `handoff に見えるが実は neither` を厚めに当てた。r0 では B01〜B05/B08 が default_bugfix や generic boundary へ強く吸収され、B01 では相手文にない `外注先と連絡が取れず` の context bleed も出た
- 想定効果: 複数サービス展開時に、Stripe関連でも FAQ / 操作マニュアル / 仕様書 / 新機能説明メモ / secret値台帳 / 全体監査を安易に handoff へ吸収しない。neither を冷たくならず自然に切る gold を増やす
- 非変更: 新規 rule 化はしない。通常 live への handoff 解禁はしない。今回の 25,000円案内は #BR future-dual simulation 内の shadow gold として扱う

### 2026-04-28 / CHG-102
- 分類: `reply-only`
- レイヤ: #BR batch-current r1 accepted / external audit close
- 変更: BR-13 の外部 Codex 監査で必須崩れなし・採用圏となったため、`返信監査_batch-current.md` の状態を `r1 accepted` に更新し、`boundary-routing-shadow-rehearsal.ja.md` に外部監査結果を追記した。B06 の診断調表現は preference 扱いで本文修正なし
- きっかけ: neither の切り方、secret値の扱い、全体監査の1フロー制限、diagnosis-only pressure、handoff repair absorption が安定していると評価された
- 想定効果: BR13 を採用済み gold として扱い、次の BR14 では引き続き neither / bundle pressure / deliverable boundary を厚めに検査できる
- 非変更: 新規 rule 化はしない。通常 live への handoff 解禁はしない。`25,000円` / `handoff-25000` / 主要1フロー整理の購入導線は #BR 内の future-dual simulation に留める

### 2026-04-28 / CHG-103
- 分類: `reply-only`
- レイヤ: #BR batch-current r1 / mixed handoff-positive boundary gold
- 変更: BR-14 fixture を追加し、`返信監査_batch-current.md` を r1 へ手反映した。B01 は active defect with code confusion、B02 は decided one-flow handoff、B03 は bugfix light explanation、B04 は environment/setup boundary、B05 は GitHub work-surface boundary、B06 は broad architecture review mismatch、B07 は secret-safe settings map、B08 は bundle pressure として整理した
- きっかけ: BR13 で neither が安定したため、BR14 は handoff に入れてよい相談と、handoff へ広げてはいけない作業面・成果物面の境界を混ぜて検査した。r0 では handoff-first が bugfix へ吸収され、全体設計レビューも原因不明の不具合相談のように誤読された
- 想定効果: dual-service 化した時に、有効な handoff 相談を自然に受けつつ、環境構築・README整備・GitHub Issue/PR作業・全体設計レビュー・セット料金化へ広げない。bugfix 内の軽い説明と本格 handoff も分離できる
- 非変更: 新規 rule 化はしない。通常 live への handoff 解禁はしない。今回の `25,000円` 案内は #BR future-dual simulation 内の shadow gold として扱う

### 2026-04-28 / CHG-104
- 分類: `reply-only`
- レイヤ: #BR batch-current r2 / code sharing wording close
- 変更: BR-14 の外部 Codex 監査で必須崩れなし・採用圏となったため、軽微指摘の B02 だけ反映した。`対象リポジトリまたは該当コード一式を共有してください` を、`該当コード一式や関係ファイルを共有してください` へ変更した
- きっかけ: `対象リポジトリ` という表現が、GitHub招待や外部repo上作業を連想させる余地があると指摘された
- 想定効果: decided handoff の購入後共有物を自然に案内しつつ、GitHub Issue/PR/label 作業や外部repo work-surface への誤読を減らす
- 非変更: 新規 rule 化はしない。通常 live への handoff 解禁はしない。今回の修正は #BR batch 内の case_fix として扱う

### 2026-04-29 / CHG-105
- 分類: `common`
- レイヤ: transaction/payment route isolation
- 変更: `platform-contract.yaml` に `service_scope_vs_payment_route` と `keep_service_boundary_and_payment_route_separate` を追加し、サービス境界と支払い導線を分離した。`service-plan.ja.md` は追加料金欄を支払い導線の運用メモとして明確化した。handoff の `boundaries.yaml` から `同じトークルーム内で追加料金の修正として続けられる` を外し、`decision-contract.yaml` でも修正追加は handoff 本体と分けて進め方と費用を相談する表現へ弱めた。#BR メモと内部 gold も、支払い方法を前面化しない形へ調整した
- きっかけ: `bugfix -> handoff` / `handoff -> bugfix` の追加対応導線が、サービス境界の正本に混ざると、AI が後続サービス前提・一括料金化・おひねり導線を通常返信へ出しやすくなる懸念があった
- 想定効果: #BR では `別成果物` `別対応` `進め方と費用を相談` までに留め、同じトークルーム内 / 有料オプション / おひねりは buyer が支払い方法を聞いた時だけ、取引状態に応じて案内する。通常 live / #RE への handoff 漏れも抑える
- 非変更: `bugfix-15000` / `handoff-25000` の価格・成果物・公開状態は変更しない。`handoff-25000` は引き続き public:false

### 2026-04-29 / CHG-106
- 分類: `common`
- レイヤ: #BR batch-current r1 / payment-route separation gold
- 変更: BR-15 fixture を追加し、`返信監査_batch-current.md` を r1 へ手反映した。B01 は prequote no-ohineri promise、B02 は handoff-first no payment-route、B03 は no cheap trial、B04 は no bundle/no same-room promise、B05 は purchased state-allowed payment route、B06 は handoff repair split、B07 は delivered-not-closed payment route、B08 は closed no-old-talkroom-ohineri として整理した。監査プロンプトにも `payment_route_bleed` と `phase_payment_mismatch` を追加した
- きっかけ: CHG-105 で支払い導線を platform layer に隔離したため、その分離が #BR の route gold で効くかを検査する必要があった
- 想定効果: サービス境界と支払い導線を混ぜず、必要な場面だけ state に応じて支払い導線を出せる。ココナラ固有の導線を返信判断コアへ常駐させず、将来の汎用返信OSにも移植しやすくする
- 非変更: 通常 live への handoff 解禁はしない。`handoff-25000` は引き続き public:false。支払い導線の詳細は buyer が明示的に聞いた時だけ扱う

### 2026-04-29 / CHG-107
- 分類: `common`
- レイヤ: #BR batch-current r2 / delivered payment route hedge
- 変更: BR-15 の外部 Codex 監査で必須崩れなし・採用圏となったため、軽微指摘の B07 だけ反映した。`合意後におひねり等の追加支払いで進める形になります` を、`合意後におひねり等の追加支払いで進められる場合があります` へ変更した
- きっかけ: delivered / クローズ前で buyer が支払い方法を聞いているため追加支払い導線は妥当だが、断定を少し弱めると取引状態依存の表現としてより安全だと指摘された
- 想定効果: 支払い導線を出すべき場面でも、ココナラ上の状態や手続きに依存する余地を残し、自動追加・確定導線に見える事故を減らす
- 非変更: 新規 rule 化はしない。通常 live への handoff 解禁はしない。今回の修正は #BR batch 内の case_fix として扱う

### 2026-04-29 / CHG-108
- 分類: `common`
- レイヤ: handoff source-of-truth cleanup / payment route isolation
- 変更: Pro 4/29 完成条件監査で指摘された `handoff-25000.ready.txt` の source drift を受け、サービス本文と FAQ から `修正が必要な場合は、同じトークルーム内で続けてご案内できます` 系の表現を外した。修正や別フロー確認は、基本範囲とは分けて対応範囲・費用・進め方を事前相談する表現へ寄せた。あわせて handoff service-pack 内の支払い導線メモも、具体的な同一トークルーム導線ではなく `platform contract` 参照へ抽象化した
- きっかけ: `handoff-25000` は public:false のため即時外向け事故ではないが、public:true 前には service boundary と payment route を混ぜる表現が blocker になると評価された
- 想定効果: handoff service page が将来 public:true になっても、修正対応・追加フロー・同一トークルーム導線を一体化して案内する事故を減らす。支払い方法は platform layer に留め、service facts には成果物・範囲・除外事項を残す
- 非変更: `handoff-25000` は引き続き public:false。サービス価格・有料オプション価格・成果物定義は変更しない。通常 live / #RE への handoff 解禁もしない

### 2026-04-29 / CHG-109
- 分類: `common`
- レイヤ: Pro 4/29 roadmap P0/P1 / public leak and delivery-completion regression
- 変更: 通常 live / #RE の public ケースで `handoff-25000` / `25,000円` / `主要1フロー` / `future-dual` などの shadow 語彙が出た場合に `public_mode_leakage` として落とす hard gate を unified pipeline に追加した。既存の `bugfix37` / `bugfix38` fixture を `eval-sources.yaml` に接続し、新たに `public-private-leakage-bugfix39.yaml` と `delivery-completion-bugfix40.yaml` を追加した。あわせて、`変更ファイルと確認順だけで足りるか` の public bugfix 返信と、delivered 承諾前の別件かもしれない質問を専用分岐で受けられるようにした
- きっかけ: Pro 4/29 監査で、完成判定にはレンズ追加より `mode leakage 防止`、`bugfix37 系 regression`、`delivery/completion regression` が必要と整理された
- 想定効果: #BR の future-dual 語彙が通常 live / #RE に染み込む事故を機械的に止める。購入後・納品後の old generic template / delivered fallback drift を再発検知し、承諾前・クローズ後・確認材料と実作業の境界を固定する
- 非変更: `handoff-25000` は public:false のまま。soft lens は validator 化しない。`response_weight_mismatch` / `buyer_state_ack_gap` は引き続き reviewer / gold / regression 側で扱う

### 2026-04-29 / CHG-110
- 分類: `common`
- レイヤ: #BR batch-current r1 / post-Pro confirmation gold
- 変更: BR-16 fixture を追加し、`返信監査_batch-current.md` を Pro 4/29 対応後の確認走行として作成した。active defect の bugfix-first、valid handoff の支払い導線先回り防止、bugfix 内の軽い説明、handoff repair absorption 防止、delivered / closed micro-state、closed 後の確認材料と実作業分離、操作手順書・顧客FAQの neither 境界、prequote same-room repair promise 防止を検査した。外部監査で必須崩れなし・採用圏となったため、軽微指摘の B07 だけ `含めにくいです` から `含まれません` へ締めた
- きっかけ: Pro 4/29 対応で source cleanup / public-private wording separation / payment-route isolation / delivery-completion regression を入れたため、#BR の future-dual 文面でも同じ分離が効いているか確認する必要があった
- 想定効果: handoff 公開前の shadow asset として、サービス境界・支払い導線・納品後状態理解の安定性を確認できる。通常 live へ戻せる汎用境界と、#BR 内に留める 25,000円 / handoff 案内の線引きも維持できる
- 非変更: 新規 rule 化はしない。通常 live への handoff 解禁はしない。`handoff-25000` は引き続き public:false。今回の修正は #BR batch 内の case_fix として扱う

### 2026-04-29 / CHG-111
- 分類: `reply-only`
- レイヤ: #BR BR13-16 shelf / live-return candidates
- 変更: BR13〜16 の採用結果を `rehearsal-shelf-20260429-br13-16.ja.md` に棚卸しした。通常 live / #RE に戻してよい候補として、active defect の bugfix-first、bugfix 内の軽い説明、運用資料/顧客対応資料の除外、raw secret 禁止、diagnosis-only pressure 防止、service boundary と payment route 分離、delivered / closed micro-state、context bleed guard を整理した。あわせて `question-type-batch-plan-20260425.ja.md` と `phase-contract-batch-plan-20260425.ja.md` に観察候補だけ反映し、`self-check-core-always-on.ja.md` の公開状態・支払い導線・delivered/closed 確認を最小補強した
- きっかけ: BR13〜16 は連続して採用圏となったため、次の #BR を増やす前に、通常 live / #RE へ戻せる汎用境界と shadow asset に留めるものを分ける必要があった
- 想定効果: 25,000円 / handoff-25000 / dual-service 導線を通常 live へ漏らさず、汎用の返信判断コアだけを強化できる。次の #RE では、未公開サービス混線、運用資料要求、支払い導線先回り、delivered / closed 状態誤認を観察しやすくなる
- 非変更: renderer / validator は変更しない。新規 rule 化もしない。通常 live への handoff 解禁はしない。BR17 はすぐ回さず、再発や公開前チェックが必要になった時の候補として保留する

### 2026-04-29 / CHG-112
- 分類: `reply-only`
- レイヤ: #RE bugfix41 r1 / post-BR live boundary renderer
- 変更: `post-br-live-boundary-bugfix41.yaml` を eval source に接続し、通常 live の #RE で BR13〜16 由来の汎用境界を検査できるようにした。r0 外部監査で必須修正となった、操作手順書・顧客FAQの bugfix 吸収、原因だけ安く/診断メモだけ、raw secret inventory、prequote のおひねり追加約束を、`estimate_initial` renderer の専用分岐へ戻した。あわせて active defect でコード全体整理を先に挟まなくてよい表現も補強した
- きっかけ: r0 は handoff-25000 / 25,000円の live 漏れはなかったが、対象外・neither 系を汎用 bugfix 受付文に吸収していた
- 想定効果: 通常 live / #RE で未公開 handoff 導線を出さずに、bugfix 単体の範囲外、secret 生値不可、diagnosis-only 不可、支払い導線先回り不可を自然に返せる。BR の学びを shadow 語彙なしで live 側へ戻す
- 非変更: `handoff-25000` は public:false のまま。通常 live への 25,000円 / 主要1フロー / handoff 購入導線は解禁しない。今回の修正は返信文 renderer / regression の補強であり、サービスページ価格や成果物定義は変更しない

### 2026-04-29 / CHG-113
- 分類: `reply-only`
- レイヤ: #RE bugfix41 r2 / accepted audit light close
- 変更: r1 外部監査で採用圏・必須修正なしとなったため、軽微候補だけ反映した。delivered 承諾前の別件確認は `ご確認ありがとうございます` から入り、今回の修正とつながる内容かを軽く見る表現へ自然化した。closed 後の確認材料ケースでは固定時刻コミットを外し、`送っていただいた範囲で、見立てを短くお返しします` へ変更した。closed follow-up lint も、確認材料だけの場面では条件付き見立てを許可するようにした
- きっかけ: r1 監査で、B06 は `確認` の重複が少し機械的、B07 は固定時刻が送信時刻依存で実運用ノイズになり得ると指摘された
- 想定効果: 採用圏を保ったまま、承諾前/closed 後のマイクロ状態をより自然に扱える。固定時刻の古びやすさを減らし、未受領材料に依存する見立ては条件付きで書く既存方針にも合わせる
- 非変更: 新規 rule 追加はしない。通常 live への handoff 解禁はしない。B06 / B07 は軽微自然化と batch close であり、B03 / B04 / B05 / B08 の hard boundary は CHG-112 のまま維持する

### 2026-04-29 / CHG-114
- 分類: `common`
- レイヤ: service-grounding audit / prequote grounding bridge
- 変更: `service-grounding-audit-20260429.ja.md` を追加し、`bugfix-15000.live.txt` から `service-registry.yaml`、`service.yaml`、`service-pack`、renderer、validator、regression までの接続を棚卸しした。あわせて `estimate_initial` renderer でも `service-registry.yaml` から public bugfix の `service_grounding` を読み込み、prequote case に保持するようにした。`check-rendered-prequote-estimate.py` でも public bugfix prequote の `service_grounding`、`public_service`、`base_price`、`hard_no`、`source_of_truth` を検査する
- きっかけ: 最初に公開する `bugfix-15000` について、サービス本丸の記憶領域が返信システムへ本当に接続されているかを確認する必要があった。購入後 / delivered / closed は registry 接続済みだったが、prequote はハードコード寄りで接続が浅かった
- 想定効果: 一番重要な購入前 live 返信でも、公開中サービスの正本・価格・hard no・scope unit への接続を明示できる。サービスページ変更時に、page -> service-pack -> renderer / validator のどこがずれたか追いやすくなる
- 非変更: サービス価格・成果物・公開状態は変更しない。renderer 内の既存 `15,000円` リテラルを全面動的化する作業はまだ行わない。`handoff-25000` は引き続き public:false

### 2026-04-29 / CHG-115
- 分類: `reply-only`
- レイヤ: skill / docs noise audit
- 変更: `skill-noise-audit-20260429.ja.md` を追加し、project-local skills、返信品質 docs、汎用テンプレ、判断フロー、quote_sent renderer に残っていた旧導線を棚卸しした。`同じトークルーム内追加料金`、`クローズ前ならおひねり`、`有料オプション追加不可だから追加支払いへ`、未公開 handoff の `25,000円 / 主要1フロー / 購入導線` を、通常 live / #RE では出さない状態依存の表現へ修正した。`japanese-chat-natural-ja` も、自然化 layer で支払い導線を新しく決めないようにした
- きっかけ: service-grounding audit 後、runtime は安定している一方、古い skill / docs が横から payment route や private handoff 語彙を戻す懸念があった
- 想定効果: 通常 live / #RE は `bugfix-15000` の公開語彙だけに留まり、#BR の shadow 語彙やココナラ固有の支払い導線は、必要な state と lane でだけ扱う。返信判断コアと支払い導線の分離も維持しやすくなる
- 非変更: `handoff-25000` は public:false のまま。chatgptPro 過去分析、BR 履歴、service-pack fidelity fixture は履歴/検査材料として残し、正本ノイズとしては編集しない

### 2026-04-29 / CHG-116
- 分類: `common`
- レイヤ: docs cleanup / active-source pruning
- 変更: `docs/` を現行 Codex が起動・返信・実装・納品で参照する資料へ絞った。旧外部調査ログ、出品初期準備、旧 service catalog / service plan、旧 live 監査サマリ、self-check 再編途中メモ、古い backup / checklist / UI cheat sheet を削除した。`docs/README.ja.md` と `docs/reply-quality/README.ja.md` は現行入口として書き直し、`next-codex-prompt.txt` も 4/29 の grounding / noise / BR 棚卸しを読む形へ更新した
- きっかけ: 過去 Codex が実装中に作った docs が増え、現行返信OSの正本と古い調査・初期設計メモが混ざると、次の Codex が古い支払い導線や公開状態へ戻るリスクがあった
- 想定効果: Codex が今必要な正本だけを辿れる。`service-registry.yaml`、service page 正本、reply-quality 現行入口、delivery / implementation 用 docs の境界が明確になり、古い docs が runtime の判断を邪魔しにくくなる
- 非変更: `handoff-25000` は public:false のまま。`chatgptPro/`、`note用/`、`HANDOFF_NEXT_CODEX.ja.md` などの履歴領域は今回の docs pruning 対象外

### 2026-04-29 / CHG-117
- 分類: `reply-only`
- レイヤ: #RE bugfix42 / post-docs-cleanup noise sentry
- 変更: docs cleanup 後の確認走行として `post-docs-cleanup-noise-bugfix42.yaml` を追加し、`返信監査_batch-01.md` を `RE-2026-04-29-bugfix-42-post-docs-cleanup-noise-r0` へ更新した。初回生成で出た `外注先と連絡が取れず` の context bleed、`操作マニュアル` の汎用 bugfix 吸収、closed 後のおひねり質問への直答抜けを、最小 renderer / lint 補強として戻した
- きっかけ: `docs/` から旧 service-plan / service-catalog / 外部調査ログ / 初期設計メモを削った直後に、通常 live / #RE が古い支払い導線や private handoff 語彙へ戻らないか確認する必要があった
- 想定効果: 通常 live で、古い docs 由来の整理・引き継ぎ・おひねり導線・操作マニュアル吸収が再発しにくくなる。相手文にない外注先事情を足さず、closed 後は旧トークルーム内のおひねりへ誘導しない
- 非変更: `handoff-25000` は public:false のまま。通常 live / #RE への 25,000円 / 主要1フロー / handoff 購入導線は解禁しない。今回の修正は bugfix live の noise sentry と最小 renderer 補強

### 2026-04-29 / CHG-118
- 分類: `reply-only`
- レイヤ: #RE bugfix42 r1 / accepted audit light revision
- 変更: bugfix42 r0 外部監査で採用圏・必須崩れなしとなったため、軽微3点だけ r1 へ反映した。B02 は相手文にない `顧客向けFAQ` を削除し、B03 は `15,000円の不具合修正で確認できます` を冒頭へ出して `全体整理が必要` を削除した。B08 は `確認材料の受領と実作業の開始を分ける必要があります` を、購入者向けの `メッセージ上で状況だけ確認し、修正が必要な場合は見積り提案または新規依頼` へ自然化した
- きっかけ: r0 は safety / public leak は安定していたが、docs cleanup 後の残り香として、相手文にない資料名追加、通常 live の整理語、closed 後の内部ルール露出が軽微に残っていた
- 想定効果: 通常 live の `bugfix-15000` 返信で、古い docs 由来の言葉をさらに薄くし、buyer の主質問への直答と次行動を保ったまま自然さを上げる
- 非変更: 新規 rule 追加はしない。`handoff-25000` は public:false のまま。通常 live / #RE への 25,000円 / 主要1フロー / handoff 購入導線は解禁しない

### 2026-04-29 / CHG-119
- 分類: `reply-only`
- レイヤ: #RE bugfix43 r0 / live core human review sentry
- 変更: `live-core-human-review-bugfix43.yaml` を追加し、`返信監査_batch-01.md` を `RE-2026-04-29-bugfix-43-live-core-human-review-r0` へ更新した。短文の対象可否、他者修正後の再発不安、AI生成コードで中身不明、フロント表示崩れ + Stripe反映漏れ、Preview環境Webhook 400 + secret値不安、購入後の進捗不安、納品後の軽い説明依頼、closed 後のリピート相談を検査対象にした。初回生成で出た汎用 bugfix 吸収、secret 値不要の明示不足、progress anxiety 検知不足、delivered の前回続き誤発火、相手文にない症状名の context bleed を、最小 renderer 補強として戻した
- きっかけ: ユーザー監査も取り込み、hard boundary だけでなく `買う側が迷わないか` `ぶつ切り感がないか` `サービス本丸に接地しているか` を live 本丸で確認する必要があった
- 想定効果: `bugfix-15000` の通常 live 返信で、主質問への直答、状態理解、軽い説明と本格資料の分離、secret-safe 進行、複数症状の切り分けが安定する。将来アプリ化する時の human review 系 regression としても使える
- 非変更: 新規サービス導線は出さない。`handoff-25000` は public:false のまま。今回の human review 観点は validator hard rule にはせず、まず batch / reviewer lens / renderer の最小補強に留める

### 2026-04-29 / CHG-120
- 分類: `reply-only`
- レイヤ: #RE bugfix43 r1 / phase and human-review cleanup
- 変更: bugfix43 r0 外部監査で B03 が必須修正、B05/B07/B08 が軽微修正となったため r1 へ反映した。B03 は prequote でファイル送付・一次結果へ滑らないよう `ご購入後` に寄せ、B05 も Preview環境確認を `ご購入後は、まず...確認します` へ締めた。B07 は次アクションを `確認結果` ではなく `補足説明` に変更し、B08 は `見積りできます` より先に `このメッセージでまず相談いただいて大丈夫です` と直答するようにした。あわせて prequote / delivered / closed の lint に、今回の phase 滑りと主質問抜けを再発検知する最小チェックを追加した
- きっかけ: r0 は facts / public leak は安定していたが、購入前返信で作業開始に見える箇所と、納品後・closed 後の主質問に対する語のズレが残っていた
- 想定効果: `bugfix-15000` live で、購入前/購入後の phase、納品後の補足説明、closed 後の相談可否への直答がより安定する。human review 観点を hard rule 化しすぎず、事故になりやすい phase / direct answer だけを lint へ戻せる
- 非変更: `handoff-25000` は public:false のまま。通常 live / #RE への 25,000円 / 主要1フロー / handoff 購入導線は解禁しない

### 2026-04-29 / CHG-121
- 分類: `reply-only`
- レイヤ: #RE bugfix43 r2 / accepted audit light close
- 変更: bugfix43 r1 外部監査で採用圏・必須修正なしとなったため、軽微2点だけ r2 へ反映した。B03 は `コード全体の整理を前提にせず` へ自然化し、購入後に求める材料を既出の症状ではなく `関連しそうなファイルやログ` へ寄せた。B08 は closed 後の新症状を `前回とは別件の可能性もあるため` と受け、無料診断に見えやすい `確認だけで済む範囲` を `状況の見立てまでは、このメッセージ上で確認できます` へ締めた
- きっかけ: r1 は hard boundary と public leak は問題なかったが、B03 の語感と B08 の断定・無料期待の幅に軽微な実務ノイズが残っていた
- 想定効果: `bugfix-15000` live の購入前/closed 後返信で、buyer が既に書いた症状を再要求せず、クローズ後の相談可否と実作業の境界を自然に分けられる
- 非変更: 新規 rule 追加はしない。`handoff-25000` は public:false のまま。通常 live / #RE への 25,000円 / 主要1フロー / handoff 購入導線は解禁しない

### 2026-04-29 / CHG-122
- 分類: `reply-only`
- レイヤ: #RE bugfix44 r0 / public-launch practical sentry
- 変更: `public-launch-practical-bugfix44.yaml` を追加し、`返信監査_batch-01.md` を `RE-2026-04-29-bugfix-44-public-launch-practical-r0` へ更新した。金額だけ質問、曖昧な直せますか相談、active defect なしの不安相談、raw secret inventory、購入前 diagnosis-only 圧力、3症状まとめ依頼、purchased 中の複数症状追加、closed 後の別件相談入口を検査対象にした。初回生成で弱かった金額直答、曖昧相談の未断定、no-concrete の自然化、複数症状の1件起点、購入後 bundle pressure への直答を最小 renderer / lint 補強として戻した
- きっかけ: bugfix43 で live 本丸が採用圏になったため、次は公開直前に実際に来そうな短文・曖昧・支払い/秘密/複数症状圧力をまとめて確認する必要があった
- 想定効果: `bugfix-15000` live で、購入前の主質問直答、active defect 有無の切り分け、secret-safe 進行、diagnosis-only 防止、複数不具合の一括化防止、purchased / closed の状態境界が安定する
- 非変更: `handoff-25000` は public:false のまま。通常 live / #RE への 25,000円 / 主要1フロー / handoff 購入導線は解禁しない。今回の補強は bugfix live の公開直前 sentry として扱う

### 2026-04-29 / CHG-123
- 分類: `reply-only`
- レイヤ: #RE bugfix44 r1 / accepted audit light revision
- 変更: bugfix44 r0 外部監査で採用圏・必須修正なしとなったため、軽微4点だけ r1 へ反映した。B05 は購入前に原因だけ見る形ではないことと、購入後に原因確認から修正まで進める導線を明示した。B06 は複数症状の1件目見立て後に購入前の次アクションを足した。B07 は `つながっているかを先に見る` の重複を削り、境界・未確認点・依頼を1回で出す形にした。B08 は closed 後の主質問へ `はい、その流れで大丈夫です` と先に直答し、症状送付依頼を1回に圧縮した
- きっかけ: r0 は hard boundary と public leak は安定していたが、buyer の次アクションと、purchased / closed の重複表現に軽微な実務ノイズが残っていた
- 想定効果: `bugfix-15000` live の公開直前入口で、購入前の次行動、購入後の追加症状境界、closed 後の相談導線がより自然に伝わる
- 非変更: 新規 rule 追加はしない。`handoff-25000` は public:false のまま。通常 live / #RE への 25,000円 / 主要1フロー / handoff 購入導線は解禁しない

### 2026-04-29 / CHG-124
- 分類: `reply-only`
- レイヤ: #RE bugfix44 r2 / accepted re-audit polish
- 変更: bugfix44 r1 外部再監査で採用圏・必須修正なしとなったため、軽微4点だけ r2 へ反映した。B05 は `15,000円` と原因確認の説明を圧縮し、購入後に修正済みファイル返却まで進める軸へ寄せた。B06 は `その内容` を避け、決済や注文反映に近い症状を1件目として進める前提を明示した。B07 は `つながっているか確認` と `関連は未確認` の重複を1段落にまとめた。B08 は `費用の有無` を `対応方法と費用` に締め、無料余地を広く見せない表現へ自然化した
- きっかけ: r1 は hard boundary と public leak は問題なかったが、文量・重複・closed 後の費用表現に gold 寄せの余地が残っていた
- 想定効果: `bugfix-15000` live の公開直前入口で、購入前診断拒否、複数症状の1件目設定、購入後追加症状、closed 後相談の次行動がさらに短く自然に伝わる
- 非変更: 新規 rule 追加はしない。`handoff-25000` は public:false のまま。通常 live / #RE への 25,000円 / 主要1フロー / handoff 購入導線は解禁しない

### 2026-04-29 / CHG-125
- 分類: `common`
- レイヤ: Pro後 service-grounding sentries
- 変更: `scripts/check-service-grounding-sentries.py` を追加し、`service-page-semantic-smoke`、`renderer-literal-drift-scan`、`public_false_shadow_lexeme` を1本の検知 suite として実装した。`bugfix-15000.live.txt` の価格・同一原因・修正済みファイル返却・secret 値禁止・原因だけ診断不可・追加作業の事前相談が facts / service-pack / rendered reply に落ちているかを確認する。renderer 内の価格・private/shadow 語彙は fail ではなく warn とし、live / #RE の代表 fixture では `handoff-25000` / 25,000円 / 主要1フロー / 引き継ぎメモ漏れを fail にする。`check-coconala-reply-role-suites.py` からも最後に1回だけ実行する。あわせて `service-registry.yaml` に `facts_service_id` を追加し、`bugfix-15000` と `next-stripe-bugfix` の alias を明文化した
- きっかけ: Pro 分析で、サービス記憶領域と返信システムの接続はかなり強いが、renderer の第二正本化リスク、service page と返信文の semantic diff の弱さ、#BR shadow 語彙の live 漏れ sentry 固定化が残課題として示された
- 想定効果: #RE / #BR をさらに増やす前に、サービス本丸 -> registry / facts -> renderer / validator / regression の意味接続を薄く検知できる。renderer のリテラルをすぐ全面動的化せず、warn として可視化しながら public leak だけは hard fail にできる
- 非変更: renderer の全面 dynamic 化はしない。`handoff-25000` は public:false のまま。renderer 内の既存 `15,000円` リテラルは現時点では warn 扱いで、返信出力の live 漏れのみ fail とする

### 2026-04-29 / CHG-126
- 分類: `reply-only`
- レイヤ: timestamp policy lint
- 変更: `scripts/check-timestamp-policy.py` を追加し、購入後 / 納品後 / closed の代表 fixture を runtime で再描画して、`本日HH:MMまでに` が過去時刻や異常な時刻になっていないかを検査するようにした。renderer 内に `本日18:00までに` のような固定時刻リテラルがあれば fail、現在の監査用 md に残る固定時刻は warn として出す。`check-coconala-reply-role-suites.py` からも最後に1回だけ実行する
- きっかけ: Pro 分析で、具体時刻コミットは runtime 生成なら有用だが、fixture / rehearsal に固定時刻として残ると stale deadline 事故や bot 感の原因になると指摘された
- 想定効果: 実際の送信用返信では runtime 時刻の鮮度を維持しつつ、監査用 batch に残る固定時刻を可視化できる。固定時刻を全廃せず、外部監査前に必要なら再生成する判断材料にする
- 非変更: 時刻コミットの運用自体は廃止しない。監査用 md の固定時刻は現時点では warn 扱いで、送信用 renderer の固定時刻だけ fail とする

### 2026-04-29 / CHG-127
- 分類: `reply-only`
- レイヤ: #RE bugfix45 / post-Pro grounding sentry
- 変更: `post-pro-grounding-bugfix45.yaml` を追加し、`返信監査_batch-01.md` を `RE-2026-04-29-bugfix-45-post-pro-grounding-r0` へ更新した。service grounding / timestamp sentry 追加後の確認走行として、対象可否、コード出どころ不明、active defect + 新機能追加、quote_sent の購入前材料送付、purchased の進捗不安と直接 push / 本番反映依頼、delivered の承諾待ち、closed 後のおひねり継続圧力を検査対象にした。初回生成で出た `クーポン機能` 入力への `CSVダウンロードボタン` context bleed を、feature addon renderer と validator の最小補強として戻した。あわせて `eval-sources.yaml` と timestamp-policy の runtime fixture に接続した
- きっかけ: Pro後ロードマップで service page -> facts -> renderer の接続と timestamp policy を入れたため、実際の `bugfix-15000` live 返信で本丸接地・public leak・phase・時刻が崩れないか確認する必要があった
- 想定効果: `bugfix-15000` live で、サービス正本に接地した可否返答、新機能追加の吸収防止、購入前作業開始防止、直接 push / 本番デプロイ拒否、closed 後の実作業分離がさらに安定する
- 非変更: `handoff-25000` は public:false のまま。通常 live / #RE への 25,000円 / 主要1フロー / handoff 購入導線は解禁しない。今回の補強は bugfix live の post-Pro sentry として扱う

### 2026-04-29 / CHG-128
- 分類: `reply-only`
- レイヤ: #RE bugfix45 r1 / compound boundary fix
- 変更: bugfix45 r0 外部監査で B06 / B08 が必須修正となったため r1 へ反映した。B06 は direct push だけでなく本番反映もこちらでは行わないと明示し、本番反映は返却した差分・手順をもとに依頼者側で行う形へ締めた。B08 は `クローズ後` も旧トークルームおひねり継続圧力として検知し、旧トークルーム内のおひねり追加で別件修正を進められないこと、実作業が必要なら見積り提案または新規依頼として対応方法と費用を先に相談することを明示した。軽微指摘として B01 の重複謝意、B02 の前任者/AI拾い漏れ、B03 の `この内容` 曖昧さも修正した
- きっかけ: r0 は private leak や価格崩れはなかったが、buyer が明示した禁止事項への否定が compound question 内で一部落ちていた
- 想定効果: `bugfix-15000` live で、直接 push + 本番反映、closed 後の旧トークルーム + おひねり追加のような複合危険質問に対して、禁止事項を破らないだけでなく主質問へ明示的に答えられる
- 非変更: 新しい支払い導線は解禁しない。`handoff-25000` は public:false のまま。通常 live / #RE への 25,000円 / 主要1フロー / handoff 購入導線は出さない

### 2026-04-29 / CHG-129
- 分類: `reply-only`
- レイヤ: #RE bugfix45 r1 accepted / light naturalization
- 変更: bugfix45 r1 外部再監査で採用圏・必須修正なしとなったため、軽微3点だけ反映した。B01 は購入前文脈をより明確にするため `ご購入後、必要情報がそろい次第...` に変更した。B06 は直接 push と本番反映の否定を短く切り、境界説明の読みやすさを上げた。B08 は `確認しました` 系の内部処理っぽさを避け、`クローズ後の別件相談ですね` へ自然化した
- きっかけ: r1 で hard boundary と public leak は解消済みだったが、phase 明示、文量、語感に gold 寄せの余地が残っていた
- 想定効果: `bugfix-15000` live で、購入前の作業開始誤解、直接 push / 本番反映の読みづらさ、closed 後の機械的な受けをさらに減らせる
- 非変更: 新規 rule 追加はしない。`handoff-25000` は public:false のまま。通常 live / #RE への 25,000円 / 主要1フロー / handoff 購入導線は出さない

### 2026-04-29 / CHG-130
- 分類: `reply-only`
- レイヤ: Pro後 reviewer prompt soft lenses
- 変更: bugfix-15000 と #BR の Codex xhigh 監査プロンプトに、Pro が挙げた5つの補助監査レンズを soft lens として追記した。対象は `source_traceability`、`commitment_budget`、`semantic_grounding_drift`、`shadow_to_live_contamination`、`evidence_minimality`。あわせて、これらを hard fail に直結させず、明確な public leak / phase drift / secret 値要求 / 保証断定など deterministic な事故だけ必須修正にする注意も追加した
- きっかけ: Pro 分析では、監査精度を上げる候補として5レンズが示された一方、全レンズの hard validator 化や売上最大化 CTA / 汎用 empathy / 全 platform legal lens はノイズ化すると警告されていた
- 想定効果: 返信生成や renderer を変えず、外部監査AIに見るべき観点だけを渡せる。骨格を壊さず、source traceability / commitment budget / evidence minimality のような実務違和感を拾いやすくする
- 非変更: renderer / validator / service facts は変更しない。Pro後5レンズは生成 rule ではなく reviewer prompt の soft lens として扱う

### 2026-04-29 / CHG-131
- 分類: `reply-only`
- レイヤ: #RE bugfix46 / post-Pro reviewer lens sentry
- 変更: `post-pro-review-lenses-bugfix46.yaml` を追加し、`返信監査_batch-01.md` を `RE-2026-04-29-bugfix-46-post-pro-review-lenses-r0` へ更新した。Pro後5レンズの確認走行として、保証・直らなかった場合、raw secret inventory、buyer 文内の25,000円/整理語、quote_sent の購入前材料送付、purchased の既出材料確認、キー名のみ共有、delivered の軽い補足説明、closed 後の関係確認を検査対象にした。local preflight で出た保証質問の追加作業境界不足、quote_sent の購入前材料送付検知順、`届いていますか` の表記揺れを最小補修した。あわせて `eval-sources.yaml`、service-grounding sentry、timestamp-policy の runtime fixture に接続した
- きっかけ: 監査プロンプトに Pro後5レンズを追加したため、生成本体を変えずに外部監査の観点がノイズ化しないか確認する必要があった
- 想定効果: `bugfix-15000` live で、source traceability / commitment budget / semantic grounding drift / shadow-to-live contamination / evidence minimality を、hard rule 化せず監査観点として扱えるか確認できる
- 非変更: `handoff-25000` は public:false のまま。通常 live / #RE への 25,000円 / 主要1フロー / handoff 購入導線は出さない。Pro後5レンズは引き続き soft lens として扱う

### 2026-04-29 / CHG-132
- 分類: `reply-only`
- レイヤ: #RE bugfix46 r1 / accepted audit light revision
- 変更: bugfix46 r0 外部監査で採用圏・必須修正なしとなったため、軽微3点だけ r1 へ反映した。B01 は buyer が症状を書いている場面で聞き直さず、`この内容で進める場合は、そのままご購入ください` へ締めた。B03 は相手文にない `Webhookエラー` を足さず、`Stripe決済後に注文が作られない件` と buyer 文ベースへ戻した。B07 は補足説明を求める buyer に対し、追加質問を前提にせず、こちらで先に補足を整理する文へ寄せた
- きっかけ: r0 は private leak や hard boundary の崩れはなかったが、Pro後5レンズが拾った evidence minimality / semantic grounding drift / commitment budget の軽微な違和感が残っていた
- 想定効果: `bugfix-15000` live で、症状の聞き直し、相手文にない技術語の先読み、納品後補足の質問前提化を減らし、Pro後5レンズを soft lens として自然に活かせる
- 非変更: 新規 rule 追加はしない。`handoff-25000` は public:false のまま。通常 live / #RE への 25,000円 / 主要1フロー / handoff 購入導線は出さない

### 2026-04-29 / CHG-133
- 分類: `reply-only`
- レイヤ: #RE bugfix46 r1 accepted / B08 preference polish
- 変更: bugfix46 r1 外部再監査で採用・必須修正なしとなったため、B08 の `まず確認材料として見ます` だけを `まずは内容を確認します` へ自然化した
- きっかけ: `確認材料` は内部処理語に近く、送信用文面では少し硬く見えるという preference 指摘があった
- 想定効果: closed 後の関係確認で、内部ルール説明っぽさを減らし、購入者向けの自然な受けに寄せる
- 非変更: 新規 rule 追加はしない。closed 後に修正作業や修正済みファイル返却を進めない境界は維持する

### 2026-04-29 / CHG-134
- 分類: `reply-only`
- レイヤ: human audit / received-materials naturalization
- 変更: B05 の `確認しました` 直後に `はい、昨日のログとスクショは確認できています` と重ねる二重受領を、`ログとスクショありがとうございます` -> `昨日のログとスクショは届いています` へ修正した。あわせて `japanese-chat-natural-ja`、`docs/reply-quality/ng-expressions.ja.md`、`reply_quality_lint_common.py` に、`確認しました` / `受け取りました` 直後の機械的な `はい、〜確認できています` を避ける rule / lint を追加した
- きっかけ: 人間監査で、受領済みの文脈に `はい` を機械的に付けると日本語ネイティブには bot / AI 感が強く出ると指摘された
- 想定効果: purchased 中の受領確認で、同じ確認を二重に言わず、相手の行動への短い謝意 -> 受領事実 -> 次の流れ、の順に自然化できる
- 非変更: 受領確認、追加準備なし、次回時刻コミットの内容は変えない。`はい、` 全般を禁止するわけではなく、受領確認直後の重複だけを lint 対象にする

### 2026-04-29 / CHG-135
- 分類: `reply-only`
- レイヤ: #CL/#GE prompt naturalness lens
- 変更: `reply-review-prompt-ja` の単発返信文監査観点に、日本語ネイティブの実務者ならこの場面で言わなさそうな受け方、`確認しました` / `受け取りました` 直後の `はい、〜確認できています`、機械的な `はい、`、bot / AI っぽい受領確認・相づち・つなぎ語を標準観点として追加した。出力形式にも「日本語ネイティブの実務者なら言わなさそうな箇所」を追加した
- きっかけ: `#CL` だけでも、ユーザーが毎回補足しなくても bot 感や日本語実務違和感を拾えるようにしたいという要望があった
- 想定効果: Claude / Gemini への単発返信文監査で、内容の正しさだけでなく、日本のビジネスチャットとして送った時の違和感を標準で拾いやすくする
- 非変更: `reply-review-prompt-ja` は引き続き単発返信文監査専用。ChatGPT Pro への返信OS設計相談、ロードマップ分析、自然化レイヤ分析プロンプトには使わない。`はい、` 全般を禁止しない

### 2026-04-29 / CHG-136
- 分類: `reply-only`
- レイヤ: Pro後 jp business native naturalness / soft lens + lint narrowing
- 変更: Pro の自然化レイヤ分析を受け、bugfix-15000 と #BR の Codex xhigh 監査プロンプトへ `jp_business_native_naturalness` を soft lens として追加した。あわせて `reply_quality_lint_common.py` の `進め方` lint を blanket 検知から `進め方になります` / `進め方をお返しします` / `次の進め方をお返しします` / `その前提で進め方` などの PM 語彙寄りパターンに絞った。`tone-templates.ja.md` では `進め方は[手順]で進めます`、`ご共有ください`、`次の進め方をお返しします` を、より送信用に近い表現へ最小更新した
- きっかけ: Pro 分析で、日本語ビジネス自然化レイヤは必須だが、renderer ではなく意味保存型の最終整形・soft lens・狭い lint に置くべきと整理された。また `進め方` の blanket lint と古い tone template がノイズ源になり得ると指摘された
- 想定効果: `bugfix-15000` live / #BR の外部監査で、内容は正しいが bot / AI 感が出る文面を拾いやすくしつつ、`はい、` `まずは` `進め方` の全面禁止による過剰矯正を避ける
- 非変更: renderer の service / phase / scope / price / secret / public-private 判断は変更しない。`jp_business_native_naturalness` は hard fail ではなく soft lens として扱い、自然化のために支払い導線・作業可否・サービス境界を変えない

### 2026-04-29 / CHG-137
- 分類: `reply-only`
- レイヤ: #RE bugfix47 / post-Pro jp business native naturalness sentry
- 変更: `post-pro-native-naturalness-bugfix47.yaml` を追加し、`返信監査_batch-01.md` を `RE-2026-04-29-bugfix-47-post-pro-native-naturalness-r0` へ更新した。Pro後の `jp_business_native_naturalness` 確認走行として、曖昧相談、原因だけ診断圧力、quote_sent の支払い前材料送付、購入後の受領確認、短文進捗、キー名のみ共有、納品後の軽い補足、closed 後の関係確認を検査対象にした。local preflight で出た `作られません` の diagnosis-only 検知漏れ、短文進捗の重複、納品後/closed の機械的な `はい`、キー名共有の二重謝意を最小補修した。あわせて `eval-sources.yaml`、service-grounding sentry、timestamp-policy の runtime fixture に接続した
- きっかけ: 人間監査と Pro 分析で、内容は正しいが日本語ネイティブの実務チャットとして bot / AI 感が出る箇所を soft lens として継続検査する必要が明確になった
- 想定効果: `bugfix-15000` live で、二重受領、機械的な `はい`、確認語密集、購入者がすでに出した情報の聞き直し、phase / scope を壊さない範囲の自然化を継続確認できる
- 非変更: `handoff-25000` は public:false のまま。通常 live / #RE への 25,000円 / 主要1フロー / handoff 購入導線は出さない。自然化のために service / scope / price / secret / payment route の判断は変更しない

### 2026-04-29 / CHG-138
- 分類: `reply-only`
- レイヤ: #RE bugfix47 r1 / accepted audit light naturalization
- 変更: bugfix47 r0 外部監査で採用圏・必須修正なしとなったため、軽微3点だけ r1 へ反映した。B03 は `購入後に送ってください` と `お支払い完了後に送ってください` の重複を、支払い完了後の1文に圧縮した。B05 は短文進捗確認に対し、`いまは...確認しています` から `現時点では...見ている段階です` へ寄せ、予告より現在回答に近づけた。B08 は `ログやスクショを送っていただければ` と `ログやスクショを送ってください` の重複を避け、見立て可能範囲と送付依頼を分けた
- きっかけ: r0 は hard boundary と public leak は問題なかったが、日本語ビジネス自然化 lens として重複表現・進捗予告寄り表現に gold 寄せの余地があった
- 想定効果: `bugfix-15000` live で、支払い前/支払い後、購入後進捗、closed 後見立ての各文面が、意味を変えずにより自然で重複の少ない形になる
- 非変更: 新規 rule 追加はしない。`handoff-25000` は public:false のまま。通常 live / #RE への 25,000円 / 主要1フロー / handoff 購入導線は出さない

### 2026-04-29 / CHG-139
- 分類: `reply-only`
- レイヤ: #RE reviewer prompt / fixed audit output format
- 変更: `bugfix-15000` の Codex xhigh 監査プロンプトに、batch 側へ個別の出力形式がない場合でも使う固定出力形式を追加した。`結論 / 共通して良い点 / 危ない点 / ケース単位の必須修正 / 軽微修正 / 学習判定まとめ / rule 戻し / 採点 / まとめ` の順で返すようにし、必須修正なし・軽微修正なしの場合も明記させる
- きっかけ: bugfix47 の外部監査結果が採用圏として妥当だった一方、ログが短くなり、監査粒度が batch ごとに揺れる可能性が見えた
- 想定効果: #RE の外部監査で、hard fail がない場合でもケース判定・軽微指摘・採点・rule 戻し有無が安定して残る
- 非変更: 監査観点や生成ルールは変更しない。`jp_business_native_naturalness` は引き続き soft lens として扱い、好み差を hard fail 化しない

### 2026-04-29 / CHG-140
- 分類: `reply-only`
- レイヤ: #RE bugfix48 / live practical naturalness + fixed reviewer output sentry
- 変更: `live-practical-naturalness-bugfix48.yaml` を追加し、`返信監査_batch-01.md` を `RE-2026-04-29-bugfix-48-live-practical-naturalness-r0` へ更新した。監査プロンプト固定出力形式後の #RE として、金額＋納期、前任者不信、新機能追加吸収、quote_sent の本番反映確認、購入後ZIP/env値抜き、直接push/本番反映、delivered承諾、closed原因だけ圧力を検査対象にした。local preflight で出た金額のみ回答の納期抜け、`修正済みファイル` の quote_sent 検出漏れ、ZIP/env値抜き返信の二重謝意、直接push/本番反映否定の詰まり、delivered の機械的な `はい`、closed の `原因だけ先に` 検出漏れを最小補修した。あわせて `eval-sources.yaml`、service-grounding sentry、timestamp-policy の runtime fixture に接続した
- きっかけ: #RE 監査ログの粒度を固定した後、通常 live で実戦に近い buyer 質問と `jp_business_native_naturalness` が同時に安定するか確認する必要があった
- 想定効果: `bugfix-15000` live で、主質問への直答、phase 維持、secret safety、closed 後の実作業分離、自然な受領確認を同時に検査できる
- 非変更: `handoff-25000` は public:false のまま。通常 live / #RE への 25,000円 / 主要1フロー / handoff 購入導線は出さない。自然化のために service / scope / price / secret / payment route の判断は変更しない

### 2026-04-29 / CHG-141
- 分類: `reply-only`
- レイヤ: #RE bugfix48 r1 / price-and-timeline answer coverage
- 変更: bugfix48 r0 外部監査で B01 が必須修正となったため、価格＋納期の複合質問では `15,000円` とサービスページ上の目安 `3日` の両方を返すようにした。あわせて prequote renderer lint に `prequote_price_and_timeline` で `3日` が抜けたら落とす coverage check を追加した。軽微指摘として、B05 の `こちらから絞ってお願いします` を `必要なものだけこちらからお願いします` へ自然化し、B08 は概要未受領のまま固定時刻を約束せず、`送っていただいた範囲で、見立てを短くお返しします` へ寄せた
- きっかけ: 金額には答えていたが、buyer の `だいたい何日かかるか` への大まかな目安回答が落ちていた。サービスページ正本には `予想お届け日数 3日` があるため、購入前の複合質問では出すべき情報だった
- 想定効果: `費用＋期間` 型の prequote で片側 nonanswer を防ぎ、closed 後の材料未受領場面では受領前コミットを避けられる
- 非変更: 納期を保証するわけではなく、`3日` はサービス上の目安として扱う。`handoff-25000` は public:false のまま。通常 live / #RE への 25,000円 / 主要1フロー / handoff 購入導線は出さない

### 2026-04-29 / CHG-142
- 分類: `reply-only`
- レイヤ: #RE bugfix48 r1 accepted / B05 preference polish
- 変更: bugfix48 r1 外部再監査で採用圏・必須修正なしとなったため、B05 の `追加で必要なものが出たら、必要なものだけこちらからお願いします` を `追加で必要なものが出た場合は、必要なものだけこちらからお伝えします` へ軽く自然化した
- きっかけ: 意味と境界は安全だが、`こちらからお願いします` が実務文として少し不自然という preference 指摘があった
- 想定効果: secret 値を求めない境界と追加材料の最小化を維持したまま、購入者向けの自然な案内に寄せる
- 非変更: 新規 rule / lint は追加しない。単発の語感調整として扱う

### 2026-04-29 / CHG-143
- 分類: `reply-only`
- レイヤ: Deep Research + Pro後 conversation flow naturalness
- 変更: Deep Research と Pro 分析を受け、`japanese-chat-natural-ja` に `会話の流れを作る（意味保存）` を追加した。目的は文をやさしくすることではなく、短い受け止め -> 主質問への直答 -> 条件・理由 -> 次アクションの流れを、価格・scope・phase・secret・payment route を変えずに整えること。bugfix-15000 / #BR の監査プロンプトには `conversation_flow_naturalness` を soft lens として追加し、hard fail / fix recommended / preference の線引きを明記した。料金＋納期 renderer の代表文は `日数はサービス上3日が目安ですが、コードの状態やエラー内容によって前後します` に寄せ、`必要情報がそろい次第` を `コードとエラー内容を確認できた時点` へ具体化した。Gold Reply 36 と warning-only lint collector も追加した
- きっかけ: 人間監査で、句点の有無そのものではなく、短文断定が続いて会話の流れが切れるとマニュアル的・AI的に見える問題が見えた。Pro は、これを全面自然化ではなく、会話フロー補助レイヤとして限定採用すべきと整理した
- 想定効果: `bugfix-15000` live / #BR で、固定価格・範囲・phase・非公開境界を保ったまま、金額＋納期、受領確認、追加情報依頼、scope out、進捗報告、納品後補足、closed 後再相談の文章が会話として読みやすくなる
- 非変更: 句点「。」は全面禁止しない。`はい、` `まずは` `です` を blanket NG にしない。固定価格を `想定しています` に弱めない。renderer 全体を自然化エンジン化しない。warning lint は hard fail ではなく、監査・gold・human audit で扱う

### 2026-04-29 / CHG-144
- 分類: `reply-only`
- レイヤ: #RE bugfix49 / conversation flow naturalness sentry
- 変更: `conversation-flow-naturalness-bugfix49.yaml` を追加し、`返信監査_batch-01.md` を `RE-2026-04-29-bugfix-49-conversation-flow-naturalness-r0` へ更新した。Deep Research + Pro 後の確認走行として、金額＋納期、原因不明相談、quote_sent の支払い前診断、購入後の受領確認、短い進捗確認、secret 値なしのキー名共有、delivered の補足説明、closed 後の関係確認を検査対象にした。あわせて `eval-sources.yaml`、service-grounding sentry、timestamp-policy の runtime fixture に接続した
- きっかけ: 会話フロー補助レイヤを入れた後、通常 live の `bugfix-15000` で、自然化が境界を壊さず効いているかを外部監査にかける必要があった
- 想定効果: `conversation_flow_naturalness` が hard fail 化せず、短文断定の連続、確認語密集、次アクション不足、曖昧な待機条件を拾えるか確認できる
- 非変更: `handoff-25000` は public:false のまま。通常 live / #RE への 25,000円 / 主要1フロー / handoff 購入導線は出さない。自然化のために service / scope / price / secret / payment route の判断は変更しない

### 2026-04-29 / CHG-145
- 分類: `reply-only`
- レイヤ: #RE bugfix49 r1 / accepted conversation flow polish
- 変更: bugfix49 r0 外部監査で採用圏・必須修正なしとなったため、軽微4点だけ r1 へ反映した。B02 は原因不明相談に対して `原因が分からない状態でも相談できます` と先に直答し、15,000円の不具合修正へ自然につないだ。B04 は `こちらからお願いします` を `こちらからお伝えします` へ修正した。B05 は `まず状況を整理します` を避け、短い進捗希望に対して現在見ている箇所へ寄せた。B07 は `資料が少し難しかったとのこと、確認しました` を `確認手順が少し分かりにくかったとのこと、承知しました` へ自然化した。B02 は Gold 36 に anchor として追加した
- きっかけ: r0 は hard boundary と public leak に問題はなかったが、conversation_flow_naturalness の soft lens として、処理語の硬さ・主質問直答の薄さが残っていた
- 想定効果: `bugfix-15000` live で、原因不明相談、受領確認、短い進捗確認、納品後補足が、意味と境界を変えずに実務チャットとして自然になる
- 非変更: 新規 hard rule は追加しない。`conversation_flow_naturalness` は引き続き soft lens として扱う。句点・`はい`・`まず` を blanket NG にしない

### 2026-04-29 / CHG-146
- 分類: `reply-only`
- レイヤ: #RE bugfix49 r2 / human audit B08 closed flow repair
- 変更: 人間監査で B08 の closed 後関係確認が、安全境界は守れている一方で `まずは内容を確認します`、`ログやスクショを送ってください`、`見立てを短くお返しします` などの部品列挙になっていると判明したため、`closed_materials_check` renderer を修正した。先に `ログやスクショは、このメッセージで送っていただいて大丈夫です` と主質問へ答え、届いた範囲で前回修正との関係を見立てる文に圧縮し、その後で closed 境界と実作業時の見積り提案 / 新規依頼を示す順番へ変更した。Gold Reply 36 と `japanese-chat-natural-ja` に closed 後の関係確認 anchor を追加し、warning-only lint には旧型の `閉じているため` + `ログやスクショを送ってください` + `見積り提案または新規依頼` の部品列挙を拾う警告を追加した
- きっかけ: 外部監査では採用圏だったが、送信用文面として見ると句点で区切られた安全部品の羅列になり、Deep Research / Pro で狙った `会話の流れ` が B08 に届いていなかった
- 想定効果: `bugfix-15000` live の closed 後相談で、旧トークルーム継続・無料修正・修正済みファイル返却を約束せずに、buyer の「ここに送ってよいか」へ自然に答えられる
- 非変更: `conversation_flow_naturalness` は引き続き soft lens / warning として扱う。句点「。」を blanket NG にしない。closed 後に実作業や修正済みファイル返却をこの場で約束しない。`handoff-25000` は public:false のまま通常 live / #RE へ出さない

### 2026-04-29 / CHG-147
- 分類: `reply-only`
- レイヤ: #RE bugfix49 r3 / renderer-level chat flow repair
- 変更: r2 でも batch 全体が `安全パーツを段落ごとに並べた文章` に見えていたため、B01/B02/B03/B04/B05/B06/B07 の各 renderer も会話型の段落へ寄せた。B01 は金額・対象不具合・3日目安を自然につなぎ、B02 は原因不明相談と15,000円案内を1段落にまとめた。B03 は quote_sent で `提案内容と...の件ですね` を外し、支払い前原因確認不可と購入後開始を同じ段落で説明した。B04 は受領確認と今後の確認行動を接続し、B05 は短い進捗希望に対して `先に現状だけお伝えします` から入る形へ修正した。B06 は `値の方` を `値そのもの` へ自然化し、B07 は `補足できます -> 補足はこちらで整理します` の重複を、承諾前の確認ポイント補足としてまとめた。`返信監査_batch-01.md` を r3 へ更新し、Gold Reply 36 も r3 の代表文へ差し替えた
- きっかけ: ユーザー監査で、Deep Research / Pro 後にもかかわらず `。` で区切られた処理文が多く、チャット文として流れていないと判明した
- 想定効果: `conversation_flow_naturalness` を後処理だけでなく renderer の段落設計へ戻し、#RE r0/r1 で出る文章そのものをチャット寄りにする
- 非変更: 句点や短文を blanket NG にしない。価格・scope・phase・secret・支払い導線・作業可否の判断は変えない。`handoff-25000` は public:false のまま通常 live / #RE へ出さない

### 2026-04-29 / CHG-148
- 分類: `reply-only`
- レイヤ: #RE/#R alignment / renderer provenance
- 変更: Pro の `返信OS品質監査4-29` を受け、`render-coconala-reply.py` の #RE 出力に `candidate_source / audit_target / contract_source / writer_used / naturalizer` を明示するようにした。現行 #RE 候補は `renderer_baseline`、`writer_used=false`、`naturalizer=identity_only` と表示される。`closed_materials_check` には `semantic_slots` を持たせ、HRC49-008 fixture に `expected_semantics` を追加した。`check-reply-projection-warnings.py` は統合 pipeline 経由の出力を見るように変更し、監査プロンプトには `renderer_baseline` の自然さ指摘をすぐ共通 rule 化しない注意を追加した
- きっかけ: #RE の文面が安全パーツの組み立てになり、#R より不自然に見える問題が発生した。Pro は、現行 #RE が #R 実返信品質ではなく deterministic renderer の文面品質を監査している状態に近いと指摘した
- 想定効果: 人間監査と外部監査で、いま見ている候補が #R 相当の writer 候補なのか renderer baseline なのかを取り違えにくくなる。#RE only の自然さ問題を共通 skill / rule に戻しすぎて #R の思考を削る事故を防ぐ
- 非変更: 本物の LLM writer stage はまだ自動化しない。現時点で `writer_v1` と偽装せず、renderer baseline として明示する。service-registry / platform-contract / service facts の hard boundary は変更しない。`handoff-25000` は public:false のまま通常 live / #RE へ出さない

### 2026-04-29 / CHG-149
- 分類: `reply-only`
- レイヤ: #RE/#R alignment / writer brief + manual candidate validation
- 変更: `render-coconala-reply.py` に `--writer-brief` と `--candidate-file` を追加した。`--writer-brief` は固定 fixture から buyer 原文、service facts、reply_contract、response_decision_plan、semantic slots、expected semantics、write rules をまとめ、#R 相当の writer candidate を作るための意味契約を出力する。`--candidate-file` は手動で作った writer candidate を同じ fixture / contract / lint / expected semantics で検査し、`candidate_source: writer_candidate_manual` として provenance を表示する。`ops/tests/README.ja.md` と `docs/reply-quality/README.ja.md` に運用を追記した
- きっかけ: `#RE` と `#R` の出力経路がズレると、人間監査の指摘が #R 本丸に効かない、または本来問題ない #R を過剰矯正するリスクがあると判明した
- 想定効果: renderer baseline の違和感を見つけた時に、同じ fixture から writer brief を出し、#R 相当の候補でも再現するかを検証できる。#RE only / #R reproduced / safety deterministic / preference の切り分けが実装運用上可能になる
- 非変更: LLM writer の自動呼び出しはまだ行わない。writer candidate は Codex / 人間が brief を見て作る手動候補として扱う。自然化 warning は hard fail 化しない

### 2026-04-29 / CHG-150
- 分類: `reply-only`
- レイヤ: #RE/#R alignment / writer candidate batch validation
- 変更: `render-coconala-reply.py` に `--candidate-batch-file` を追加し、`#RE` markdown batch 内の `stock_id` と `返信候補` を読み取って、各返信候補を `writer_candidate_manual` として同じ fixture / contract / lint に通せるようにした。`返信監査_batch-01.md` は r6 として、監査対象を `renderer_baseline` ではなく `writer_candidate_manual` に修正し、batch 全体の検証コマンドを明記した
- きっかけ: 仕組み上は writer brief と単体 candidate 検証ができても、実際の監査 batch のメタデータが `renderer_baseline` のままだと、監査者が #R 本丸ではない文章を見て自然さ指摘を戻すリスクが残るため
- 想定効果: 外部監査に出す batch の候補が、#R 相当の writer 候補なのか renderer baseline なのかを取り違えにくくなる。人間監査で見つけた自然さの問題を、本丸に戻してよいか判断しやすくなる
- 非変更: LLM writer stage はまだ自動化しない。`--candidate-batch-file` は batch 内に明示された手動 writer 候補を検証する入口であり、定形文生成を増やすものではない

### 2026-04-29 / CHG-151
- 分類: `reply-only`
- レイヤ: #RE/#R alignment / Pro checklist
- 変更: `docs/reply-quality/re-alignment-checklist-20260429.ja.md` を追加し、Pro の `返信OS品質監査4-29` で出た `#RE / #R` 生成経路ズレ、renderer 責務過多、naturalizer identity 状態を、反映済み / 一部反映 / 未反映のチェックリストに整理した。`README.ja.md` からも参照できるようにし、古い「#RE は生成本体の再設計ではない」という説明を、`writer_candidate` へ寄せる移行中という説明へ更新した
- きっかけ: `#R` 実出力では自然化が効いている一方、`#RE` の renderer baseline が本丸より機械的に見える問題があり、次の作業順を曖昧にしない必要があった
- 想定効果: 次回以降、外部監査へ出す前に `#R` スモーク、writer candidate 化、batch validation、戻し先分類の順で進められる。`#RE only` の自然さ問題を共通 skill へ戻しすぎる事故を防ぐ
- 非変更: 自動 LLM writer stage はまだ実装しない。チェックリストは実装順と運用判断の正本であり、renderer に固定文を増やすものではない

### 2026-04-29 / CHG-152
- 分類: `reply-only`
- レイヤ: #RE revival / #R smoke style anchors
- 変更: `#R` スモークで自然に出た 5 件を `docs/reply-quality/r-smoke-style-anchors-20260429.ja.md` として保存し、`返信監査_batch-01.md` を r7 に更新した。r7 では B01/B02/B04/B05/B06/B07/B08 を中心に、サービスページ調・処理文調ではなく、相手文を1点拾って主質問へ答える `#R` 相当 writer candidate に寄せた。`README.ja.md` と `re-alignment-checklist-20260429.ja.md` も更新し、style anchor がテンプレではなく writer 判断の基準であることを明記した
- きっかけ: `#RE` を学習場として復活させるには、監査候補が本丸 `#R` より機械的なままでは不十分だったため。`#R` スモークでは Deep Research / Pro 後の会話自然化が効いており、その標準を `#RE` writer candidate 側へ合わせる必要があった
- 想定効果: `#RE` で自然さを監査した時に、renderer baseline の癖ではなく、実際の `#R` に近い文面品質を見られる。今後の外部監査結果を `#R reproduced / #RE only / safety deterministic / preference` に分けやすくなる
- 非変更: style anchor は Gold Reply や固定テンプレではない。renderer に職人風の固定文を大量登録しない。`handoff-25000` は public:false のまま通常 live / #RE へ出さない

### 2026-04-29 / CHG-153
- 分類: `reply-only`
- レイヤ: #RE bugfix50 / realistic live writer candidate batch
- 変更: 実際に来そうな `bugfix-15000` live 相談文として `live-realistic-r-smoke-bugfix50.yaml` を追加し、`返信監査_batch-01.md` を `RE-2026-04-29-bugfix-50-realistic-live-r-smoke-r0` に更新した。価格・範囲・納期、急ぎと成功保証圧力、複数症状、購入前 GitHub 招待、購入後 secret-safe 材料、短い進捗確認、delivered 後の同症状、closed 後の前回修正との関係確認を検査対象にした。batch は `writer_candidate_manual` とし、`candidate-batch-file` 検証で 8 件通過した。あわせて eval-sources と service-grounding sentry に接続した
- きっかけ: r7 採用後、さらに実戦で来そうな文章を使って、#RE が本丸 #R に近い学習場として機能するか確認する必要があった。closed 後のスクショ相談では、action-first で「このメッセージで送って大丈夫です」と先に答える方が自然なため、closed renderer / checker も同じ意味契約へ寄せた
- 想定効果: 人間監査と外部監査で、実務に近い相談文に対して `#R` 相当の返信品質、public:false 境界、secret safety、phase 境界、会話フロー自然さを同時に見られる。closed 後の資料送付可否で、感謝や状態説明より先に主質問へ答える型を検査できる
- 非変更: `handoff-25000` は public:false のまま通常 live / #RE へ出さない。`writer_candidate_manual` は固定テンプレではなく、fixture の意味契約をもとに作った監査候補として扱う。conversation flow は soft lens のままで、句点や短文を blanket NG にしない

### 2026-04-29 / CHG-154
- 分類: `reply-only`
- レイヤ: #RE bugfix50 r1 / minor precision polish
- 変更: 外部監査で `RE-2026-04-29-bugfix-50-realistic-live-r-smoke-r0` が採用圏・必須修正なしとなったため、B03 のみ軽微修正した。複数症状相談で buyer が優先度を明示していないのに `一番困っている` と推測していた箇所を、`まずは「注文が作られない」症状を起点に見る形でよければ` へ変更した
- きっかけ: scope / price 事故ではないが、相手が言っていない優先度をこちらで断定しない方が `jp_business_native_naturalness` と grounding の両面で安定するため
- 想定効果: 複数症状の入口で、buyer の優先順位を断定せず、こちらの確認起点だけを自然に提示できる
- 非変更: 新規 rule は追加しない。固定価格・複数症状の同一原因判定・別原因時の事前相談の扱いは変更しない

### 2026-04-29 / CHG-155
- 分類: `reply-only`
- レイヤ: #RE bugfix50 r2 / guarantee vs deliverable wording
- 変更: B02 の成功保証圧力に対する返信で、`確実に直ることまではお約束できません` の直後に `原因確認から修正済みファイルの返却まで進められます` と続けると、成功保証を否定しながら修正完了を約束しているように読めるため、`まず原因確認から進められます。修正できる箇所が特定できた場合は、修正済みファイルをお返しします` へ修正した
- きっかけ: 人間監査で、論理上は「作業範囲」と「成功保証」の違いでも、buyer 視点では矛盾に見える可能性があると分かったため
- 想定効果: 急ぎ・成功保証圧力の場面で、保証断定を避けつつ、15,000円の不具合修正として原因確認から入ることと、修正可能時の成果物を自然に分けて案内できる
- 非変更: 15,000円、不具合1件、修正済みファイル返却というサービス軸は変更しない。購入前に成功保証・返金保証・原因断定はしない

### 2026-04-29 / CHG-156
- 分類: `reply-only`
- レイヤ: promise_consistency / soft lens rollout
- 変更: Pro の `Promise Consistency Analysis4-29` を受け、`promise_consistency` を #RE / #BR の外部監査プロンプトへ soft lens として追加した。1文ごとの事実ではなく、留保・不可・条件付き回答を後段の成果物・納期・料金・次アクションが上書きして見えないかを確認する。subtype は `success_guarantee_shadow / deliverable_promise_shadow / diagnosis_assertion_drift / phase_promise_drift / secret_request_contradiction / closed_work_promise / scope_bundle_promise / payment_scope_promise / production_action_shadow` とした。あわせて `docs/reply-quality/promise-consistency-lens-20260429.ja.md` と Gold 37 を追加し、今回の成功保証 shadow 修正文を gold anchor として保存した
- きっかけ: #RE bugfix50 の B02 で、成功保証を否定した直後に修正済みファイル返却まで無条件に進めるように読める接続が見つかった。既存の scope / phase / secret / naturalness では拾い切れない「約束レベルの接続」だったため
- 想定効果: #RE / #BR で、文章単体は安全でも buyer に未約束の約束として読まれる drift を拾える。hard boundary を弱めず、固定価格・対応可能範囲・購入後開始できる作業は明確に保ったまま、未確認の成果だけ条件づけられる
- 非変更: hard validator / renderer rule / lint はまだ追加しない。`進められます`、`対応できます`、`修正済みファイル` を blanket NG にしない。`japanese-chat-natural-ja` へ common rule としてはまだ戻さない。ng-expressions への追加は同型再発後に判断する

### 2026-04-29 / CHG-157
- 分類: `reply-only`
- レイヤ: #RE bugfix51 / promise_consistency rehearsal
- 変更: `promise-consistency-bugfix51.yaml` を追加し、`返信監査_batch-01.md` を `RE-2026-04-29-bugfix-51-promise-consistency-r0` へ更新した。成功保証と未修正時対応、固定価格と修正完了保証、複数症状の条件付き scope、quote_sent の購入前原因確認、secret 値不要、原因未確定と今日中成果物、delivered の承諾前再確認、closed 後の関係確認と実作業分離を検査対象にした。batch は `writer_candidate_manual` とし、候補文 8 件を candidate-batch lint に通した。fixture は eval-sources と service-grounding sentry に接続した
- きっかけ: `promise_consistency` を監査プロンプトへ soft lens として追加した直後に、実際に同レンズがノイズ化せず live bugfix 文脈で機能するかを見る必要があったため
- 想定効果: #RE で、成功保証 shadow、条件付き scope の曖昧化、購入前着手 promise、secret request contradiction、diagnosis assertion drift、closed work promise を本番 #R 寄りの候補文で監査できる
- 非変更: `promise_consistency` は引き続き soft lens。lint / renderer rule / ng-expressions への追加はまだ行わない。`handoff-25000` は public:false のまま通常 live / #RE へ出さない

### 2026-04-29 / CHG-158
- 分類: `reply-only`
- レイヤ: #RE bugfix51 r1 / prequote next action polish
- 変更: 外部監査で `RE-2026-04-29-bugfix-51-promise-consistency-r0` が採用圏・必須修正なしとなったため、B02 のみ軽微修正した。固定価格と修正完了保証の説明後、prequote として次アクションが少し弱かったため、末尾に `この前提で問題なければ、そのままご購入ください` を追加した
- きっかけ: promise consistency / scope / price は崩れていなかったが、購入前返信として buyer が次に進む導線を明確にする余地があったため
- 想定効果: 15,000円の内容、未確認の修正完了保証をしない線、修正済みファイル返却条件を保ったまま、prequote の締めが自然になる
- 非変更: 新規 rule は追加しない。`promise_consistency` の lint / ng / renderer 反映はまだ行わない

### 2026-04-30 / CHG-159
- 分類: `reply-only`
- レイヤ: #RE bugfix52 / promise_consistency second pass
- 変更: `promise-consistency-bugfix52.yaml` を追加し、`返信監査_batch-01.md` を `RE-2026-04-30-bugfix-52-promise-consistency-r0` へ更新した。保証圧力、3症状の条件付き scope、quote_sent の GitHub / `.env` 値圧力、購入後の原因候補と今日中成果物、secret-safe 材料、作業中の追加症状、delivered の修正ファイル側/反映側確認、closed 後の前回修正との関係確認と無償修正圧力を検査対象にした。batch は `writer_candidate_manual` とし、候補文 8 件を candidate-batch lint に通した。fixture は eval-sources と回帰に接続し、full regression も通過した
- きっかけ: `promise_consistency` を1回の成功保証 shadow だけで終わらせず、複数症状、secret、phase、delivered / closed の約束ズレにも効くかを見る必要があったため
- 想定効果: #RE で、未確定・条件付き・購入後開始・値不要・closed 後境界を後段の成果物/導線が上書きして見えないかを、より実戦寄りの buyer 文で監査できる。`conditional_scope_clarity` も補助観点として観察できる
- 非変更: `promise_consistency` は引き続き soft lens。lint / renderer rule / ng-expressions への追加はまだ行わない。`handoff-25000` は public:false のまま通常 live / #RE へ出さない

### 2026-04-30 / CHG-160
- 分類: `reply-only`
- レイヤ: #RE bugfix53 / promise_consistency + ack_to_answer_bridge observation
- 変更: 外部監査で `RE-2026-04-30-bugfix-52-promise-consistency-r0` が採用・必須修正なし・軽微修正なし・9.6/10 となったため、次 batch として `promise-bridge-bugfix53.yaml` を追加し、`返信監査_batch-01.md` を `RE-2026-04-30-bugfix-53-promise-bridge-r0` へ更新した。`promise_consistency` と `conditional_scope_clarity` を継続しつつ、状態受けから主回答へ飛ばない短い橋として `ack_to_answer_bridge` を観察項目に加えた。batch は `writer_candidate_manual` とし、候補文 8 件を candidate-batch lint に通した。fixture は eval-sources と回帰に接続し、full regression も通過した
- きっかけ: 人間監査で、他者修正失敗後の不安を受けた直後に `コードとエラー内容を見る前に...` と判定文へ飛ぶと、意味は正しくてもパーツ感が残ると分かったため
- 想定効果: `promise_consistency` で約束レベルを整えたまま、`その点については`、`ご購入後は` などの短い橋を使って、状態受け・主回答・条件・次アクションが会話として自然につながるかを #RE で観察できる
- 非変更: `ack_to_answer_bridge` は正式 hard lens ではない。`conversation_flow_naturalness` の下位観点として batch 観察に留める。lint / renderer rule / ng-expressions への追加はまだ行わない。`handoff-25000` は public:false のまま通常 live / #RE へ出さない

### 2026-04-30 / CHG-161
- 分類: `reply-only`
- レイヤ: #RE bugfix54 / permission_benefit_alignment observation
- 変更: 外部監査で `RE-2026-04-30-bugfix-53-promise-bridge-r0` が採用圏・必須修正なしとなった一方、人間監査で B04 の `ログや関連コードは、お支払い完了後で大丈夫です` が seller 側の許可調に見えると分かったため、`permission-benefit-alignment-bugfix54.yaml` を追加し、`返信監査_batch-01.md` を `RE-2026-04-30-bugfix-54-permission-benefit-alignment-r0` へ更新した。`大丈夫です` を全面禁止せず、buyer の負担を軽くする用法と、支払い・購入・材料送付で seller が buyer の負担を許可しているように見える用法を分けて観察する
- きっかけ: `大丈夫です` は便利で自然な場面も多いが、支払い後材料共有の案内で使うと、buyer が負担する支払い・作業を seller が「許可」しているように読める可能性があるため
- 想定効果: secret 値不要など buyer 負担を減らす `大丈夫です` は残しつつ、支払い・購入・作業開始の導線では `共有してください` `共有いただければ、そこから確認に入ります` のような手順表現へ寄せられるかを #RE で観察できる
- 非変更: `permission_benefit_alignment` は正式 hard lens ではない。`大丈夫です` の blanket ban、lint 化、skill への恒久反映はまだ行わない。`handoff-25000` は public:false のまま通常 live / #RE へ出さない

### 2026-04-30 / CHG-162
- 分類: `reply-only`
- レイヤ: #RE bugfix55 / soft refusal and payment-flow naturalness
- 変更: 外部監査で `RE-2026-04-30-bugfix-54-permission-benefit-alignment-r0` が採用・必須修正なし・軽微修正なしとなった一方、人間監査で `支払い前にスクショを送っていただいて、こちらで確認を先に始める形ではありません` のような否定フレームが協力的な buyer には冷たく見えると分かったため、`soft-refusal-payment-flow-bugfix55.yaml` を追加し、`返信監査_batch-01.md` を `RE-2026-04-30-bugfix-55-soft-refusal-payment-flow-r0` へ更新した。`permission_benefit_alignment` に加え、不要な否定フレームを避け、支払い・材料共有を手順として自然に案内できるかを検査する
- きっかけ: phase boundary は必要でも、buyer が単に材料共有のタイミングを確認している場面では、拒否文から入るより `お支払い完了後にトークルームで共有いただければ進められます` のような手順案内の方が実務チャットとして自然なため
- 想定効果: 支払い前作業開始・購入前コード確認・成功保証・secret 値要求を防ぎつつ、協力的な buyer への返信が防御的になりすぎないかを #RE で観察できる。`unnecessary_refusal_frame` は Pro 分析キューに追加し、まだ hard rule 化しない
- 非変更: `〜する形ではありません` の blanket ban はしない。強い要求・規約違反・secret値・外部誘導などは引き続き明確に止める。`handoff-25000` は public:false のまま通常 live / #RE へ出さない

### 2026-04-30 / CHG-163
- 分類: `reply-only`
- レイヤ: #RE bugfix55 r1 / GitHub invite boundary
- 変更: Codex xhigh 監査および人間監査で、B03 の `コード一式の zip や GitHub 招待は、お支払い完了後にトークルームで共有いただければ進められます` が、GitHub 招待を購入後に受ける前提に読めると判定されたため、B03 を `コードは、お支払い完了後にトークルームで共有できる形でお願いします。zip か、関係ファイルをまとめた形で進められます。GitHub上でのやり取りは使わず、確認や連絡はこのトークルーム内で進めます` へ修正した。あわせて `coconala-reply-bugfix-ja` に、GitHub 招待 / 外部リポジトリ上の Issue / PR / コメントを通常の材料共有や作業面として受けないことを明記した
- きっかけ: 既存の共通ガードには `GitHubに招待してください` 禁止があるが、#RE の writer_candidate_manual 作成時に、`GitHub 招待` をコード共有方法の一つとして扱ってしまったため
- 想定効果: 外部共有・外部作業面へ寄せず、コード共有はココナラのトークルーム内 ZIP / 関係ファイル添付へ寄せる。公開URL・非公開招待・PR/Issue作業・直接pushが混ざる事故を減らす
- 非変更: `GitHub` という単語自体を blanket NG にはしない。buyer が言及した場合は、必要なら `GitHub上でのやり取りは使わず` と境界を示し、ココナラ内の代替共有へ戻す

### 2026-04-30 / CHG-164
- 分類: `reply-only`
- レイヤ: #RE bugfix56 / GitHub external work-surface rehearsal
- 変更: `github-external-work-surface-bugfix56.yaml` を追加し、`返信監査_batch-01.md` を `RE-2026-04-30-bugfix-56-github-external-work-surface-r0` へ更新した。公開GitHub URL、非公開GitHub招待、購入後のGitHub招待/PRコメント、直接push/本番反映、Google Drive共有、zip共有、delivered の PR コメント要求、closed 後の GitHub招待相談を検査対象にした。batch は `writer_candidate_manual` とし、候補文 8 件を candidate-batch lint に通した
- きっかけ: `GitHub 招待` を外向け live で材料共有の一種として受けると、外部共有・外部作業面・外部連絡に寄る危険があるため、単発修正ではなく複数 phase で再検査する必要があった
- 想定効果: GitHub という単語を blanket NG にせず、公開URL・非公開招待・PR/Issue作業・直接push・本番反映・Drive共有を切り分け、ココナラ内の zip / 関係ファイル添付へ自然に戻せるかを #RE で監査できる
- 非変更: `GitHub` の全禁止、公開URLへの過剰反応、外向けに「規約違反」と断定する文面は追加しない。`handoff-25000` は public:false のまま通常 live / #RE へ出さない

### 2026-04-30 / CHG-165
- 分類: `reply-only`
- レイヤ: #RE bugfix57 / mixed boundary naturalness rehearsal
- 変更: `mixed-boundary-naturalness-bugfix57.yaml` を追加し、`返信監査_batch-01.md` を `RE-2026-04-30-bugfix-57-mixed-boundary-naturalness-r0` へ更新した。価格＋納期＋成功保証、quote_sent の Drive / GitHub 共有タイミング、購入後 zip 内 secret 値混入、直接push / 本番反映、複数症状と追加料金不安、原因候補と今日中成果物圧、delivered の軽い補足とFAQ/運用マニュアル境界、closed 後の外部共有と費用相談を検査対象にした。batch は `writer_candidate_manual` とし、候補文 8 件を candidate-batch lint に通した
- きっかけ: GitHub 境界を単独で鍛えた後、promise consistency / conditional scope / secret safety / external work surface / naturalness が同じ返信内で衝突しないかを、より実戦に近い混合ケースで確認する必要があったため
- 想定効果: #RE が単一レンズの確認だけでなく、公開直前の live 実戦に近い複合質問でも #R 相当の文章を監査できる。外部共有を止めつつ冷たすぎない案内、secret 値混入時の安全な戻し方、成功保証と成果物条件の分離、closed 後の概要見立てと実作業導線の分離をまとめて検査できる
- 非変更: 無料修正圧は今回の混合 batch では `費用発生前の相談` に落として扱い、closed 後の無料修正 promise 専用 batch はまだ作らない。`handoff-25000` は public:false のまま通常 live / #RE へ出さない

### 2026-04-30 / CHG-166
- 分類: `reply-only`
- レイヤ: #RE bugfix57 r1 / GitHub invite work-surface fix
- 変更: 外部監査で `RE-2026-04-30-bugfix-57-mixed-boundary-naturalness-r0` の B04 が必須修正となったため、`返信監査_batch-01.md` を `RE-2026-04-30-bugfix-57-mixed-boundary-naturalness-r1` へ更新した。B04 は、直接 push と本番反映を行わないだけでなく、GitHub招待を作業場所にしないこと、今回の不具合に関係するコードやログを zip または関係ファイルとしてトークルーム内で共有してもらうことを明示した。あわせて B02 は ZIP共有時に秘密値を含めない一言を追加し、B03 は secret 混入疑いのある zip ではなく送り直し分をもとに確認する文面へ締めた
- きっかけ: `push はしない` とだけ返すと、GitHub上で確認する余地が残り、GitHub招待を外部作業面として受けるように読めるため
- 想定効果: GitHub招待・直接push・本番反映が同じ相談内で出ても、外部作業面へ乗らず、ココナラ内の zip / 関係ファイル共有、修正済みファイルまたは差分返却、依頼者側の本番反映という境界を安定して出せる
- 非変更: 新規 rule 化はまだ行わない。既存の GitHub invite boundary / external work surface guard の運用強化として扱う。`GitHub` という単語自体を blanket NG にはしない

### 2026-04-30 / CHG-167
- 分類: `reply-only`
- レイヤ: #RE bugfix58 / closed free-refund boundary rehearsal
- 変更: `closed-free-refund-boundary-bugfix58.yaml` を追加し、`返信監査_batch-01.md` を `RE-2026-04-30-bugfix-58-closed-free-refund-boundary-r0` へ更新した。closed 後の同じエラー無料対応圧、返金・キャンセル語、旧トークルーム内のおひねり追加、原因だけ先見、closed 後 secret 値送付、repeat price、delivered 承諾前の同症状確認、closed 後の次回相談導線を検査対象にした。batch は `writer_candidate_manual` とし、候補文 8 件を candidate-batch lint に通した
- きっかけ: `bugfix57` で外部作業面・secret・保証・closed 後導線が採用圏になったため、次に実務事故になりやすい closed 後の無料修正・返金・キャンセル・旧トークルーム継続圧を厚めに見る必要があったため
- 想定効果: クローズ後でも buyer の不満を受けながら、無料対応 / 再度15,000円 / 返金 / キャンセルを確認前に断定せず、メッセージ上の概要見立てと実作業前の相談へ自然に分けられるかを #RE で監査できる
- 非変更: 返金やキャンセルの法務・プラットフォーム判断をこちらで断定しない。closed 後に旧トークルームの続きとして実作業や修正済みファイル返却を約束しない。`handoff-25000` は public:false のまま通常 live / #RE へ出さない

### 2026-04-30 / CHG-168
- 分類: `reply-only`
- レイヤ: #RE bugfix58 r1 / closed minor clarity fixes
- 変更: 外部監査で `RE-2026-04-30-bugfix-58-closed-free-refund-boundary-r0` が採用圏・必須修正なしとなったため、軽微3点のみ反映し、`返信監査_batch-01.md` を `RE-2026-04-30-bugfix-58-closed-free-refund-boundary-r1` へ更新した。B01 は確認材料の依頼を直接化し、B02 は前回トークルームが閉じていることを1文で明示し、B03 は同一原因未確認の段階で `別件修正` と断定しないよう `修正作業` へ差し替えた
- きっかけ: closed 後の無料対応・返金・キャンセル・旧トークルーム継続の主要境界は守れていたが、buyer の次アクションと誤読防止を少し上げる余地があったため
- 想定効果: closed 後に、概要確認で何を送ればよいかが明確になり、返金/キャンセルやおひねり追加の圧力にも、同一原因・別件・費用発生を確認前に断定しない文面を維持できる
- 非変更: 新規 rule 化はしない。今回の修正は case_fix として扱い、既存の closed boundary / promise_consistency / transaction model guard を維持する

### 2026-04-30 / CHG-169
- 分類: `reply-only`
- レイヤ: #RE bugfix59 / prepurchase urgency anxiety rehearsal
- 変更: `prepurchase-urgency-anxiety-bugfix59.yaml` を追加し、`返信監査_batch-01.md` を `RE-2026-04-30-bugfix-59-prepurchase-urgency-anxiety-r0` へ更新した。初めての依頼者の価格/流れ/保証不安、急ぎの今日中復旧圧、quote_sent の支払い前材料共有、原因だけ先見、自分で触った後の追加料金不安、今日中の見通し確認、purchased の納期不安、追加症状と追加料金不安を検査対象にした。batch は `writer_candidate_manual` とし、候補文 8 件を candidate-batch lint に通した。fixture は eval-sources と回帰に接続し、full regression も通過した
- きっかけ: closed/free/refund 境界が採用圏に入ったため、次に実務で多い購入直前・見積り提案後の迷いと急ぎ/保証圧を厚めに見る必要があったため
- 想定効果: 初めての buyer に流れを見せつつ、15,000円・購入後開始・成功保証不可・今日中復旧不可・追加料金未断定を矛盾なく自然に案内できるかを #RE で監査できる
- 非変更: 先払い前の原因調査、診断だけ安価入口、今日中の修正完了保証、`handoff-25000` の live 導線は追加しない

### 2026-04-30 / CHG-170
- 分類: `reply-only`
- レイヤ: #RE bugfix59 r1 / urgency and extra-fee clarity fixes
- 変更: 外部監査で `RE-2026-04-30-bugfix-59-prepurchase-urgency-anxiety-r0` が採用圏・必須修正なしとなったため、B05/B06 の軽微2点を反映し、`返信監査_batch-01.md` を `RE-2026-04-30-bugfix-59-prepurchase-urgency-anxiety-r1` へ更新した。B05 は、自分で触った後の追加料金不安に対して、別原因や追加対応が必要な場合も進める前に対応方法と費用を相談する文を追加した。B06 は、今日中の修正完了は保証しないまま、お支払い後に材料がそろえば原因の方向性と次の見通しをできるだけ早く返す形へ直答を補強した
- きっかけ: 主要境界は守れていたが、追加料金不安の buyer に「勝手に追加されない」こと、急ぎ buyer に「今日中に見通しまで返るか」への答えがもう少し明確な方が実務上安心できるため
- 想定効果: 追加料金を断定せず事前相談へ戻し、今日中復旧保証にも寄らず、急ぎの相談で返せるものを `原因の方向性と次の見通し` として自然に示せる
- 非変更: 新規 rule 化はしない。支払い前原因確認、今日中修正完了保証、追加料金の自動確定、`handoff-25000` の live 導線は追加しない

### 2026-04-30 / CHG-171
- 分類: `reply-only`
- レイヤ: #RE bugfix60 / live practical trust mixed rehearsal
- 変更: `live-practical-trust-bugfix60.yaml` を追加し、`返信監査_batch-01.md` を `RE-2026-04-30-bugfix-60-live-practical-trust-r0` へ更新した。実際に来そうな初回相談、quote_sent の zip / secret-safe 材料共有、購入後の進捗催促、原因候補と今日中修正圧、送り忘れファイルと追加料金不安、delivered の軽い反映箇所補足、closed 後の無料/新規迷いを検査対象にした。batch は `writer_candidate_manual` とし、候補文 8 件を candidate-batch lint に通した。fixture は eval-sources と回帰に接続し、full regression も通過した
- きっかけ: bugfix59 で購入直前・見積り提案後の不安が採用圏に入ったため、次に実務で混ざりやすい信頼不安・進捗催促・原因確定圧・納品後軽い確認・closed後迷いをまとめて見る必要があったため
- 想定効果: サービス内容と取引状態を踏まえた送信直前候補として、成功保証・今日中修正保証・支払い前作業・secret値・本番反映・無料/新規断定を避けつつ、自然な実務返信を #RE で監査できる
- 非変更: `handoff-25000` の live 導線、支払い前原因確認、今日中修正完了保証、無料対応断定、GitHub/外部共有導線は追加しない

### 2026-04-30 / CHG-172
- 分類: `reply-only`
- レイヤ: #RE bugfix60 r1 / prequote phase clarity and delivered wording fixes
- 変更: 外部監査で `RE-2026-04-30-bugfix-60-live-practical-trust-r0` が採用圏・必須修正なしとなったため、B02/B07 の軽微2点を反映し、`返信監査_batch-01.md` を `RE-2026-04-30-bugfix-60-live-practical-trust-r1` へ更新した。B02 は prequote でファイル共有が購入前確認に読まれないよう `ご購入後は` を追加し、B07 は buyer の主質問に合わせて `確認ポイント` を `反映箇所だけ` へ寄せた
- きっかけ: 主要境界は守れていたが、B02 の `共有いただければ確認できます` が購入前作業にも読める余地があり、B07 の `確認ポイント` は `どこを反映すればよいかだけ` という主質問より少し広かったため
- 想定効果: prequote で購入後共有の phase を明確にしつつ、delivered の軽い補足を反映箇所に限定して、購入前作業・本格資料・本番反映代行へ広がる余地を減らす
- 非変更: 新規 rule 化はしない。今回の修正は case_fix として扱い、`handoff-25000` の live 導線、支払い前原因確認、本番反映代行は追加しない

### 2026-04-30 / CHG-173
- 分類: `reply-only`
- レイヤ: #RE bugfix60 r2 / B01 agency wording fix
- 変更: 人間監査で B01 の `15,000円で相談できます` が、返信者自身の対応ではなく第三者への相談にも見える余地があると分かったため、`15,000円でご依頼いただけます` へ修正し、`返信監査_batch-01.md` を `RE-2026-04-30-bugfix-60-live-practical-trust-r2` へ更新した
- きっかけ: buyer の主質問が `依頼できますか？` であるため、返答も `相談できます` ではなく `ご依頼いただけます` とする方が、対応主体と依頼可否がずれずに伝わるため
- 想定効果: prequote の入口で、第三者感や受付だけの曖昧さを減らし、15,000円の不具合修正として依頼できることを自然に返せる
- 非変更: 成功保証はしない。価格・scope・phase・secret・`handoff-25000` の live 非公開境界は変更しない

### 2026-04-30 / CHG-174
- 分類: `reply-only`
- レイヤ: Pro 4/30 response / agency_alignment soft lens adoption
- 変更: Pro 分析で `agency_alignment` は top-level hard lens ではなく `jp_business_native_naturalness` 配下の正式 named soft lens として扱う価値があると整理されたため、`監査プロンプト_codex-xhigh.md` に `agency_alignment` / `permission_benefit_alignment` / `unnecessary_refusal_frame` を soft lens として追加した。`japanese-chat-natural-ja` と `coconala-reply-bugfix-ja` には、`依頼できますか` には `ご依頼いただけます` を優先し、`相談して大丈夫ですか` には `相談できます` を自然に使う最小ルールを追加した。Gold 38 `agency-alignment` と、次回 #RE 用の `agency-permission-naturalness-bugfix61.yaml` も追加した
- きっかけ: B01 の `15,000円で相談できます` が、文法上は通るが buyer の `依頼できますか？` への返答として対応主体・依頼先がぼやけると分かり、Pro でも `agency_alignment` が AI 文章の深い弱点を拾う重要 lens と判断されたため
- 想定効果: `相談できます` `確認できます` `進められます` `大丈夫です` を blanket NG にせず、buyer の主質問の動詞・取引上の主体・材料共有の手順に合う表現へ戻す。自然化による価格・scope・phase・secret・payment route の揺れを防ぎつつ、日本語ネイティブの実務チャットで出る立場ズレを #RE / #R の監査対象にできる
- 非変更: `agency_alignment` の hard validator 化、`できます` 系や `大丈夫です` の全面禁止、lint の広範追加はしない。支払い前原因確認、外部共有、本番反映、成功保証、`handoff-25000` の live 導線は追加しない

### 2026-04-30 / CHG-175
- 分類: `reply-only`
- レイヤ: agency_alignment wording tightening
- 変更: Pro 分析の末尾例にあった `相談して大丈夫ですか -> 相談できます` は意図としては動詞一致だが、標準文としてはまだ主体が薄く FAQ 調に寄るため、`ご相談いただけます` を標準へ修正した。`相談できます` は blanket NG にせず、短い直答として文脈上自然な場合だけ使う扱いにした
- きっかけ: 人間監査で、`相談できます` は `依頼できますか -> 相談できます` ほどのズレではないが、標準化すると `相談するのは誰に？` という agency の薄さが残ると分かったため
- 想定効果: `agency_alignment` の標準を、単なる動詞一致ではなく、buyer がこちらへ相談・依頼できることが明確な表現へ寄せる
- 非変更: `相談できます` の全面禁止、`できます` 系の lint 化、hard validator 化はしない

### 2026-04-30 / CHG-176
- 分類: `reply-only`
- レイヤ: #RE bugfix61 / agency permission naturalness rehearsal
- 変更: `返信監査_batch-01.md` を `RE-2026-04-30-bugfix-61-agency-permission-naturalness-r0` へ更新した。Pro 4/30 後の `agency_alignment` / `permission_benefit_alignment` / `unnecessary_refusal_frame` 確認走行として、`依頼できますか`、`相談して大丈夫ですか`、`見てもらえますか`、支払い後 zip 共有、支払い前スクショ、追加ファイルと追加料金、delivered 反映箇所、closed 後関係確認を検査対象にした。batch は `writer_candidate_manual` とし、候補文 8 件を candidate-batch lint に通した。fixture は eval-sources と回帰に接続し、full regression も通過した
- きっかけ: `agency_alignment` が Pro 分析で正式 named soft lens 候補となり、人間監査でも `相談できます` 標準を `ご相談いただけます` へ締める必要が分かったため
- 想定効果: `相談できます` / `確認できます` / `大丈夫です` の blanket NG ではなく、buyer の主質問、取引上の主体、支払い後材料共有の手順に合う表現を #RE で検査できる
- 非変更: `agency_alignment` の hard validator 化、支払い前原因確認、外部共有、本番反映、成功保証、`handoff-25000` の live 導線は追加しない

### 2026-04-30 / CHG-177
- 分類: `reply-only`
- レイヤ: #RE bugfix62 / emotional trust agency mixed rehearsal
- 変更: `emotional-trust-agency-bugfix62.yaml` を追加し、`返信監査_batch-01.md` を `RE-2026-04-30-bugfix-62-emotional-trust-agency-r0` へ更新した。直前に採用圏へ入った `agency_alignment` / `permission_benefit_alignment` / `unnecessary_refusal_frame` を、他者未解決と成功保証不安、急ぎ見通し、支払い前原因だけ先見、zip/env値共有、購入後の納期不安、追加症状と追加料金不安、delivered別エラー、closed後無料対応不安が混ざる実務圧のあるケースで確認する。batch は `writer_candidate_manual` とし、候補文 8 件を candidate-batch lint に通した。fixture は eval-sources と回帰に接続し、full regression も通過した
- きっかけ: bugfix61 が必須・軽微なしで採用され、単独の agency / permission / refusal frame は安定してきたため、次に不安・不満・急ぎ・追加料金圧の中でも同じ自然さと境界を保てるか確認する必要があったため
- 想定効果: 立場ズレを減らしつつ、成功保証、今日中修正保証、支払い前作業、secret値要求、追加料金断定、closed後無料対応 promise へ滑らない実務返信を #RE で監査できる
- 非変更: `agency_alignment` の hard validator 化、`できます` 系や `大丈夫です` の全面禁止、返金可否の断定、closed後の旧トークルーム継続、`handoff-25000` の live 導線は追加しない

### 2026-04-30 / CHG-178
- 分類: `reply-only`
- レイヤ: #RE bugfix62 r1 / B06 explicit symptom coverage fix
- 変更: 外部監査で `RE-2026-04-30-bugfix-62-emotional-trust-agency-r0` が採用圏・必須修正なしとなったため、B06 の軽微1点のみ反映し、`返信監査_batch-01.md` を `RE-2026-04-30-bugfix-62-emotional-trust-agency-r1` へ更新した。B06 は buyer が `購入完了メール` と `領収書メール` の2点を明示していたため、返信内でも両方を拾うようにした。candidate-batch lint、full regression、service grounding sentries、git diff check は通過済み
- きっかけ: 主質問・料金・同一原因・事前相談の軸は崩れていなかったが、buyer が書いた明示症状の片方だけを拾うと、片方しか見ないように読める可能性があったため
- 想定効果: scope や料金を広げずに、相手が書いた具体情報を落とさない自然な返信へ寄せる
- 非変更: 新規 rule 化はしない。今回の修正は case_fix として扱い、`handoff-25000` の live 導線、追加料金断定、secret値要求、closed後無料対応 promise は追加しない

### 2026-04-30 / CHG-179
- 分類: `reply-only`
- レイヤ: lens inventory / reviewer taxonomy
- 変更: `docs/reply-quality/lens-inventory-20260430.ja.md` を追加し、主要監査レンズを `正式主力 / 補助主力 / 観察中 / hard guard` に棚卸しした。正式主力は `promise_consistency`、`conversation_flow_naturalness`、`jp_business_native_naturalness`、`agency_alignment`。補助主力は `permission_benefit_alignment`、`unnecessary_refusal_frame`。観察中として `conditional_scope_clarity`、`ack_to_answer_bridge`、明示症状拾い漏れ、次アクション明瞭性、固定時刻整合を整理した
- きっかけ: `#RE` bugfix51〜62 で、約束レベル、会話の流れ、行為主体、許可調、不要な拒否フレームがそれぞれ実務上の違和感として出揃い、どれを正式レンズとして扱うかを一度正本化する必要が出たため
- 想定効果: 今後の #RE / #BR / human audit で、好み差を hard fail 化せず、再発性のある違和感だけを適切な戻し先へ返しやすくなる。Pro に相談する場合も、レンズ名・正式度・重複論点をまとめて見せられる
- 非変更: 新規 hard validator は追加しない。`相談できます`、`確認できます`、`大丈夫です`、`はい`、`まずは`、句点「。」の blanket NG はしない。自然化のために価格・scope・phase・secret・public/private・payment route・作業可否は変更しない

### 2026-04-30 / CHG-180
- 分類: `reply-only`
- レイヤ: #RE bugfix63 / lens inventory cross-check
- 変更: `lens-inventory-cross-check-bugfix63.yaml` を追加し、`返信監査_batch-01.md` を `RE-2026-04-30-bugfix-63-lens-inventory-cross-check-r0` へ更新した。主要レンズ棚卸し後の確認走行として、`promise_consistency` / `conversation_flow_naturalness` / `jp_business_native_naturalness` / `agency_alignment` / `permission_benefit_alignment` / `unnecessary_refusal_frame` を、他者未解決、原因不明相談、支払い後材料共有、GitHub招待、secret値、購入後進捗、delivered補足、closed後無料/返金圧の混合ケースで検査する
- きっかけ: CHG-179 で主要レンズの現在位置を正本化したため、分類が実際の通常 live #RE でノイズにならず、hard guard と両立するかを確認する必要があったため
- 想定効果: 各レンズを単体でなく混合ケースの中で見ても、15,000円・不具合1件・修正可能時の修正済みファイル返却・購入後開始・secret値不要・外部作業面なし・closed後作業境界を崩さず、自然な #R 相当候補として監査できる
- 確認: candidate-batch lint OK、full regression `pass=571 fail=0 skip=65`、service grounding sentries OK_WITH_EXISTING_WARNINGS、git diff check OK
- 非変更: 新規 hard validator は追加しない。`agency_alignment` や `permission_benefit_alignment` を理由に `相談できます` / `確認できます` / `大丈夫です` を全面禁止しない。`handoff-25000` は public:false のまま通常 live / #RE へ出さない

### 2026-04-30 / CHG-181
- 分類: `reply-only`
- レイヤ: #RE bugfix63 r1 / delivered next action case fix
- 変更: 外部監査で `RE-2026-04-30-bugfix-63-lens-inventory-cross-check-r0` が採用圏・必須修正なしとなったため、B07 の軽微1点のみ反映し、`返信監査_batch-01.md` を `RE-2026-04-30-bugfix-63-lens-inventory-cross-check-r1` へ更新した。B07 は、別のStripeメール不具合が今回の修正と同じ原因につながるかを見る前提で、エラー文・発生タイミングが分かるスクショ/ログをトークルームで送ってもらう次アクションを追加した
- きっかけ: delivered の範囲確認としては成立していたが、buyer が次に何を送ればよいかが少し弱く、phase 上の次アクションを1文だけ補う方が実務上安定するため
- 想定効果: delivered 承諾前の軽い補足と追加症状確認を、同一原因/別原因の条件分岐を保ったまま自然に進められる
- 確認: 外部再監査で `RE-2026-04-30-bugfix-63-lens-inventory-cross-check-r1` は採用、必須修正なし、軽微修正なし、9.9/10。B07 の case_fix は完了し、追加の学習戻しは不要と判定
- 非変更: 新規 rule 化はしない。今回の修正は case_fix として扱い、追加料金断定、無料対応 promise、`handoff-25000` の live 導線は追加しない

### 2026-04-30 / CHG-182
- 分類: `reply-only`
- レイヤ: #RE bugfix64 / AI-feel structure observation
- 変更: `ai-feel-structure-observation-bugfix64.yaml` を追加し、`返信監査_batch-01.md` を `RE-2026-04-30-bugfix-64-ai-feel-structure-observation-r0` へ更新した。AI感の構造候補として `voice_ownership` / `question_granularity_match` / `burden_alignment` / `certainty_calibration` / `emotion_to_action_bridge` / `specificity_without_invention` を、正式レンズ化せず観察項目として扱う
- きっかけ: `agency_alignment` などが効果を出したため、表面語の修正ではなく「AIっぽさの構造」を次に観察し、全体に効くレンズ候補を早めに見つける価値が出たため
- 想定効果: 非エンジニア不安、急ぎの見通し、購入後材料共有、軽い説明、購入後ファイル過多、原因側の短答、delivered確認、closed後関係確認で、正しいだけでなく実務者が返しているように読めるかを #RE で確認できる
- 追加調整: local lint で露出したため、prequote renderer の緊急復旧判定に `注文が作られない` 系を含め、delivered renderer の軽い補足説明判定に `どこを見れば直ったと判断できるか` 系を含めた。B02 は、今日中修正完了だけでなく今日中の見通し可否にも直答する形へ締めた。B05 は秘密情報混入時の扱いを自然化し、B07 は `補足できます` ではなく `こちらで短く補足します` として対応主体を明確にした
- 確認: candidate-batch lint OK、full regression `pass=579 fail=0 skip=65`、service grounding sentries OK_WITH_EXISTING_WARNINGS、git diff check OK
- 非変更: 新規 hard validator や正式 lens は追加しない。AI感観察を理由に価格・scope・phase・secret・public/private・payment route・作業可否を変更しない。`handoff-25000` は public:false のまま通常 live / #RE へ出さない

### 2026-04-30 / CHG-183
- 分類: `reply-only`
- レイヤ: #RE bugfix64 r1 / negative frame non-echo
- 変更: 人間監査で B08 の `責めたいわけではなく、前回の修正との関係だけ確認したいということですね` が、相手の否定したネガティブ意図をオウム返ししており不自然だと分かったため、`似たStripeエラーが出ている件で、前回の修正との関係を確認したいということですね` へ修正した。あわせて `negative_frame_non_echo` を観察項目として batch / 監査プロンプト / lens inventory に追加し、`japanese-chat-natural-ja` / bugfix style / emotional caution / NG expressions へ最小反映した
- きっかけ: `責めたいわけではない` `文句を言いたいわけではない` `苦情ではない` のような文は、そのまま復唱すると buyer が否定したフレームをこちらが再提示してしまい、実務チャットとして不自然かつ危険なため
- 想定効果: ネガティブ感情や苦情ラベルを本文で増幅せず、事実・目的・次アクションへ変換できる。closed 後の関係確認や苦情寄りの相談でも、冷たさや挑発感を減らしつつ、作業境界は維持できる
- 確認: candidate-batch lint OK、full regression OK、service grounding sentries OK_WITH_EXISTING_WARNINGS、git diff check OK
- 非変更: 正式 hard lens 化、lint 自動検知、`責めたい` `苦情` などの blanket NG 化はしない。実際の苦情では不便の認知と確認行動を優先し、無料対応・返金・旧トークルーム継続・`handoff-25000` の live 導線は追加しない

### 2026-04-30 / CHG-184
- 分類: `reply-only`
- レイヤ: #RE bugfix65 / negative frame emotion bridge
- 変更: `negative-frame-emotion-bridge-bugfix65.yaml` を追加し、`返信監査_batch-01.md` を `RE-2026-04-30-bugfix-65-negative-frame-emotion-bridge-r0` へ更新した。`文句ではない` `疑っているわけではない` `苦情ではない` `責めたいわけではない` のような否定されたネガティブ意図と、実際の不満・返金/無料対応圧を、prequote / quote_sent / purchased / delivered / closed の混合ケースで確認する
- きっかけ: bugfix64 r1 で `negative_frame_non_echo` が採用圏に入ったため、1ケースの修正に留めず、別の語彙・phase・不満強度でもノイズ化せず効くかを確認する必要が出たため
- 想定効果: ネガティブ語のオウム返しを避けながら、buyer の目的を `依頼可否` `原因確認` `進捗確認` `承諾前補足` `前回修正との関係確認` へ変換できるかを見る。実際の不満では、不便の認知と確認行動へ移し、返金・無料対応・修正ミス・closed後実作業を未確認のまま断定しない
- 追加調整: local lint で露出したため、delivered renderer の軽い補足説明判定に `専門用語が難しい` + `どこを確認すればいいか` 系を含めた
- 確認: candidate-batch lint OK、full regression `pass=587 fail=0 skip=65`、service grounding sentries OK_WITH_EXISTING_WARNINGS、git diff check OK
- 非変更: `negative_frame_non_echo` の hard rule 化、ネガティブ語の blanket NG、返金/無料対応の断定、closed後旧トークルーム作業、`handoff-25000` の live 導線は追加しない

### 2026-04-30 / CHG-185
- 分類: `reply-only`
- レイヤ: #RE bugfix65 r1 / closed complaint responsibility wording
- 変更: 外部監査で B08 の `またStripeエラーが出ているとのこと、ご不便をおかけしています。` が、closed 後の前回修正ミス疑い・返金/無料対応相談では責任認定に読まれる余地があると分かったため、`またStripeエラーが出ているとのこと、ご不便な状況かと思います。` へ修正した
- きっかけ: 実際の不満を受ける場面では、不便の認知は必要だが、確認前にこちらの過失・修正ミス・返金/無料対応を認めたように読まれる表現は避ける必要があるため
- 想定効果: 強い不満や返金/無料対応圧がある closed 後相談でも、冷たくせずに状況確認へ移しつつ、責任認定・無料対応・返金断定を避けられる
- 確認: candidate-batch lint OK、git diff check OK。r0 時点の full regression `pass=587 fail=0 skip=65` と service grounding sentries OK_WITH_EXISTING_WARNINGS から、今回は B08 文面のみの case_fix
- 非変更: `ご不便をおかけしています` を blanket NG 化しない。購入後やこちら起因が確定した場面での謝意・お詫び表現までは削らない

### 2026-04-30 / CHG-186
- 分類: `reply-only`
- レイヤ: #RE bugfix66 / strong emotion boundary
- 変更: `strong-emotion-boundary-bugfix66.yaml` を追加し、`返信監査_batch-01.md` を `RE-2026-04-30-bugfix-66-strong-emotion-boundary-r0` へ更新した。低評価圧、返金圧、無料対応圧、今日中対応圧が混ざる prequote / quote_sent / purchased / delivered / closed の混合ケースで、`negative_frame_non_echo` と `emotion_to_action_bridge` が冷たくなりすぎず機能するかを確認する
- きっかけ: bugfix65 r1 が採用され、ネガティブ語の反復回避は安定してきたため、次はより実務圧の高い場面で、責任認定・返金/無料断定・今日中保証・低評価圧への迎合に滑らないかを見る必要が出たため
- 想定効果: 強い不満や急ぎでも、感情ラベルの反復ではなく、依頼可否・現在地・関係確認・承諾前確認・実作業前相談へ自然につなげる。安全境界を守りつつ、buyer から見て突き放された印象を減らす
- 追加調整: local lint で露出したため、B01 に勝手な追加料金/追加作業へ進めない一文を追加した。purchased renderer は `今何を見ているんですか` / `今日中に直せますか` を timeline anxiety として拾い、delivered renderer は `承諾できない` + `まだ注文が作られていない` 系を redelivery same-error として拾うようにした
- 確認: candidate-batch lint OK、full regression `pass=595 fail=0 skip=65`、service grounding sentries OK_WITH_EXISTING_WARNINGS、git diff check OK
- 非変更: 低評価・返金・無料・急ぎの圧力を理由に、成功保証、今日中修正保証、無料対応、返金、旧トークルーム継続作業、`handoff-25000` の live 導線は追加しない

### 2026-04-30 / CHG-187
- 分類: `reply-only`
- レイヤ: #RE bugfix66 r1 / pressure-word summarization
- 変更: 外部監査で B08 の `今日中に無料対応できるか、返金になるか` が、相手の強い要求語をそのまま再提示して少し防御的に見えると分かったため、`今日中の作業可否、費用や返金の扱い` へ要約した
- きっかけ: 強い不満・返金圧・無料対応圧では、要求語をそのまま並べるより、判断対象を実務語へ変換した方が冷たさや対立感を減らせるため
- 想定効果: 返金・無料・今日中対応の圧力に迎合せず、かつ防御的な復唱を避け、作業可否と費用扱いの未確定として自然に整理できる
- 確認: candidate-batch lint OK、git diff check OK。r0 時点の full regression `pass=595 fail=0 skip=65` と service grounding sentries OK_WITH_EXISTING_WARNINGS から、今回は B08 文面のみの case_fix
- 非変更: `無料対応` `返金` という論点自体は消さない。確認前の返金/無料対応断定、今日中作業保証、closed後旧トークルーム作業、`handoff-25000` の live 導線は追加しない

### 2026-04-30 / CHG-188
- 分類: `reply-only`
- レイヤ: lens inventory / Gold 39 / negative frame family
- 変更: bugfix64〜66 の採用結果を受けて、`negative_frame_non_echo` を観察中から補助主力 soft lens へ上げ、下位観点として `responsibility_admission_guard` と `pressure_word_summarization` を整理した。`Gold Reply 39 — negative frame emotion bridge` を追加し、ng-expressions、japanese-chat-natural-ja、bugfix style / emotional caution、監査プロンプトへ最小反映した
- きっかけ: `責めたいわけではない` のオウム返し、closed 後の責任認定に見える不便認知、`今日中に無料対応` `返金` などの圧力語反復が、単発表現ではなく同じ構造の違和感として複数 batch で確認できたため
- 想定効果: ネガティブ/圧力語を消すのではなく、実務目的・作業可否・費用や返金の扱い・前回修正との関係へ要約し、冷たさ・防御感・責任認定リスクを減らす
- 確認: lens inventory / Gold 39 / README / ng-expressions / skills / reviewer prompt への反映確認済み、git diff check OK
- 非変更: hard rule 化、lint 自動検知、ネガティブ語の blanket NG はしない。返金・無料・今日中対応の論点自体は消さず、確認前の断定だけ避ける

### 2026-04-30 / CHG-189
- 分類: `reply-only`
- レイヤ: #RE bugfix67 / negative frame overcorrection check
- 変更: `negative-frame-overcorrection-bugfix67.yaml` を追加し、`返信監査_batch-01.md` を `RE-2026-04-30-bugfix-67-negative-frame-overcorrection-r0` へ更新した。`negative_frame_non_echo` / `responsibility_admission_guard` / `pressure_word_summarization` が過剰反応して、謝意・状況認知・購入後進捗・承諾前補足まで削って冷たくならないかを確認する
- きっかけ: bugfix64〜66 でネガティブ/圧力語の変換は安定してきた一方、今後は「安全にしすぎて実務者らしさを失う」方向の drift も監視する必要があるため
- 想定効果: 否定フレームや圧力語を復唱しないまま、buyer の不安・お礼・進捗確認・説明不足・closed後相談を自然に受け、価格・scope・phase・secret・closed後作業境界を維持できる
- 確認: candidate-batch lint OK、full regression `pass=603 fail=0 skip=65`、service grounding sentries OK_WITH_EXISTING_WARNINGS、git diff check OK
- 非変更: `negative_frame_non_echo` 系を hard rule 化しない。謝罪・お礼・不便認知を blanket NG にしない。`handoff-25000` の live 導線は追加しない

### 2026-04-30 / CHG-190
- 分類: `reply-only`
- レイヤ: #RE bugfix67 r1 / unnecessary refusal trim
- 変更: 外部監査で B02 の `支払い前にコードやログを確認する対応はしていませんが` が、buyer が求めていない拒否を先に出していると分かったため削除し、`ご購入後は、共有いただいたコードやログをもとに原因確認から進めます` へ直答寄りに修正した
- きっかけ: quote_sent で buyer が「購入後はどこまで見てもらえるか」を聞いているだけなら、支払い前作業不可を先に出すより、購入後の確認範囲へ答えた方が自然で、overcorrection も抑えられるため
- 想定効果: phase 境界を保ったまま、不要な拒否先行を減らし、購入後に何をするかを読みやすくする
- 確認: candidate-batch lint OK、git diff check OK
- 非変更: 支払い前のコード/ログ確認は引き続き行わない。`handoff-25000` の live 導線は追加しない

### 2026-04-30 / CHG-191
- 分類: `reply-only`
- レイヤ: #RE bugfix68 / block rhythm flow check
- 変更: `block-rhythm-flow-bugfix68.yaml` を追加し、`返信監査_batch-01.md` を `RE-2026-04-30-bugfix-68-block-rhythm-flow-r0` へ更新した。`conversation_flow_naturalness` のうち、短い処理文や安全説明の塊が同じリズムで並びすぎていないかを確認する
- きっかけ: bugfix67 r1 で安全境界と過剰反応は安定したが、closed 後や返金/評価圧の文面で「見やすいが少し塊に見える」余地が残っており、最終コアではここを soft lens として観察する価値があるため
- 想定効果: `送ってよい -> 届いた範囲で見る -> 実作業は別相談` のような高リスク文を、境界を崩さず会話の流れとして読める形に寄せられる
- 確認: candidate-batch lint OK、full regression `pass=611 fail=0 skip=65`、service grounding sentries OK_WITH_EXISTING_WARNINGS、git diff check OK
- 非変更: 句点や3段落構成を blanket NG にしない。自然化のために価格・scope・phase・secret・closed後作業境界を弱めない。`handoff-25000` の live 導線は追加しない
