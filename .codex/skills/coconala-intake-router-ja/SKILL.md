---
name: coconala-intake-router-ja
description: "ココナラ相談文の入口判定専用。相手文を、経路・状態・サービス適合・リスク・不足情報・次アクションへ構造化し、返信文生成の前段を固定する。"
---

# ココナラ入口ルーター

## 目的
- 相手文をいきなり返信文へせず、先に安全な判定結果へ落とす。
- 誤判定、聞きすぎ、規約事故、スコープ事故を減らす。
- 返信文作成 skill の前段として使う。
- `何を返すか` だけでなく、`どう向き合って返すか` も前段で固定する。
- 返信姿勢だけでなく、下流が勝手に骨格を戻しにくい実行契約も前段で固定する。

## このskillを使う場面
- 相手文を貼られて、まず何を返すべきか整理したいとき
- `#A` で分析のみ返したいとき
- プロフィール経由やメッセージ経由で、主力サービス適合を見たいとき
- 返信文を作る前に、リスクと不足情報を固定したいとき

## 最初に見るファイル
1. `/home/hr-hm/Project/work/ops/common/output-schema.yaml`
2. `/home/hr-hm/Project/work/ops/common/interaction-states.yaml`
3. `/home/hr-hm/Project/work/ops/common/risk-gates.yaml`
4. `/home/hr-hm/Project/work/ops/common/routing-table.yaml`
5. `/home/hr-hm/Project/work/ops/common/coconala-rule-guard.md`
6. `/home/hr-hm/Project/work/ops/services/next-stripe-bugfix/service.yaml`
7. `/home/hr-hm/Project/work/ops/services/next-stripe-bugfix/evidence-minimum.yaml`
8. `/home/hr-hm/Project/work/ops/services/next-stripe-bugfix/scope-matrix.md`

## 入力の最小形
- `src`: `service` / `profile` / `message` / `talkroom`
- `state`: `prequote` / `quote_sent` / `purchased` / `predelivery` / `delivered` / `closed`
- `reply`: `analysis_only` / `make_reply`
- `raw_message`: 相手文そのまま
- `service_hint`: 任意。分かるときだけ

## 標準ルート
1. 相手文から事実だけ抽出する。
2. 主力サービス適合を `high / medium / service_mismatch_but_feasible / low / unknown` で置く。
3. `risk-gates` に当てて、`allow / hold / decline` 相当の危険を拾う。
4. スコープを `same_cause_likely / different_cause_likely / undecidable / not_applicable` のどれかへ落とす。
5. `case_type` と `certainty` を決める。
6. `explicit_questions` を作り、`primary_question_id` を1つ決める。
7. `answer_map` と `ask_map` を含む `reply_contract` を作る。
8. `reply_stance` を決める。`answer_timing` は `primary_question_id` に対応する `answer_map[].disposition` から要約として置く。
9. 不足情報は、その状態で本当に必要なものだけ最大3点に絞る。
10. `next_action` を1つに絞る。
11. `reply` が明示されていない限り、送信用文面は作らない。

## 判定フロー
1. 相手文から事実だけ抽出する。
2. 主力サービス適合を `high / medium / service_mismatch_but_feasible / low / unknown` で置く。
3. `risk-gates` に当てて、`allow / hold / decline` 相当の危険を拾う。
4. スコープは `same_cause_likely / different_cause_likely / undecidable / not_applicable` のどれかへ落とす。
5. `case_type` と `certainty` を決める。
6. `explicit_questions` を作り、`primary_question_id` を1つ決める。
7. `answer_map` と `ask_map` を含む `reply_contract` を作る。
8. `reply_stance` を決める。`answer_timing` は `primary_question_id` に対応する `answer_map[].disposition` から要約として置く。
9. 不足情報は、その状態で本当に必要なものだけ出す。
10. 次アクションを1つに絞る。
11. `reply` が明示されていない限り、送信用文面は作らない。

## `case_type` と `certainty` の決め方
出力に次を含める。

```yaml
case_type: bugfix | handoff | boundary | after_purchase | after_close
certainty: high | low
```

### case_type
- 具体的な症状・不具合調査・修正が主なら `bugfix`
- 主要1フローの整理や引き継ぎが主なら `handoff`
- bugfix / handoff / 実装支援の境界で即断しにくいなら `boundary`
- `state: purchased / predelivery / delivered` で進行中や購入後対応が主なら `after_purchase`
- `state: closed` の再相談や再発なら `after_close`

