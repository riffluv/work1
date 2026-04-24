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

## 思考保全モード
- この skill は Codex の代わりに考える層ではなく、入口を薄く構造化する層として使う。
- ここで決めるのは `state / primary_question / answer_map / ask_map / next_action` までに留め、本文 phrasing は下流へ残す。
- reference は必要なものだけを読み、長い template 群を入口判定に持ち込まない。
- 優先順は `/home/hr-hm/Project/work/docs/reply-quality/skill-thought-preservation-minimal.ja.md` に従う。

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
- `user_override`: 任意。`#R` の後ろや次行に付いた自由補足がある時だけ入れる

## 標準ルート
1. 相手文から事実だけ抽出する。
2. `user_override` があれば先に読む。tone / opening は `temperature_plan`、ask / format / service emphasis は `reply_contract` と `response_decision_plan` に流す前提で扱う。
3. 主力サービス適合を `high / medium / service_mismatch_but_feasible / low / unknown` で置く。
4. `risk-gates` に当てて、`allow / hold / decline` 相当の危険を拾う。
5. スコープを `same_cause_likely / different_cause_likely / undecidable / not_applicable` のどれかへ落とす。
6. `case_type` と `certainty` を決める。
7. `explicit_questions` を作り、`primary_question_id` を1つ決める。
8. `answer_map` と `ask_map` を含む `reply_contract` を作る。
9. `reply_stance` を決める。`answer_timing` は `primary_question_id` に対応する `answer_map[].disposition` から要約として置く。
10. 不足情報は、その状態で本当に必要なものだけ最大3点に絞る。
11. `next_action` を1つに絞る。
12. `reply` が明示されていない限り、送信用文面は作らない。

## 判定フロー
1. 相手文から事実だけ抽出する。
2. `user_override` があれば、hard constraints と矛盾しない範囲で `temperature_plan`、`reply_contract`、`response_decision_plan` へ反映する前提で読む。
3. 主力サービス適合を `high / medium / service_mismatch_but_feasible / low / unknown` で置く。
4. `risk-gates` に当てて、`allow / hold / decline` 相当の危険を拾う。
5. スコープは `same_cause_likely / different_cause_likely / undecidable / not_applicable` のどれかへ落とす。
6. `case_type` と `certainty` を決める。
7. `explicit_questions` を作り、`primary_question_id` を1つ決める。
8. `answer_map` と `ask_map` を含む `reply_contract` を作る。
9. `reply_stance` を決める。`answer_timing` は `primary_question_id` に対応する `answer_map[].disposition` から要約として置く。
10. 不足情報は、その状態で本当に必要なものだけ出す。
11. 次アクションを1つに絞る。
12. `reply` が明示されていない限り、送信用文面は作らない。

## `#R` 補足指示の扱い
- `#R` の後ろや次行に自由文の補足があれば、`user_override.raw_text` として扱う。
- 優先順は `hard constraints > user_override > デフォルト推論`。
- `ここは柔らかめに` `まず謝罪から` は `temperature_plan` へ寄せる。
- `質問は1つだけ` `追加料金の話は今回は避けて` `handoff の案内は出さないで` は、`reply_contract` と `response_decision_plan` を狭める方向で使う。
- ただし、公開状態・規約・セキュリティ・最低限必要な確認と衝突する補足は、そのままは採用しない。
- `handoff を出さないで` と書かれていても、実際に対象外や別サービス案内が必須なら hard constraints を優先する。
- `質問は1つだけ` と書かれていても、実行に最低2点必要なら、2点のまま最小化して残す。

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
- `boundary` でも、相手の主目的が明確に修正なら handoff を前面に出さず、bugfix 起点で進める前提を優先する
- `コードが分からない` `外注コード` `AIで作った` は単独では handoff 判定理由にしない。購入者の状態として扱う
- 修正主目的だが症状がまだ絞れていない時は、handoff 推奨へ倒さず `boundary / low certainty` として購入前の絞り込みへ進める
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

### response_decision_plan.phase_act
- `state: prequote` の `estimate_initial / estimate_followup` -> `estimate_answer` または `estimate_hold`
- `state: purchased` の `post_purchase_quick / post_purchase_report` -> `purchase_check_started` または `purchase_scope_recheck`
- `estimate_*` は見積もり判断の speech act であり、未受領のコードやログを見始めたような現在形へ寄せない
- `purchase_*` は購入後の確認・切り分け・範囲見直しの speech act であり、見積もり相談の受付文面へ戻さない

