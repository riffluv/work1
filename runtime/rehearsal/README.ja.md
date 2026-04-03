# リハーサル一時置き場

## 役割
- raw の `batch-*.txt` を一時的に置く場所
- `ops/tests/rehearsal/` を curated なメモ専用に保つため、作業中の plain text はここへ出す

## ルール
- ここは一時領域。raw batch を長期保存しない
- 監査や差分確認が終わったら削除する
- 長期保存したい場合だけ、`ops/tests/rehearsal/archive/*.tar.gz` に圧縮退避する
- skill / docs の正本参照先として扱わない
