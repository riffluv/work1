# バックアップ起動クイックスタート

目的:
- Codex が一時的に使えない時でも、Claude / Gemini / ChatGPT でココナラ受託運用を継続する
- 読むファイルを最小限に絞り、起動時間を短くする

## まず読むファイル（最小セット）
1. `/home/hr-hm/Project/work/次セッション用_起動プロンプト.txt`
2. `/home/hr-hm/Project/work/AGENTS.md`
3. `/home/hr-hm/Project/work/サービスページ/bugfix-15000.live.txt`
4. `/home/hr-hm/Project/work/現在のプロフィール`
5. `/home/hr-hm/Project/work/ops/common/coconala-rule-guard.md`
6. `/home/hr-hm/Project/work/ops/services/next-stripe-bugfix/estimate-decision.yaml`
7. `/home/hr-hm/Project/work/docs/coconala-message-templates-short.ja.md`
8. `/home/hr-hm/Project/work/docs/coconala-japanese-banlist.ja.md`
9. `/home/hr-hm/Project/work/docs/coconala-japanese-must-rules.ja.md`
10. `/home/hr-hm/Project/work/docs/coconala-golden-replies.ja.md`
11. `/home/hr-hm/Project/work/docs/coconala-reply-self-check.ja.md`

ローカルパスが読めない環境では:
- 上のファイルを貼り付けるか、アップロードして読ませる

## 起動時の一言
以下をそのまま使う:

```text
/home/hr-hm/Project/work/docs/claude-backup-quickstart.ja.md を読んで運用開始してください
```

ローカルパスが読めない環境では:

```text
以下のバックアップ起動資料を読んで運用開始してください
```

の後に、このファイルと最小セットを渡す。

## まず返すこと
- 最初の返答は `読み込み完了` と `運用要約（短く）` のみ

## 代替運用の基本順

### 見積り前
1. 入口判定
   - 経路
   - 状態
   - サービス適合
   - 感情注意の有無
2. 4分岐
   - `15,000円`
   - `5,000円`
   - `保留`
   - `断る`
3. 返信文作成
4. Ban / Must / Golden / Self-Check で最終確認

### 購入後
1. 必須5点確認
   - 期待挙動
   - 実際の挙動
   - 再現手順
   - エラーログ
   - 技術スタック / ランタイム / デプロイ先
2. スコープ確認
   - 同一原因か
   - 別原因か
3. 返信文作成
4. 必要なら `#S / #M / #C` に従って案件記録

## タグ運用
- `#A`: 分析のみ
- `#R`: 送信用返信文
- `#D`: 下書き
- `#S`: 購入確定後の案件記録開始
- `#M`: 重要判断の中間保存
- `#C`: クローズ保存
- `#$0` 〜 `#$3`: 購入後 / 見積り提案の定型運用
- 案件メモの保存先:
  - open: `/home/hr-hm/Project/work/ops/cases/open/`
  - closed: `/home/hr-hm/Project/work/ops/cases/closed/`
  - CSV: `/home/hr-hm/Project/work/ops/case-log.csv`
- 送信順: `#$1` を送る -> 提案ボタンを押す -> `#$2` を送る（同時送信しない）

## 価格の固定条件
- 基本料金: `15,000円`
- 追加修正1件: `15,000円`
- 追加調査30分: `5,000円`

意味:
- `15,000円` = 同一原因の不具合1件を切り分けから修正まで
- `5,000円` = 確認だけ / 方向性整理 / 小さい追加調査

## 絶対に崩さない境界
- 通話しない
- 直接 push しない
- 本番デプロイしない
- 生の秘密情報を受け取らない
- 外部連絡へ誘導しない
- 外部共有へ誘導しない
- 外部決済へ誘導しない

## 返信文の最低品質
- 相手の質問には結論から答える
- 相手がすでに書いたことを聞き直さない
- 初回見積りでは見立て1文を入れる
- 質問は 1〜2 点を優先
- 時刻目安を入れる
- 感情注意では `ご不便をおかけしています` を優先
- 送信前に `coconala-reply-self-check.ja.md` を通す
- 感情注意の検知:
  - 即フラグ: `直っていない` / `お金を払ったのに` / `返金` / `納得できない`
  - 文脈判定: `また` + `前回` / `まだ` + `直らない` / `困る` + `してほしい`
  - 迷ったら感情注意寄りに倒す

## 特に避ける表現
- `整理してお返しします`
- `もっともです`
- `ように見えた`
- `形になります`
- `切り分けて考える`
- `確認案件`
- `別件として整理する`
- `スコープを切って`
- `返金` と `承知しました` の近接
- `安全です / 自然です / 合っています / 分かりやすいです`

## 困った時の優先順位
1. `AGENTS.md`
2. `サービスページ/bugfix-15000.live.txt`
3. `現在のプロフィール`
4. `coconala-rule-guard.md`
5. `estimate-decision.yaml`
6. `coconala-message-templates-short.ja.md`
7. Ban / Must / Golden / Self-Check

## バックアップ運用で再現しにくいこと
- Codex の skill 自動チェーン
- 同一セッションの長い文脈保持
- ローカルスクリプト前提の起動確認

対処:
- ファイルを順に手動適用する
- 長い案件は `#M` で要点を残す
- 迷ったら `#A` で分析に止める

## Claude / Gemini / ChatGPT を呼ぶべき場面
- 新しいケースパターンが出た時
- 5件以上の返信文をまとめて作る時
- `苦情 + 返金 + closed` が重なる複合ケース

## 最後に
- このファイルは「起動短縮用」
- 詳細ルールは最小セット側を正本とする