### certainty
- 価格・入口・対応可否を、今ある情報でほぼ即答できるなら `high`
- 入口や価格の判定に、追加証跡や追加1〜2点が必要なら `low`

## `reply_stance` の決め方
出力に次の4項目を含める。

```yaml
reply_stance:
  answer_timing: now | after_check
  burden_owner: us | client | shared
  empathy_first: true | false
  reply_skeleton: estimate_initial | estimate_followup | post_purchase_receipt | post_purchase_quick | post_purchase_report | delivery
```

### answer_timing
- `answer_timing` は主質問の要約フィールドであり、実行契約の正本ではない
- 実際に何を今答えるか / 確認後に返すかは `reply_contract.answer_map[]` を正本にする
- `answer_timing` を出す場合は、`primary_question_id` に対応する `answer_map[].disposition` と矛盾させない

### burden_owner
- 相手が `おまかせで` `分からないので` `決めてほしい` なら `us`
- 相手が必要情報を出すだけで足りるなら `client`
- こちらが方向を決めつつ、相手にも最小限の判断を求めるなら `shared`

### empathy_first
- `emotional_caution: true` なら原則 `true`
- 相手が疲弊、焦り、放置不安、自責を強く出しているなら `true`
- 技術質問が中心で感情負荷が低いなら `false`

### reply_skeleton
- `state: prequote` の初回相談 -> `estimate_initial`
- `state: prequote` の追加往復 -> `estimate_followup`
- `state: purchased` で資料受領直後 -> `post_purchase_receipt`
- `state: purchased` の軽い質問や追加報告 -> `post_purchase_quick`
- `state: purchased` の途中報告や調査進捗 -> `post_purchase_report`
- `state: predelivery / delivered` -> `delivery`

## `reply_contract` の決め方
`reply_stance` の次に、下流が守るべき実行契約を出力に含める。

```yaml
reply_contract:
  primary_question_id: q1
  explicit_questions:
    - id: q1
      text: 15,000円で対応できますか
      priority: primary
      source_span: optional
  answer_map:
    - question_id: q1
      disposition: answer_now | answer_after_check | ask_client | decline
      answer_brief: optional
      hold_reason: optional
      revisit_trigger: optional
      evidence_refs: optional
  ask_map:
    - id: a1
      question_ids: [q1]
      ask_text: 不具合が起きる画面を1つ教えてください
      why_needed: 同一原因 / 1フロー判定のため
      evidence_kind: optional
  issue_plan:
    - issue: 税込みか
      disposition: answer_now | answer_after_check | ask_client | decline
      reason: optional
      depends_on: optional
  required_moves:
    - answer_directly_now
    - defer_with_reason
  forbidden_moves:
    - reopen_estimate_intake
    - numbered_QA_for_all_questions
```

### primary_question_id / explicit_questions
- `explicit_questions` には、相手が明示した質問だけを入れる。
- 勝手な善意解釈で `implicit_questions` を増やさない。
- `primary_question_id` は、最初に答えるべき主質問を1つだけ指す。

### answer_map
- `answer_map` は renderer と lint が使う正本で、`issue_plan` より優先する。
- 各質問を `answer_now / answer_after_check / ask_client / decline` のどれかへ落とす。
- `answer_after_check` には必ず `hold_reason` と `revisit_trigger` を入れる。
- `answer_brief` は、最終文面で先に答えるべき結論の短い核として使う。

### ask_map
- `ask_map` は、相手に依頼する最小限の確認だけを置く。
- 各 ask は、何の質問を解くためかを `question_ids` と `why_needed` で明示する。
- `ask_map` にない質問を、下流で善意追加しない。

### issue_plan
- `issue_plan` は互換用の要約として残す。
- 実行契約の正本は `answer_map` と `ask_map` と考える。
- `issue_plan` を本文生成側の別真実源にしない。

### required_moves
- `answer_timing: after_check` なら `defer_with_reason` を原則入れる。
- `burden_owner: us` なら `decide_for_user` を原則入れる。
- `empathy_first: true` や purchased の軽い追加報告では `react_briefly_first` を優先する。
- purchased で証跡が必要なら `request_minimum_evidence`、進行中なら `commit_next_update_time` を入れる。

