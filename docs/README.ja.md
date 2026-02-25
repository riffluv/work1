# docs 目次（人間向け）

このファイルは、人間が「今どの資料を見ればいいか」を迷わないための入口です。

## まず見る（優先順）
1. `docs/coconala-listing-final.ja.md`  
出品ページに反映する本文の正本

2. `docs/20260212-coconala-monetization-deepresearch.clean.ja.md`  
価格・追加料金・KPI・90日運用の方針

3. `docs/first-case-sop-1page.ja.md`  
初案件を受注してから納品までの最短手順

4. `docs/coconala-premium-roadmap.ja.md`  
現行15,000円サービスから上位プレミアムへ派生する実行ロードマップ

5. `docs/service-catalog.ja.md`  
サービスIDと公開状態の台帳（複数サービス運用時の正本）

6. `docs/coconala-guide-market-ops.ja.md`  
ココナラ公式段取り（購入時挨拶 / 滞留時連絡 / 正式納品）を固定した運用メモ

7. `docs/coconala-seller-help-key-links.ja.md`  
サービス出品者向けヘルプの要点（見積り経路・紐付け・受付設定）

8. `docs/coconala-special-case-policy.ja.md`
特例対応の判断基準・文面・記録ルール（価格崩壊防止）

9. `docs/coconala-estimate-ui-cheatsheet.ja.md`  
見積り設定UIの挙動を3行で確認するチートシート

10. `docs/stripe-dashboard-japanese-ui-guide.ja.md`
Stripe案内を日本語UI基準で行うための運用メモ（Checkout/Portal/price_idの切り分け）

## 正本ルール（重要）

- 現行サービス内容の簡易正本は `Next.js_Stripe不具合診断・修正.md`（ルート直下）とする。
- 出品画面に反映する実文面・実価格は `docs/coconala-listing-final.ja.md` を正本とする。
- `deepresearch.clean` 系は調査ログであり、旧案（LIGHT/STANDARD/PREMIUM）を含む場合がある。
- 実運用で矛盾が出た場合は、正本側（listing final）を優先して更新する。
- 複数サービス運用時は `docs/service-catalog.ja.md` の `Service ID` を起点に参照先を固定する。

## 文章運用
- `docs/writing-guideline.ja.md`  
返信文の文体・NG表現・言い換えルール
- `docs/coconala-message-templates-short.ja.md`  
初回返信、納品形式確認、見積り判定、進捗、追加料金、納品の短文テンプレ
- `docs/文章コミュニケーション完全ガイド.md`  
文章運用の詳細版（長文）

## 実装運用
- `docs/code-comment-style.ja.md`  
AI臭を避けるコードコメント規約（確定版）
- `docs/stripe-dashboard-japanese-ui-guide.ja.md`
Stripeダッシュボードを日本語UIで案内するためのチートシート

## 調査ログ（Clean）
- `docs/20260212-coconala-flow-deepresearch.clean.ja.md`  
取引フロー・規約・テンプレ整理
- `docs/20260212-coconala-monetization-deepresearch.clean.ja.md`  
収益化設計の要点整理

## 公開前チェック
- `docs/coconala-listing-checklist.md`  
出品前の確認リスト
- `docs/service-plan.ja.md`  
提供プランの定義

## Skill一覧
- `coconala-reply-bugfix-ja`  
不具合修正サービス専用の返信作成（固定条件・規約・スコープ判定前提）
- `japanese-chat-natural-ja`  
サービス非依存の日本語自然化（重複質問回避・過剰敬語抑制）
- `coconala-reply-ja`（互換・旧テンプレ参照）
旧返信テンプレの参照用
- `scope-judge-ja`  
スコープ判定（同一原因/別原因の分岐）
- `delivery-pack-ja`  
納品物3点セット + 正式納品文の作成
- `coconala-listing-ja`  
出品文の整備

## 返信作成の推奨順
1. `coconala-reply-bugfix-ja` で内容判定と下書き作成
2. `japanese-chat-natural-ja` で最終自然化
