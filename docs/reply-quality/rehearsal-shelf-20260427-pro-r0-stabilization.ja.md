# Pro監査棚卸し 2026-04-27: r0 初手分岐安定化

## 位置づけ

ChatGPT Pro の `返信システム監査4-27.txt` を、`#RE` の次工程へ落とすための棚卸しメモ。
外部調査結果をそのまま rule 化するのではなく、既存の `#RE` 再発証拠と合わせて、戻し先を整理する。

## 結論

現設計の骨格は壊れていない。
ただし、r0 で繰り返し崩れる型は、もう Gold 追加だけでは足りない。

r1 / r2 で直せることは学習ループが効いている証拠だが、同じ型が r0 で戻る場合は、初回生成側の接続不足として扱う。

## r0 未安定型と戻し先

| 型 | 主な症状 | 戻し先 |
| --- | --- | --- |
| 旧三点セット | 具体症状があるのに `内容ありがとうございます -> この不具合なら15,000円 -> どこで止まっているか確認` へ戻る | prequote validator / renderer |
| 非Stripe scope | PayPay / GMO / Square 等を provider 全体として受ける | renderer / validator / service facts |
| 緊急復旧時間 | `今日中に復旧できますか` へ復旧保証不可と一次結果目安を分けて返せない | renderer / validator |
| 保証期間 | 固定保証期間の有無、同じ原因、別原因の扱いが分かれない | service facts / renderer / validator |
| 返金/キャンセル | seller が返金可否やキャンセル可否を断定しそうになる | platform contract / renderer / validator |
| 仕様/不具合境界 | `仕様ですか、不具合ですか` に断定か汎用テンプレで返す | renderer / gold |
| purchased 進捗 | `確認中です` だけ、または同義反復で現在地が見えない | renderer / validator |
| quote_sent 語彙 | 購入前なのに `トークルーム内` `作業中` `納品` が出る | platform contract / validator / renderer |
| closed 後導線 | 旧トークルーム継続、無料作業、別件割引の導線が曖昧 | platform contract / renderer / validator |

## validator に向くもの

決定的に落とせるものだけ入れる。

- 旧三点セット
- 同義反復3回
- `quote_sent` の現在形 phase 語彙
- `closed` 後の旧トークルーム継続
- 秘密値要求
- 外部共有 / 外部連絡 / 外部決済
- `handoff-25000` / `25,000円` など private service leak
- 返金 / キャンセル / 保証 / 復旧の断定
- 非Stripe名があるのに Next.js / Webhook / API 境界なしで丸受け
- purchased 進捗で `確認中です` だけ

## validator に入れないもの

- 怒り気味 buyer への温度全般
- buyer が聞いていない返金・保証説明の強制
- Gold と文言が違うだけの差分
- 一律の文字数制限
- 非Stripe名が出たこと自体の fail

これらは reviewer_prompt / naturalizer / gold anchor で扱う。

## renderer に戻すもの

`primary_question_type` を先に確定し、通常の bug intake へ流さない。

- `normal_bug_intake`
- `scope_boundary`
- `emergency_time`
- `guarantee`
- `refund_or_cancel`
- `spec_vs_bug`
- `purchased_progress`
- `quote_sent_material_or_scope`
- `closed_new_route`

特に `direct_answer_line` は、r0 で主質問に答えるための skeleton 要素として扱う。

## 次の #RE 方針

普通の mixed batch ではなく、まず r0 未安定型だけの regression batch を作る。

対象候補:

- non_stripe_scope
- urgent_recovery_time
- warranty_period_question
- refund_cancel_question
- spec_vs_bug_boundary
- purchased_progress_anxiety
- quote_sent_phase_wording
- closed_discount_or_new_request
- angry_buyer_temperature

見る指標:

- r0 で主質問に直答しているか
- phase 語彙が合っているか
- private service leak がないか
- 秘密値 / 外部共有 / 外部決済が出ていないか
- 復旧・保証・返金を断定していないか

## 今回はやらないこと

- Gold 34 追加
- skill 本体へのケース知識追加
- 人間っぽく短くする圧縮
- 怒り buyer の温度を validator 化

短文化・自然化は、安全性と r0 初手分岐がもう少し安定してから行う。
