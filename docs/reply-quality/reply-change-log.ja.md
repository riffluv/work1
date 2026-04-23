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
