# #AR 調査結果 — LLM 思考保全の研究と改善案

## 調査対象
「LLM の思考（reasoning）が出力で上書きされる問題」の原因・研究・改善手法

## ソース
- arxiv.org（論文複数）
- alignmentforum.org（AI 安全性研究）
- medium.com（実務記事）
- prompthub.us（プロンプトエンジニアリング）
- various AI engineering blogs（2024-2026）

---

## 1. 問題の正体

研究では「Unfaithful Chain-of-Thought」と呼ばれている。

```
正常:
  thinking:「buyer は怒っている → 感情を拾う」
  output: 感情を拾った返信

異常（unfaithful）:
  thinking:「buyer は怒っている → 感情を拾う」
  output: 感情を無視した定型文 ← thinking と矛盾
```

### 原因は3つ
1. **構造 vs 推論の衝突**: テンプレート制約が強いと、LLM は「正しい形式」を優先して「正しい内容」を犠牲にする
2. **Post-hoc rationalization**: LLM は先に答えを決めてから、後付けで reasoning を生成することがある（thinking が飾り）
3. **Token 確率の引力**: 定型フレーズ（「確認できます」等）は出現確率が高いため、reasoning で避けるべきと判断しても出力で引っ張られる

---

## 2. 研究が示す解決策

### A. Two-Step Generation（2段階生成）★★★ 最有望

```
現在:
  1ステップで reasoning + 出力 を同時にやらせている
  → 出力フォーマットが reasoning を上書きする

改善:
  Step 1: Reasoning Call（思考だけ）
    → 「buyer の主質問は何か」「感情は？」「scope は？」
    → フォーマット制約なし、自由に考えさせる

  Step 2: Formatting Call（出力だけ）
    → Step 1 の結果を受け取って、返信文を書く
    → ここで初めてテンプレート制約を適用
```

**なぜ効くか:**
- Step 1 では「考える」ことだけに集中できる
- Step 2 では「書く」ことだけに集中できる
- 思考と出力が別の呼び出しなので、出力が思考を上書きできない

### B. Self-Consistency（複数出力からベストを選ぶ）★★

```
現在:
  1回生成 → 1つの出力 → そのまま採用

改善:
  3回生成 → 3つの出力 → 一番良いものを選ぶ
  選び方:
    - LLM-as-a-judge（別の AI に判定させる）
    - ルールベースチェック（near-echo, 主質問回答の有無）
```

**なぜ効くか:**
- 1回の生成で思考が消されても、3回中2回は保全される可能性が高い
- 確率の問題を「試行回数」で解決する

**コスト:** API 呼び出しが3倍になる

### C. Post-Render Integrity Check（出力後の整合チェック）★★

```
現在:
  response_decision_plan → 出力 → 送信

改善:
  response_decision_plan → 出力 → 整合チェック → 送信
  
  整合チェックの内容:
    ① plan で「buyer は怒っている」と書いた → 出力で感情を拾っているか？
    ② plan で「主質問は返金か」と書いた → 出力で返金に答えているか？
    ③ plan で「scope 外」と書いた → 出力で scope 外と伝えているか？
    → 矛盾があれば再生成 or フラグ
```

**なぜ効くか:**
- thinking の内容と output の内容を突き合わせる
- thinking が正しいのに output が間違っている場合を検出できる

### D. 禁止パターンの確率的抑制 ★

```
現在:
  validator で禁止ワードをチェック

改善:
  生成時に logit_bias で特定トークンの確率を下げる
  例: 「確認できます」の先頭トークンの確率を -5 にする
  → LLM がそのフレーズを選びにくくなる

  ※ API によっては使えない
```

---

## 3. あなたのシステムへの適用案

### 現在の構造
```
response_decision_plan → renderer → japanese-chat-natural-ja → validator → 出力
```

### 改善案（実装難易度順）

#### 即実装可能
```
改善1: Plan-Output 整合チェック（validator に追加）
  → plan の「主質問」フィールドが output に含まれているかチェック
  → plan の「buyer 感情」フィールドが output で触れられているかチェック
  → コスト: API 追加なし、validator のルール追加のみ

改善2: 禁止パターンリストの強化
  → 「確認できます」の前に必ず buyer の症状を入れるルール
  → 「先にお伝えします」→ 次の行で実際に伝えているかチェック
  → コスト: ルール追加のみ
```

#### 中期的に実装
```
改善3: Two-Step Generation
  → Step 1: Codex に thinking だけ書かせる（JSON で構造化）
  → Step 2: thinking の結果を別の呼び出しに渡して返信文を生成
  → コスト: API 2倍、実装工数中

改善4: Self-Consistency（2回生成 + ベスト選択）
  → 同じ入力で2回生成 → validator スコアが高い方を採用
  → コスト: API 2倍
```

#### 将来的
```
改善5: LLM-as-a-judge（Claude/Gemini が Codex の出力を自動監査）
  → 今手動でやっている監査を自動化
  → コスト: API 追加、ただし今の手動作業が消える
```

---

## 4. 最も効果対コストが高い改善

```
★ Plan-Output 整合チェック（改善1）
  効果: 思考が消されても、出力が思考と矛盾していれば検出できる
  コスト: validator にルール追加するだけ
  実装: Codex に依頼すれば数時間

  具体的なチェック項目:
  ① plan.primary_question が output に含まれているか
  ② plan.buyer_emotion != null なら、output で触れているか
  ③ plan.scope_judgment が output と一致しているか
  ④ 「先にお伝えします」と書いたら、次の行で何か伝えているか
```

**これだけで、CASE 7（空約束）と CASE 1（感情無視）の問題は自動検出できる。**

---

## 5. raw データ

/tmp/ に保存なし（Web 検索結果のみ、URL は上記ソース参照）
