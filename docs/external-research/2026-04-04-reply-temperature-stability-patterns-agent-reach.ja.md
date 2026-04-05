# 2026-04-04 返信文の温度感 安定化パターン調査（Agent-Reach）

## 目的
- 返信 system で、構造の正しさはかなり安定してきた一方、温度感だけが「直す -> 再発」を繰り返す理由を外部情報から調べる。
- 特に、prompt 追記や NG 語彙追加ではなく、**温度感を再発しにくくする実装パターン**を見たい。

## 先に結論
- いま足りないのは「もっと共感的に書け」という大きい指示ではなく、**温度感を構造から分離して first-class に扱う設計**です。
- 外部ソースを突き合わせると、温度感の安定化で効くのは次の5点でした。
  1. `温度感を vibe ではなく評価可能な下位項目へ分解する`
  2. `generic empathy ではなく user-context-aware な受け止めにする`
  3. `答えを作る段と、温度をのせる段を分ける`
  4. `温度感の評価は総合点より pairwise / rubric / held-out stress set に寄せる`
  5. `必要なら prompt 改善で止めず、preference optimization まで進める`
- つまり、今の system で次に足すべきは `もっと自然化` ではなく、**temperature_plan + tone eval + slot-preserving style transfer** です。

## 今の system がモグラ叩きになる理由
- 既存改善で、`何に答えるか` `何を保留するか` `何を聞くか` はかなり contract 化されている。
- ただし `どの温度で受け止めるか` は、まだ
  - NG 語彙
  - self-check
  - 自然化
  - Claude 監査
  に散っていて、**出力契約の主語になっていない**。
- その結果、semantic は守れても tone は毎回 prose 側で再生成され、場面ごとに再発する。

## 外部ソースから見えた共通パターン

### 1. 温度感は「総合的に優しいか」ではなく、下位要素で評価した方が安定する
- Nature Machine Intelligence の 2025 論文は、 empathic communication を単一感情ではなく、複数の evaluative framework と subcomponent で見るべきだと整理している。
- ここで重要なのは、`empathy-as-a-trait` ではなく、**その言葉が相手にどう受け取られるか** を評価対象にしている点。
- 示唆:
  - 「温度感」を1本の抽象軸で持つと again vibe 評価になる。
  - system では次のように分解した方がよい。
    - 相手の状態シグナルを拾ったか
    - 負担を下げたか
    - 行動を先に置けたか
    - 弁明に流れていないか
    - 冷たい内部語彙が漏れていないか

### 2. generic empathy はできても、user-context-aware support が不足しやすい
- EmoHarbor (2026) は、先端 LLM でも generic empathetic response は出せる一方、**個別の心理状態や状況に合わせた support には失敗しやすい** と報告している。
- これは今の症状とかなり一致する。
  - 相手文に返してはいる
  - でも「その人がいま何に困っているか」に合った温度になりきらない
- 示唆:
  - 足りないのは empathy phrase の数ではなく、`stress / hesitation / confusion / relationship / negative_feedback / time_pressure` のような **状況シグナル別の微分岐**。

### 3. 1段生成より、内容生成 -> style transfer の2段に分けた方が安定する
- 2023 Findings of EMNLP の empathy style transfer 論文では、GPT-4 に対する prompting で、**few-shot target prompting** と **dialog-act-conditioned prompting** が、content を保ちながら empathy を上げた。
- 論文内では、prior work として **two-stage system (response generation + style transfer)** が one-stage よりよい、という整理も置かれている。
- 示唆:
  - いまの naturalize を free rewrite のまま使うのではなく、
    - neutral but correct draft
    - signal-conditioned warmth rewrite
    の2段に分ける方がよい。
  - ただし rewrite は全文自由化ではなく、**slot-preserving** にする必要がある。

