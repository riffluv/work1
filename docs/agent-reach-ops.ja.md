# Agent-Reach 運用メモ

この文書は、`Agent-Reach` を **外部調査レーン専用** で使うための最小メモです。

## 位置づけ
- `Agent-Reach` は OS 本体ではない
- 返信文、実装判断、納品物作成の主文脈に常駐させない
- 必要な時だけ外部情報を取りに行く補助ツールとして使う

## 使う時
- ユーザーが `Agent-Reachを使って` と明示した時
- 外部リポジトリ、GitHub Issue、Reddit、YouTube、Web 検索などの横断調査が必要な時
- 技術調査、競合調査、需要の言い回し収集などで、外部証跡が欲しい時

## 使わない時
- 通常の返信文作成
- 実案件のコード分析・修正そのもの
- 納品物本文の作成
- `internal-quality-samples` の編集判断そのもの

## 運用ルール
- 取得情報をそのまま正本へ入れない
- 一度、短い調査メモへ落としてから扱う
- 採否判断と正本反映は常に Codex が行う
- 外部の感想や論評より、ログ・コード・再現手順などの一次証跡を優先する

## 現在の導入状態
- `agent-reach` コマンドは user space に導入済み
- 状態確認: `./scripts/agent-reach-status.sh`
- 直接確認: `agent-reach doctor`

## 今すぐ使える主なチャネル
- Web ページ
- 全網語義検索
- YouTube
- Reddit
- RSS
- V2EX
- WeChat 記事検索
- Bilibili 基本検索
- GitHub 公開情報

## 追加設定が必要なもの
- GitHub の完全機能: `gh auth login`
- X / 小紅書 / 微博 / LinkedIn / 抖音 / 雪球 / 小宇宙: Cookie や追加設定が必要

## Codex への依頼例
- `Agent-Reachを使って、Next.js/Stripe の類似不具合を Reddit と GitHub で調べて`
- `Agent-Reachを使って、handoff-25000 に近い悩み表現を X と Reddit から集めて`
- `Agent-Reachを使って、この公開リポジトリの README / Issue / 構成を整理して`
