# temperature-assets

目的:
- `ops/tests` の原本を動かさずに、温度感改善用の派生資産をまとめる。
- `stress / boundary / negative_feedback` の bucket を固定し、今後の温度回帰確認に使う。
- quality-audit で得た「好ましい返信」を、再利用しやすい形で残す。

置き方:
- `inventory.jsonl`
  - active source 全体を横断した温度 asset の総索引。
  - `signals` と `buckets` を case 単位で持つ。
- `sources.yaml`
  - どの source を読んで asset を生成したかの一覧。
- `stress-candidates.yaml`
  - stress 系候補。
- `boundary-candidates.yaml`
  - boundary 系候補。
- `negative_feedback-candidates.yaml`
  - negative feedback 系候補。
- `preferred/quality-audit-preferred.jsonl`
  - 50件質感監査から抽出した「最小修正版」の保存先。
- `pairs/`
  - 今後の pairwise / reranker 用置き場。
- `reranker/`
  - `complete.jsonl` から切り出した pairwise 学習用の `train / holdout` 置き場。

運用ルール:
- ここは派生資産置き場であり、`ops/tests` の原本や `eval-sources.yaml` を置き換えない。
- 原本の移動や改名はしない。必要な分類だけをここへ生成する。
- holdout は元の `ops/tests` と切り離さず、温度確認用 bucket はここで別管理する。
- quality-audit 由来の preferred rewrite は置けるが、full pair は初稿返信の保存がないと作れない。

P5 でやること:
1. `inventory.jsonl` から bucket 別に候補を確認する
2. `preferred/quality-audit-preferred.jsonl` で「どの場面でどの言い換えが好まれたか」を参照する
3. 将来の batch では、初稿返信も保存して `pairs/` に `draft_reply / preferred_reply` の比較ペアを置く
4. `pairs/complete.jsonl` が溜まったら `reranker/` に学習用 export を切る

生成コマンド:
- `python3 scripts/build-coconala-temperature-assets.py --save-report`
- `python3 scripts/build-coconala-temperature-pairs.py --save-report`
- `python3 scripts/save-coconala-temperature-preferred.py --case-id <ID> --preferred-file <path> --report-path <path> --send-ok yes --rebuild-pairs`
- `python3 scripts/export-coconala-temperature-reranker-set.py --save-report`
- `python3 scripts/check-coconala-temperature-buckets.py --save-report`

出力レポート:
- `/home/hr-hm/Project/work/runtime/regression/coconala-reply/temperature/latest.txt`
- `/home/hr-hm/Project/work/runtime/regression/coconala-reply/temperature/pairs/latest.txt`
- `/home/hr-hm/Project/work/runtime/regression/coconala-reply/temperature/buckets/latest.txt`

draft 保存:
- `python3 scripts/save-coconala-temperature-draft.py --case-id QLT-051 --draft-file <path> --source-file <path> --refresh-assets`
- `python3 scripts/save-coconala-temperature-draft.py --case-id QLT-051 --from-runtime --refresh-assets`
- quality-case の batch を作るときは、外部監査に出す前の初稿返信をここで 1 件ずつ残す

preferred 保存:
- `python3 scripts/save-coconala-temperature-preferred.py --case-id QLT-051 --preferred-file <path> --report-path <path> --send-ok yes --refresh-assets`
- `python3 scripts/import-coconala-temperature-preferred-report.py --report <resolved_report_path> --case-id QLT-051 --refresh-assets`
- `--refresh-assets` を付けると `pairs/complete.jsonl` と reranker export まで更新される
