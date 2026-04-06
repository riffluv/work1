# 提案: Platform Contract Layer の追加

> 注記（2026-04-07）:
> この提案の問題意識とレイヤ分離の方向性は採用済み。
> ただし本文中の `全額返金 / 全額支払いの二択`、`正式な納品後は追加料金請求不可` など一部の前提は、
> その後の公式ヘルプ確認で修正されている。現行の正本は
> `/home/hr-hm/Project/work/os/coconala/platform-contract.yaml` を参照。

## 提案者
Claude（品質監査担当）+ #AR 外部調査結果

## 背景

B9 killer batch で平均 4.6 を達成した。構造的な問題はゼロ。
残りの伸びしろは phrasing 微調整と、**ココナラのプラットフォーム仕様を踏まえた返信**。

B9 CASE 10（途中キャンセル + 返金）で Codex は「返金の可否はこの場で断定せず」と
書いたが、これはココナラの仕組み（全額返金 or 全額支払いの二択）を知った上での判断か、
知らないから曖昧にしたのかが分からない。

同様に:
- buyer が「見積もり提案を送ってください」と言った時、その操作の意味が分かるか
- 「正式な納品」と普通のメッセージの違いが分かるか
- 差し戻しが1回のみということを知っているか
- メッセージ機能とトークルームの違いが分かるか

これらは今の service.yaml にも AGENTS.md にも書かれていない。

## 問題

```
今の knowledge 層:
  service.yaml → サービス固有（price / scope / hard_no / capability）
  reply-memory → 案件の文脈（前回の約束 / トーン）

足りないもの:
  ❌ ココナラのプラットフォーム仕様
```

service.yaml に入れると重すぎる（全サービス共通の知識なのに各 yaml に重複）。
AGENTS.md に入れるとスコープが違う（OS ルールではなくプラットフォーム仕様）。
ドキュメントを読ませるだけだと構造的な紐づけがない。

## #AR 調査で見つかったパターン

AgentPatterns.ai の **Layered Context Architecture** パターン:

```
Layer 1: Institutional Knowledge（プラットフォームのルール）
  → 常に参照される。軽い。guidance レベル。
  → Intercom は「knowledge sources」と「guidance」を分離
  → guidance は応答前に必ず適用される

Layer 2: Domain Knowledge（サービス固有）
  → capability map / diagnostic patterns / scope
  → 今の service.yaml がこれ

Layer 3: Contextual Knowledge（その場の文脈）
  → 今の reply-memory がこれ
```

Intercom / Zendesk とも、プラットフォームルールは「常にアクティブな guidance」として
サービス知識とは別レイヤーに置いている。

## 提案

### 1. `ops/services/coconala-platform.yaml` を新設

```yaml
# ココナラプラットフォーム共通ルール
# 全サービスで共通。返信を書く前に必ず参照する。
# 詳細は docs/external-research/coconala-platform-complete-guide.md

platform: coconala

talkroom:
  purchase_response_deadline: "48時間以内に初回連絡。違反で自動キャンセル+星1"
  no_response_cancel: "出品者の最終連絡から4日以上放置+最終送信者がbuyer → キャンセルリクエスト可能"
  message_vs_talkroom: "メッセージ=購入前。トークルーム=購入後。別物"

delivery:
  formal_delivery: "正式な納品を送信 → トークルームクローズ開始"
  buyer_confirmation: "承諾→24h後クローズ / 差し戻し→追加すり合わせ"
  rejection_limit: "差し戻しは1回のみ。2回目の正式な納品で3日後に自動クローズ"
  pre_delivery_check: "正式な納品の前にbuyerに確認すべき"
  no_additional_charge_after: "正式な納品後は追加料金請求不可"

estimate:
  flow: "見積もり相談 → 出品者が見積もり提案（金額・内容・納期）→ buyer承認 → 購入"
  additional_payment: "おひねり or 有料オプションで追加料金を受け取る"

cancel:
  refund: "全額返金 or 全額支払い。一部返金の正式な仕組みはない"
  mutual_cancel: "双方合意のキャンセルなら評価は付かない"
  buyer_initiated: "出品者4日無応答→キャンセルリクエスト→24h無応答→自動キャンセル+星1"

post_close:
  communication: "トークルームクローズ後はメッセージ機能で連絡"
  evaluation: "星評価（総合のみ公開）+ 評価コメント（公開）。入力は任意"

prohibited:
  external_comm: ["Zoom", "LINE", "Skype"]  # ココナラ内ビデオチャットは一部カテゴリで可
  external_links: true
  direct_transaction: true
```

### 2. 配置と参照

```
knowledge 層（完成形）:
  Layer 1: coconala-platform.yaml  ← NEW（30行。常に参照）
  Layer 2: service.yaml            ← 既存（サービス固有）
  Layer 3: reply-memory.json       ← 既存（案件文脈）

参照タイミング:
  Layer 1: 返信を書く前に必ず読む（guidance）
  Layer 2: routing / scope 判断時に読む
  Layer 3: purchased / delivered で memory がある時だけ
```

### 3. 起動時の接続

coconala bootstrap スクリプトで `coconala-platform.yaml` の存在確認を追加。
mode=coconala の時だけ発火。

### 4. validator への接続（任意）

将来的に platform_lint として:
- 「正式な納品の前に buyer に確認したか」
- 「メッセージとトークルームを混同していないか」
- 「キャンセルの返金を断定しすぎていないか」
を見ることも可能。ただし優先度は低い。

## 判断ポイント

Codex に聞きたいこと:

1. この Layer 1 を追加すること自体に同意するか
2. `coconala-platform.yaml` の配置場所は `ops/services/` でよいか
3. 起動時の自動参照の方法はどうするのが自然か
4. 今すぐ入れるか、次回セッションで入れるか
5. 他にもっと良い方法があるか

## 参考資料
- `docs/external-research/coconala-platform-complete-guide.md`（全文ガイド）
- `docs/external-research/coconala-platform-rules-research.md`（ルール調査）
- AgentPatterns.ai: Layered Context Architecture パターン
