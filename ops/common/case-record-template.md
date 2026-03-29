# 案件記録テンプレ

## 目的
- 進行中案件の判断根拠を、会話ログと切り離して短く残す。
- `#S / #M / #C` で同じ形の記録を作り、クローズ後も追えるようにする。
- コンテキストに常駐させず、必要時だけ読み返す。

## 保存先
- 進行中: `/home/hr-hm/Project/work/ops/cases/open/{case_id}/`
- クローズ後: `/home/hr-hm/Project/work/ops/cases/closed/{case_id}/`
- 一覧: `/home/hr-hm/Project/work/ops/case-log.csv`
- 案件メモ本体: `README.md`

## case_id の作り方
- 形式: `YYYYMMDD-連番-経路`
- 例: `20260315-01-service`
- 連番は同日の open / closed を見て空き番号を使う

## `#S` で作る内容
- 案件フォルダ
- `README.md`
- case_id
- 開始日時
- Service ID
- 経路
- phase
- scope_status
- 依頼要約
- 次アクション
- implementation_focus
- delivery_status

## `#M` で追記する内容
- open案件フォルダ内の `README.md`
- 追記日時
- 今回の判断
- 根拠
- 価格 / スコープの変化
- 次の見通し

## phase 切替で更新する内容
- open案件フォルダ内の `README.md`
- `phase`
- 必要に応じて `delivery_status`
- `current_decision`
- `next_action`

## `#C` で確定する内容
- 案件フォルダごと `closed` へ移動
- クローズ日時
- 最終結果
- 金額
- 何を直したか
- 同一原因 / 別原因の判定
- 感情注意の有無
- レビューや再発防止に効くメモ

## open 用 `README.md` テンプレ
```md
# {case_id}

- started_at:
- service_id:
- route:
- phase:
- scope_status:
- client_summary:
- current_decision:
- next_action:
- implementation_focus:
- delivery_status:

## Mid Snapshots
<!-- #M を時系列で追記 -->

## Delivery Notes
<!-- delivery mode で必要な要点だけ追記 -->

## Close Draft
<!-- #C 前に必要なら下書き -->
```

## `#M` 追記テンプレ
```md
### {timestamp}
- decision:
- reason:
- scope:
- price:
- next_action:
```

## closed 用 `README.md` テンプレ
```md
# {case_id}

- started_at:
- closed_at:
- route:
- final_state:
- amount:
- emotional_caution:
- outcome:

## What Happened
- issue:
- fix:
- verification:

## Scope Notes
- same_or_different_cause:
- additional_handling:

## Ops Memo
- review_risk:
- reuse_hint:
```

## 最小構成
- `ops/cases/open/{case_id}/README.md`
- 追加ファイルが必要になった時だけ、同じ案件フォルダ配下に増やす
- サブフォルダは必要時のみ手動作成とし、日本語名を使う
- 推奨: `受領物/` `納品物/` `作業メモ/`
- サブフォルダ自動作成は現時点では行わない
- 正本 script:
  - `#S` -> `/home/hr-hm/Project/work/scripts/case-open.sh`
  - `#M` -> `/home/hr-hm/Project/work/scripts/case-note.sh`
  - phase 切替 -> `/home/hr-hm/Project/work/scripts/case-phase.sh`
  - `#C` -> `/home/hr-hm/Project/work/scripts/case-close.sh`
