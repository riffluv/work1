# 温度感レイヤー調査書 — Human Warmth Layer Research

## 調査目的
返信システムの品質 4.8 を壊さずに、人間が書いたような温度感を足す方法を調査する。
構造面の実装パターンを世界の業界実践・学術研究から取得し、Codex への提案の根拠とする。

## ソース一覧
1. Rasa Documentation — Assistant Tone（Response Rephraser）
2. Intercom — Fin AI Agent tone of voice customization
3. Zendesk — Best practices for AI agent tone of voice
4. LTVplus — 9 Guardrails for Emotional AI Detection
5. Oxford University — "Training language models to be warm and empathetic makes them less reliable and more sycophantic"
6. Springer — "Linguistic humanization in conversational AI"
7. IEEE — "Care-by-Design: Enhancing Customer Experience through Empathetic AI Chatbots"
8. ScienceDirect — "Emotional AI: The impact of chatbot empathy and emotional tone on consumer satisfaction"
9. doda / 日本ビジネスメール協会 平野友朗氏
10. サイボウズ THE HYBRID WORK — テキストコミュニケーション感情表現
11. BerriAI litellm — Tone Detector Guardrail PR

---

## 1. 業界の実装パターン（3社比較）

### Rasa: Response Rephraser（★★★ 最も参考になる）
- **方法**: 事実的な返信を先に生成 → Response Rephraser が最終的にブランドトーンで書き直す
- **構造**: `reasoning → base response → rephraser (LLM) → final output`
- **テスト**: 2つの assertion で品質保証
  - `generative_response_is_relevant`: トピックから外れていないか（閾値 0.90）
  - `generative_response_is_grounded`: 元の事実が保たれているか（閾値 0.90）
- **重要**: rephraser は「意味と事実を保持しながら、トーンだけ変える」ことを保証
- **適用**: 全レスポンスに一括適用 or 特定レスポンスのみ（metadata で制御）
- **カスタムプロンプト**: Jinja2 テンプレートでブランドトーン指示を書ける

### Intercom Fin: Tone of Voice
- **方法**: guidance として tone description を渡す（inline 型）
- **設定**: "friendly", "formal", "professional" などから選択 + カスタム記述
- **構造**: guidance が生成時に適用される（post-processing ではない）
- **重要**: knowledge sources と guidance を分離。guidance は応答前に必ず適用

### Zendesk: AI Agent Tone
- **方法**: persona + tone of voice + pronoun formality を設定
- **重要なベストプラクティス**:
  > "The AI agent should be assertive when gathering information
  > and empathetic if the customer has had a bad experience.
  > Try and avoid an overly formal tone as this can sound robotic."
- **文脈依存のトーン切替**: 情報収集時は assertive、bad experience 時は empathetic
- **反映タイミング**: 生成時（inline 型）

---

## 2. 学術研究の知見

### Oxford University（2025）— ★★★ 最重要
**論文**: "Training language models to be warm and empathetic makes them less reliable and more sycophantic"

**結論**: 温かさと共感を「訓練」で入れると、正確性が下がり、おべっかが増える。

**意味**:
- 温度感を system prompt で「常に温かく書け」と入れると、正確さが犠牲になるリスクがある
- 特に、buyer の間違いを指摘する場面で「共感しすぎて事実を曲げる」事故が起きる
- → 温度感は「全面適用」ではなく「条件付き・最小限」で入れるべき

### Springer（2025）— Linguistic Humanization
**論文**: "Linguistic humanization in conversational AI: humor, empathy, tone, and imperfection"

**知見**:
- 人間らしさを作るのは「完璧さの欠如」（imperfection）
- ユーモア、共感、トーンの揺れ、言い間違い → これらが「人間っぽさ」を構成
- ただし、ビジネス文脈では imperfection は信頼を下げるリスクもある
- → 「完璧すぎない」が「不正確」になってはいけない

### ScienceDirect（2026）— Emotional AI と顧客満足度
**論文**: "Emotional artificial intelligence: The impact of chatbot empathy and emotional tone on consumer satisfaction"

**知見**:
- 共感的なトーンは顧客満足度と口コミを向上させる
- ただし、共感が「過剰」だと逆効果（不誠実に見える）
- 最適なのは「文脈に応じた共感の濃度調整」

---

## 3. 日本語固有のテキスト温度感

### doda / 日本ビジネスメール協会（平野友朗氏）
**核心**: 「情報が正しく伝わっていないのに温度感を気にしても意味がない」

**温度感テクニック（優先順）**:
1. 漢字を開く: 致します → いたします、宜しく → よろしく
2. 「させていただく」は1通1回以下
3. クッション言葉は最小限
4. テンプレ挨拶は省略（心からの言葉でなければ逆効果）
5. **テンプレートの対極にある言葉が心に届く**
   - 例: 「〇〇さんの進め方が円滑でとても助かりました」
   - → 具体的で、その人にしか言えない言葉

