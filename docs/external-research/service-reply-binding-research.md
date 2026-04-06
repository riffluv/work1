# #AR 調査結果 — サービス定義と返信システムの結合強化

## 調査対象
「サービス定義（service.yaml）と返信システムの結合をどう強化すれば、返信の精度と一貫性が上がるか」

## ソース
- 複数の AI アーキテクチャ研究記事
- RAG / Grounding の 2025 ベストプラクティス
- YAML-as-single-source-of-truth パターン
- 顧客対応 AI エージェントの実装事例

---

## 1. 今のシステムの状態

```
service.yaml（サービス定義）
├── base_price: 15000
├── scope_unit: same_cause_and_same_flow_and_same_endpoint
├── in_scope / out_of_scope
├── capability_map（strong / cautious / out_of_scope）
├── diagnostic_patterns（evidence_priority）
├── prequote_minimum（必要情報リスト）
├── deliverables
└── hard_no

返信システム（renderer / validator）
├── response_decision_plan
├── render-quote-sent-followup.py
├── render-post-purchase-quick.py
├── render-delivered-followup.py
├── reply_quality_lint_common.py
└── japanese-chat-natural-ja
```

### 今の結合状態

```
service.yaml ──→ capability_map ──→ renderer が参照
                                     ↑ ここだけ繋がっている

繋がっていない部分:
  ❌ base_price → renderer は 15,000 をハードコードで書いている可能性
  ❌ in_scope / out_of_scope → validator が scope 判断に使っていない
  ❌ prequote_minimum → renderer が ask すべき項目を知らない
  ❌ hard_no → validator が禁止行動をチェックしていない
  ❌ deliverables → delivered lane が納品物を正確に伝えていない可能性
```

**つまり service.yaml は「知識を保存している場所」だが、返信システムが「読んで使っている部分」は capability_map と diagnostic_patterns だけ。残りは切断されている。**

---

## 2. 外部研究が示すパターン

### A. Single Source of Truth（正本一元化）★★★

```
原則: サービスに関する事実は1箇所にだけ書き、
      返信システムはそこから読む。
      コピーは作らない。

悪い例:
  service.yaml: base_price: 15000
  renderer:     ...15,000円で進めます...（ハードコード）
  → 価格を変えたとき、renderer の修正を忘れる

良い例:
  service.yaml: base_price: 15000
  renderer:     ...{service.base_price}円で進めます...（参照）
  → 価格を変えれば自動で反映
```

### B. Deterministic Grounding（確定的な接地）★★

```
原則: LLM が「推測」してはいけない情報は、
      service.yaml から読んで確定値として使う。

確定的であるべき情報:
  ✅ 価格（15,000円）
  ✅ scope 境界（in_scope / out_of_scope）
  ✅ 禁止行動（hard_no）
  ✅ 必要情報リスト（prequote_minimum）
  ✅ 納品物の内容（deliverables）
  
LLM に任せてよい情報:
  ○ buyer の感情の読み取り
  ○ 文面の自然化
  ○ 温度感の調整
```

### C. Contract Binding（契約的結合）★★

```
原則: renderer が service.yaml のフィールドを
      「必ず参照してから書く」構造にする。

今の renderer:
  → service.yaml を参照しているが、どのフィールドを使うかは任意
  → 使い忘れても検出されない

改善:
  → renderer の出力に「使った service.yaml のフィールド」を記録
  → validator が「必須フィールドを使ったか」をチェック
```

### D. Tiered Context（階層的コンテキスト注入）★

```
原則: renderer に渡す情報を3階層に分ける

Tier 1（必ず参照）:
  → base_price, in_scope, out_of_scope, hard_no
  → これを無視した返信は即NG

Tier 2（状況に応じて参照）:
  → capability_map, diagnostic_patterns
  → buyer の症状にマッチしたものだけ注入

Tier 3（ガードレール）:
  → prequote_minimum（ask すべき項目）
  → deliverables（納品物に言及するとき）
```

---

## 3. 今のシステムに落とし込める改善案

### 優先度1: service.yaml の確定値を renderer に注入する

```yaml
# renderer が必ず参照すべきフィールドを明示
renderer_binding:
  always_inject:
    - base_price        # 価格に言及するとき必ず使う
    - scope_unit        # scope 説明に使う
    - in_scope          # 「確認できます」の根拠
    - out_of_scope      # 「別の相談になります」の根拠
    - hard_no           # 絶対に言ってはいけないこと
  
  inject_when_relevant:
    - prequote_minimum  # 情報不足のとき ask リストとして参照
    - deliverables      # 納品物に触れるとき参照
    
  already_connected:    # 今もう繋がっているもの
    - capability_map
    - diagnostic_patterns
```

### 優先度2: validator に service.yaml チェックを追加

```yaml
service_grounding_checks:
  # 価格正確性
  price_accuracy:
    条件: output に金額が含まれる
    チェック: service.base_price と一致しているか
    失敗例: 「10,000円で」（値引き不可なのに）

  # scope 正確性
  scope_accuracy:
    条件: output に scope 判断が含まれる
    チェック: in_scope / out_of_scope と一致しているか
    失敗例: 新機能開発を「確認できます」と言う

  # hard_no 遵守
  hard_no_compliance:
    条件: 常時
    チェック: hard_no に該当する行動を提案していないか
    失敗例: 「GitHubに直接pushします」

  # ask リスト参照
  ask_list_reference:
    条件: buyer の情報が prequote_minimum を満たしていない
    チェック: 不足している項目を1つだけ ask しているか
    失敗例: 何も聞かずに「確認できます」（情報不足なのに）
```

### 優先度3: scope 判断の自動化

```yaml
# 今: renderer が buyer の文を読んで scope を推測
# 改善: buyer の文を service.yaml のマーカーと機械的に照合

scope_auto_judgment:
  step1: buyer の文から技術キーワードを抽出
  step2: capability_map の markers と照合
  step3: strong_fit / cautious_fit / out_of_scope を自動判定
  step4: renderer に判定結果を渡す
  
  → renderer は scope を「推測」ではなく「受け取る」
```

---

## 4. 効果の予測

```
今:
  service.yaml は「ドキュメント」として存在している
  renderer は「読むこともある」けど必須ではない
  → 結合度: 弱い（loose coupling）

改善後:
  service.yaml は「データベース」として機能する
  renderer は「必ず読んでから書く」構造になる
  → 結合度: 強い（tight binding）

期待される効果:
  ✅ 価格の間違いがゼロになる
  ✅ scope 判断が安定する
  ✅ 「何を聞くべきか」がブレなくなる
  ✅ 禁止行動を絶対に提案しなくなる
  ✅ service.yaml を更新すれば返信が自動で変わる
```

---

## 5. Codex への提案の要点

```
1. service.yaml を「読み物」から「返信の入力データ」に昇格させる
2. renderer が必ず参照するフィールドを明示する（renderer_binding）
3. validator に service.yaml との照合チェックを追加する
4. まず price_accuracy と hard_no_compliance から始める（コスト低）
5. scope_auto_judgment は中期的に検討
```
