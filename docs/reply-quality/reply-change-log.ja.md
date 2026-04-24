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
