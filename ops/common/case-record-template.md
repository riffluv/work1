# 案件記録テンプレ

## 目的
- 進行中案件の判断根拠を、会話ログと切り離して短く残す。
- `#S / #M / #C` で同じ形の記録を作り、クローズ後も追えるようにする。
- コンテキストに常駐させず、必要時だけ読み返す。

## 保存先
- 進行中: `/home/hr-hm/Project/work/ops/cases/open/`
- クローズ後: `/home/hr-hm/Project/work/ops/cases/closed/`
- 一覧: `/home/hr-hm/Project/work/ops/case-log.csv`

## case_id の作り方
- 形式: `YYYYMMDD-連番-経路`
- 例: `20260315-01-service`
- 連番は同日の open / closed を見て空き番号を使う

## `#S` で作る内容
- case_id
- 開始日時
- 経路
- 状態
- 依頼要約
- 価格初期値
- 感情注意の有無
- 次アクション

## `#M` で追記する内容
- 追記日時
- 今回の判断
- 根拠
- 価格 / スコープの変化
- 次の見通し

## `#C` で確定する内容
- クローズ日時
- 最終結果
- 金額
- 何を直したか
- 同一原因 / 別原因の判定
- 感情注意の有無
- レビューや再発防止に効くメモ

## open 用テンプレ
```md
# {case_id}

- started_at:
- route:
- state:
- price_track:
- emotional_caution:
- client_summary:
- current_decision:
- next_action:

## Mid Snapshots
<!-- #M を時系列で追記 -->

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

## closed 用テンプレ
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
