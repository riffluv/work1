---
name: coconala-prequote-ops-ja
description: "ココナラ見積り相談の前段専用。相手文を、入口判定 -> 15,000円/5,000円/保留/断る の分岐 -> 返信文生成まで一貫処理し、送信用返信文・内部判定メモ・補足提案の3点セットで返す。"
---

# ココナラ見積り相談オペレーター

## 目的
- 見積り相談（prequote）の判断順序を固定し、再現性を上げる。
- ユーザーが相手文を貼るだけで、送信用返信文まで返せる状態を作る。
- 無償で見すぎる事故と、金額判断のブレを減らす。

## このskillを使う場面
- `#R` または `#A` で、`state: prequote` の相手文が貼られたとき
- サービス経由 / プロフィール経由 / メッセージ経由の見積り相談
- 初回判定、および保留案件の再判定

## このskillを使わない場面
- `state` が `purchased` 以降のとき
- `#$0` / `#$1` / `#$2` / `#$3` の UI進行タグが付いているとき
- トークルーム購入後の受領返信、進捗返信、納品前後の案内

上記は `coconala-reply-bugfix-ja` を直接使う。

## 最初に見るファイル
1. `/home/hr-hm/Project/work/ops/common/output-schema.yaml`
2. `/home/hr-hm/Project/work/ops/common/interaction-states.yaml`
3. `/home/hr-hm/Project/work/ops/common/coconala-rule-guard.md`
4. `/home/hr-hm/Project/work/ops/common/routing-table.yaml`
5. `/home/hr-hm/Project/work/ops/services/next-stripe-bugfix/service.yaml`
6. `/home/hr-hm/Project/work/ops/services/next-stripe-bugfix/evidence-minimum.yaml`
7. `/home/hr-hm/Project/work/ops/services/next-stripe-bugfix/estimate-decision.yaml`
8. `/home/hr-hm/Project/work/docs/coconala-message-templates-short.ja.md`

## intake-router から引き継ぐ項目
- `service_fit`
- `risk_level`
- `risk_flags`
- `scope_judgement`
- `missing_info`
- `next_action`
- `reply_generation`

## 実行フロー
1. `coconala-intake-router-ja` で入口判定を行う。
2. 引き継ぎ項目を確認し、`prequote` 以外ならこのskillを使わない。
3. `risk_level` が高く、価格や規約判断が揺れる場合は分析のみで止める。
4. `estimate-decision.yaml` を参照し、`15,000円 / 5,000円 / 保留 / 断る` を判定する。
5. 判定結果に対応するテンプレを選ぶ。
   - `accept_15k` -> `§11`
   - `accept_5k` -> `§13-2`
   - `hold` -> `§13-3`
   - `decline` -> `§18`
6. `#R` のときだけ `coconala-reply-bugfix-ja` で送信用返信文を作る。
7. 必要なら `japanese-chat-natural-ja` で自然さだけ整える。
8. `#A` のときは、判定メモと次アクションだけ返す。

## 判定ルール
- `15,000円`
  - 高適合
  - 同一原因の1件に見える
  - 情報が足りていて見積れる
  - 基本料金内で収まりそう
- `5,000円`
  - 方向性は見えるが、修正1件と断定できない
  - 30分で懸念点整理や次に見る場所は返せそう
  - 確認だけで終わる意図が明確
  - 修正そのものは含めない
- `保留`
  - 情報不足で判定不能
  - 追加質問は1回まで
  - 2回目も曖昧なら `5,000円` か辞退へ倒す
- `断る`
  - 範囲外
  - 新機能 / 新規実装
  - 別原因が多すぎる
  - 幅が広すぎる

## closed後の再発相談（重要）
- 経路が `message` で、前回取引の再発相談かつ未解決感が強い場合は、最初の1通で価格を出さない
- `新しい相談` `新規依頼` を先に出さず、`トークルームが閉じているため、ここから改めて状況を確認する` と表現する
- 最初の依頼はスクショ1枚と、前回と同じ症状かどうかの確認に絞る
- 同一原因の再発に見える場合は、いきなり15,000円ではなく、5,000円の確認案件を優先検討する

## 出力フォーマット
### 1. 判定メモ
- `estimate_decision`: `accept_15k / accept_5k / hold / decline`
- `hold_round`: `0 / 1`
- `service_fit`
- `cause_estimate`
- `info_sufficiency`
- `next_action`

### 2. 送信用返信文
- `#R` のときのみ
- そのまま送れる文面

### 3. 補足提案
- 必要なときだけ
- 例: `5,000円で先に方向性だけ整理する方が安全です`
- `5,000円 -> 追加で15,000円` が不自然になりそうなときは、`A) 5,000円確認のみ / B) 15,000円で修正込み` の2択で案内する

## 保留案件の扱い
- 初回保留では `hold_round: 0`
- 相手が回答して再判定するときは `hold_round: 1`
- 自動判定に頼らず、必要なら前回の判定メモを添えて再実行する
- 2回目も判定不能なら、`5,000円` または辞退へ倒す

## 送信用返信文の扱い
- 送信用文面を作ったときは `/home/hr-hm/Project/work/返信文_latest.txt` に保存する
- `#R` は prequote のときだけ、このskillを優先する
- 購入後の `#R` は従来どおり `coconala-reply-bugfix-ja` を使う

## 仕上げ前チェック
- `prequote` かどうかを取り違えていないか
- 追加質問が2回以上になっていないか
- 原因候補の詳細説明を無料で出していないか
- 見積り経路では有料オプションを後から足せない前提で金額判断しているか
- `#A` で送信用文面を混ぜていないか
- `5,000円 -> 追加で15,000円` が相手に割高に見えないかを確認したか
