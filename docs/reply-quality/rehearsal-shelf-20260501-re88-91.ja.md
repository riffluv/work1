# #RE88-91 短い棚卸し

作成日: 2026-05-01

対象:

- `RE-2026-05-01-bugfix-88-business-chat-viability-followup-r1`
- `RE-2026-05-01-bugfix-89-semantic-grounding-progress-r0`
- `RE-2026-05-01-bugfix-90-semantic-grounding-practical-r0`
- `RE-2026-05-01-bugfix-91-business-chat-semantic-grounding-r0`

## 結論

#RE88-91 は採用圏。

#RE88 で出た purchased 現在地説明の grounding drift は、#RE89-91 でかなり安定した。

現時点では、新しい hard rule / lint / renderer 追加は不要。既存の `相手文にない技術語・原因候補・作業状況を足さない` を、#RE で継続確認する段階。

## 採用済み

- purchased の現在地説明では、未提示の Event ID / Webhook / DB / Stripe記録 / 原因候補を足さない
- 受領材料を起点に、`いただいた内容をもとに、今回の不具合に関係する流れを確認しています` 程度で現在地を出す
- 材料が多い時は、全部を同じ深さで見ると言わず、関係が強そうな箇所から見る
- 追加材料は、必要になった時だけこちらから絞って伝える
- delivered の軽い補足では、`補足できます` で止まらず、こちらが何を短く整理して返すかを書く
- quote_sent の軽い手順確認では、通常フローを先に案内する
- 支払い前診断 / GitHub作業面 / secret値 / closed後実作業の境界突破要求では、必要な不可表明を残す
- closed 後は、メッセージ上の関係確認と実作業前相談を分ける

## まだ観察中

- `business chat viability`: 正しいが、受付票・FAQ・規約説明っぽく見えないか
- `block_rhythm_flow`: 低リスク場面で、処理文・条件文・安全説明が同じリズムで並びすぎないか
- `positive_flow_before_refusal`: 軽い手順確認と境界突破要求の切り替えが過剰発火しないか
- `agency_alignment`: buyer が軽い補足を求めた場面で、対応可否宣言ではなく、返す内容へ進めているか

## 次の #RE92 で見るとよいもの

1. purchased の現在地説明を別表現で続ける
   - 材料受領
   - 何を見ているか
   - まだ断定していないこと
   - 追加材料は必要時のみ
2. delivered の軽い補足を続ける
   - `教えてください` に対して、実際に何を返すかを書く
   - 本格資料・運用マニュアル・本番反映代行へ広げない
3. quote_sent の手順確認をもう少し混ぜる
   - 支払い後共有の通常フロー
   - 支払い前診断不可
   - secret 値を含めない
4. closed 後の穏やかな再相談を1件入れる
   - 関係確認までは可
   - 実作業・返金・無料対応は確認前に断定しない

## Pro に聞くタイミング

まだ急がなくてよい。

#RE92-93 まで回して、以下が見えてからがよい。

- semantic grounding は安定したが、文章がまだ説明書っぽく見える箇所
- business chat と安全境界のどちらを優先するべきか迷う箇所
- `positive_flow_before_refusal` を gold / reviewer prompt へ昇格してよいか
- `business chat viability` を独立 lens にするか、自然化 layer の観察に留めるか

## 非変更

- 新しい hard rule / lint / renderer 変更は追加しない
- `できます`、`ではありません`、`大丈夫です`、`〜の件` は blanket NG にしない
- 通常 live / #RE に `handoff-25000`、25,000円、主要1フロー整理、未公開導線は出さない
- 自然化のために、価格、scope、phase、secret、payment route、closed 後実作業境界を弱めない
