# Work Workspace（日本語）

この `work` は、ココナラ受託運用の恒久ワークスペースです。  
英語版は作らず、日本語ドキュメントを正本として運用します。

## 最初に読む
- `HANDOFF_NEXT_CODEX.ja.md`（最新方針・更新履歴）
- `AGENTS.md`（作業ルール）
- `docs/README.ja.md`（人間向けドキュメント目次）

## よく使う入口
- 出品文: `docs/coconala-listing-final.ja.md`
- 収益化方針: `docs/20260212-coconala-monetization-deepresearch.clean.ja.md`
- 取引フロー/規約メモ: `docs/20260212-coconala-flow-deepresearch.clean.ja.md`
- 文面ルール: `docs/writing-guideline.ja.md`
- コメント規約: `docs/code-comment-style.ja.md`

## 案件運用（最短）
1. 新規案件作成: `./scripts/new-case.sh <case-slug>`
2. 作業場所: `cases/ACTIVE/<case-slug>`
3. 保留移動: `./scripts/move-case.sh <case-slug> HOLD`
4. 完了移動: `./scripts/move-case.sh <case-slug> CLOSED`
5. 案件一覧更新: `CASES_INDEX.md`

## 補助ドキュメント
- Claude用運用: `CLAUDE.md`
- 案件運用ルール: `OPERATIONS.md`

## フォルダ構成（要点）
- `AGENTS.md`: 全体ルール（最重要）
- `CLAUDE.md`: Claudeの役割とレビュー手順
- `OPERATIONS.md`: 案件運用ルール
- `CASES_INDEX.md`: 案件一覧
- `TEMPLATES/`: 提案・診断・納品テンプレ
- `docs/`: 出品文、チェックリスト、調査Clean版
- `scripts/`: 案件作成/移動や補助スクリプト
- `cases/`: 案件本体

## cases 配下の意味
- `cases/ACTIVE/`: 進行中
- `cases/HOLD/`: 保留中
- `cases/CLOSED/`: 完了
- `cases/_case-template/`: 新規案件テンプレ

## 1案件フォルダの中身（例）
- `source/`: 受領ファイル
- `work/`: 作業用ファイル
- `deliverables/`: 納品物
- `logs/`: 案件ログ
- `CASE.md`: 状態・期限・プラン
- `README.md`: 案件メモ

## 注意
- 秘密情報（`.env*`、APIキー、生データ）は保存・共有しない
- 共通方針は `cases` 配下に置かない
- 納品物は再現手順付きで残す
