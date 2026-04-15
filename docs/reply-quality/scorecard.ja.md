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
