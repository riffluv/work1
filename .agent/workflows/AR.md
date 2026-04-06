---
description: "#AR — Agent-Reach を使った外部調査"
---

# #AR — Agent-Reach 外部調査ワークフロー

ユーザーが `#AR` と書いたら、Agent-Reach の CLI ツールを使って外部調査を行う。

## 前提ルール（AGENTS.md 準拠）
- 外部調査ツールは、ユーザーが明示した時だけ使う
- 外部調査の結果はそのまま正本へ入れず、要約・選別した調査メモ経由で持ち込む
- OS 本体に常駐させず、外部調査レーンとして切り離して扱う

## 調査手順

1. ユーザーの `#AR` の後ろに書かれたキーワード・URL・調査対象を確認する

2. 対象に応じて適切なツールを選ぶ（ルーティング表）：

| 対象 | コマンド |
|---|---|
| ウェブ検索 | `mcporter call 'exa.web_search_exa(query: "...", numResults: 5)'` |
| 任意の URL | `curl -s "https://r.jina.ai/URL"` |
| GitHub リポジトリ | `gh repo view owner/repo` |
| GitHub 検索 | `gh search repos "query" --sort stars --limit 10` |
| Twitter 検索 | `twitter search "query" --limit 10` |
| Reddit 検索 | `rdt search "query" --limit 10` |
| Reddit 読み込み | `rdt read POST_ID` |
| YouTube 字幕 | `yt-dlp --write-sub --skip-download -o "/tmp/%(id)s" "URL"` |

3. コマンドを実行する
// turbo

4. 結果を要約して、以下の形式でユーザーに報告する：
```
#AR 調査結果
────────────
対象: [調査対象]
ソース: [URL / プラットフォーム名]
────────────
要点:
- ...
- ...
────────────
raw は /tmp/ に保存済み（必要なら見せます）
```

5. 調査結果を正本に入れる場合は、ユーザーの明示的な許可を得てから行う

## 注意事項
- 一時ファイルは `/tmp/` に保存する（ワークスペース内に作らない）
- 調査結果をそのまま AGENTS.md や正本ファイルに反映しない
- 要約・選別した調査メモとして扱う
- 複数プラットフォームをまたぐ場合は、プラットフォームごとに結果を分けて報告する
