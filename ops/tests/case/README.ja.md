# Case OS テスト

## 目的
- `#S / #M / #C` と phase 切替が script 主導で回るか確認する
- `runtime` と `ops/cases` の整合が崩れないか確認する

## 最低確認
1. `./scripts/case-open.sh` で open case を作る
2. `./scripts/case-note.sh` で判断を追記する
3. `./scripts/case-phase.sh --phase delivery` で納品準備へ切り替える
4. `./scripts/case-close.sh` で closed へ移動する
5. `ops/case-log.csv`、`runtime/mode.txt`、`runtime/active-case.txt` が整合することを確認する

## 自動スモーク
- `./scripts/check-internal-os-flows.sh`
- case open -> note -> delivery phase -> reply save -> close を一通り検証する
