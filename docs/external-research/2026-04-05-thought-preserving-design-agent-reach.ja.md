# 2026-04-05 Thought-Preserving Design 調査メモ（Agent-Reach）

## 結論
- 大きな方向性の見落としはなかった。
- ただし、`構造化 + 温度感` の上に、**思考を潰さない設計**を明示的に入れる必要がある。
- 実務的には新しい巨大な第3軸を足すというより、既存の構造化パイプラインの中に
  - `routing/classification を独立 stage 化`
  - `plan/action plan を final text から分離`
  - `known_facts / metadata で再要求を防止`
  - `answer coverage / unresolved / churn risk を eval に追加`
  を入れるのが本筋。

## 外部ソースから見えたこと

### 1. routing は helper ではなく独立 stage
- Anthropic の ticket routing guide は、intent だけでなく urgency / customer type / SLA / language も routing criteria に含めるべきと明記している。
- また、routing の success criteria として routing accuracy / rerouting rate / first-contact resolution rate を置いている。
- つまり、routing は renderer の前の軽い前処理ではなく、**品質指標を持つ独立 layer** として扱うのが実務寄り。

出典:
- https://platform.claude.com/docs/en/about-claude/use-case-guides/ticket-routing

### 2. consistency は schema で固定し、自由文はその後に扱う
- Anthropic は「常に schema に従う JSON が必要なら Structured Outputs を使うべき」としている。
- これは、構造化が必要な層と、柔らかい自然文の層を分ける発想に一致する。
- つまり、`reply_contract` や `temperature_plan` のような構造は hard に固定し、その後の自然文は別扱いにするのが自然。

出典:
- https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/increase-consistency

### 3. final answer と reasoning / planning は分けて持つ方がよい
- OpenAI の Structured Outputs 紹介では、final answer と supporting reasoning / additional commentary を別 field に分けるのが useful とされている。
- これは今回の文脈では、
  - `reply_contract`: 相手に返すべき意味
  - `temperature_plan`: どう受け止めるか
  - `internal reasoning / concern_focus / direct_answer_line`: 先に model が決める中間表現
  を分ける方向を支持する。
- 重要なのは、**最終文面に reasoning を露出させることではなく、reasoning を final text と混ぜないこと**。

出典:
- https://openai.com/index/introducing-structured-outputs-in-the-api/

### 4. 応答生成は plan / policy と realization を分けるのが研究的にも王道
- `Policy-Driven Neural Response Generation for Knowledge-Grounded Dialogue Systems` は、dialogue policy が knowledge / dialogue acts / topic などを含む action plan を決め、その plan を response generator が utterance に realization する構造を提案している。
- これは、今回議論している
  - route
  - direct_answer_line
  - concern_focus
  - hold_reason
  - ask gating
  のような中間表現を先に作り、その後で日本語化する設計と整合する。

出典:
- https://arxiv.org/abs/2005.12529

### 5. exemplar は words ではなく semantic frames で効かせる方が壊れにくい
- `Controlling Dialogue Generation with Semantic Exemplars` は、exemplar の表層語を強くコピーすると incoherent になりやすく、semantic frames で制御した方が conversation goals と semantic meaning を保ちやすいとしている。
- これは今回の system で、文例そのものを template 化するより
  - concern type
  - direct answer type
  - ask burden level
  - closing move
  のような frame ベースで制御した方がよいことを示唆する。

出典:
- https://arxiv.org/abs/2008.09075

### 6. support 現場では unresolved / churn risk / repeated contact を観測対象にする
- Zendesk の real-time QA は、`churn risk` と `unresolved issue` を per-message で検出する。
- これは今回の「金銭不安に答えていない」「2日待たせてゼロ情報」「また同じ症状なのに手続き文先行」のような failure を、tone ではなく **未解決リスク** として eval 化できることを示す。

出典:
- https://support.zendesk.com/hc/en-us/articles/9745122485914-Real-time-QA-insights-EAP

### 7. metadata / known facts は再質問削減の基礎
- Zendesk は messaging metadata により product / confirmation number / order ID などの relevant information を programmatic に渡し、agent が再質問しなくて済むようにしている。
- 今回の文脈なら `ZIP送付済み`, `既にエラー文あり`, `前回と同じ症状と言っている`, `金額質問済み` などを `known_facts` として renderer 前に持たせるのが相当。

出典:
- https://support.zendesk.com/hc/en-us/articles/5658339908378

### 8. prompt や guardrail を絞るのは、まず top performance を見てから
- Anthropic の reducing latency guide は、「まず prompt が constraints なしで well に動くようにして、その後で削る方がよい」としている。
- これは今回の設計に引き直すと、template-first に hardening する前に、**model が一番良く答えられる中間表現**を先に見つけるべきという示唆になる。

出典:
- https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-latency

## 実装に落とすと何が必要か

### 1. routing / scenario selection を helper から独立 stage に格上げ
- `detect_scenario()` を内部 helper のままにしない
- success criteria を持たせる
  - route accuracy
  - generic fallback rate
  - reroute rate

### 2. final text の前に `micro-plan` を持つ
- 最小で必要なのは:
  - `concern_focus`
  - `direct_answer_line`
  - `hold_reason`
  - `ask_needed`
  - `known_facts_used`

### 3. `reaction_line()` を label 定型だけで返さない
- `stress` や `negative_feedback` の label だけでは不十分
- raw_message から抽出した `concern_focus` を opening に反映させる

### 4. slot 重複を lint で落とす
- 同義反復は style issue ではなく design bug
- `bridge_to_hold / answer_core / hold_core` の semantic overlap を検査対象にする

### 5. eval に `answer coverage / unresolved / reask_known_info` を追加
- いまの bucket に
  - 金銭不安へ直接答えたか
  - 同じ症状の再発不満を opening で拾ったか
  - 既出情報の再要求をしていないか
  を追加する

## いまの system に対する判断
- `temperature_plan` 自体は keep でよい
- `fixed_slots / editable_slots` も keep でよい
- 問題はそれらの前にある `micro-plan` 不在
- したがって次に必要なのは、新しい巨大 architecture ではなく
  **reasoning-first, constraint-checked を成立させる中間表現の追加**

## 次の実装候補
1. `concern_focus` 抽出
2. `direct_answer_line` を必須 slot 化
3. `known_facts` による ask suppression
4. slot dedupe lint
5. `answer coverage / unresolved / reask_known_info` checker

