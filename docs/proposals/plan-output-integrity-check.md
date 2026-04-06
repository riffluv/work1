# Codex 向け提案: Plan-Output 整合チェックの導入

## 提案元
- 外部調査（#AR）+ 横断監査（4バッチ60件）の結果に基づく
- Claude（日本語品質レビュー担当）から Codex（主軸）への採用提案
- 最終判断と正本反映は Codex に委ねる

---

## 1. 問題の概要

**response_decision_plan（thinking）は正しいのに、output が thinking を無視するケースが4バッチ連続で再発している。**

### 証拠（4バッチ60件の監査結果）

| バッチ | 問題ケース | 症状 |
|---|---|---|
| B2 CASE 2 | 空約束 | plan で「まだ伝えることがない」→ output で「先にお伝えします」（何も伝えない） |
| B2 CASE 3 | 感情無視 | plan で「buyer は前回失敗で不安」→ output で感情完全スルー |
| B2 CASE 15 | 感情無視 | plan で「buyer は怒りと不信感」→ output で感情完全スルー |
| B4 CASE 7 | 空約束（再発） | B2 CASE 2 と同一パターン。3バッチ経っても直っていない |
| B4 CASE 1 | 不適切コメント | plan で妥当な判断 → output で「日本語が整理しきれていない」（失礼） |

### なぜ validator だけでは防げなかったか

```
今の validator:
  → output だけを見ている
  → 「確認しました」等の禁止ワードは検出できる
  → しかし「plan で考えたことが output に反映されているか」は見ていない
  → だから「thinking は正しいのに output が定型に引っ張られる」問題を検出できない
```

---

## 2. 外部調査の結果

研究では「Unfaithful Chain-of-Thought」と呼ばれている問題。

### 原因（論文・研究の要約）
1. **構造 vs 推論の衝突**: テンプレート制約が強いと、LLM は「正しい形式」を優先して「正しい内容」を犠牲にする
2. **Token 確率の引力**: 定型フレーズ（「確認できます」等）は出現確率が高いため、reasoning で避けるべきと判断しても出力で引っ張られる
3. **Post-hoc rationalization**: LLM は先に答えを決めてから、後付けで reasoning を生成することがある

### 研究が示す解決策のうち、今のシステムに適用可能なもの

```
A. Plan-Output 整合チェック ← ★ 今回の提案
   → plan の内容と output を突き合わせて矛盾を検出
   → コスト: ルール追加のみ、API 追加なし

B. Two-Step Generation（2段階生成）
   → Step 1 で thinking だけ、Step 2 で output だけ
   → コスト: API 2倍 → 中期的に検討

C. Self-Consistency（複数生成 + ベスト選択）
   → コスト: API 3倍 → 将来的に検討
```

詳細: `/home/hr-hm/Project/work/docs/external-research/reasoning-preservation-research.md`

---

## 3. 提案内容: Plan-Output 整合チェック

### 概要

response_decision_plan の内容と、renderer の output を突き合わせるチェックを validator に追加する。

### 具体的なチェック項目

```yaml
plan_output_integrity_checks:

  # チェック1: 主質問への回答
  primary_question_answered:
    条件: plan.primary_question が設定されている
    チェック: output に plan.primary_question への直接回答が含まれているか
    失敗例: plan で「主質問は返金可否」→ output で返金に触れていない
    対応: 再生成 or フラグ

  # チェック2: buyer 感情の反映
  buyer_emotion_reflected:
    条件: plan.buyer_emotion が null でない（怒り、不安、遠慮、等）
    チェック: output の最初の3行以内に、感情への応答が含まれているか
    失敗例: plan で「buyer は前回の被害で怒っている」→ output で感情スルー
    対応: 再生成 or フラグ

  # チェック3: 空約束の検出
  empty_promise_detection:
    条件: output に「先にお伝えします」「確認できているところから」等が含まれる
    チェック: その文の直後に、実際に何かを伝えているか
    失敗例: 「確認できているところから先にお伝えします」→ 次の行が「本日〇時までに」（何も伝えていない）
    対応: 該当文を削除 or 再生成

  # チェック4: scope 判断の一致
  scope_judgment_match:
    条件: plan.scope_judgment が設定されている（strong / cautious / out_of_scope）
    チェック: output の scope 表現が plan と一致しているか
    失敗例: plan で「cautious」→ output で「確認できます」（strong のトーン）
    対応: フラグ

  # チェック5: buyer 語彙の保全
  buyer_vocabulary_preserved:
    条件: plan.buyer_keywords が設定されている
    チェック: buyer が使った重要な語彙が output で弱められていないか
    失敗例: buyer「二重請求」→ output「請求が重なる」
    対応: フラグ（phrasing 修正）
```

### 実装の場所

```
既存: response_decision_plan → renderer → japanese-chat-natural-ja → validator → output
追加:                                                                  ↑ ここに追加
                                                              plan_output_integrity_check
```

validator の既存ロジックに、上記5つのチェックを追加する形。

### 期待される効果

```
チェック1 で防げるケース: B4 CASE 5（主質問「直せますか？」への回答漏れ）
チェック2 で防げるケース: B2 CASE 3, 15（buyer 感情の無視）
チェック3 で防げるケース: B2 CASE 2, B4 CASE 7（空約束の再発）
チェック4 で防げるケース: B3 CASE 3（情報十分なのに「合えば」）
チェック5 で防げるケース: B4 CASE 1（buyer 語彙の弱め）
```

### コスト

```
API コスト: 追加なし（validator 内のルールチェックのみ）
実装工数: validator にチェック関数を追加（数時間）
リスク: 低（false positive が出たら閾値を調整するだけ）
破壊的変更: なし（既存の validator に追加するだけ）
```

---

## 4. Claude（レビュー担当）の見解

### 採用すべきと判断する理由

1. **4バッチ60件の監査で、同一パターンの再発が3回確認されている**（空約束: B2→B4、感情無視: B2→B3）
2. **phrasing only では防げない問題**（思考の段階では正しいのに出力で消える）
3. **コストがほぼゼロ**（validator にルール追加するだけ）
4. **研究の裏付けがある**（Unfaithful CoT は LLM の既知の問題で、post-generation validation が推奨されている）
5. **既存の response_decision_plan の投資を活かせる**（plan を作っているのに検証していないのはもったいない）

### 注意点

- チェック1〜3 を最優先で実装することを推奨
- チェック4〜5 は phrasing only でも対応可能なので、優先度は下げてよい
- false positive（正しい output を誤検出）が出た場合は、チェックの閾値を緩めて対応
- この proposal は設計の提案であり、Codex の既存アーキテクチャとの整合は Codex が判断する

---

## 5. 参照ファイル

- 外部調査結果: `/home/hr-hm/Project/work/docs/external-research/reasoning-preservation-research.md`
- 監査結果 B2: batch2 audit artifact
- 監査結果 B3: batch3 audit artifact
- 監査結果 B4: batch4 audit artifact
- service.yaml: `/home/hr-hm/Project/work/ops/services/next-stripe-bugfix/service.yaml`