## `temperature_plan` の決め方
`temperature_plan` は、reply の意味ではなく、冒頭の受け方と温度の上限を固定する interaction contract として出す。

```yaml
temperature_plan:
  user_signal: stress | hesitation | confusion | negative_feedback | gratitude | weakness | neutral
  support_goal: reduce_burden | normalize | receive_feedback | receive_goodwill | set_boundary_calmly | move_forward
  opening_move: action_first | pressure_release | normalize_then_clarify | receive_and_own | brief_ack_then_answer | yes_no_first | neutral_ack
  ack_style: none | brief_generic | brief_specific
  ack_anchor: none | buyer_action | buyer_effort | buyer_result | buyer_goodwill | buyer_openness | issue_detail
  warmth_cap: none | one_sentence | two_clauses
```

### user_signal
- `gratitude`: `ありがとうございます` `助かりました` `星5` `大満足` `バッチリでした` `動作確認もOK` など、好意や前向きな結果共有が主
- `weakness`: `自分では触れない` `よく分からない` `コードが読めない` `自信がない` など、弱さや率直さが主
- `negative_feedback`: 品質不足、説明不足、遅延不満、記載ミス指摘など
- `stress`: 急ぎ、本番障害、売上影響、繰り返し催促
- `confusion` / `hesitation`: 方向が決められない、何を送ればよいか分からない、価格や入口で迷っている
- どれにも強く寄らなければ `neutral`

### opening_move
- 情報収集や前進が主なら `action_first`
- bad experience や品質不足をまず受けるなら `receive_and_own`
- gratitude / weakness で短い受けを置いてから答えるなら `brief_ack_then_answer`
- Yes/No 直答が最優先で、温度は薄くてよい時は `yes_no_first`

### ack_style / ack_anchor
- v1 の核心は、generic な共感ではなく、buyer が実際にした行動や差し出した情報に1文で触れること
- `ack_style: brief_specific` を使う場面:
  - 動作確認や評価を返してくれた
  - 詳細を整理して送ってくれた
  - 弱さや率直さを短く差し出した
- `ack_anchor` の優先順:
  - `buyer_action`: `動作確認までしていただけて`
  - `buyer_effort`: `情報をここまで整理していただけたので`
  - `buyer_result`: `バッチリ動いたとのことで`
  - `buyer_goodwill`: `評価まで入れていただけて`
  - `buyer_openness`: `率直に書いていただけたので`
  - `issue_detail`: buyer の具体事象を1点だけ受ける
- anchor が拾えないのに具体文を捏造しない。拾えなければ `brief_generic` か `none` に落とす

### warmth_cap
- v1 は原則 `one_sentence`
- 温度は冒頭の1文までで止め、本題の回答や境界説明に侵食させない
- `two_clauses` は、短い謝意 + すぐ結論のような一息分までに留める

### 実務ルール
- `buyer の行動に具体的に触れる1文` は、褒めるためではなく「ちゃんと読んでいる」証拠として使う
- 情報収集フェーズでは assertive を優先し、感情応答を長くしない
- bad experience では empathetic でもよいが、境界・価格・事実を曲げない
- `この手の症状はよくある` `大丈夫です` のような根拠のない安心は v1 では使わない
- boundary 判定や scope 説明は `temperature_plan` で軟化させない
- 受け止めで buyer が言っていない感情語を補完しない。`迷いますよね` `つらいですよね` のような感情完成より、buyer の言葉か状況描写へ寄せる
- 冒頭で受け止めを1文入れる時は、その直後を `ですが` で逆接しない。受けるなら1文で止めるか、根拠説明からそのまま本題へ入る

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
- 価格、追加料金、別原因リスク、広いスコープ説明は、相手が明示していない限り `explicit_questions` へ勝手に昇格させない。
- `お願いできますか` `依頼できそうですか` のような可否質問が主なら、`対応可否` を primary にし、価格や範囲説明を別の主質問として混ぜない。

### answer_map
- `answer_map` は renderer と lint が使う正本で、`issue_plan` より優先する。
- 各質問を `answer_now / answer_after_check / ask_client / decline` のどれかへ落とす。
- `answer_after_check` には必ず `hold_reason` と `revisit_trigger` を入れる。
- `answer_brief` は、最終文面で先に答えるべき結論の短い核として使う。
- `answer_brief` は primary question の核だけを書く。二次論点の価格・分岐・広い範囲説明をここへ混ぜない。
- 相手が価格を聞いていない場面では、`answer_brief` に価格を入れない。価格は policy 上必要な場合か、相手の主質問に含まれる場合だけ後段で扱う。

