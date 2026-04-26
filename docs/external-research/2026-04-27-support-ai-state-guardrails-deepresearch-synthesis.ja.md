# Support AI State / Transaction Guardrails Deep Research 統合メモ

日付: 2026-04-27  
入力:
- ChatGPT Deep Research: `実務返信AIを状態・取引構造・監査ループ付きシステムとして成立させる方法4-27.txt`
- Gemini Deep Research: `gemini-実務返信AIにおける状態管理と取引構造監査の設計手法：次世代カスタマーサポートLLMの実装論4-27.txt`

扱い: 外部調査メモ。正本 rule へ直入れしない。#RE の再発証拠と照合し、`validator / reviewer_prompt / gold / 入れない` に棚卸しする。

## 総合結論

2本とも、現在の返信システムの方向性を強く支持している。

特に重要なのは、AI support agent の実務設計は「LLMにうまい返信を書かせる」ではなく、`state / workflow / policy / action boundary / QA / continuous improvement` を LLM の外側に置く方向へ収束していること。

これは、現在の `phase contract`、`transaction_model_gap`、`closed 後の確認材料/実作業境界`、`#RE -> 監査 -> 再発だけ戻す` と整合する。

## ChatGPT Deep Research の強い点

- 実務実装への落とし込みが具体的。
- Intercom / Zendesk / Salesforce / Dialogflow CX / NeMo / Replicant / Rasa / LangGraph などを、`knowledge / workflow / policy / action / QA / analytics` の責任分界として整理している。
- `transaction_model_gap` を、既存概念の合成としてかなり的確に位置づけている。
  - `policy-invisible violations`
  - `business-state-aware DST`
  - `common-ground audit`
  - `route clarity`
- `validator / reviewer_prompt / gold / 入れないもの` への分類が、そのまま棚卸し材料になる。
- 「単発違和感で rule を増やさず、failure cluster で戻す」方針を支持している。

## Gemini Deep Research の強い点

- 批判的検証として、`transaction_model_gap` は既存概念で代替しきれず、独自ラベルとして価値が高いと明言。
- 英語圏の `refund / compensation / zero-touch resolution` を日本語・C2C/スキルシェアへ直輸入する危険性を強く指摘。
- 日本語の `Responsibility Over-admission Risk`、過剰謝罪、直接的拒否、敬語崩れを詳しく整理。
- `Validator = 決定論的 hard block`、`Reviewer = 文脈監査`、`Gold = phase別の良例型` という分担を明確にしている。
- `transaction_model_gap` を「言語生成レイヤーとビジネス取引レイヤー間の構造的断絶」と表現しており、今の違和感の説明としてかなり強い。

## 共通している重要結論

### 1. LLM 単体では足りない

両者とも、LLM の文章力や RAG だけでは、実務 support AI は安定しないと見ている。

必要なのは:

- 明示 state
- phase contract
- deterministic validator
- business workflow
- policy/action guardrails
- QA scorecard
- continuous improvement loop

### 2. transaction_model_gap は本質を突いている

完全一致する既存用語はないが、近い概念はある。

- Dialogue State Tracking: 会話状態の追跡
- policy-invisible violations: 見えない policy state による違反
- semantic grounding: 事実・定義への接地
- context drift: multi-turn での状態逸脱
- common ground misalignment: 会話前提のズレ
- workflow / action guardrails: 許可された行為の境界

ただし、`transaction_model_gap` はこれらより実務寄りで、支払い状態・作業開始条件・成果物返却・正式導線・buyer の次アクションまで含む。

現時点では、内部ラベルとして残す価値が高い。

### 3. closed / delivered / quote_sent は validator 寄り

両者とも、以下は prompt の言い回しではなく、hard guard に寄せるべきとしている。

- quote_sent で入金前にコード/ログを見て原因確認しない
- delivered で承諾前/承諾後/closed 後導線を混ぜない
- closed 後に旧トークルーム継続・成果物返却・実作業を前提にしない
- closed 後は確認材料と実作業を分ける
- secrets / PII / 外部共有 / 返金断定 / 責任認定は hard guard

### 4. QA は単一スコアではなく多軸

既存軸:

- 主質問への直答
- scope 順守
- 情報節約
- 自然さ
- 次アクション明確さ

追加候補は妥当:

- transaction clarity
- phase route clarity
- work/payment boundary clarity
- buyer not lost
- responsibility over-admission risk
- free-support expectation risk
- surface overexposure / request minimality

