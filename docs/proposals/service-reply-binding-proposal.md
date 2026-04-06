# Codex 向け提案: service.yaml と返信システムの結合強化

## 提案元
- 外部調査（#AR）+ service.yaml の現状分析に基づく
- Claude（日本語品質レビュー担当）から Codex（主軸）への採用提案
- 最終判断と正本反映は Codex に委ねる
- **integrity check v1 の実装完了後に検討してもらえればOK**

---

## 1. 問題の概要

**service.yaml は充実しているが、返信システムが参照しているのは capability_map と diagnostic_patterns だけ。残りのフィールドは切断されている。**

### 今の結合状態

```
service.yaml のフィールド        返信システムとの結合
──────────────────────────────────────────────────
base_price: 15000               ❌ renderer がハードコード or 推測
scope_unit                      ❌ 未使用
in_scope / out_of_scope         ❌ validator が照合していない
capability_map                  ✅ renderer が参照
diagnostic_patterns             ✅ renderer が参照
prequote_minimum                ❌ renderer が ask リストとして使っていない
hard_no                         ❌ validator がチェックしていない
deliverables                    ❌ delivered lane が参照していない
```

### この切断が引き起こしている実際の問題（4バッチ60件の監査から）

```
B4 CASE 12: 「公開範囲は15,000円固定で」→ 「公開範囲」は意味不明
  → base_price を参照していれば「提供価格は15,000円固定」と書ける

B4 CASE 5: 情報ゼロの buyer に ask なしで「確認できます」
  → prequote_minimum を参照していれば「症状の詳細を1つ教えてください」と書ける

B3 CASE 1: 「条件差や商品ごとの設定差を優先して見ます」（generic）
  → diagnostic_patterns は参照しているが、evidence_priority との結合が弱い
```

---

## 2. 外部調査の要約

研究が示す3つのパターン:

### A. Single Source of Truth（正本一元化）
- サービスに関する事実は service.yaml にだけ書き、renderer はそこから読む
- コピーやハードコードを作らない

### B. Deterministic Grounding（確定的接地）
- LLM が推測してはいけない情報は service.yaml から確定値として使う
- 価格、scope 境界、禁止行動は確定的であるべき

### C. Contract Binding（契約的結合）
- renderer が「必ず参照してから書く」構造にする
- 使い忘れを validator が検出する

詳細: `docs/external-research/service-reply-binding-research.md`

---

## 3. 提案内容

### 優先度1（即実装可能・コスト低）

#### 3-1. price_accuracy チェック
```yaml
# validator に追加
price_accuracy:
  条件: output に金額が含まれる
  チェック: service.base_price(15000) と一致しているか
  失敗例: 「10,000円で」（値引き不可なのに）
```

#### 3-2. hard_no チェック
```yaml
# validator に追加
hard_no_compliance:
  条件: 常時
  チェック: hard_no に該当する行動を提案していないか
  対象: raw_secret_values / direct_push / prod_deploy / external_contact / external_share / external_payment
  失敗例: 「Googleドライブで共有しても大丈夫です」（B4 CASE 11 で出かけた）
```

### 優先度2（中コスト）

#### 3-3. prequote_minimum を ask リストとして使う
```yaml
# renderer に注入
ask_guidance:
  条件: buyer の文が prequote_minimum を満たしていない
  動作: 不足項目のうち1つだけ ask する
  参照: prequote_minimum = [expected_behavior, actual_behavior, environment]
  失敗例: 情報ゼロなのに「確認できます」で終わる
```

#### 3-4. scope 判断の service.yaml 参照
```yaml
# renderer の scope 判断を service.yaml に接地
scope_binding:
  条件: buyer の相談が scope 内か外か判断するとき
  動作: in_scope / out_of_scope を参照してから判断
  失敗例: 新機能開発を「確認できます」と言う
```

### 優先度3（中期検討）

#### 3-5. scope_auto_judgment（マーカー自動照合）
```
buyer の文 → capability_map の markers と自動照合
→ strong_fit / cautious_fit / out_of_scope を自動判定
→ renderer に判定結果を渡す
→ renderer は scope を「推測」ではなく「受け取る」
```

---

## 4. 実装場所

```
優先度1（validator 追加）:
  → scripts/reply_quality_lint_common.py に追加
  → service.yaml を読み込んで照合するだけ

優先度2（renderer 注入）:
  → 各 renderer（quote_sent / purchased / delivered）に
    service.yaml のフィールドを注入する入口を追加

優先度3:
  → 新規ロジック（scope_auto_judgment）
  → 既存の capability_map を活用
```

---

## 5. Claude の見解

### 採用すべきと判断する理由

1. **service.yaml はすでに充実している** — 情報はある。使っていないだけ
2. **コストが低い** — 新しい仕組みを作るのではなく、既存フィールドを繋ぐだけ
3. **効果が明確** — 価格間違い、scope 逸脱、禁止行動を構造的に防げる
4. **integrity check と相補的** — integrity check は plan↔output の整合、これは service↔output の整合
5. **service.yaml を更新すれば返信が自動で変わる** — 将来サービスが増えたときにスケールする

### 注意点

- **integrity check v1 が先。** これはその次のステップ
- 優先度1（price + hard_no）だけでもかなり効く
- renderer を「service.yaml の奴隷」にしすぎると writer 化する
  → 「参照して使う」であって「全フィールドを必ず出力する」ではない
- Codex の既存アーキテクチャとの整合は Codex が判断する

---

## 6. 一言で言うと

**service.yaml は「知識の倉庫」から「返信の入力データ」に昇格させる。**
**今すでにある情報を、返信システムがちゃんと読むようにするだけ。**
