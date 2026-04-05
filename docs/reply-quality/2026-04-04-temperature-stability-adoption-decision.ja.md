# 2026-04-04 温度感安定化 採用判断メモ（reply-only）

## 目的
- `#AR` 調査と ChatGPT Pro の設計レビューを受けて、温度感安定化の実装方針を 1 本に固定する。
- 実装前に
  - 採用するもの
  - 見送るもの
  - 後回しにするもの
  を明文化し、手戻りを減らす。

## 前提
- 構造側の方針
  - `reply_contract`
  - `section renderer`
  - `deterministic lint`
  - `eval`
  は維持する。
- 今回の改善は `reply-only`。
- 外向け live は `bugfix-15000` のみ。
- `handoff-25000` は private のまま。

## 結論
- 第一推奨として採用するのは、**`temperature_plan` を `reply_contract` の sibling として追加し、renderer 後段では `ack / bridge / closing` だけを slot-preserving に書き換える構成**。
- ねらいは「温かい文を書く」ことではなく、**prose 側の再解釈権を狭めること**。
- これにより、stress / negative feedback / boundary で再発していた
  - 相手の状態シグナル拾い漏れ
  - 負担感
  - 弁明
  - 内部語彙漏れ
  を、free prose から executable field へ移す。

## 採用するもの

### 1. `temperature_plan` の導入
- 置き場所:
  - `reply_contract` の sibling
- 理由:
  - semantic truth source と interaction truth source を分けるため
  - tone 調整で `answer_map` を巻き戻さないため

最小 schema:

```json
{
  "temperature_plan": {
    "user_signal": "stress | hesitation | confusion | negative_feedback | neutral",
    "support_goal": "reduce_burden | normalize | receive_feedback | set_boundary_calmly | move_forward",
    "opening_move": "action_first | pressure_release | normalize_then_clarify | receive_and_own | yes_no_first | neutral_ack",
    "tone_constraints": [
      "no_defense",
      "no_internal_terms",
      "no_burden_shift",
      "no_negative_lead"
    ]
  }
}
```

### 2. semantic freeze の明確化
- `reply_contract` で意味を固定する。
- 以後の layer では、以下を変更させない。
  - answer polarity
  - hold reason / hold trigger
  - ask 数
  - quoted facts
  - next action
  - scope / boundary core

### 3. renderer の `fixed_slots / editable_slots` 分離
- `fixed_slots`
  - `answer_core`
  - `hold_reason`
  - `hold_trigger`
  - `ask_core`
  - `next_action`
  - `quoted_facts`
  - `boundary_core`
- `editable_slots`
  - `ack`
  - `bridge_to_hold`
  - `bridge_to_ask`
  - `closing`

### 4. `japanese-chat-natural-ja` の役割変更
- 現状:
  - 全文自然化器
- 変更後:
  - `typed slot rewriter`
- 入力してよいもの:
  - `editable_slots`
  - `slot_manifest`
  - `reply_skeleton`
  - `temperature_plan`
  - 同 bucket の good example 2〜3 本
- 入力してはいけないもの:
  - raw user message
  - full service facts
  - full reply_contract
  - full draft
  - fixed slot 本文

### 5. validator の fail-closed 化
- validator fail 時は全文 regenerate しない。
- renderer の fixed output をそのまま採用する。
- 理由:
  - semantic drift を増やさないため

### 6. eval の bucket 化
- aggregate 1 本ではなく、以下を固定 holdout にする。
  - `stress`
  - `boundary`
  - `negative_feedback`
- 監視する failure mode:
  - `stress`
    - `action_first_pass`
    - `burden_leak_rate`
    - `opening_overlength_rate`
  - `boundary`
    - `yes_no_first_pass`
    - `calm_boundary_pass`
    - `internal_term_leak_rate`
  - `negative_feedback`
    - `receive_and_own_pass`
    - `defense_rate`
    - `burden_leak_rate`

### 7. 50件監査ログの初期用途
- 第一用途:
  - `pairwise reranker`
- 使い方:
  - 同一 `fixed_slots` に対する `editable_slots` 候補 A/B の比較
- 理由:
  - blast radius が小さい
  - accepted/rejected contrast をそのまま使える

## 見送るもの

### 1. `temperature_plan` を free-text memo のまま prompt に流すこと
- 理由:
  - executable field にならず再発防止力が弱い

### 2. `temperature_plan` を `reply_contract` の child にすること
- 理由:
  - semantic retry と interaction retry が一体化する

### 3. 全文自然化の強化
- 理由:
  - 意味まで壊すリスクが高い

### 4. full-reply DPO
- 理由:
  - schema と slot 制約が固まる前にやると、好みと意味が混ざる

### 5. full-reply SFT
- 理由:
  - 50件では少ない
  - semantic と interaction を一緒に焼き込みやすい

## 後回しにするもの

### 1. DPO
- 条件:
  - `temperature_plan`
  - slot 制約
  - pairwise eval
  が安定した後

### 2. runtime rerank
- 条件:
  - offline reranker で bucket 改善が確認できた後

### 3. trace grading の強化
- 条件:
  - planner / renderer / naturalize / validator の責務が固定した後

## 実装順

### P1. `temperature_plan` 追加
- 先に planner / contract の schema を増やす

### P2. renderer を `fixed_slots / editable_slots` 出力へ変更
- まず reply-only の対象 skeleton から適用する

### P3. `japanese-chat-natural-ja` を slot-local 化
- 全文自然化をやめる

### P4. validator を fail-closed 化
- tone 制約と semantic freeze を最終文面で検査する

### P5. 50件ログを reranker 用 pair に整形
- runtime 適用前に offline eval へつなぐ

## 実装しないまま固定してよいルール
- boundary は `temperature_plan.user_signal` に混ぜない
- `温度感` は総合点 1 本で見ない
- pairwise judge に semantic の違う候補同士を比較させない
- stress / boundary / negative feedback を aggregate score に埋めない
- validator fail 時に全文 regenerate しない

## 次の検証方針
- quality-cases 50件を再度フルで回さない
- まずは holdout bucket に絞る
  - `stress`
  - `boundary`
  - `negative_feedback`
- Claude 監査は再発確認の judge として使う
  - 追加ルール採掘より bucket 改善確認を優先する

## 参照元
- [温度感安定化設計レビュー.txt](/home/hr-hm/Project/work/chatgptPro/温度感安定化設計レビュー.txt)
- [2026-04-04-reply-temperature-stability-patterns-agent-reach.ja.md](/home/hr-hm/Project/work/docs/external-research/2026-04-04-reply-temperature-stability-patterns-agent-reach.ja.md)
- [2026-04-04-reply-structure-direction-validation-agent-reach.ja.md](/home/hr-hm/Project/work/docs/external-research/2026-04-04-reply-structure-direction-validation-agent-reach.ja.md)
- [2026-04-04-reply-system-major-axes-validation-agent-reach.ja.md](/home/hr-hm/Project/work/docs/external-research/2026-04-04-reply-system-major-axes-validation-agent-reach.ja.md)
