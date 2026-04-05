# reranker

目的:
- `pairs/complete.jsonl` から、pairwise 比較にそのまま使える `train / holdout` を切り出す。
- まずは `candidate_a = draft_reply`, `candidate_b = preferred_reply`, `preferred = b` の単純形式で保存する。

生成元:
- `/home/hr-hm/Project/work/ops/tests/temperature-assets/pairs/complete.jsonl`

生成コマンド:
- `python3 scripts/export-coconala-temperature-reranker-set.py --save-report`

出力:
- `train.jsonl`
- `holdout.jsonl`

メモ:
- まだ `complete.jsonl` が空なら、ここも空のままになる。
- 次回以降の quality batch で draft と preferred が両方揃えば、自動で比較資産が増える。
- 典型手順は `save-coconala-temperature-draft.py --from-runtime --refresh-assets` → `import-coconala-temperature-preferred-report.py --report <resolved_report_path> --case-id <ID> --refresh-assets`
