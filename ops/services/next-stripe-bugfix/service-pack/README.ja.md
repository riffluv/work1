# bugfix-15000 service-pack

## 目的
- `bugfix-15000` に関するサービス固有知識を、共通 runtime から切り離して持つ
- 外向けサービス文面は変えず、`public contract / decision contract / evidence contract / routing / state / runtime assets` に分ける
- 返信品質を壊さずに、他サービスへ移植しやすい形へ近づける

## 構成
- `facts.yaml`
  - 公開サービス文面から直接引ける事実。価格、納品物、公開してよい範囲、phase ごとの許容範囲
- `boundaries.yaml`
  - 公開サービス文面と運用境界から引く、やること / やらないこと / hard no
- `decision-contract.yaml`
  - same-cause 判定、原因不明時の止め方、正式納品 gate、最終確認責任者
- `evidence-contract.yaml`
  - phase 別に何を・どの順で・どこまで聞くか。Stripe 系の first-class evidence もここで持つ
- `routing-playbooks.yaml`
  - よくある入口に対して、どの route で何を先に返すか。state の初期値も含む
- `state-schema.yaml`
  - multi-turn で保持すべき状態
- `seeds.yaml`
  - live prompt に差し込む候補 seed。service の source-of-truth ではなく runtime asset
- `tone-profile.yaml`
  - 温度感、直接性、簡潔さなどの既定値。semantic fidelity ではなく runtime asset

## 位置づけ
- この pack は service 固有資産だが、source-of-truth は一枚ではない
- `writer-brief` や `self-check L1/L2` は共通 runtime 側
- L3 の検査は、まず `facts / boundaries / decision-contract / evidence-contract` を優先参照し、`routing / state` を会話運用の補助として使う
- `seeds / tone` は runtime asset であり、公開契約の source-of-truth には置かない
- 共通ポリシーは `/home/hr-hm/Project/work/docs/reply-quality/service-pack-source-of-truth-policy.ja.md` を参照する

## source of truth
- 公開文面:
  - `/home/hr-hm/Project/work/サービスページ/bugfix-15000.live.txt`
- service-pack facts:
  - `/home/hr-hm/Project/work/ops/services/next-stripe-bugfix/service-pack/facts.yaml`
  - 2026-05-01 時点では、このファイルを service-pack 側の公開事実正本として扱う。ルート直下の `service.yaml` は既存互換の facts 参照として残す。
- 公開ページ由来の回帰源:
  - FAQ とトークルーム回答例は `/home/hr-hm/Project/work/ops/tests/regression/service_pack_fidelity_bugfix/cases.yaml` で contract 回帰源として扱う
- 既存 facts:
  - `/home/hr-hm/Project/work/ops/services/next-stripe-bugfix/service.yaml`
- 既存 route / scope 判断:
  - `/home/hr-hm/Project/work/ops/services/next-stripe-bugfix/estimate-decision.yaml`
  - `/home/hr-hm/Project/work/ops/services/next-stripe-bugfix/evidence-minimum.yaml`
  - `/home/hr-hm/Project/work/ops/services/next-stripe-bugfix/scope-matrix.md`

## contract の優先順
1. 公開サービスページ
2. `facts.yaml` / `boundaries.yaml`
3. `decision-contract.yaml` / `evidence-contract.yaml`
4. `routing-playbooks.yaml` / `state-schema.yaml`
5. `seeds.yaml` / `tone-profile.yaml`

## source-of-truth から外すもの
- `routing-playbooks.yaml`
  - route ごとの返し方と state 初期値を持つが、公開契約そのものの正本ではない
- `state-schema.yaml`
  - multi-turn の保持項目を持つが、buyer 向けの契約本文ではない
- `seeds.yaml`
  - runtime asset
- `tone-profile.yaml`
  - runtime asset

## 運用方針
- まずはこの pack を `bugfix-15000` の逆充填版として扱う
- 新しい知見は、単発の返信修正で終わらせず
  - 共通なら runtime 側
  - サービス固有ならこの pack 側
  へ戻す
- `service 理解` と `reply スタイル` を混ぜない
