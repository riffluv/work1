# 運用テストケース運用

## 目的
- 実案件前に、見積り判定・返信文・感情注意・金額分岐の回帰確認をする。
- 新しいテンプレや skill 変更を入れた時に、主要ケースで崩れていないかを見る。

## 優先して使う入力
- 主ケース集: `/home/hr-hm/Project/work/ops/tests/prequote-test-cases.txt`
- 骨格ケース: `/home/hr-hm/Project/work/ops/tests/prequote-cases.yaml`
- エッジケース: `/home/hr-hm/Project/work/ops/tests/edge-cases.yaml`
- `reply_contract v2` fixture: `/home/hr-hm/Project/work/ops/tests/prequote-contract-v2-top5.yaml`
- 評価ソース整理: `/home/hr-hm/Project/work/ops/tests/eval-sources.yaml`

## mode 別の入口
- `coconala`: 既存の `prequote-test-cases.txt` / `prequote-cases.yaml` / `edge-cases.yaml`
- `implementation`: `/home/hr-hm/Project/work/ops/tests/implementation/README.ja.md`
- `delivery`: `/home/hr-hm/Project/work/ops/tests/delivery/README.ja.md`
- `case`: `/home/hr-hm/Project/work/ops/tests/case/README.ja.md`
- `journeys`: `/home/hr-hm/Project/work/ops/tests/journeys/README.ja.md`
- 自動スモーク: `/home/hr-hm/Project/work/scripts/check-internal-os-flows.sh`

## 役割の違い
- `prequote-test-cases.txt`
  - Claude 作成の自然文ケース集。
  - 実際の相談文に近い温度感で、手動テストや reply 品質確認に向く。
- `prequote-cases.yaml`
  - 代表ケースの期待判定メモ。
  - 15K / 保留 / 断る の基本分岐確認に使う。
- `edge-cases.yaml`
  - 金銭事故や状態遷移の谷間に寄せた確認用。
  - 値引き、確認範囲の説明、quote_sent、closed 後などを見る。
- `prequote-contract-v2-top5.yaml`
  - `prequote-bulk-20.txt` 上位5件を、`reply_contract v2` 前提で手マッピングした fixture。
  - renderer / lint 実装前に、`primary_question_id / answer_map / ask_map` の切り方を確認するのに使う。
  - `./scripts/render-prequote-estimate-initial.py --case-id BLK-001` の入力にも使う。
- `eval-sources.yaml`
  - `ops/tests` 直下と `rehearsal` のどちらを、何の目的で使うかの整理。
  - 構造評価は直下、文体回帰は rehearsal を使う。
- `stock/`
  - 実ストックの置き場。
  - `inbox / seed / eval / holdout / edge` に分けて運用する。
  - 詳細は `/home/hr-hm/Project/work/ops/tests/stock/README.ja.md` を見る。

補足:
- `expected_template` の参照先は 1 ファイルに固定しない。`short:§21` のような表記は `docs/coconala-message-templates-short.ja.md`、`golden:§53` のような表記は `docs/coconala-golden-replies.ja.md` を見る。

