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
