# Work Workspace（日本語）

この `work` は、ココナラ受託運用の恒久ワークスペースです。  
英語版は作らず、日本語ドキュメントを正本として運用します。

## 人間が見る場合
まずは [docs/README.ja.md](/home/hr-hm/Project/work/docs/README.ja.md) を見てください。以下は Codex と運用構造の案内が中心です。

## 最初に読む
- `AGENTS.md`（Core OS の共通ルール）
- `docs/next-codex-prompt.txt`（起動正本）
- `os/core/boot.md`（基本設定の起点）
- `docs/README.ja.md`（人間向けドキュメント目次）
- `HANDOFF_NEXT_CODEX.ja.md` は履歴専用で、起動正本には使わない

## よく使う入口
- 出品文: `docs/coconala-listing-final.ja.md`
- 収益化方針: `docs/20260212-coconala-monetization-deepresearch.clean.ja.md`
- 取引フロー/規約メモ: `docs/20260212-coconala-flow-deepresearch.clean.ja.md`
- 文面ルール: `docs/writing-guideline.ja.md`
- コメント規約: `docs/code-comment-style.ja.md`
- 実運用最短ガイド: `Codex実運用ガイド.ja.md`

## 基本設定 / 案件管理 / いまの状態（最短）
1. `./scripts/os-check.sh` を通す
2. `./scripts/internal-os-status.sh` で現在状態を見る
3. 基本設定は `os/core/boot.md` を起点に見る
4. 返信中心なら `os/coconala/boot.md`
5. 実装中心なら `os/implementation/boot.md`
6. 納品前後なら `os/delivery/boot.md`

## 案件運用（最短）
1. 購入確定後に `#S #R` または `#S #A` を使う
2. `#S` の正本は `scripts/case-open.sh`（互換: `scripts/start-case-record.sh`）
3. 作業場所: `ops/cases/open/{case_id}/README.md`
4. 重要判断は `#M` で追記（正本: `scripts/case-note.sh`）
5. 納品準備へ入る時は `scripts/case-phase.sh --phase delivery`
6. クローズ時は `#C` を使う（正本: `scripts/case-close.sh`）
7. 一覧は `ops/case-log.csv`

## 補助ドキュメント
- Claude用運用: `CLAUDE.md`
- 案件運用ルール: `OPERATIONS.md`
- 履歴ログ: `HANDOFF_NEXT_CODEX.ja.md`

## フォルダ構成（要点）
- `AGENTS.md`: 全体ルール（最重要）
- `CLAUDE.md`: Claudeの役割とレビュー手順
- `OPERATIONS.md`: 案件運用ルール
- `TEMPLATES/`: 提案・診断・納品テンプレ
- `docs/`: 出品文、チェックリスト、調査Clean版
- `scripts/`: チェックスクリプトや補助スクリプト
- `os/`: 基本設定
- `runtime/`: いまの状態
- `ops/`: 案件管理
- `ops/cases/`: 案件記録
- `ops/case-log.csv`: 案件一覧

## 案件管理（ops/）配下の意味
- `ops/cases/open/{case_id}/README.md`: 進行中案件の記録本体
- `ops/cases/closed/{case_id}/README.md`: クローズ済み案件の記録本体
- 必要な追加ファイルは、同じ案件フォルダ配下に増やす
- 追加サブフォルダは日本語で統一する
  - `受領物/`
  - `納品物/`
  - `作業メモ/`

## 注意
- 秘密情報（`.env*`、APIキー、生データ）は保存・共有しない
- 共通方針は `cases` 配下に置かない
- 納品物は再現手順付きで残す
