# Gold Reply 46 — context anchor granularity / input summary overfit

status: `current`
scope: `reply-only`
family: `context_anchor_granularity`
phases: `prequote`, `quote_sent`, `purchased`, `delivered`, `closed`
related_lenses:
- `conversation_flow_naturalness`
- `context_anchor_granularity`
- `answer_focus_alignment`
- `response_weight_mismatch`
- `buyer_burden_alignment`

## 使いどころ

- buyer が長めの相談文で、症状・作成経緯・材料不安・価格質問をまとめて書いている時。
- 返信冒頭で buyer 文をきれいにまとめ直しすぎて、入力要約 bot のように見える時。
- ただし、相手文をまったく拾わずに雑な直答へしたくない時。

## 判断

主質問への直答を先に置く。
context anchor は、主質問への答えに必要な核だけにする。
背景や不安は、直答後に分けて扱う。

## 避けたい例

```text
AIで作った部分と外注コードが混ざっていて、関係するファイルが分からない状態でも、15,000円でご依頼いただけます。
Stripe決済は完了しているのにサイト側で購入済みにならない症状として、原因確認から進めます。
```

この文は意味としては合っている。
ただし、buyer の長い入力を分類して条件句にまとめ直してから回答しているように見える。

## 推奨例

```text
ご相談ありがとうございます。

15,000円でご依頼いただけます。
決済後にサイト側で購入済みにならない不具合として対応できます。

AIで作った部分や外注コードが混ざっていても問題ありません。
関係ファイルも、無理に絞らなくて大丈夫です。必要な範囲はこちらで見ながら確認します。

ご購入後は、プロジェクト一式をZIPでトークルームに添付してください。
あわせて、購入済みにならない画面のスクショや、出ているログがあれば送ってください。

.env、APIキー、Webhook Secret、DB接続文字列などの値そのものは、ZIPやログに含めないでください。
不足があれば、こちらから追加でお伝えします。

この内容で問題なければ、そのままご購入ください。
```

## reviewer 観点

- 主質問への直答が先にあるか。
- 冒頭で buyer 文の背景・症状・不安・作成経緯を全文要約していないか。
- scope に必要な anchor は1文だけ残っているか。
- 材料不安は材料案内の位置で扱えているか。
- secret 値除外、phase、価格、scope を自然化で削っていないか。

## 避けること

- `状態でも` / `症状として` を blanket NG にする。
- 相手文を拾わず、何に答えているのか分からない直答にする。
- ZIP を全ケース hard rule にする。
- 自然化のために支払い前診断・GitHub確認・secret 値要求へ滑る。
