# docs 目次（人間向け）

このファイルは、人間が「今どの資料を見ればいいか」を迷わないための入口です。

## 一次ソース（最優先）
1. `/home/hr-hm/Project/work/サービスページ/bugfix-15000.live.txt`
サービス商品ページの実体正本（本番反映ベース）

2. `/home/hr-hm/Project/work/現在のプロフィール`
プロフィールの実体正本（本番反映ベース）

## まず見る（優先順）
1. `docs/coconala-listing-final.ja.md`  
出品ページ文面の同期ミラー（一次ソースから同期する）
補足: 2026-03-12 時点で、サービス本文・プロフィール・購入にあたってのお願い・Q&A・トークルーム回答例まで文章調整済み

2. `docs/20260212-coconala-monetization-deepresearch.clean.ja.md`  
価格・追加料金・KPI・90日運用の方針

3. `docs/coconala-win-strategy.ja.md`
今の主力サービスで、最初の高評価コメントを取りにいくための勝ち筋メモ

4. `docs/first-case-sop-1page.ja.md`  
初案件を受注してから納品までの最短手順

5. `docs/coconala-premium-roadmap.ja.md`  
現行15,000円サービスから上位プレミアムへ派生する実行ロードマップ

6. `docs/service-catalog.ja.md`  
サービスIDと公開状態の台帳（複数サービス運用時の正本）

7. `docs/coconala-guide-market-ops.ja.md`  
ココナラ公式段取り（購入時挨拶 / 滞留時連絡 / 正式納品）を固定した運用メモ

8. `docs/coconala-seller-help-key-links.ja.md`  
サービス出品者向けヘルプの要点（見積り経路・紐付け・受付設定）

9. `docs/coconala-special-case-policy.ja.md`
特例対応の判断基準・文面・記録ルール（価格崩壊防止）

10. `ops/common/coconala-rule-guard.md`
返信・提案・納品の前に読む共通ガード（規約事故・外部共有・秘密情報・正式納品の境界）

11. `ops/services/next-stripe-bugfix/service.yaml`
主力サービスの固定条件・証跡回収・人手判断条件をまとめた設定ファイル

12. `docs/coconala-estimate-ui-cheatsheet.ja.md`  
見積り設定UIの挙動を3行で確認するチートシート

13. `/home/hr-hm/Project/work/stripe日本語UI案内`
Stripeでお客さんに確認してもらう項目と導線の運用版（返信文作成時の最優先参照先）

14. `docs/stripe-dashboard-japanese-ui-guide.ja.md`
Stripe案内を日本語UI基準で行うための運用メモ（Checkout/Portal/price_idの切り分け）

## 正本ルール（重要）

- サービス商品ページの実体正本は `/home/hr-hm/Project/work/サービスページ/bugfix-15000.live.txt` とする。
- プロフィールの実体正本は `/home/hr-hm/Project/work/現在のプロフィール` とする。
- `docs/coconala-listing-final.ja.md` は同期ミラー。直接編集より、一次ソース更新後の同期を優先する。
- `Next.js_Stripe不具合診断・修正.md` は参考要約（一次ソースではない）。
- `deepresearch.clean` 系は調査ログであり、旧案（LIGHT/STANDARD/PREMIUM）を含む場合がある。
- 実運用で矛盾が出た場合は、一次ソース（サービス正本 + プロフィール正本）を優先する。
- 複数サービス運用時は `docs/service-catalog.ja.md` の `Service ID` を起点に参照先を固定する。

## 同期手順（固定）
1. 先に一次ソース（サービス正本 + プロフィール正本）を更新する
2. `./scripts/check-coconala-listing-sync.sh` で同期/文字数を確認する
3. 必要な `docs` 側へ同期反映する

## 文章運用
- `docs/writing-guideline.ja.md`  
返信文の文体・NG表現・言い換えルール
- 補足: 2026-03-12 に「相手の言葉を拾ってから質問する」「抽象安心語より具体的な安心表現を使う」を追記済み
- `docs/coconala-message-templates-short.ja.md`  
初回返信、納品形式確認、見積り判定、進捗、追加料金、納品の短文テンプレ
- `docs/文章コミュニケーション完全ガイド.md`  
文章運用の詳細版（長文）

## 実装運用
- `docs/code-comment-style.ja.md`  
AI臭を避けるコードコメント規約（確定版）
- `docs/stripe-dashboard-japanese-ui-guide.ja.md`
Stripeダッシュボードを日本語UIで案内するためのチートシート

## 入口OS
- `ops/common/interaction-states.yaml`
経路 × 状態ごとの allowed / forbidden action
- `ops/common/risk-gates.yaml`
規約・秘密情報・push/prod・正式納品前の停止条件
- `ops/common/output-schema.yaml`
入口判定の返却項目
- `ops/common/routing-table.yaml`
主力サービスへの適合と次アクション
- `ops/common/model-escalation.md`
Codex / Claude / Gemini / ChatGPT Pro の使い分け
- `ops/common/scope-snapshot-template.md`
見積り時と納品時の範囲固定テンプレ
- `ops/services/next-stripe-bugfix/evidence-minimum.yaml`
最小3点、必須5点、Stripe条件付き質問
- `ops/services/next-stripe-bugfix/scope-matrix.md`
same / different / undecidable の具体例
- `ops/review-checkpoints.md`
人手で止めるべき判断ポイント
- `ops/case-log.csv`
実案件の誤判定・離脱・追加見積りの記録
- `ops/future-service-candidates.csv`
プロフィール経由の反復需要メモ
- `ops/macro-15.md`
ココナラ定型文15枠の推奨配分

## 調査ログ（Clean）
- `docs/20260212-coconala-flow-deepresearch.clean.ja.md`  
取引フロー・規約・テンプレ整理
- `docs/20260212-coconala-monetization-deepresearch.clean.ja.md`  
収益化設計の要点整理

## 公開前チェック
- `docs/coconala-launch-prep.ja.md`
公開当日の入力値・設定値・48時間運用を1ページで確認するための実行用キット
- `docs/coconala-listing-checklist.md`  
出品前の確認リスト
- `docs/service-plan.ja.md`  
提供プランの定義

## Skill一覧
- `coconala-intake-router-ja`
相手文を、経路・状態・サービス適合・リスク・不足情報・次アクションへ構造化する入口判定
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
  - 納品レポートでは `今回の対応に含まれない部分` を毎回独立見出しにしない。誤解されやすい場合のみ、`今回の修正が関係する部分` の中で短く補足する。
- `coconala-listing-ja`  
出品文の整備

## 返信作成の推奨順
1. `coconala-intake-router-ja` で入口判定
2. 必要なら `scope-judge-ja` で same / different / undecidable を補強
3. `coconala-reply-bugfix-ja` で下書き作成
4. `japanese-chat-natural-ja` で最終自然化

補足:
- 入口判定で `service_mismatch_but_feasible` が出た場合は、「サービス説明とは少しズレるが技術的には現実的」の意味。
- この場合は自動で断らず、人手で「実績目的で拾うか」「価格が見合うか」を判断する。
