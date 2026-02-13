# HANDOFF_NEXT_CODEX.ja.md

最終更新: 2026-02-13

## 目的

このファイルは、`/home/hr-hm/Project/work` で新しく起動したCodexに、
現在の方針と運用状態を引き継ぐための恒久メモです。

セッションが切れても、このファイルを最初に読ませれば継続できます。

## 現在の最優先ミッション

1. ココナラ受託（Next.js / Stripe / API連携の不具合修正）を安定運用する
2. スコープ暴走を防ぎつつ、初案件を確実に完了させる
3. テキストのみで高品質納品できる運用を維持する

## 固定方針（変更しない前提）

- 連絡: テキストのみ（通話なし）
- 標準範囲外: 直接push / 本番デプロイ / 新機能開発
- 入口訴求: Next.js + Stripe + API連携（広め）
- 強み訴求: Stripe Webhook（署名検証・不達・重複処理）

### 価格・提供モデル（確定）

1. 基本料金: 15,000円（不具合1件の切り分け〜修正差分/適用手順）
2. 有料オプション: 追加修正1件 15,000円
3. 有料オプション: 追加調査30分 5,000円

## 参照ルート

- 仕事ワークスペース: `/home/hr-hm/Project/work`
- 実績参照（ゲーム）: `/home/hr-hm/Project/jomonsho`
- 実績参照（Stripeキット）: `/home/hr-hm/Project/stripe`

## work配下の重要ファイル

- `AGENTS.md`
- `CLAUDE.md`
- `OPERATIONS.md`
- `README.md`
- `Next.js_Stripe不具合診断・修正.md`（現行サービス内容の正本）
- `docs/service-plan.ja.md`
- `docs/coconala-listing-checklist.md`
- `docs/README.ja.md`
- `TEMPLATES/*.md`
- `scripts/new-case.sh`
- `scripts/move-case.sh`

## 新しいCodexに最初に依頼する内容（コピペ可）

1. `AGENTS.md` と `docs/service-plan.ja.md` を先に読み、矛盾がないか確認
2. ココナラ出品文（タイトル/本文/FAQ/注意事項）を最終版にする
3. 初案件の受注〜納品手順を1ページで整理する
4. 提案文・ヒアリング文・納品文をテンプレから実運用版へ仕上げる

## 更新ルール（大事）

- セッションが終わる前に、このファイルの「更新履歴」に必ず追記する
- 追記するのは以下の3点だけ
  1. 何を決めたか
  2. 何を変更したか（ファイルパス）
  3. 次回の最優先タスク

## 更新履歴

### 2026-02-11
- `work` を恒久運用の案件ワークスペースとして整備
- テンプレを日本語化
- プラン価格を 15,000 / 30,000 / 60,000 で確定
- 履歴置き場を `cases/CLOSED` に統一（`archive` 廃止）

### 2026-02-11（追記）
- 何を決めたか: `AGENTS.md` と `docs/service-plan.ja.md` の方針は整合しており、初回作業は「出品文最終化・1ページ運用手順化・主要テンプレ実運用化」を採用
- 何を変更したか（ファイルパス）: `docs/coconala-listing-final.ja.md`, `docs/first-case-sop-1page.ja.md`, `TEMPLATES/proposal.md`, `TEMPLATES/intake.md`, `TEMPLATES/delivery.md`
- 次回の最優先タスク: 出品画面へ文面を反映し、公開前チェック（チェックリスト照合）を実施する

### 2026-02-12（追記）
- 何を決めたか: コードコメントは「AI臭を排除した自然な実務文」をデフォルト運用にする（毎回の個別指示不要）。
- 何を変更したか（ファイルパス）: `docs/code-comment-style.ja.md`, `AGENTS.md`, `CLAUDE.md`
- 次回の最優先タスク: 実案件で新規コメント追加時に同ルールを運用し、必要なら規約を微調整する

### 2026-02-12（追記2）
- 何を決めたか: `codecomment調査.md` を反映し、コメント規約を確定版へ更新。運用は「Codex実装→Claudeレビュー→Codex最終決定」に固定。
- 何を変更したか（ファイルパス）: `docs/code-comment-style.ja.md`, `CLAUDE.md`, `AGENTS.md`
- 次回の最優先タスク: 実案件でレビュー手順を実運用し、禁止語リストやテンプレを必要最小限で調整する

### 2026-02-12（追記3）
- 何を決めたか: 収益化調査の元レポートは内部引用トークンが多いため、運用用は `docs` 側の clean 版を正本として扱う。
- 何を変更したか（ファイルパス）: `docs/20260212-coconala-monetization-deepresearch.clean.ja.md`
- 次回の最優先タスク: 出品文とFAQに、clean版の「成果物定義」「追加料金判定」「KPI週次運用」を反映する

### 2026-02-12（追記4）
- 何を決めたか: 英語READMEは廃止し、日本語ドキュメントを正本として一本化する。人間向けの docs 目次を新設する。
- 何を変更したか（ファイルパス）: `README.md`, `docs/README.ja.md`
- 次回の最優先タスク: `docs/README.ja.md` を入口に、出品準備の実作業（反映・チェック）を進める

### 2026-02-12（追記5）
- 何を決めたか: `WORKSPACE_MAP.ja.md` の内容を `README.md` に統合し、重複ドキュメントを削減する。
- 何を変更したか（ファイルパス）: `README.md`, `HANDOFF_NEXT_CODEX.ja.md`, `WORKSPACE_MAP.ja.md`（削除）
- 次回の最優先タスク: `README.md` と `docs/README.ja.md` を入口として、ドキュメント運用を一本化する

### 2026-02-12（追記6）
- 何を決めたか: `AGENTS.md` は英語混在をやめ、全項目を日本語で運用する。
- 何を変更したか（ファイルパス）: `AGENTS.md`
- 次回の最優先タスク: 他の運用ドキュメントで英語混在が残る箇所を必要に応じて日本語へ統一する

### 2026-02-12（追記7）
- 何を決めたか: `CLAUDE.md` の英語混在（後半の運用セクション）をやめ、全体を日本語へ統一する。
- 何を変更したか（ファイルパス）: `CLAUDE.md`
- 次回の最優先タスク: 運用ドキュメントの文言統一を維持し、必要な更新は `docs/README.ja.md` から辿れる形で管理する

### 2026-02-12（追記8）
- 何を決めたか: 出品モデルを「3プラン（LIGHT/STANDARD/PREMIUM）」から「基本15,000円 + 有料オプション（追加修正1件/追加調査30分）」へ統一する。
- 何を変更したか（ファイルパス）: `docs/coconala-listing-final.ja.md`, `docs/service-plan.ja.md`, `docs/coconala-listing-checklist.md`, `docs/first-case-sop-1page.ja.md`, `HANDOFF_NEXT_CODEX.ja.md`
- 次回の最優先タスク: ココナラ出品画面の実入力値と `docs/coconala-listing-final.ja.md` の一致確認を行い、差分があれば正本側を更新する

### 2026-02-13（追記9）
- 何を決めたか: サービス内容の現行正本を「基本15,000円で不具合1件対応 + 最終確認は依頼者環境（結果ログで追加調整）」として確定した。
- 何を変更したか（ファイルパス）: `Next.js_Stripe不具合診断・修正.md`, `docs/coconala-listing-final.ja.md`, `HANDOFF_NEXT_CODEX.ja.md`, `docs/README.ja.md`, `docs/service-plan.ja.md`, `AGENTS.md`, `CLAUDE.md`
- 次回の最優先タスク: 依頼相談への初回返信時に、現行正本の定義（不具合1件の範囲・最終確認フロー）で回答を統一する