### forbidden_moves
- `burden_owner: us` なら `ask_client_to_prioritize_when_burden_owner_us` を避ける。
- `reply_skeleton: post_purchase_quick` なら `numbered_QA_for_all_questions` を避ける。
- purchased では `reopen_estimate_intake` を避ける。
- 保留だけで終わる `vague_hold_without_reason`、内部語露出の `internal_term_exposure` を避ける。
- purchased の軽い追加報告では `overexplain_branching` を避ける。

## Gotchas
- 相手文が貼られただけなら分析のみで止める。自動で返信文を作らない。
- `service_mismatch_but_feasible` は売上都合で使わない。技術的現実性と実績上の検討余地が両方ある時だけ使う。
- `undecidable` の場面で、こちらの都合で無理に `same` / `different` を決めない。
- 価格や無料対応は、この段階で断定しない。
- 既出情報を質問として再パッケージしない。
- `reply_stance` は文体の好みではなく、返信姿勢の固定として使う。`now / after_check` `us / client / shared` を曖昧にしない。
- `reply_contract` は強めのヒントではなく、下流が守る実行契約として扱う。特に `primary_question_id / answer_map / ask_map` を本文側で再解釈しない。
- `answer_timing` を reply-global の正本として扱わない。主質問の要約に留める。

## 出力ルール
- `output-schema.yaml` の項目名に沿って返す。
- 返信文ではなく、まず判定結果を返す。
- `missing_info` は最大3点までを優先する。
- 既出情報の聞き直しをしない。
- `case_type` と `certainty` を必ず埋める。
- `reply_stance` は必ず埋める。
- `reply_contract` は必ず埋める。
- `primary_question_id` は必ず `explicit_questions` のいずれかを指す。
- `answer_map` は `explicit_questions` の全項目を取りこぼさずに覆う。
- `ask_map` は必要最小限にし、各 ask が何の解除条件かを持たせる。
- 主力サービスに素直には乗らないが、技術的には現実的で実績目的なら検討余地があるときは `service_mismatch_but_feasible` を使う。
- `service_mismatch_but_feasible` のときは、自動で断らず、人間判断へ上げる。
- 主力サービスに乗るか不明なときは、無理に受けず `undecidable` または `medium fit` で止める。

## 感情注意フラグの検知
相手文に以下のシグナルがある場合、出力に `emotional_caution: true` を含める。

### 高信頼シグナル（単体でフラグ）
- `直っていない` / `直ってない`
- `解決していない` / `解決してない`
- `お金を払ったのに` / `料金を払ったのに`
- `返金`
- `納得できない` / `納得いかない`

### 中信頼シグナル（文脈と組み合わせ）
- `また` + 過去取引への言及（例: `前回` `以前` `クローズ` `前にお願いした`）
- `前回` + 不満を示す接続（例: `のに` `けど` `だったはず`）
- `困る` + 要求（例: `してほしい` `してもらわないと` `対応してください`）
- `まだ` + 否定（例: `直らない` `反映されない` `変わらない`）

### フラグしない例
- `また連絡します`
- `前回の続きで`
- `困っています` だけの単純相談

### 判定ルール
- 高信頼シグナルは1つでもあれば `emotional_caution: true`
- 中信頼シグナルは組み合わせ条件を満たす場合のみ `emotional_caution: true`
- 迷ったら `true` に倒す（冷たい返信の方がリスクが高いため）

## replyが必要なとき
- このskill自身は長い送信用文面を主担当にしない。
- `reply: make_reply` かつ `risk_level` が高くない場合のみ、短い返信方針メモを付けてよい。
- 本文生成は `coconala-reply-bugfix-ja` へ渡す。

## 仕上げ前チェック
- 経路と状態を混同していないか
- `case_type` と `certainty` が返信方針に必要な粒度で埋まっているか
- 主力サービス適合を売上都合で上げていないか
- 価格や無料対応を断定していないか
- `next_action` が1つに絞れているか
- `issue_plan` が、明示質問や実質別論点を取りこぼしていないか
- `primary_question_id` が主質問を正しく指しているか
- `answer_map` が `explicit_questions` を過不足なく覆っているか
- `ask_map` にない質問を、下流で勝手に増やさない設計になっているか
- `required_moves` / `forbidden_moves` が、reply-bugfix 側へ渡す契約として具体的か
- `service_mismatch_but_feasible` を、単なる売上欲しさではなく「技術的現実性 + 実績上の検討余地」で使っているか
