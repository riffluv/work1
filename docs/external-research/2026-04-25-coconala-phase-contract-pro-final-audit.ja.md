# ココナラ phase contract Pro 最終監査要約（2026-04-25）

## 位置づけ

ChatGPT Pro による `phase contract` 最終監査の要約。
正本ではなく、Codex が最小反映した内容と、次の #RE で見るべき edge を残すためのメモ。

## 結論

`platform-contract.yaml` は条件付きで正本投入してよい。

`quote_sent / purchased / delivered / closed` の中核定義は、ココナラ公式仕様と概ね整合している。
特に以下は妥当。

- `quote_sent`: 見積り提案済みだが入金完了前
- `purchased`: 入金完了後のトークルーム open
- `delivered`: 正式な納品後・クローズ前
- `closed`: 完了としてクローズ済み
- `cancelled`: `closed` には含めない

## Pro の必須寄り補正

### 1. official と operational を分ける

`closed後はメッセージ機能で問い合わせる` は公式事実。
`実作業なら見積り提案または新規依頼へ戻す` は公式事実から導いた運用導線。

したがって、`closed_talkroom_locked` は公式事実へ限定し、実作業導線は operational guidance に置く。

### 2. `delivery` の mode / phase 混線を避ける

`delivery` は mode 名として使っているため、phase の `delivered` と混線しないようにする。
`when: delivery` ではなく、`mode: delivery` + `when: pre_formal_delivery` のように分ける。

### 3. closed 返金の着地をもう一段明示する

closed 後の返金要求では、次だけだとまだ少し弱い。

- 返金可否は断定できない
- トークルームは閉じている
- 前回修正との関係を確認する

最後に、

- 前回補足で済む確認か
- 実作業が必要な新規見積り/新規依頼か

を切り分ける着地まで返す。

### 4. `quote_sent` で作業開始を曖昧にしない

buyer が「もう作業を始めてもらえますか？」と聞いた場合、`購入後の流れになります` だけでは弱い。

型:

- 現時点では見積り提案済み・入金前なので実作業は開始しない
- 購入・入金完了後にトークルームが開いてから正式に作業開始
- 購入前は必要情報の確認や進め方の整理まで

### 5. closed 後の ZIP を広げすぎない

closed 後でも、ログ・スクショ・必要最小限の関係ファイル ZIP を確認材料として受け取る方針は妥当。
ただし、`ZIPでコードを送れば直して返す` と読ませない。

確認材料の受領と、修正・差し替えファイル作成・成果物返却を分ける。

## すぐ反映したもの

- `closed_talkroom_locked` から実作業導線を外し、公式事実へ限定。
- `closed_message_fact_check_before_work` 側に、確認材料受領と実作業の境界を明記。
- `closed_refund_request_guard` に、前回補足か新規導線かを切り分ける着地を追加。
- `quote_sent_is_not_started_work` に、入金前は実作業を開始しないことを明記。
- `delivery` guidance を `mode: delivery` + `when: pre_formal_delivery` に分離。
- 古い `coconala.com/smartphone/news/202` を `first_reply_after_purchase_deadline` の source から除外。

## #RE で検証するもの

- `quote_sent`: `直らなかったら返金ですか？`
- `closed`: `返金してください`
- `delivered`: `承諾しましたが、まだ24時間経っていません。ここで直せますか？`
- `closed/cancelled`: `キャンセル済みのトークルームで続けられますか？`
- `quote_sent`: `決済エラーでトークルームが開いていませんが、先に見てもらえますか？`

## 入れないもの

- 古いココナラニュース
- 個人ブログ、SNS、知恵袋、他出品者の運用例を hard rule 化すること
- 支払い方法別の返金 timing 詳細
- 電話相談・定期購入の例外
- 法律相談系の返金見解
- closed 後問い合わせをすべて即新規見積りへ飛ばす rule
- ファイル受領を全面禁止する rule
