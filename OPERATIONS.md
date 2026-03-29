# OPERATIONS.md

## 目的
このワークスペースを、すべてのクライアント案件で継続利用する。
案件ごとに新しいワークスペースは作らない。

## 基本ルール
- 共有の運用ドキュメントはワークスペース直下に置く。
- 案件固有の成果物は、各 case フォルダ内にのみ置く。

## フォルダ方針
- ルート (`/work`): 運用ルール、テンプレート、スクリプト、共通参照資料
- `ops/cases/open/{case_id}/`: 進行中案件
- `ops/cases/closed/{case_id}/`: 完了案件
- 一覧は `ops/case-log.csv`

表示ラベルの考え方:
- `os/` は `基本設定`
- `ops/` は `案件管理`
- `runtime/` は `いまの状態`

## case フォルダに入れるもの
- ヒアリングメモ
- 依頼者から受領したソースファイル
- 作業中のパッチファイル
- 納品物
- 案件固有ログ
- 必要なら `受領物/` `納品物/` `作業メモ/` を作って整理する

## case フォルダに入れないもの
- 全体向けエージェント指示
- 全体向けテンプレート
- 全サービス共通の長期戦略ドキュメント
- 再利用スクリプト

## 命名規則
- `YYYYMMDD-連番-経路` を使う
- 例: `20260328-01-service`
- `#S` の正本は `scripts/case-open.sh`
- phase 切替の正本は `scripts/case-phase.sh`
- 互換のため `scripts/start-case-record.sh` も残すが、内部では `case-open.sh` へ委譲する

## ライフサイクル
1. `#S` で `ops/cases/open/{case_id}/README.md` を開始
2. `runtime/active-case.txt` と `runtime/mode.txt` を更新する
3. 作業して `#M` で判断を追記（正本: `scripts/case-note.sh`）
4. 納品準備へ入る時は `scripts/case-phase.sh --phase delivery`
5. 納品してクローズ時に `#C`（正本: `scripts/case-close.sh`）
6. `#C` で `ops/cases/closed/{case_id}/` へ移動し、`case-log.csv` を更新

## 推奨サブフォルダ名
- `受領物/`: 相手から受け取った ZIP・コード・資料
- `納品物/`: 相手に渡す md / zip / patch
- `作業メモ/`: スクショ、ログ抜粋、自分用の補足
- いずれも必要になった時だけ手動で作る

## AI コンテキスト方針
- 毎回この同じ `/work` ワークスペースを開く。
- AGENTS/CLAUDE をルートに置き、新規タスクでも運用基準を継承する。
- 案件ごとの README に事実を集約し、同じ説明の繰り返しを減らす。
