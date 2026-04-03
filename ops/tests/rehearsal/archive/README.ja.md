# リハーサル Archive

## 役割
- raw の `batch-*.txt` を plain text のまま active 側へ置かないための退避場所
- 監査や回帰確認で「当時の試作文を見返したい」ときだけ手動で展開して参照する

## 運用ルール
- `ops/tests/rehearsal/` には curated な監査メモと回帰確認メモだけを残す
- raw batch を長期保存したい場合は、このディレクトリへ `tar.gz` で退避する
- archive は履歴であり、skill / prompt / docs の実行時参照元にしない

## 現在の archive
- `raw-batches-2026-04-03.tar.gz`
  - 2026-04-03 時点で `ops/tests/rehearsal/` に残っていた plain text の `batch-*.txt` 一式

## 確認方法
- 中身一覧だけ見たいとき:
  - `tar -tzf /home/hr-hm/Project/work/ops/tests/rehearsal/archive/raw-batches-2026-04-03.tar.gz`
- 展開して確認したいとき:
  - 作業用の一時ディレクトリへ手動で展開し、確認後は再度 plain text を常置しない