### ask_map
- `ask_map` は、相手に依頼する最小限の確認だけを置く。
- 各 ask は、何の質問を解くためかを `question_ids` と `why_needed` で明示する。
- `ask_map` にない質問を、下流で善意追加しない。
- その ask が任意確認で済むなら、下流で必須質問として押し出さない前提にする。
- `burden_owner: us` かつ、答えがなくてもこちらで仮に進められる場面では、`ask_map` は「任意確認 + 既定方針あり」の扱いにする。

### issue_plan
- `issue_plan` は互換用の要約として残す。
- 実行契約の正本は `answer_map` と `ask_map` と考える。
- `issue_plan` を本文生成側の別真実源にしない。
- `issue_plan` に価格や別原因リスクが入っていても、primary question でなければ先頭へ出さない。

### required_moves
- `answer_timing: after_check` なら `defer_with_reason` を原則入れる。
- `burden_owner: us` なら `decide_for_user` を原則入れる。
- `empathy_first: true` や purchased の軽い追加報告では `react_briefly_first` を優先する。
- purchased で証跡が必要なら `request_minimum_evidence`、進行中なら `commit_next_update_time` を入れる。
- 任意確認で進められる場面では、`state` を問わず `state_default_path_if_no_answer` を優先候補に入れる。

### forbidden_moves
- `forbidden_moves` は「気をつけるメモ」ではなく、下流 writer へ渡す実行契約として具体的に立てる。
- 外向け返信では、原則として `internal_term_exposure` を入れる。
- `state: purchased / predelivery / delivered / closed` では、原則として `reopen_estimate_intake` を入れる。
- `burden_owner: us` では、原則として `ask_client_to_prioritize_when_burden_owner_us` を入れる。
- `reply_skeleton: post_purchase_quick` で短く返すべき場面では、原則として `numbered_QA_for_all_questions` を入れる。
- `answer_map` に `answer_after_check` が1件でもあるなら、原則として `vague_hold_without_reason` を入れる。
- purchased の軽い追加報告で、分岐説明が主題でないなら `overexplain_branching` を入れる。
- 相手が価格を明示質問しておらず、primary question が可否・対象性なら `frontload_price_when_not_asked` を入れる。
- 相手が別原因や追加料金を明示質問しておらず、分岐説明が主題でないなら `frontload_branching_risk_when_not_asked` を入れる。
- 相手が範囲説明を明示質問しておらず、scope 説明が主題でないなら `frontload_scope_explanation_when_not_asked` を入れる。
- `frontload_*` 3種は、policy 上の必須説明が主質問そのものになっている時だけ外してよい。
- 詳細基準は `/home/hr-hm/Project/work/docs/reply-quality/forbidden-moves-matrix.ja.md` を正本として参照する。

## Gotchas
- 相手文が貼られただけなら分析のみで止める。自動で返信文を作らない。
- `service_mismatch_but_feasible` は売上都合で使わない。技術的現実性と実績上の検討余地が両方ある時だけ使う。
- `undecidable` の場面で、こちらの都合で無理に `same` / `different` を決めない。
- 価格や無料対応は、この段階で断定しない。
- 既出情報を質問として再パッケージしない。
- `整理が技術的に必要` と `整理サービスを買わせる` を混同しない。前者は売り手の工程、後者は購入者の購入判断
- 修正主目的の相談を、`コードが複雑そう` という理由だけで handoff へ送らない
- `bugfix で購入後に handoff へ振り直す` 前提で購入判断を曖昧にしない。境界判定は購入前にできるだけ終わらせる
- `reply_stance` は文体の好みではなく、返信姿勢の固定として使う。`now / after_check` `us / client / shared` を曖昧にしない。
- `reply_contract` は強めのヒントではなく、下流が守る実行契約として扱う。特に `primary_question_id / answer_map / ask_map` を本文側で再解釈しない。
- `answer_timing` を reply-global の正本として扱わない。主質問の要約に留める。
- primary question へ答える前に、二次論点の価格・分岐・広いスコープ説明を前に出さない。

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
- 修正主目的かつ症状が1つに絞れていない境界案件では、購入前に `一番困っている症状` を1つだけ絞る next_action を優先する。

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
- `burden_owner: us` の場面で、任意確認を相手への判断丸投げに変えていないか
- 答えがなくても進められる場面で、下流へ既定方針を渡せる設計になっているか
- `required_moves` / `forbidden_moves` が、reply-bugfix 側へ渡す契約として具体的か
- `service_mismatch_but_feasible` を、単なる売上欲しさではなく「技術的現実性 + 実績上の検討余地」で使っているか
