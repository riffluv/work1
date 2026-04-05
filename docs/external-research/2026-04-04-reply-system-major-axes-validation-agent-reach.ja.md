# 2026-04-04 返信システムの主軸は「構造化と温度感だけか」検証（Agent-Reach）

## 目的
- 現在の仮説である
  - 構造化
  - 温度感
  の2本柱だけで十分かを、プロの support / reply system の実装パターンから確認する。
- 足りない主軸があるなら、温度感の実装前に把握しておく。

## 先に結論
- **「構造化と温度感だけ」で reply system 全体を説明するのは不足。**
- ただし、**あなたの現行 system の改善対象としては、構造化と温度感が主戦場である**という理解はかなり正しい。
- なぜなら、プロの現場では少なくとも次の **6軸** で作っているが、この workspace ではそのうち複数は既に相当入っているから。

## プロの現場で共通して出てくる主軸

### 1. Structure / Workflow
- 何を答えるか
- どこで保留するか
- 何を聞くか
- section order / state / branch
- これは今の `reply_contract -> renderer -> lint` に近い。

### 2. Tone / Relational behavior
- 相手の状態シグナルをどう受けるか
- 距離感
- burden relief
- 弁明回避
- brand voice
- これは今回の main gap。

### 3. Knowledge / Grounding
- FAQ / policy / solved tickets / docs / live context
- citations
- hallucination 抑制
- OpenAI でも Anthropic でも Zendesk でも、support quality の土台としてかなり前面にある。

### 4. Action / Tooling / Resolution capability
- 返答だけでなく、lookup / order cancel / incident check / quote submit などの action 実行
- つまり「話すAI」ではなく「解決するAI」。
- OpenAI support model 記事や Anthropic customer support guide は、ここをかなり重く見ている。

### 5. Evaluation / Observability / Feedback loop
- evals
- classifiers
- traces
- QA scoring
- holdouts
- ここは OpenAI / Anthropic / Zendesk / Google の全員が共通して強調。

### 6. Governance / Safety / Scope control
- policy adherence
- commitments を勝手にしない
- PII / compliance / trust
- out-of-scope / escalation
- security and trust

## 主要ソースから見えたこと

### OpenAI
- OpenAI の support model 記事では、中心要素を
  - Surfaces
  - Knowledge
  - Evals and classifiers
  としている。
- さらに production primitive として
  - traces / observability
  - tone / correctness / policy adherence classifiers
  - dynamic actions
  が出てくる。
- つまり、少なくとも
  - knowledge
  - evals/classifiers
  - action
  - observability
  は主軸。
- 出典:
  - https://openai.com/index/openai-support-model/

### Anthropic
- customer support guide では
  - ideal interaction の定義
  - interaction を task に分解
  - success criteria の定義
  - RAG
  - tool use
  - output consistency guardrails
  - eval
  を明示している。
- tone もあるが、それだけではなく
  - task decomposition
  - knowledge retrieval
  - action
  - escalation
  - sentiment maintenance
  がセットになっている。
- 出典:
  - https://platform.claude.com/docs/en/about-claude/use-case-guides/customer-support-chat
  - https://platform.claude.com/docs/en/test-and-evaluate/develop-tests

### Zendesk
- Zendesk の AI platform 記述では
  - actions and integrations
  - knowledge base / connected knowledge
  - quality assurance with automatic scoring
  - reporting and analytics
  - security and trust
  が並んでいる。
- さらに tone rewrite もあるが、それは platform の1要素であって主軸の全部ではない。
- 出典:
  - https://www.zendesk.com/service/ai/
  - https://www.zendesk.com/blog/auto-qa/

### Google Cloud
- Contact Center AI / Quality AI 系では
  - knowledge assist
  - sentiment analysis
  - Quality AI scorecards
  - conversation analytics
  が中心。
- 特に scorecard / quality evaluation / sentiment / knowledge assist が分かれているのが重要。
- 出典:
  - https://cloud.google.com/contact-center/ccai-platform/docs/agent-assist
  - https://cloud.google.com/contact-center/insights/docs/qai-best-practices
  - https://cloud.google.com/contact-center/insights/docs/sentiment-analysis

## では「2本で足りない」のか？
- system 全体の設計としては、**足りない**。
- ただし、あなたの workspace で「これから強化する主戦場」としては、**かなり足りている**。

理由:
- 既にかなり持っている軸があるから。

### 既に相当入っているもの
- Structure / Workflow
  - mode, lane, contract, renderer, lint, regression
- Governance / Scope control
  - service-registry, live/private 境界, forbidden moves, boundary rules
- Evaluation / Feedback loop
  - quality-cases, stock, regression, Claude 監査, lint 反映
- 一部の Knowledge grounding
  - service page 正本, registry, docs 正本, runtime 正本

### まだ弱い / 今後の本丸
- Tone / Relational behavior
  - first-class field 化されていない
- Knowledge freshness / retrieval discipline
  - support platformほど明確な retrieval / citation / context ranking にはなっていない
- Action / tooling
  - 返信 system 自体では、解決実行より message generation 寄り
- Observability at trace level
  - regression はあるが、step trace の grading や classifier dashboard はまだ薄い

## 実務的な整理
- 「本当に大事なのは構造化と温度感だけか？」への答えは、
  - **全体設計としては no**
  - **今の品質改善の主戦場としては yes に近い**
  です。

つまり、
- プロの現場では 6軸前後で作る
- でもあなたの system はそのうち
  - 構造
  - ガバナンス
  - eval
  はかなり進んでいる
- だから次に効くのが
  - 温度感
  - 最終 validator
  - knowledge / action / observability の取りこぼし確認
  になる

## 今の system に対する判断

### 主軸として維持すべきもの
- 構造化
- 温度感

### 「第3の確認軸」として見るべきもの
- Knowledge / Grounding
  - 何を根拠に返すか
  - context の freshness と selection

### 「第4の実務軸」として見るべきもの
- Eval / Observability
  - ただしこれは既にかなり入っているので、ゼロから追加ではなく強化対象

### 今は優先度を上げなくてよいもの
- 大規模 action orchestration
- enterprise 級の BI dashboard
- heavy compliance platform 化

## 暫定結論
- あなたが今見ている
  - 構造化
  - 温度感
  の2軸は、**次の改善対象としては正しい**。
- ただし system 全体を俯瞰すると、プロの現場ではそれに加えて
  - knowledge / grounding
  - action / tooling
  - eval / observability
  - governance / safety
  が主軸として存在する。
- この workspace では、そのうち複数は既にかなり入っている。
- したがって、次の設計判断として正しいのは
  1. 構造方針は維持
  2. 温度感を first-class 化
  3. 同時に knowledge / final validator / holdout observability が穴になっていないかだけ確認
  である。

## 参考ソース
- OpenAI, Improving support with every interaction at OpenAI
  - https://openai.com/index/openai-support-model/
- Anthropic, Customer support agent
  - https://platform.claude.com/docs/en/about-claude/use-case-guides/customer-support-chat
- Anthropic, Define success criteria and build evaluations
  - https://platform.claude.com/docs/en/test-and-evaluate/develop-tests
- Zendesk AI
  - https://www.zendesk.com/service/ai/
- Zendesk Auto QA
  - https://www.zendesk.com/blog/auto-qa/
- Google Cloud Agent Assist
  - https://cloud.google.com/contact-center/ccai-platform/docs/agent-assist
- Google Cloud Quality AI best practices
  - https://cloud.google.com/contact-center/insights/docs/qai-best-practices
- Google Cloud Sentiment analysis
  - https://cloud.google.com/contact-center/insights/docs/sentiment-analysis