### 4. Tone は open-ended 採点より pairwise / criteria-based の方が安定する
- OpenAI の evaluation best practices は、LLM は open-ended generation より、**pairwise comparison / classification / specific criteria scoring** の評価で安定しやすいとしている。
- Anthropic の eval docs も、customer service の tone/style を LLM-based Likert で見つつ、**detailed, clear rubrics** を持つべきとしている。
- 示唆:
  - 今の「Claude に厳しめ監査」は方向として合っている。
  - ただし今後は、総評中心ではなく
    - A/B のどちらが自然か
    - signal pickup はあるか
    - burden leak はないか
    - defense はないか
    の rubric へ寄せた方が再発防止に効く。

### 5. 温度感は prompt 調整だけでなく preference optimization 向きの領域
- OpenAI の model optimization guide は、DPO を `Generating chat messages with the right tone and style` に向く手法として挙げている。
- つまり、温度感のような「正解が1本ではないが、悪い候補は分かる」領域は、**accepted / rejected pairs** をためて preference 学習に乗せるのが自然。
- 示唆:
  - 50件の監査ログは、まさに DPO / reranker / pairwise judge 用の種になる。
  - すぐ fine-tune しなくても、
    - pairwise reranker
    - best-of-k
    - accepted/rejected bank
    にはすぐ使える。

### 6. empathy は強ければよいわけではなく、状況依存
- Journal of Business Research の 2024 論文は、 empathic chatbot が social presence と information quality を高める一方、**time pressure 下では customer experience を損なうこともある** と報告している。
- 示唆:
  - 「温度を上げる」は危ない。
  - 正しくは、場面ごとに
    - 急ぎ: action-first, short reassurance
    - 遠慮: pressure-release first
    - ネガティブFB: receive, no defense
    - 境界ケース: yes/no first, scope calmly
    のように切り替える必要がある。

### 7. support quality は tone 単独ではなく、 knowledge / classifiers / evals の循環で育てる
- OpenAI の support model article は、良い support system を
  - knowledge
  - evals and classifiers
  - observability
  の循環で育てるものとして書いている。
- これは今の workspace 運用と相性がよい。
- 示唆:
  - 温度感も `writer の才能` ではなく、**classify -> render -> style-transfer -> grade -> feed back** の循環へ入れるべき。

## 外部調査から見た「まだ足りないもの」

### 1. tone を決める explicit contract
- 今の reply_contract に近い層の横に、次のような `temperature_plan` を置くのがよい。

```json
{
  "user_signal": "stress | hesitation | confusion | relationship | negative_feedback | neutral",
  "support_goal": "reassure | reduce_burden | normalize | appreciate_relation | receive_feedback | move_forward",
  "opening_move": "action_first | pressure_release | value_return | receive_and_own | normalize_confusion",
  "tone_constraints": [
    "no_defense",
    "no_internal_scope_words",
    "no_pm_words",
    "no_negative_lead"
  ]
}
```

- 重要なのは、`温度感を自然化工程に丸投げしない` こと。

### 2. stress-set / boundary-set / feedback-set の holdout
- これまでの50件でも、落ちる条件は
  - handoff境界
  - ストレス時
  - ネガティブFB
  に集中していた。
- これは外部知見と一致する。
- したがって eval は全件平均ではなく、**落ちやすい3条件を別bucketで監視** した方がよい。

### 3. A/B 比較ベースの tone grader
- 1文だけ見て `温かいか` を採点するより、
  - draft A
  - draft B
  を比べて「どちらが相手の温度に合うか」を選ばせる方が安定する。
- OpenAI docs の方針とも一致。
- 監査 prompt も、今後は
  - 単独批評
  より
  - before / after 比較
  - baseline / candidate 比較
  の方が使いやすい。

### 4. accepted / rejected ペアの蓄積
- 今回の 50件監査は、単なる添削履歴ではなく
  - original
  - Claude最小修正
  - 採用版
  の pair データになっている。
- これは
  - reranker
  - DPO
  - preference bank
  のどれにも転用できる。

