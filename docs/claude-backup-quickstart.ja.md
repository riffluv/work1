# バックアップ起動クイックスタート

目的:
- Codex が一時的に使えない時でも、Claude / Gemini / ChatGPT で Internal OS を崩さず継続運用する
- 読む資料を最小限に絞り、実装時に返信ノイズを混ぜない

## 最初に読む最小セット
1. `/home/hr-hm/Project/work/docs/next-codex-prompt.txt`
2. `/home/hr-hm/Project/work/AGENTS.md`
3. `/home/hr-hm/Project/work/os/core/boot.md`
4. `/home/hr-hm/Project/work/os/core/policy.yaml`
5. `/home/hr-hm/Project/work/os/core/service-registry.yaml`
6. `/home/hr-hm/Project/work/docs/code-comment-style.ja.md`

mode ごとに追加で読むもの:
- `coconala`: `/home/hr-hm/Project/work/os/coconala/boot.md`
- `implementation`: `/home/hr-hm/Project/work/os/implementation/boot.md`
- `delivery`: `/home/hr-hm/Project/work/os/delivery/boot.md`

## ローカルパスが読めない環境
- 上のファイルを貼り付けるか、アップロードして読ませる
- `HANDOFF_NEXT_CODEX.ja.md` は履歴専用なので、起動の代替には使わない

## 起動時の一言
以下をそのまま使う:

```text
/home/hr-hm/Project/work/docs/claude-backup-quickstart.ja.md を読んで、Internal OS に従って運用開始してください
```

## 最初の返答
- `読み込み完了`
- `運用要約（短く）`

## mode ごとの考え方
### coconala
- 見積り相談、購入前後の返信、公開中サービス案内
- 送信用返信を作った時は `runtime/replies/latest.txt` に保存する
- 外向け live は `bugfix-15000` のみ

### implementation
- 主文脈は `case README + コード + ログ`
- 返信 docs を常駐させない
- active case が無ければ case を開始する

### delivery
- 納品物と正式納品文だけに集中する
- 新しい実装判断を増やさない
- クローズ前後の整理に使う

## タグ運用
- `#R`: 送信用返信文
- `#A`: 分析のみ
- `#D`: 下書き
- `#P`: 購入後の途中報告
- `#CL`: 直近の相手文と送信用返信文を対象に、Claude向け監査プロンプトを作る
- `#GE`: 直近の相手文と送信用返信文を対象に、Gemini向け監査プロンプトを作る
- `#S`: 購入後の案件記録開始
- `#M`: 重要判断の保存
- `#C`: クローズ保存

## 絶対に崩さない境界
- 外部連絡、外部共有、外部決済へ誘導しない
- 通話しない
- 直接 push しない
- 本番デプロイしない
- 生の秘密情報を受け取らない

## 困った時の優先順位
1. `AGENTS.md`
2. `os/core/boot.md`
3. 現在の mode の boot
4. `ops/cases/open/{case_id}/README.md`
5. `/home/hr-hm/Project/work/stripe日本語UI案内`

## 注意
- 返信ルールを実装 mode に持ち込まない
- `handoff-25000` は未公開の間、外向け返信に使わない
- 迷ったら `#A` で分析に止める
