# temperature pairs

- `inbox/`
  - batch 初稿返信の保存先。
  - `python3 scripts/save-coconala-temperature-draft.py ...` で 1 件ずつ置く。
- `complete.jsonl`
  - `draft_reply` と `preferred_reply` の両方がそろった比較ペア。
- `pending-preferred-only.jsonl`
  - preferred rewrite はあるが、draft が未保存のケース。
- `dangling-drafts.jsonl`
  - draft はあるが、preferred rewrite が未接続のケース。

生成コマンド:
- `python3 scripts/build-coconala-temperature-pairs.py --save-report`

現状:
- quality-audit の最小修正版は抽出済み。
- ただし過去 batch の初稿返信は workspace に残っていないため、既存 50 件は `pending-preferred-only` から始まる。
- 次回以降の quality batch から、初稿保存 -> pair join を回す。
