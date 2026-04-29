# Gold Replies（reply-only）

## 目的
- 良い返信を「雰囲気で思い出す」のではなく、再利用できる基準として残す。
- 温度感、情報量、質問数、次アクションの出し方を安定させる。
- 個別案件の完全テンプレではなく、近いケースのアンカーとして使う。

## 使い方
- 新しく返信を作る前に、近い 1 本だけ見る。
- `status: current` 相当として扱えるものだけを few-shot に使う。古い比較用・監査用の例は `eval_only`、現行ルールと矛盾する例は `superseded` として扱い、送信用の基準にしない。
- 内容をそのまま流用するのではなく、
  - 書き出しの温度感
  - 依頼の数
  - 既出情報の受け方
  - 次アクションの置き方
  を合わせる。
- 返信後は `ng-expressions.ja.md` と仕上げ前チェックで再確認する。

## 運用ルール
- 3〜5本で始める。最初から増やしすぎない。
- 実案件で「ほぼそのまま送れた」「手修正が少なかった」返信だけ追加する。
- 1回限りの好みや偶然うまくいった文は入れない。
- 納品物本文には使わず、トークルーム返信だけで使う。
- 旧ルールと競合する例を見つけた場合は、削除より先に `superseded` として参照資格を落とす。

## 初期セット
- `01_bugfix_non_engineer_first-contact.ja.md`
- `02_bugfix_repeat-request_same-area.ja.md`
- `03_bugfix_scope-judge_separate-cause.ja.md`
- `04_bugfix_boundary_clear-symptom-first.ja.md`
- `05_handoff_private_quote-gate.ja.md`
- `06_purchased-closed_scope-continue.ja.md`
- `07_handoff_explanation_non_engineer.ja.md`
- `08_bugfix_scope-buyer-words.ja.md`
- `09_bugfix_setting-vs-code_self-fix-intent.ja.md`
- `10_delivered_value-doubt_light-fix.ja.md`
- `11_boundary_unknown-spec-vs-bug.ja.md`
- `12_boundary_refuse-external-share-and-push.ja.md`
- `13_bugfix_structured-intake_ack-then-ask-delta.ja.md`
- `14_quote-sent_refuse-zoom_with-anxiety.ja.md`
- `15_repeat-project_discount-firm-but-natural.ja.md`
- `16_handoff_followup_deeper-memo-paid-supplement.ja.md`
- `17_purchased_secret-value_and-share-split.ja.md`
- `18_purchased_deploy-anxiety_no-direct-deploy_but-guide.ja.md`
- `19_prequote_success-rate-fear_no-guarantee_but_clear_value.ja.md`
- `20_closed_repeat_with-refund-anxiety_scope-first.ja.md`
- `21_boundary_bugfix-vs-handoff_confused-route_bugfix-first.ja.md`
- `22_phase-contract-edge_next-path.ja.md`
- `23_closed-materials-work-boundary.ja.md`
- `24_transaction-model-gap_edges.ja.md`
- `25_pre-shelf-regression-boundaries.ja.md`
- `26_prequote-concrete-symptom-pickup.ja.md`
- `27_closed-general-check-method.ja.md`
- `28_prequote-price-scope-boundaries.ja.md`
- `29_price-guarantee-refund-risk.ja.md`
- `30_normal-boundary-routing.ja.md`
- `31_normal-scope-support.ja.md`
- `32_boundary-mixed-routing.ja.md`
- `33_boundary-transfer.ja.md`
- `34_post-chg068-near-miss.ja.md`
- `35_response-weight-mismatch.ja.md`
- `36_conversation-flow-naturalness.ja.md`

## Gold 26-33 family index

Gold はテンプレートではなく、近い判断順序を思い出すための anchor として使う。
26 以降は件数が増えてきたため、個別ファイル名ではなく family で探す。

| family | gold | 使う場面 | 使わない場面 |
| --- | --- | --- | --- |
| concrete_prequote | 26 | 具体症状がある prequote で、buyer の語を拾ってから価格・購入導線へ進む時 | 価格・保証・返金・復旧時間など、主質問がサービス仕様の時 |
| closed_general_check | 27 | closed 後に一般的な確認方法だけを聞かれ、実作業に入らない時 | コード修正指示・成果物返却・返金要求が混ざる時 |
| price_scope_boundary | 28, 29 | 値引き、保証、返金、復旧時間、複数症状、追加料金不安など、料金・範囲の主質問に答える時 | 通常の症状受けだけで足りる時 |
| technical_boundary | 30, 31 | 非Stripe決済、ブラウザ依存、本番/preview差、秘密情報、外部共有、テスト追加など、技術境界を切る時 | provider 側の管理画面操作や外部共有を受ける時 |
| boundary_transfer | 32, 33, 34 | 仕様/不具合境界、quote_sent 語彙、closed 後の別件・割引・新規導線、怒り気味 buyer、複数質問混在への回収を扱う時 | phase が単純な通常 prequote の時 |
| response_weight | 35 | 安全境界は守れているが、buyer の文量・温度・質問数に対して返信が重い時。短くても安全な例と、重くても必要な例を比べる時 | 返金/保証/closed/秘密情報などの必要境界を削る理由にする時 |
| conversation_flow | 36 | 内容は正しいが、短文断定の連続・確認語密集・次アクション不足で会話の流れが切れている時 | 価格・scope・phase・secret・payment route を弱めて自然化する理由にする時 |

### 抽出して validator / renderer へ戻す候補

- Gold 26: `内容ありがとうございます -> この不具合なら15,000円 -> どこで止まっているか確認` の旧三点セット検出。
- Gold 29: 復旧時間・保証期間・返金/キャンセル質問で、通常の不具合受付テンプレに流さない direct answer。
- Gold 30/31: 非Stripe名が出た時に、決済サービス全体ではなく `Next.js側のWebhook/API受信処理` へ scope を閉じる。
- Gold 32/33: `quote_sent` / `closed` の phase 語彙と導線。`トークルーム内` や旧トークルーム継続を validator 候補にする。
- Gold 34: 複合質問で、返金・料金・Slack・秘密情報・closed 後導線など事故りやすい明示質問を落とさない。
- Gold 35: `response_weight_mismatch` は validator 化せず、短くても安全 / 重くても必要の対比 anchor として使う。
- Gold 36: `conversation_flow_naturalness` は hard validator 化せず、固定価格・scope・phase を保ったまま、短文断定の連続、確認語密集、次アクション不足を最小差分で整える anchor として使う。