### サイボウズ THE HYBRID WORK
**テキストコミュニケーションの感情表現5つ**:
1. お礼・理解・肯定・共感をまず明示する
2. 口語的なリズムを残す（「あー」「なるほど」は使わないが、呼吸感を持たせる）
3. 否定だけせず提案もする
4. 記号や絵文字を戦略的に使う（ビジネスでは「！」程度）
5. テキストで伝えにくいことを無理にテキストで伝えようとしない

---

## 4. 実装パターンの比較

### Pattern A: Post-Processing Filter（事後フィルタ）
```
buyer message → Codex が返信生成 → 温度フィルタ（別LLM）→ 最終出力
```
- **例**: Rasa の Response Rephraser
- **利点**: 既存のロジックを壊さない。事実は先に確定している
- **欠点**: 2回のLLM呼び出し。フィルタが事実を壊すリスク
- **Rasa の対策**: grounded assertion で事実保持を検査
- **評価**: ★★ 安全だが、Codex 環境では2段呼び出しが難しい

### Pattern B: Inline Guidance（生成時ガイダンス）
```
buyer message + 温度ガイダンス → Codex が温度込みで返信生成
```
- **例**: Intercom Fin, Zendesk
- **利点**: 1回の生成で完結。既存の scaffolding に自然に入る
- **欠点**: ガイダンスが重すぎると reasoning を圧縮する
- **評価**: ★★★ 最もフィットする。platform contract と同じ仕組み

### Pattern C: Conditional Variation（条件分岐）
```
state に応じて異なるトーンテンプレートを適用
```
- **例**: Rasa の Conditional Response Variations
- **利点**: 完全に制御可能
- **欠点**: 全ケースの事前定義が必要。scaffolding の自由さを殺す
- **評価**: ★ framework 回帰になる。今のシステムには合わない

### Pattern D: Context-Dependent Tone Map（★★★ 推奨）
```
buyer の感情状態 × state で、適用する温度レベルを決める
→ Codex に guidance として渡す
→ 判断は Codex
```
- **Zendesk のベストプラクティスに最も近い**:
  > "assertive when gathering information, empathetic if bad experience"
- **利点**: 全面適用しないから sycophancy リスクが低い
- **Oxford 論文の警告を回避できる**
- **評価**: ★★★ 最も安全 + 効果的

---

## 5. 実装提案（Codex レビュー用）

### 提案: Context-Dependent Warmth Guidance

**原則:**
- 温度は「常に ON」ではなく「条件に応じて濃度を変える」
- 温度の判断は Codex に任せる（scaffolding を維持）
- 事実と正確性は絶対に優先する（Oxford 警告の回避）

**温度マップ（案）:**
```yaml
warmth_guidance:
  # buyer の感情状態別の温度濃度
  buyer_is_grateful:
    warmth: high
    guidance: "buyerの好意や感謝には、具体的な受けを1文入れる"
    example: "お役に立てたなら嬉しいです"
    anti_pattern: "ありがとうございます。（だけで終わる）"

  buyer_is_frustrated:
    warmth: medium
    guidance: "共感は1文で短く。すぐ具体的な対応を示す"
    example: "ご不便をおかけしてすみません。"
    anti_pattern: "ご心配のお気持ち、とても分かります。（共感が長すぎる）"

  buyer_is_neutral:
    warmth: default
    guidance: "余計な温度は足さない。正確に端的に"
    anti_pattern: "不要な感情表現を入れる"

  buyer_is_anxious:
    warmth: medium-high
    guidance: "安心できる根拠を1つ示してから本題に入る"
    example: "この手の症状はよく見るケースです。"
    anti_pattern: "大丈夫ですよ！（根拠のない安心）"
```

**日本語固有のルール（案）:**
```yaml
japanese_warmth_rules:
  open_kanji:
    - 致します → いたします
    - 宜しく → よろしく
    - 有難う → ありがとう
    - 下さい → ください

  avoid:
    - 「させていただく」は1返信に1回以下
    - クッション言葉の連発
    - テンプレート的な時候の挨拶
    - 「ご認識のほどよろしくお願いいたします」

  prefer:
    - 「思います」> 「存じます」
    - 「嬉しいです」>「幸甚です」
    - 「助かります」>「幸いに存じます」
    - 具体的な受けの1文（相手の行動に触れる）

  never:
    - 根拠のない安心（「大丈夫ですよ！」）
    - 共感の長文化（1文を超える共感は過剰）
    - 相手の感情の先読み・完成
    - sycophancy（おべっか）
```

**テスト方法:**
- B11 で同じケースを温度 guidance あり/なしで比較
- 監査観点に「温度適切か」を追加
- 事実の正確性が落ちていないか検証（Oxford 警告チェック）

---

## 6. Codex への質問

1. この guidance は skill に入れるか、self-check に入れるか、別の場所か？
2. warmth_guidance は platform-contract のように常時ロードか、mode 依存か？
3. japanese_warmth_rules は既存の code-comment-style.ja.md や
   japanese-chat-natural-ja と統合すべきか、分離すべきか？
4. Oxford の警告（温度を入れると sycophancy が増える）にどう対処するか？
5. v1 はどこまで入れるか？
