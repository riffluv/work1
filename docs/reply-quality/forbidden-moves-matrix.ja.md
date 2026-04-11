# forbidden_moves 付与マトリクス（reply-only）

更新日: 2026-04-11

## 目的

- `forbidden_moves` を感覚で付けず、`どの場面で何を立てるか` を固定する
- `主質問ファースト` と `phase漏れ防止` を、文面調整ではなく契約レベルで止める
- 5件バッチ監査で見つかった崩れを、再現可能な付与ルールへ戻す

## 原則

- `forbidden_moves` は writer を縛るためではなく、`正しいが余計なこと` を前に出させないためのガードレール
- `required_moves` と対で考える
- `forbidden_moves` が必要な場面で立っていないなら、文面の問題ではなく contract の問題として扱う

## 付与順

1. `state`
2. `reply_skeleton`
3. `burden_owner`
4. `primary_question_id`
5. `explicit_questions`
6. policy 上の必須説明があるか

この順で見て、最後に `forbidden_moves` を決める。

## ルール一覧

### 1. `reopen_estimate_intake`

付与する:
- `state: purchased / predelivery / delivered / closed`

意図:
- 購入後や継続会話で、見積り相談の初回受付へ戻るのを止める

止めたい崩れ:
- `まず対応できるか判断します`
- `対象かどうかを見ます`
- `見積もりからになります`

主な分類:
- `QA-03 phase漏れ`

### 2. `ask_client_to_prioritize_when_burden_owner_us`

付与する:
- `burden_owner: us`

意図:
- 方向決めをこちらが担うべき場面で、優先順位づけを buyer に返さない

止めたい崩れ:
- `どちらを先に見るか決めてください`
- `優先順位を教えてください`

主な分類:
- `QA-01 主質問ズレ`
- `QA-07 温度感ズレ`

### 3. `numbered_QA_for_all_questions`

付与する:
- `reply_skeleton: post_purchase_quick`
- 主質問が1つで、残りは後段補足で足りる場面
- 短く返す指定がある場面

付与しない:
- buyer 自身が番号付き回答を求めている
- 明示質問が複数あり、全部に分離回答しないと誤読する

意図:
- 何でも番号回答にして機械感を出すのを止める

主な分類:
- `QA-06 テンプレ臭`

### 4. `vague_hold_without_reason`

付与する:
- `answer_map` に `answer_after_check` が1件でもある場面

意図:
- 保留が必要でも、理由も再回答条件もなく濁すだけの文を止める

止めたい崩れ:
- `現時点では分かりません`
- `見てみないと分かりません`

主な分類:
- `QA-01 主質問ズレ`
- `QA-07 温度感ズレ`

### 5. `internal_term_exposure`

付与する:
- 外向け返信のほぼ全件

意図:
- 内部ラベル、内部評価語、運用都合の語感を外へ漏らさない

止めたい崩れ:
- `対象候補です`
- `切り分けたいです`
- `今回は範囲で見ています`

主な分類:
- `QA-04 内部語漏れ`

### 6. `overexplain_branching`

付与する:
- `state: purchased` の軽い追加報告
- 主質問が単純な進捗・可否確認で、分岐説明が主ではない場面

付与しない:
- 実際に scope 再確認が主題
- 追加料金や別原因の説明自体が主質問

意図:
- 購入後の短い返答で、必要以上に分岐説明へ寄るのを止める

主な分類:
- `QA-02 余計情報差し込み`
- `QA-06 テンプレ臭`

### 7. `frontload_price_when_not_asked`

付与する:
- 相手が価格を明示質問していない
- primary question が `お願いできますか / 対応できそうですか / 対象になりますか` 系
- policy 上、価格を先に言わないと誤解が大きい場面ではない

付与しない:
- primary question 自体が価格
- 予算不安、追加料金不安、税込み確認が明示されている
- route / service の説明上、価格直答が必須

意図:
- `正しい価格情報` を、主質問より先に差し込む事故を止める

主な分類:
- `QA-02 余計情報差し込み`

### 8. `frontload_branching_risk_when_not_asked`

付与する:
- 相手が別原因や追加料金の不安を明示していない
- primary question が可否、対象性、今の段階の動き方
- 分岐説明が policy 上の必須先出しではない

付与しない:
- buyer が `別料金になりますか` `追加でかかりますか` `複数原因だったらどうなりますか` と聞いている
- scope 再確認そのものが主題

意図:
- 善意で境界説明しすぎて、主質問からズレるのを止める

主な分類:
- `QA-02 余計情報差し込み`

### 9. `frontload_scope_explanation_when_not_asked`

付与する:
- 相手が広い範囲説明を求めていない
- primary question が単純な対応可否、対象可否、次の一手
- scope の長い説明を先頭へ置く必要がない

付与しない:
- `どこまで入りますか` `何が範囲ですか` が主質問
- 断る / 保留する理由として scope 説明が先に必要

意図:
- 内部では大事な範囲説明を、外向けで先頭に出しすぎない

主な分類:
- `QA-01 主質問ズレ`
- `QA-02 余計情報差し込み`

## 最低セット

### prequote / bugfix / primary が可否質問

基本で立てる:
- `internal_term_exposure`
- `frontload_price_when_not_asked`
- `frontload_branching_risk_when_not_asked`
- `frontload_scope_explanation_when_not_asked`

### purchased / quick reply

基本で立てる:
- `reopen_estimate_intake`
- `internal_term_exposure`
- `overexplain_branching`

必要なら追加:
- `ask_client_to_prioritize_when_burden_owner_us`
- `numbered_QA_for_all_questions`

### hold 系

基本で立てる:
- `internal_term_exposure`
- `vague_hold_without_reason`

prequote なら追加候補:
- `frontload_price_when_not_asked`
- `frontload_branching_risk_when_not_asked`
- `frontload_scope_explanation_when_not_asked`

## 実装上の見方

- `forbidden_moves` の付与漏れは、naturalizer ではなく router / contract 層の問題
- 文面側で毎回頑張って直すのではなく、まず `reply_contract` に戻す
- 5件監査で同じ崩れが2回出たら、付与条件をこの表へ追加する

## 固定したいこと

- `forbidden_moves` は「思いついたら足す」ではなく、`state / skeleton / burden_owner / primary question` から半機械的に決める
- 主質問ファースト事故は、writer の気合いではなく contract で止める
