# Scope Snapshot

- 対象サービス: bugfix-15000
- 依頼経路: public サービスから直接購入
- 現在状態: delivery rehearsal
- 題材コード: `nextjs/saas-starter`
- 今回の不具合1件の定義: 決済成功後に `/dashboard` の `Current Plan` が `Free` のまま残る 1 フロー 1 件
- 現時点の原因判定: `customer.subscription.created` を Webhook 側で拾っておらず、`/api/stripe/checkout` の到達に初回反映を依存していた
- 対象フロー: Checkout 成功から会員状態更新、`/dashboard` 表示反映まで
- 対象エンドポイント: `app/api/stripe/webhook/route.ts`
- 基本料金内で対応する範囲: 原因特定、修正済みファイル作成、確認手順整理
- 追加対応に切り替わる条件: 別原因の決済失敗、Billing Portal 側の不具合、別フローの表示不整合
- 依頼者側の最終確認: テスト購読を1件実行し、`/dashboard` の `Current Plan` と `subscriptionStatus` が更新されるか確認
