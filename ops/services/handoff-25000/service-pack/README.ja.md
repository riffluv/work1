# handoff-25000 service-pack

## 目的
- `handoff-25000` に関するサービス固有知識を、共通 runtime から切り離して持つ
- `bugfix-15000` と同じく、`public contract / decision contract / evidence contract / routing / state / runtime assets` の責務分離を前提に管理する
- private / ready 状態のままでも、routing や L3 判定の置き場を明確にする

## 構成
- `facts.yaml`
  - 価格、納品物、公開してよい事実、phase ごとの許容範囲
- `boundaries.yaml`
  - やること / やらないこと / hard no
- `decision-contract.yaml`
  - one_flow / extra_flow / repair / undecidable の判断順と delivery gate
- `evidence-contract.yaml`
  - phase ごとに何を・どの順で・どこまで聞くか
- `routing-playbooks.yaml`
  - handoff 入口、bugfix との境界、補足依頼、追加フロー案内。state の初期値も含む
- `state-schema.yaml`
  - multi-turn で保持すべき状態
- `seeds.yaml`
  - live prompt に差し込む候補 seed。runtime asset
- `tone-profile.yaml`
  - 温度感、直接性、簡潔さなどの既定値。runtime asset

## 位置づけ
- この pack は service 固有資産だが、source-of-truth は一枚ではない
- `handoff-25000` は現時点では private / ready
- 返信で案内してよいかどうかは、公開状態の正本に従う
- L3 の検査は、まず `facts / boundaries`、次に `decision / evidence` を優先参照し、`routing / state` を会話運用の補助として使う
- `seeds / tone` は runtime asset であり、公開契約の source-of-truth には置かない
- 共通ポリシーは `/home/hr-hm/Project/work/docs/reply-quality/service-pack-source-of-truth-policy.ja.md` を参照する

## source of truth
- 公開準備文面:
  - `/home/hr-hm/Project/work/サービスページ/handoff-25000.ready.txt`
- 既存 facts:
  - `/home/hr-hm/Project/work/ops/services/handoff-25000/service.yaml`
- 既存 route / scope 判断:
  - `/home/hr-hm/Project/work/ops/services/handoff-25000/evidence-minimum.yaml`
  - `/home/hr-hm/Project/work/ops/services/handoff-25000/scope-matrix.md`

## source-of-truth から外すもの
- `decision-contract.yaml`
  - 公開ページと scope matrix 由来の判断を構造化したもの。公開ページそのものの代替ではない
- `evidence-contract.yaml`
  - 購入お願い文と evidence minimum 由来の質問契約。公開ページそのものの代替ではない
- `routing-playbooks.yaml`
  - route ごとの返し方と state 初期値を持つが、公開契約そのものの正本ではない
- `state-schema.yaml`
  - multi-turn の保持項目を持つが、buyer 向けの契約本文ではない
- `seeds.yaml`
  - runtime asset
- `tone-profile.yaml`
  - runtime asset

## 運用方針
- `handoff-25000` が live になるまでは、外向け案内の source にはしない
- ただし、boundary 判定や内部 route 設計ではこの pack を正として使う
- `service 理解` と `reply スタイル` を混ぜない
- FAQ / 回答例は `/home/hr-hm/Project/work/ops/tests/regression/service_pack_fidelity_handoff/cases.yaml` を通じて回帰源として扱う
