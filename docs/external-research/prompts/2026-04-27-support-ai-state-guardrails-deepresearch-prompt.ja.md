# ChatGPT Deep Research 用プロンプト

以下を ChatGPT Deep Research にそのまま投げてください。

---

あなたは、AI customer support agent / LLM guardrails / support QA / workflow orchestration / conversational AI evaluation の専門リサーチャーとして調査してください。

目的は、公開情報から「実務返信AIを、単なる文章生成ではなく、状態・取引構造・業務ルール・顧客心理・監査ループを持つシステムとして成立させる方法」を調べることです。

私のプロジェクトでは、ココナラ向けの日本語返信システムを作っています。  
現状の重要概念は以下です。

- `phase contract`: 購入前 / 見積り提案後 / 購入後 / 正式納品後承諾前 / closed 後など、取引 phase ごとに「言ってよいこと」「できること」「できないこと」を分ける。
- `transaction_model_gap`: 返信文が不自然になる原因を、日本語だけでなく、取引構造・支払い状態・作業開始条件・成果物返却導線の欠落として見る監査レンズ。
- `closed 後の確認材料/実作業境界`: closed 後でもメッセージ上でログ・スクショ・症状概要を見ることはあるが、コード修正・具体的修正指示・成果物返却などの実作業は、見積り提案や新規依頼などの正式導線が必要。
- `#RE 学習ループ`: 実ストックの返信候補を作り、Codex / Claude などで監査し、必須修正だけ batch 内で反映し、再発証拠があるものだけ validator / gold / reviewer_prompt / rule へ戻す。
- 方針: 骨格を広く再設計しない。単発の違和感で rule を増やさない。再発性があり、ノイズを増やさず、実務リスクを下げるものだけ最小反映する。

調査してほしいこと:

1. 英語圏・海外で、customer support AI / AI agent / helpdesk AI / conversational AI において、状態管理、workflow guardrails、policy guardrails、action guardrails、support QA scorecard、continuous improvement loop を実務実装している公開事例を調べてください。

2. Intercom Fin、Zendesk AI agents、Salesforce Agentforce、Google Conversational Agents / Dialogflow CX、NVIDIA NeMo Guardrails、Replicant、その他 support automation ベンダーや open-source framework について、以下の観点で比較してください。
   - knowledge base / business rules / workflow / state / tools / policy / QA / analytics のどこを担っているか
   - LLM に任せている部分と、決定的ルール・workflow・validator に分けている部分
   - multi-turn / customer state / closed ticket / escalation / refund / billing dispute / privacy / secrets の扱い
   - 継続改善ループの作り方

3. 学術研究・技術記事から、LLM customer support agents の失敗モードを調べてください。
   特に以下を重点的に:
   - multi-turn で迷子になる
   - 必要情報を集めない
   - 早い段階の誤った仮定を引きずる
   - policy / confidentiality / privacy を破る
   - できない作業をできるように見せる
   - customer の次アクションが不明になる
   - tone は自然だが、取引構造が曖昧で危険になる

4. `transaction_model_gap` に近い既存概念があるか調べてください。
   近い概念がある場合は名称・出典・定義を示してください。
   近いが完全一致しない場合は、どこが似ていてどこが違うかを説明してください。

5. support QA scorecard / conversation QA rubric の公開事例を調べ、日本語実務返信システムに転用できる評価軸を提案してください。
   既存の評価軸は以下です。
   - 主質問への直答
   - scope 順守
   - 情報節約
   - 自然さ
   - 次アクション明確さ
   追加候補として以下が妥当か検証してください。
   - transaction clarity
   - phase route clarity
   - work/payment boundary clarity
   - buyer not lost
   - responsibility over-admission risk
   - free-support expectation risk
   - surface overexposure

6. closed ticket / resolved ticket / post-resolution complaint / refund expectation / billing dispute に対して、AI support agent がどう返すべきかの best practice を調べてください。
   ただし、英語圏の返金・サポート慣習をそのまま日本語・ココナラへ持ち込まないでください。転用可能な構造だけ抽出してください。

7. 日本語の高文脈・丁寧語・責任認定回避・怒り気味 customer 対応に転用する時、英語圏 guardrail をそのまま入れるとノイズになりそうな点を指摘してください。

8. 最後に、私の返信システムへ落とし込むなら、以下の4分類で提案してください。
   - validator に入れるべきもの
   - reviewer_prompt に入れるべきもの
   - gold reply として持つべき型
   - 入れない方がよいもの / ノイズになるもの

出力形式:

1. Executive Summary
2. Public Examples / Products
3. Research Findings
4. Failure Mode Taxonomy
5. `transaction_model_gap` と既存概念の比較
6. QA / Review Rubric 提案
7. ココナラ日本語返信システムへの適用案
8. 直接入れない方がよいもの
9. 優先度つき action list
10. 参考リンク一覧

注意:

- 必ず出典リンクを付けてください。
- ベンダーの宣伝文句は鵜呑みにせず、実装上使える部分と誇張を分けてください。
- 「AIで全部自動化できる」という一般論ではなく、実務で事故らないための state / workflow / guardrail / QA / improvement loop を重点的に見てください。
- 私の目的は、抽象論ではなく、日本語実務返信システムの validator / reviewer_prompt / gold / rule に落とせる形の知見を得ることです。
