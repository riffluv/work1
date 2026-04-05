# 2026-04-04 返信生成の構造方針 妥当性確認（Agent-Reach）

## 目的
- 既に導入済みの構造方針
  - contract 化
  - section renderer
  - deterministic lint
  - eval
  が、外部の一次ソースから見ても妥当かを確認する。
- 温度感の改善に入る前提として、土台の構造側に大きな設計ミスがないかを確かめる。

## 先に結論
- **大筋はかなり合っている。**
- 特に次の方向は、OpenAI / Anthropic / Google の一次情報と整合している。
  1. 自由文より schema / contract を先に固定する
  2. 単発 prompt より multistep workflow に分ける
  3. renderer と validator を分離する
  4. eval を後付けでなく最初から設計する
- 逆に、まだ締めるべき点は 3 つある。
  1. contract と tone の責務境界を明示する
  2. final output に対する validator をもっと重くする
  3. holdout を edge bucket ごとに分けて監視する

## 外部ソースから見た妥当性

### 1. schema / structured output を中心に置くのは正しい
- OpenAI の Structured Outputs docs は、JSON Schema に合わせて出力を固定し、required key や enum の逸脱を減らす方向を強く勧めている。
- Google Gemini の structured output docs も、型・enum・description を明示しつつ、**それでも最終バリデーションはアプリ側で必要**と明記している。
- 示唆:
  - `reply_contract` を executable contract 化する方向は正しい。
  - `case_type` `skeleton` `question disposition` `next action` などを free prose に置かないのは王道。

### 2. workflow 分離は正しい
- OpenAI の evaluation best practices は、complex task では single-turn より **workflow architecture** で各段を分離し、各ステップを isolated に評価する前提で説明している。
- 例としても、分類 -> 抽出 -> 最終応答、のような step 分割を置いている。
- 示唆:
  - 入口判定 / contract / renderer / naturalize / check に分ける今の方向は筋がよい。
  - 「全部を1 prompt でやる」より、今のように lane / stage を分ける方が安定する。

### 3. section renderer は prompt 強化より正しい方向
- OpenAI の safety / agent docs は、untrusted text が downstream を乱さないよう、**structured outputs between nodes** で自由文チャネルを減らすべきだとしている。
- これは安全文脈の話だが、実務上は品質ぶれ対策としても同じ構造が効く。
- 示唆:
  - skeleton ごとに section order と cardinality をコードで固定し、LLM を slot writer に寄せる設計はかなり正しい。
  - これは温度感の前段としても重要で、構造が free だと tone もぶれる。

### 4. deterministic lint を別レイヤに置くのは正しい
- Google docs は structured output が syntactic correctness を担保しても、**semantic validation は別途必要**と明記している。
- OpenAI docs も eval / graders / trace grading を使い、出力後に行動や結果を測る前提を取っている。
- 示唆:
  - `lint` を prompt へのお願いで済ませず、別レイヤで持つ方針は正しい。
  - 特に価格、state、禁止事項、ask 数、内部語彙、tone事故は post-check 化してよい。

### 5. eval を先に設計する方針は正しい
- Anthropic docs は、successful app はまず success criteria を定義し、それに沿って eval を作るべきだとしている。
- OpenAI docs も、workflow の各 step を評価し、pairwise / pass-fail / metric-based eval を使い分けることを推奨している。
- OpenAI の support model 記事でも、knowledge と evals / classifiers を loop にして support 品質を育てている。
- 示唆:
  - quality-cases / stock / regression / external review を回しながら system に戻す現在の考え方は、かなり現場に近い。

## 今の方針で「そのままでよい点」

### 1. `reply_contract` 中心の設計
- これは維持でよい。
- むしろ weak prompt に戻すべきではない。

### 2. section renderer
- 維持でよい。
- 今後は温度感も含めて、「何を code 固定にし、何を slot 可変にするか」をさらに明示すると強くなる。

### 3. deterministic lint + eval の二層
- 維持でよい。
- lint で全部見ようとせず、tone / burden / defense のような部分は LLM judge へ分ける設計も妥当。

### 4. 実例から改善を戻すループ
- 維持でよい。
- OpenAI support model 記事の
  - reps flag interactions that should become test cases
  - classifiers and evals are shared definitions of quality
  という考え方と整合する。

## まだ締めるべき点

### 1. final output validator が主戦場
- structured output や renderer が正しくても、最後の自然化や paraphrase で壊れる余地がある。
- したがって、本当に重要なのは raw render 前ではなく、**最終文面に対する validator**。
- ここは今後さらに重くしてよい。

### 2. tone を contract 外に放置しない
- 現在の構造は answer / ask / next action をかなり固定できている。
- ただし tone はまだ docs と監査に散りやすい。
- ここを `temperature_plan` などの field として sibling 化するなら、構造方針とも矛盾しない。
- つまり、温度感の改善は「構造方針の否定」ではなく「構造方針の延長」。

### 3. edge bucket ごとの holdout を分ける
- Anthropic / OpenAI の eval docs でも、edge cases や task-specific eval が強調されている。
- 平均点だけではなく、
  - stress
  - boundary
  - negative feedback
  を分けて見るのがよい。

## 実務的な判断
- 前の Codex が入れた構造方針は、**崩す必要はない**。
- むしろ次は、
  - contract
  - renderer
  - lint
  - eval
  という骨格の上に、temperature layer を足すのが自然。
- 言い換えると、温度感の改善は「別思想への乗り換え」ではなく、**今の方針を一段完成させる作業**。

## 暫定結論
- 構造側は大筋このままでよい。
- 不安になる必要があるのは「構造方針が間違っているか」ではなく、
  - final validator の重さ
  - tone layer の不在
  - edge holdout の不足
  の3点。
- したがって、次の優先順位は以下でよい。
  1. 現行の contract / renderer 方針は維持
  2. tone を sibling field 化
  3. final output validator を強化
  4. stress / boundary / negative feedback の holdout eval を追加

## 参考ソース
- OpenAI, Structured outputs
  - https://platform.openai.com/docs/guides/structured-outputs
- OpenAI, Evaluation best practices
  - https://developers.openai.com/api/docs/guides/evaluation-best-practices
- OpenAI, Safety in building agents
  - https://developers.openai.com/api/docs/guides/agent-builder-safety
- OpenAI, Improving support with every interaction at OpenAI
  - https://openai.com/index/openai-support-model/
- Anthropic, Customer support agent
  - https://platform.claude.com/docs/en/about-claude/use-case-guides/customer-support-chat
- Anthropic, Define success criteria and build evaluations
  - https://platform.claude.com/docs/en/test-and-evaluate/develop-tests
- Google, Structured outputs
  - https://ai.google.dev/gemini-api/docs/structured-output