ただし全部を本文生成 rule にしない。`validator` と `reviewer_prompt` に分ける。

## すぐ戻す候補

### Validator

以下は再発証拠がすでにあるため、優先して validator / lint 側で見る候補。

1. `closed` 後に実作業・修正返却・具体的コード修正指示を約束していないか。
2. `closed` 後の無料要求で、無料対応期待または通常料金確定のどちらにも寄せすぎていないか。
3. `quote_sent` で入金前の原因確認・コード確認を始めるように見えないか。
4. `delivered` で承諾前/承諾後/closed 後の導線が混ざっていないか。
5. `.env` / APIキー / Webhook秘密値 / 外部共有を求めていないか。
6. 責任・返金・キャンセルを確定していないか。
7. generic fallback が具体質問を潰していないか。

### Reviewer Prompt

以下は LLM 監査で見る方がよい。

1. 返信は今の取引状態に合っているか。
2. buyer が次に何をすればよいか迷わないか。
3. できる確認と、正式導線が必要な実作業を分けているか。
4. 感情受けはあるが、過失認定・無料期待・責任承認に読めないか。
5. 内部分類語を buyer 向けに言い換えているか。
6. 自然だが transaction structure が曖昧になっていないか。

### Gold

優先して増やす価値がある型。

1. `closed`: 確認材料は見る / 実作業は正式導線。
2. `closed`: 怒り気味・無料対応要求。
3. `closed`: コード修正助言は実作業の一部。
4. `quote_sent`: 入金前作業開始要求への断り。
5. `delivered`: 承諾前/承諾後の分岐。
6. `purchased`: 進捗催促で現在地を可視化。
7. `prequote`: 普通の見積り相談を硬くしない一息回答。

## まだ入れない方がよいもの

1. 英語圏の返金・補償・zero-touch resolution 慣習。
   - ココナラの C2C/スキルシェアでは危険。
2. 感情検知だけで即 escalation。
   - 日本語では婉曲不満が多く、ノイズ化しやすい。
3. 過剰な empathy / apology prompt。
   - 責任認定・無料期待につながりやすい。
4. 細かすぎる敬語 validator。
   - hard rule にすると過検知が増える。
5. 単発の言い回し禁止。
   - #RE の再発 cluster を待つ。
6. すべてを if-then で prompt に詰め込むこと。
   - 骨格を壊し、Codex の判断を削ぐ。

## Knowledge Architecture への示唆

両レポートとも、記憶領域の置き方に関して重要な示唆を含む。

今後の理想構成:

- `service facts`: 価格・範囲・公開状態・禁止事項
- `platform contract`: ココナラ phase / トークルーム / closed / 見積り導線
- `phase ledger`: 今の返信で前提にする取引状態
- `gold replies`: 通過済みの良い型
- `validator`: 絶対に落とす事故
- `reviewer_prompt`: 文脈・違和感・buyer not lost の監査
- `learning-log`: まだ rule にしない観察
- `skill`: 上記を必要な順番で読み、Writer を縛りすぎない起動レイヤー

重要なのは、知識を増やすことではなく、どの知識がどの層で効くかを固定すること。

## 次の実務アクション

### P0

- 現行 validator / lint が、上記 hard guard をどこまで拾えているか棚卸しする。
- `closed` / `delivered` / `quote_sent` の generic fallback 検出を再確認する。
- `transaction_model_gap` を reviewer_prompt の明示レンズとして維持する。

### P1

- batch-09〜21 の通過文から gold 候補を整理する。
- `buyer not lost` / `work-payment boundary` / `free-support expectation` を reviewer_prompt へ最小追加する。
- `surface_overexposure` は request minimality として扱うか検討する。

### P2

- #RE で、普通の prequote と phase sentry を混ぜて、重くなりすぎないか継続確認する。
- closed の怒り気味・無料要求・コード助言要求・外部共有要求を regression fixture として残す。

## 現時点の判断

今回の2本は、返信システムの方向性をかなり強く補強している。

特に `transaction_model_gap` は、外部概念に近いものはあるが、ココナラ日本語実務返信向けには独自ラベルとして残す価値が高い。

ただし、外部調査の知見をそのまま rule に増やすと骨格が重くなる。正しい使い方は、#RE の再発証拠と照合し、`validator / reviewer_prompt / gold` へ最小反映すること。
