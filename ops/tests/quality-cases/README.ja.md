# quality-cases

目的:
- 質感監査専用の少数ケースを置く。
- `stock` のような大量回帰用ではなく、botっぽさ、距離感、負担感、進捗不安、押し売り感を詰めるためのケースを管理する。

使い分け:
- `inbox/`
  - Claude / Gemini / 実案件から新しく作った質感監査候補を置く。
- `active/`
  - いま監査・比較・改善に使っているケースを置く。
- `reviewed/`
  - 監査が一巡し、参照用に残すケースを置く。

運用メモ:
- ここは `stock` とは分けて扱う。
- `stock` は `contract / renderer / lint / regression` の改善用。
- `quality-cases` は、少数精鋭で日本語の質感を磨く用。
- 基本は plain text で、`case_id / raw_message / note` 程度の軽い形式でよい。
- batch を回すときは、外部監査へ出す前の初稿返信も保存する。
  - 保存先: `/home/hr-hm/Project/work/ops/tests/temperature-assets/pairs/inbox/`
  - 例: `python3 scripts/save-coconala-temperature-draft.py --case-id QLT-051 --draft-file <path> --source-file <path> --refresh-assets`
  - 直前に `runtime/replies/latest.txt` と `latest-source.txt` に保存済みなら `python3 scripts/save-coconala-temperature-draft.py --case-id QLT-051 --from-runtime --refresh-assets` でよい
- 監査後の preferred rewrite は `temperature-assets/preferred/quality-audit-preferred.jsonl` に抽出されるので、次回以降は `draft_reply / preferred_reply` の pair を自動で作れる。
  - 手動で追記する時は `python3 scripts/save-coconala-temperature-preferred.py --case-id QLT-051 --preferred-file <path> --report-path <path> --send-ok yes --refresh-assets`
  - report から自動で取り込む時は `python3 scripts/import-coconala-temperature-preferred-report.py --report <resolved_report_path> --case-id QLT-051 --refresh-assets`
  - `--refresh-assets` を付けると `pairs` と reranker 用 `train / holdout` まで更新される。
