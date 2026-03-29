# Delivery OS テスト

## 目的
- 納品準備の段階で `delivery` mode へ切り替えられるか確認する
- 納品では新しい実装判断を増やさず、既存スコープの整理に集中できるか確認する

## 最低確認
1. open case を用意する
2. `./scripts/case-phase.sh --phase delivery --case-id {case_id}` を実行する
3. `runtime/mode.txt` が `delivery` になることを確認する
4. `ops/cases/open/{case_id}/README.md` の `phase` が `delivery` に変わることを確認する
5. `delivery-pack-ja` を使う時、参照の主軸が case README と納品物になることを確認する

## 合格条件
- delivery mode の入口が手作業メモではなく script で固定されている
- 納品準備で scope を広げず、正式納品とクローズへつなげられる