## 使い方
1. `prequote-test-cases.txt` から 1件ずつ選ぶ
2. `route / state / raw_message / note` を Codex に貼る
3. 判定メモ / 返信文 / 補足提案が妥当かを見る
4. 必要ならテンプレ・skill・rule を修正する
5. 修正後は `prequote-cases.yaml` と `edge-cases.yaml` でも崩れていないかを見る
6. `reply_contract v2` の整合を確認するときは `./scripts/check-reply-contract-v2-fixtures.sh` を使う
7. `raw_message -> inferred reply_contract` の確認は `./scripts/check-inferred-prequote-contracts.py --show-passes` を使う
8. contract checker の保存先は `/home/hr-hm/Project/work/runtime/regression/coconala-reply/contracts/latest.txt`
9. `estimate_initial` の本文確認は `./scripts/check-rendered-prequote-estimate.py --fixture <path>` を使う
10. `post_purchase_quick` の本文確認は `./scripts/check-rendered-post-purchase-quick.py --fixture <path>` を使う
11. `closed` 後の再相談本文確認は `./scripts/check-rendered-closed-followup.py --fixture <path>` を使う
12. `delivered` の本文確認は `./scripts/check-rendered-delivered-followup.py --fixture <path>` を使う
13. `quote_sent` の本文確認は `./scripts/check-rendered-quote-sent-followup.py --fixture <path>` を使う
14. 状態ごとの renderer をまとめて通すときは `./scripts/render-coconala-reply.py --fixture <path> --case-id <id> --lint` を使う
15. 回帰結果を保存しながらまとめて見るときは `./scripts/check-coconala-reply-regression.py --save-report` を使う
16. 保存先は `/home/hr-hm/Project/work/runtime/regression/coconala-reply/latest.txt` と `runtime/regression/coconala-reply/<timestamp>.txt`
17. 直前結果との差分も見たいときは `./scripts/check-coconala-reply-regression.py --save-report --show-diff` を使う
18. 差分保存先は `/home/hr-hm/Project/work/runtime/regression/coconala-reply/latest-diff.txt` と `runtime/regression/coconala-reply/<timestamp>.diff.txt`
19. fail ケースの raw_message / rendered_reply も残したいときは、同じ `--save-report` で `/home/hr-hm/Project/work/runtime/regression/coconala-reply/failures/latest.txt` を見る
20. fail ケースだけ再実行したいときは `./scripts/rerun-coconala-reply-failures.py --save-report` を使う
21. 再実行結果の保存先は `/home/hr-hm/Project/work/runtime/regression/coconala-reply/failures/reruns/latest.txt`
22. contract と本文回帰をまとめて見たいときは `./scripts/check-coconala-reply-full-regression.py --save-report` を使う
23. 保存先は `/home/hr-hm/Project/work/runtime/regression/coconala-reply/full/latest.txt`
24. 実ストックの件数と state 分布を見たいときは `./scripts/build-coconala-stock-report.py --save-report` を使う
25. 保存先は `/home/hr-hm/Project/work/runtime/regression/coconala-reply/stock/latest.txt`
26. seed / edge / eval / holdout / renderer_seed を箱ごとに回したいときは `./scripts/check-coconala-reply-role-suites.py --save-report` を使う
27. 保存先は `/home/hr-hm/Project/work/runtime/regression/coconala-reply/suites/latest.txt`
28. role を絞るときは `./scripts/check-coconala-reply-full-regression.py --role holdout` や `./scripts/check-coconala-reply-regression.py --role eval` を使う

## 返信文の温度感をまとめて整えたいとき
- `/home/hr-hm/Project/work/ops/tests/rehearsal/README.ja.md` を使う
- 1件ずつではなく、カテゴリごとに 5件前後まとめて返信文を作る
- まとめた返信文を Claude に監査させ、共通する AI感 を skill に戻す
- raw の返信文バッチは `ops/tests/rehearsal` に常置せず、`/home/hr-hm/Project/work/runtime/rehearsal/` を一時置き場にする
- 長期保存が必要な raw batch は、plain text のまま残さず `ops/tests/rehearsal/archive/*.tar.gz` に圧縮退避する

## 特に見る点
- 15,000円 / 保留 / 断る の分岐が妥当か
- 感情注意フラグが過不足なく立つか
- 苦情寄りケースで冷たい文面になっていないか
- 見積り経路なのに有料オプション前提で書いていないか
- `closed` 後の相談で、既存トークルーム継続前提になっていないか

## 更新ルール
- 実案件で新しい危険パターンが出たら、まずは `edge-cases.yaml` に追加する。
- 自然文で再現したい場合は `prequote-test-cases.txt` と同形式で追記する。
- 代表ケースは増やしすぎず、回帰確認で毎回見る最小セットに保つ。
- `implementation` / `delivery` / `case` の運用変更を入れた時は、`check-internal-os-flows.sh` を最低1回通す。