## 今の workspace に対する実装提案

## 推奨順位
1. `temperature_plan` を reply_contract の sibling として追加
2. naturalize を `signal-conditioned slot rewrite` に変更
3. tone grader を pairwise 化
4. holdout を `stress / boundary / feedback` で分離
5. accepted/rejected pairs を preference bank 化

### 1. temperature_plan を追加する
- reply-only 判定で十分。
- 最初から細かくしすぎず、6分類程度でよい。
  - stress
  - hesitation
  - confusion
  - relationship
  - negative_feedback
  - neutral

### 2. naturalize を「全文自然化」から「冒頭と接続部の style transfer」へ寄せる
- raw user message と service facts を全部渡すより、
  - rendered draft
  - temperature_plan
  - 해당 bucket の good examples 2〜3本
  だけを渡す。
- 固定すべきもの:
  - 結論
  - 価格
  - ask 数
  - next action
  - scope
- 可変にしてよいもの:
  - 冒頭1〜2文
  - ask 前のつなぎ
  - closing の負担感

### 3. eval を「温度総合点」から「4〜5観点の rubric + pairwise」へ変える
- 例:
  - 相手の状態シグナルを拾っているか
  - 不安 / 遠慮 / 負担を減らしているか
  - 余計な防御や説明に流れていないか
  - 社内語 / PM語 / デバッグ語が漏れていないか
  - 行動と結論の明確さを崩していないか

### 4. 落ちやすい条件だけ別に監視する
- 全件平均より、次の3条件の下限を持った方がよい。
  - scope boundary
  - stress / urgency
  - negative feedback

### 5. 必要なら preference optimization を検討する
- もし prompt + renderer + pairwise grader でも再発が続くなら、
  - DPO 用の accepted / rejected dataset
  - reranker
  - best-of-k
  へ進むのが順当。
- 50件の監査ログは、その初期データとして十分価値がある。

## 実務的な暫定判断
- いまの段階では、**「温度感専用の contract と eval」を足すのが最優先**で、すぐ fine-tune までは行かなくてよい。
- 先にやるべきは
  - `temperature_plan` の導入
  - naturalize の slot 限定
  - pairwise tone grader
  - holdout 3条件化
- その上で再発が残るなら、DPO / reranker を検討するのが順番としてきれい。

## 参考ソース
- OpenAI, Evaluation best practices
  - https://developers.openai.com/api/docs/guides/evaluation-best-practices
- OpenAI, Model optimization
  - https://developers.openai.com/api/docs/guides/model-optimization
- OpenAI, Improving support with every interaction at OpenAI
  - https://openai.com/index/openai-support-model/
- OpenAI, Strengthening ChatGPT’s responses in sensitive conversations
  - https://openai.com/index/strengthening-chatgpt-responses-in-sensitive-conversations/
- Anthropic, Customer support agent
  - https://platform.claude.com/docs/en/about-claude/use-case-guides/customer-support-chat
- Anthropic, Define success criteria and build evaluations
  - https://platform.claude.com/docs/en/test-and-evaluate/develop-tests
- Nature Machine Intelligence, When large language models are reliable for judging empathic communication
  - https://www.nature.com/articles/s42256-025-01169-6
- Journal of Business Research, Empathic chatbots: A double-edged sword in customer experiences
  - https://www.sciencedirect.com/science/article/pii/S0148296324005782
- Findings of EMNLP 2023, Conditioning on Dialog Acts Improves Empathy Style Transfer
  - https://aclanthology.org/2023.findings-emnlp.884.pdf
- arXiv, EmoHarbor: Evaluating Personalized Emotional Support by Simulating the User's Internal World
  - https://arxiv.org/abs/2601.01530
- arXiv, Cause-Aware Empathetic Response Generation via Chain-of-Thought Fine-Tuning
  - https://arxiv.org/abs/2408.11599
