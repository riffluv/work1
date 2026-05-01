# #RE85-87 短い棚卸し

作成日: 2026-05-01

対象:

- `RE-2026-05-01-bugfix-85-positive-flow-before-refusal-r0`
- `RE-2026-05-01-bugfix-86-positive-flow-practical-mixed-r0`
- `RE-2026-05-01-bugfix-87-business-chat-viability-agency-r1`

## 結論

#RE85-87 は採用圏。

この3本で、通常 live の `bugfix-15000` はかなり安定している。次は新しい hard rule を増やすより、soft lens の過剰発火を見ながら、実務チャットとしての自然さをさらに見る段階。

Pro にすぐ投げるより、#RE88-89 を追加で回してから、直近の採用候補をまとめて見せる方がよい。

## 採用済みの学び

### positive_flow_before_refusal

軽い手順確認では、拒否・禁止・否定から入らず、正しい通常フローを先に案内する。

例:

- 支払い前にスクショだけ送るべきか
- 支払い後にまとめて送ればよいか
- 購入後にどこへファイルを共有するか

ただし、支払い前診断、GitHub/Drive 作業面、secret 値、直接 push、本番反映、closed 後作業などの境界突破要求では不可表明を残す。

状態:

- soft subtype として採用寄り
- hard rule 化はまだしない
- あと数 batch 安定すれば gold / reviewer prompt 昇格候補

### agency_alignment の拡張

`依頼できますか` に `相談できます` で返す問題だけでなく、delivered の軽い補足にも広げる。

特に、buyer が `教えてもらえますか` `もう少し説明してもらえますか` と聞いている場面で、`補足できます` のような対応可否宣言で止まると AI / FAQ 感が出る。

標準:

- `反映するファイルだけ、こちらで短く整理します`
- `補足説明をお送りします`
- `確認する箇所だけ、専門用語を減らして整理します`

非変更:

- `できます` は blanket NG にしない
- 意味・phase・成果物 promise を変えない

### secret 混入時の伏せ直し導線

共有済み ZIP / ファイルに APIキー、Webhook secret、`.env` の値などが含まれている可能性がある時は、`確認対象にしません` だけで済ませない。

標準:

```text
該当部分を伏せた形で送り直してください。
こちらでは秘密値そのものは確認対象にしません。
```

扱い:

- `secret_safety` の補足として採用
- 通常の材料共有すべてに重い secret 警告を足さない
- 値混入が示唆されている時、または `.env` / APIキー / Webhook secret が共有物に含まれ得る時だけ使う

### closed 後 ack の中立化

closed 後の再相談で、前回しばらく安定していたことに反応する時は、軽すぎる `そこはよかったです` を避ける。

標準:

- `しばらく問題なかった後に似たStripeエラーが出ているとのこと、状況共有ありがとうございます。`
- `前回後しばらく問題なかったとのこと、状況共有ありがとうございます。`

扱い:

- 既存の `そこは` NG と `topic_label_distance` の延長
- hard rule ではなく自然化 / gold 候補

## 継続観察

### business chat viability

内容は正しいが、窓口回答・FAQ・受付票・規約説明に寄っていないかを見る。

見るもの:

- `補足できます` のような可否宣言で止まる文
- `〜の件ですね` で距離が出る文
- 処理文・条件文・安全説明が同じリズムで並ぶ文
- buyer が聞いた主質問への答えより、内部境界説明が前に出る文

ただし、これを理由に hard boundary を削らない。

### block_rhythm_flow

段落の塊感はまだ観察継続。

今の判断:

- 高リスク場面では少し硬くても許容
- 低リスク場面では、処理文が連続するなら少しつなぐ
- 句点や段落数そのものを NG にしない

## 次の #RE88 で見るとよいもの

1. 低リスク delivered 補足をさらに数件
   - `教えてもらえますか`
   - `もう少しだけ説明してもらえますか`
   - `どこを見ればいいかだけ`
2. quote_sent の軽い手順確認
   - スクショ / ZIP / Event ID / ログをいつ送るか
   - 通常フロー先行と支払い前作業不可の切り分け
3. purchased の材料過多・secret 混入疑い
   - 伏せ直し導線が重すぎないか
   - buyer burden を増やしすぎないか
4. closed 後の穏やかな再相談
   - 前回のお礼
   - しばらく安定
   - 似たエラー
   - 関係確認だけ

## Pro に聞くタイミング

今すぐでも聞けるが、最適ではない。

おすすめは、#RE88-89 を回してから。

Pro に見せる論点:

- `positive_flow_before_refusal` を gold / reviewer prompt へ昇格してよいか
- `agency_alignment` を delivered 補足まで広げた運用は妥当か
- `business chat viability` は独立 lens にすべきか、`jp_business_native_naturalness` 配下の観察で十分か
- secret 混入時の伏せ直し導線は hard guard / gold / skill rule のどこに置くべきか
- block rhythm / 契約説明っぽさを、どこまで改善し、どこから安全境界として残すべきか

## 固定する非変更

- 通常 live / #RE に出してよいのは `bugfix-15000` のみ
- `handoff-25000`、25,000円、主要1フロー整理、未公開導線は出さない
- 自然化のために、価格、scope、phase、secret、public/private、payment route、closed 後実作業境界を弱めない
- `できます`、`ではありません`、`大丈夫です`、`〜の件` は blanket NG にしない
