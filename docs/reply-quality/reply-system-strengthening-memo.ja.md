# 返信システム強化メモ

最終更新: 2026-04-19

## 1. 目的
- 返信システムを、`文章のその場しのぎ修正` ではなく、`主質問に正面から答える構造` として育てる。
- `AI の思考を早い段階で潰さない` ことを守りつつ、サービス内容・公開範囲・運用ルールを外さない。
- live 系を壊さず、learning / stress test / 外部AI監査を分離して運用する。

## 2. 現在の判断
- 骨格はかなり良い。全面再設計は不要。
- 弱さの主因は `scenario 不足` ではなく、`decision / reply_contract / response_decision_plan` が最終文に反映されたかの保証不足。
- 次に強くする場所は、renderer 増殖ではなく、`contract -> output` の共通 property check。

## 3. このシステムで守ること
- 相手の主質問に先に答える。
- 答えられることを答える前に、聞き返しへ逃げない。
- 既に相手が出した情報を聞き直さない。
- 相手が不安や過去の嫌な体験を明示しているときは、`整理してお返しします` `確認して返します` のような報告語で逃げず、`対応します` `進めます` の側へ着地させる。
- `切り分ける` `整理する` `ハンドリングする` のような作業者側の内部プロセス語は、buyer 向けには結果説明へ言い換える。
- 技術説明は `原因推定` より `まずどこを見るか / 何の確認が先か / まだ断定しない` を優先する。
- サービス内容・公開範囲・運用ルールを最終文でも守る。
- 自然化は最後に行う。主質問回答と policy を壊す自然化は行わない。

## 4. このシステムでやらないこと
- 失敗ケースごとに scenario を増やして塞ぐ。
- renderer をケース別に増やしてモグラたたきに戻る。
- live 系の送信可否を外部AI監査に直接委ねる。
- 「もっと自然な文」に寄せるために、主質問回答や policy を弱める。
- 新しい重い層を足して、既存の `reply_contract / answer_map / ask_map / response_decision_plan` を二重化する。

## 5. 実行原則
1. `scenario` より `主質問` を上位に置く。
2. `plan がある` では不十分で、`最終文に出た` まで見る。
3. 聞き返しは `blocking missing facts` がある時だけ許す。
4. `facts_known` や buyer が明示した情報の再質問は品質事故として扱う。
5. service grounding は生成前だけでなく、最終文でも検査する。
6. scenario 追加より property 追加を優先する。
7. live / learning / external audit を混ぜない。

## 6. 壊さない順番
### Step 1. baseline を固定する
- まず現状の合格状態を保存する。
- 先に renderer を触らない。
- 基準は `full regression` と `role suites`。

### Step 2. common validator に warn-only の property check を足す
- 最初に触るのは各 renderer ではなく、共通の最終チェック側。
- 追加対象は次の4つで十分。
  - `main_question_answered`
  - `answer_before_ask`
  - `ask_only_if_blocking`
  - `stage_policy_grounded`
- 最初は fail させず、warning / report だけ出す。

### Step 3. strict は role ごとに段階導入する
- 最初に strict にするのは `edge / eval / holdout`。
- `seed / renderer_seed` は最後。
- live に近いケースをいきなり hard fail にしない。

### Step 4. 落ちたものを fixture 化する
- 落ちたらすぐ文面 patch に行かない。
- まず bucket に分けて fixture に戻す。
- 代表 bucket:
  - `main_question_unanswered`
  - `asked_before_answering`
  - `known_fact_reask`
  - `ask_without_blocking`
  - `service_policy_violation`
  - `stage_policy_violation`

### Step 5. 最後に必要最小限だけ renderer を直す
- 直す場所は `property` で落ちた根本だけ。
- 文面 patch を先にしない。

## 7. 既存構造の使い方
### prequote
- `reply_contract` を中心に使う。
- `primary_question_id / answer_map / ask_map / required_moves / forbidden_moves` を主質問回答の正本として扱う。
- 追加するなら新層ではなく、他 lane と揃う最低限の `response_decision_plan` 要素を薄く足す。

### quote_sent / post_purchase / delivered / closed
- `response_decision_plan` を中心に使う。
- 特に次を重要 field として扱う。
  - `primary_concern`
  - `facts_known`
  - `blocking_missing_facts`
  - `direct_answer_line`
  - `response_order`

### 共通
- `reply_contract` と `response_decision_plan` は二重正本にしない。
- validator は、両者のどちらかから必要情報を fallback で読む形に寄せる。

## 8. property として見たいもの
- `main_question_answered`
  - 主質問への直接回答が最初の2段落以内にあるか
- `answer_before_ask`
  - ask / hold reason / 手順説明が direct answer より前に出ていないか
- `ask_only_if_blocking`
  - `blocking_missing_facts` が空なのに聞き返していないか
- `no_reask_known_facts`
  - `facts_known` や buyer 既出情報を再質問していないか
- `no_report_verb_landing_for_anxiety`
  - 相手が不安を明示しているのに、直接回答が `整理する / 確認する / お返しする` のような報告語で終わっていないか
- `no_internal_process_terms_for_buyer`
  - `切り分ける` `整理する` `ハンドリングする` など、こちらの作業工程の名前が buyer 向けにそのまま出ていないか
- `technical_line_is_confirmation_plan`
  - 技術説明が `可能性が高い / おそらく / 思われます` のような未確認推定ではなく、`まずどこを見るか` の確認方針として書かれているか
- `service_grounded`
  - `service-registry` と service pack に反しないか
- `stage_policy_ok`
  - stage に合わない案内をしていないか

## 9. live / learning / external audit の分け方
### live
- 少数固定。
- 目的は退行検出。
- warning は出してよいが、最初から送信ブロックしない。

### learning / stress test
- 件数を増やしてよい。
- 目的は弱点発見。
- strict で落としてよい。
- 失敗は fixture と property bucket に戻す。

### external audit
- 文章添削者ではなく、`未回答検出器` として使う。
- 聞くべき観点:
  - 主質問は何か
  - 最初の2段落以内に答えているか
  - 既出情報を聞き直していないか
  - 聞き返しは blocking missing facts に限られているか
  - サービス範囲・公開範囲・運用ルールを破っていないか
- 返答は prompt patch に直結させず、fixture / property / validator へ戻す。
- 相手が不安を明示しているケースでは、`報告語で弱く着地していないか / 行動コミットで着地しているか` も確認する。
- 内部プロセス語が buyer 向けにそのまま出ているときは、`結果としてどうなるか` の表現へ直す方向で戻す。
- 技術説明は、buyer が書いた事実から自然に言える確認方針までに留め、未確認の原因推定は warning 対象として扱う。

## 10. いま採るべき最小方針
- 新しい大規模再設計はしない。
- 新しい重い層は作らない。
- 最初にやるのは `warn-only の property check`。
- 次に `role ごとの strict 化`。
- その後に `fixture 追加`。
- renderer 修正は最後の最小変更だけにする。

## 11. 一文で言うと
- 返信品質は「文章の自然さ」より先に、「主質問に対する回答義務を最終文で履行したか」で管理する。

## 12. ベースライン例
- 技術説明の安全性では、`CASE-013` 型を良例として扱う。
- buyer が `今回の修正の影響ありえますか？` のように推定を求めても、
  - `いまの情報だけではまだ断定しません`
  - `まずどこを見るか`
  - `必要なら最小限の追加情報だけ頼む`
  の順で返し、原因推定へ飛ばない形を基準にする。
