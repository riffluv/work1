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
6. `reply_stance` を決める。
7. `reply_contract` を作る。
8. 不足情報は、その状態で本当に必要なものだけ最大3点に絞る。
9. `next_action` を1つに絞る。
10. `reply` が明示されていない限り、送信用文面は作らない。

## 判定フロー
1. 相手文から事実だけ抽出する。
2. 主力サービス適合を `high / medium / service_mismatch_but_feasible / low / unknown` で置く。
3. `risk-gates` に当てて、`allow / hold / decline` 相当の危険を拾う。
4. スコープは `same_cause_likely / different_cause_likely / undecidable / not_applicable` のどれかへ落とす。
5. `case_type` と `certainty` を決める。
6. `reply_stance` を決める。
7. `reply_contract` を作る。
8. 不足情報は、その状態で本当に必要なものだけ出す。
9. 次アクションを1つに絞る。
10. `reply` が明示されていない限り、送信用文面は作らない。

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
- 手持ち情報だけで正確に答えられる質問が主なら `now`
- コード、ログ、スクショ、実画面を見てからの方が価値が高いなら `after_check`
- 購入後で `原因はどちらか` `今週中に直るか` のような質問は、証跡未確認なら原則 `after_check`

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

### issue_plan
- 明示された質問ごと、または実質的に別論点になる要求ごとに1項目作る。
- `answer_now`: 今ある事実だけで正確に答えられる。
- `answer_after_check`: コード・ログ・スクショ・実画面確認後の方が価値が高い。
- `ask_client`: 相手にしか出せない証跡や判断が最小限必要。
- `decline`: 規約・範囲・公開状態の理由で返せない。

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
- `reply_contract` は強めのヒントではなく、下流が守る実行契約として扱う。`issue_plan` を省略して返信本文側へ再解釈を委ねない。

## 出力ルール
- `output-schema.yaml` の項目名に沿って返す。
- 返信文ではなく、まず判定結果を返す。
- `missing_info` は最大3点までを優先する。
- 既出情報の聞き直しをしない。
- `case_type` と `certainty` を必ず埋める。
- `reply_stance` は必ず埋める。
- `reply_contract` は必ず埋める。
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
- `required_moves` / `forbidden_moves` が、reply-bugfix 側へ渡す契約として具体的か
- `service_mismatch_but_feasible` を、単なる売上欲しさではなく「技術的現実性 + 実績上の検討余地」で使っているか
