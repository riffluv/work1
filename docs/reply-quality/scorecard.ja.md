# 返信 scorecard

## 目的
- `良い / 悪い` を主観だけで終わらせず、5件バッチの改善を数値で追う
- self-check とは分けて、改善速度の可視化だけに使う

## 使い方
- 1返信につき各項目を `pass / fail` で採点する
- 合計 `10/10` 満点
- `8/10` 以上を送信可の目安、`6/10` 以下は要再検討の目安にする

## 10項目
1. 主質問に先に答えている
2. phase を外していない
3. public/private 境界を外していない
4. buyer の判断段階を飛ばしていない
5. buyer が既に出した情報を聞き直していない
6. 次アクションが buyer に見える
7. 内部語・空語・ban 語がない
8. buyer の語彙か観測事実を最低1点拾っている
9. 断る時でも代替か戻り道がある
10. 日本語として引っかかりが少ない

## 補助監査軸

以下は `score_total` に足さない。10項目だけでは説明しにくい高リスクケースを、notes に短く残すための補助軸として使う。

- `transaction_model_gap`
  - 主質問、phase、支払い状態、作業開始条件、成果物返却導線、次アクションが一本の取引構造としてつながっていない
  - 主に 2 / 4 / 6 / 9 をまたぐ補助軸として扱う
- `work_payment_boundary`
  - 確認材料の受領と、コード修正・具体的修正指示・成果物返却などの実作業が混ざっている
  - `quote_sent / delivered / closed` でだけ重く見る
- `free_support_or_responsibility_risk`
  - 無料対応、返金、過失、責任を確認前に認めすぎている
  - 怒り気味 buyer や closed 後の再発不満でだけ使う
- `buyer_state_ack_gap`
  - buyer が怒り・疲弊・不安・焦り・不信・困惑・遠慮・無料/返金不満などの状態を明示しているのに、症状・価格・手順だけを受けている
  - QA-07 温度感ズレの下位 notes として扱い、点数化しない
  - 状態を1文だけ受けるための軸であり、謝罪・過失認定・返金断定・無料対応約束には広げない
- `surface_overexposure`
  - 安全条件を外向け本文に積みすぎ、buyer には規約説明やチェックリストのように見える
  - 安全境界を削るためではなく、必要な直答・境界・次アクションに圧縮するために使う
- `response_weight_mismatch`
  - buyer の文量・温度・質問数に対して、返信が重すぎて契約説明や安全条件の列挙に見えていないかを見る
  - 点数化しない。短文化の口実にせず、必要な safety boundary が残ることを確認した上で、露出量・順序・統合候補を notes に残す

## 記録形式
```yaml
case_ref:
score_total: 0
items:
  primary_answer: pass
  phase_fit: pass
  public_private_fit: pass
  decision_stage_fit: pass
  no_reask: pass
  next_action_visible: pass
  no_internal_or_ban: pass
  buyer_signal_used: pass
  refusal_with_alternative: pass
  japanese_naturalness: pass
notes:
```

## 見方
- `score_total` だけで判断しない
- `fail` がどの項目に偏るかを見る
- 同じ fail が続くなら system へ戻す

## まず見る数値
- バッチ平均点
- `8/10` 以上の件数
- `phase_fit` と `decision_stage_fit` の fail 数

## self-check との違い
- self-check:
  - 送信前 gate
- scorecard:
  - 改善の進捗確認

## 注意
- scorecard を増やしすぎない
- 最初はこの10項目で固定する
- 補助監査軸は点数化しない。該当時だけ notes に残し、再発したら gold / reviewer_prompt / validator の候補にする
