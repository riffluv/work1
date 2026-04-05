# 2026-04-05 返信 system 見落とし再確認（Agent-Reach）

## 目的
- `#AR` と Pro をもとに入れた設計が、原理として何か見落としていないかを再確認する。
- 特に、今回の障害が `temperature_plan` の思想ミスではなく、他に見落とした production pattern がないかを見る。

## 先に結論
- **大きな方向性の見落としはなかった。**
- ただし、`routing / classification` を「前処理」ではなく **独立した production primitive** として扱う深さが少し足りなかった。
- 追加で明確になったのは次の4点。
  1. `routing` は renderer の補助ではなく、独立した成功基準を持つ stage にするべき
  2. `generic fallback` は通常経路ではなく、観測可能で狭い最後の逃げ道にするべき
  3. validator は tone だけでなく、`answer coverage / unresolved / repeated-contact` を見るべき
  4. 既知情報の再質問を防ぐため、message metadata / carried context をもう一段明示的に使うべき

## 主要ソースからの補強

### 1. Routing は first-class stage
- Anthropic の ticket routing guide は、LLM support workflow の先頭で
  - 現行 routing の理解
  - intent category の定義
  - success criteria の定義
  を置いている。
- 特に
  - `Claude’s ability to route tickets effectively ... is directly proportional to how well-defined your system’s categories are`
  - `routing accuracy`
  - `rerouting rate`
  - `first-contact resolution rate`
  を success criteria に置いている。
- 示唆:
  - `detect_scenario()` は helper ではなく、独立 eval を持つ classifier stage にするべき。

出典:
- https://platform.claude.com/docs/en/about-claude/use-case-guides/ticket-routing

### 2. Fallback は狭く、観測可能であるべき
- Zendesk の intelligent triage は、intent / sentiment / language を使って
  - route
  - deflect
  - request more information
  を分けている。
- これは「全部 generic response に落とす」の逆で、fallback を業務上の意味を持つ既定返信にしない構え。
- 示唆:
  - `generic_*` は常用 lane にしてはいけない。
  - fallback を使うなら、
    - なぜ fallback になったか
    - 何を保留したか
    - 何を最小確認するか
    を別ログで見える化した方がよい。

出典:
- https://support.zendesk.com/hc/en-us/articles/5222280338202-Intelligent-triage-use-cases-and-workflows

### 3. Validator は「tone が悪いか」より「未解決 / 未回答か」を見るべき
- Zendesk Real-time QA は live conversation に対して
  - churn risk
  - unresolved issue
  を別 insight として検知する。
- `Unresolved issue` は、
  - 解決されていない
  - 満足いく答えが来ていない
  - 問題が続いている
  - 何度も連絡している
  といった兆候を拾う。
- 示唆:
  - 今回の「主質問に答えず段取りだけ返す」は tone failure ではなく unresolved failure。
  - validator / bucket に `answer coverage` と `repeated-contact / unresolved` 系を入れるべき。

出典:
- https://support.zendesk.com/hc/en-us/articles/9745122485914-Real-time-QA-insights-EAP

### 4. 既知情報の再要求を防ぐには metadata / carried context が重要
- Zendesk の messaging metadata は、
  - product SKU
  - order id
  - page context
  などを会話へ自動で渡し、ユーザーに再入力させない設計を推している。
- 明示的に
  - `End users won’t have to re-enter data already available`
  - `Without custom ticket fields, the live or AI agent must ask the end user for all this information before answering`
  と書いている。
- 示唆:
  - 今回の「既に書いてあるのに、症状を送ってください」は routing の弱さだけでなく、carried context の活用不足としても見られる。
  - 同一 thread / closed followup では、相手の既出情報を `known_facts` 的に明示保持する方がよい。

出典:
- https://support.zendesk.com/hc/en-us/articles/5658339908378-Using-messaging-metadata-with-the-Zendesk-Web-Widget-and-SDKs

### 5. QA は主観語ではなく、観測可能 criteria を使う
- Zendesk QA prompt best practices は、
  - subjective language を避ける
  - simple and focused
  - specific behaviors / actions
  - clear rating conditions
  を勧めている。
- 示唆:
  - `自然か` `温かいか` だけでは弱い。
  - 今後の grader は
    - 主質問に答えたか
    - 既知情報を再要求していないか
    - action / reassurance を先に置いたか
    - unresolved を増やしていないか
    のような観測可能項目に寄せるべき。

出典:
- https://support.zendesk.com/hc/en-us/articles/9464975500954-Best-practices-for-creating-AI-insights-prompts-in-Zendesk-QA

### 6. OpenAI support model とも矛盾しない
- OpenAI support model は
  - knowledge
  - evals and classifiers
  - observability
  を loop として扱っている。
- また
  - `we know when the model shouldn't answer`
  - classifiers for tone, correctness, policy adherence
  と書いている。
- 示唆:
  - 今回の追加学びは新思想ではなく、既存方針の延長。
  - 特に `shouldn't answer / should defer / should ask minimal clarification` を routing 側で先に判定する必要がある。

出典:
- https://openai.com/index/openai-support-model/

## 今回の再確認で「足すべきだ」と見えたもの

### 1. Scenario selection を独立評価対象にする
- `detect_scenario()` 成功率
- generic fallback 率
- reroute / reclassify 率
- lane 別 miss
を別レポートで見るべき。

### 2. generic fallback を fail-open ではなく fail-visible にする
- generic を返したら
  - scenario_miss
  - missing intent
  - needs human review
  のような内部 signal を残す。
- 返信本文は業務継続可能でも、内部では要注意として浮かせる方が安全。

### 3. `answer coverage` validator を追加する
- 相手の主質問に yes/no でも答えたか
- 既知情報を再要求していないか
- 継続会話で初回受付へ巻き戻っていないか
を validator / bucket に足すべき。

### 4. carried context を明示化する
- `known_facts`
- `already_provided`
- `prior_case_relation`
のような field を持たせると、同一会話での再質問を減らしやすい。

## 今回の再確認で「足さなくてよい」と見えたもの
- 構造方針の全面見直し
- `temperature_plan` の撤回
- `fixed_slots / editable_slots` の撤回
- evaluator を全部人手に戻すこと
- いきなり DPO / SFT へ進むこと

## 最終判断
- `#AR` と Pro の方向は引き続き正しい。
- 今回見落としていたのは新しい巨大軸ではなく、**routing / fallback / answer-coverage を production quality で締める深さ**。
- したがって次の priority は
  1. scenario selection の独立評価
  2. generic fallback の可視化
  3. answer coverage / unresolved validator 追加
  4. carried context の明示化
  でよい。
