# phase contract batch plan（2026-04-25）

## 目的

ココナラの phase 認識が絡む時に、返信が `結局どうなるの？` で終わらないかを検証する。

このメモは生成 rule ではない。`#RE` の batch archetype と reviewer 観点として使う。

## 背景

#AR と DeepResearch で、次の補正点が固まった。

- `prequote / quote_sent / purchased / delivered / closed` は公式用語ではなく内部 state。
- `quote_sent` は見積り提案済みだが入金完了前。トークルームが開くのは入金完了後。
- `delivered` は正式な納品後・クローズ前。ただし一回目/二回目の正式な納品で buyer ができることが違うため、差し戻し可否を一般化しない。
- `closed` は完了としてクローズ済み。`cancelled` とは分ける。
- `closed` 後は旧トークルーム不可。メッセージで事実確認し、実作業なら見積り提案または新規依頼へ戻す。

## 重点観察

- `closed` 後に旧トークルーム継続を前提にしていないか。
- `closed` 後におひねりや旧トークルーム内の追加購入を案内していないか。
- `closed` 後のメッセージ上の事実確認と、実作業・成果物返却を混ぜていないか。
- `delivered` を `closed` と誤認していないか。
- `delivered` で差し戻し可能と無条件に言い切っていないか。
- `quote_sent` で、入金完了前なのにトークルーム・作業中・納品後の文面へ進んでいないか。
- 返金希望に対して、返金可否を出品者側で断定していないか。
- 追加料金に対して、自動発生と読ませていないか。

## 次の batch 案

### RE-2026-04-25-bugfix-09-phase-contract-edge

- 目的: phase の誤認で導線が曖昧になるケースを検証する
- 件数: 6
- state_mix: quote_sent 1 / purchased 1 / delivered 2 / closed 2
- risk_axes: phase_miss, closed_route_miss, delivered_closed_confusion, refund_overcommit, missing_next_path, external_share_escape

入れる archetype:

- `quote_sent`: 見積り提案に同意したが、まだ支払い前。`もう作業を始めてもらえますか？`
- `purchased`: 取引中にキャンセル希望。`やっぱりキャンセルしたいです。返金されますか？`
- `delivered`: 正式納品後。`承諾したら、もう修正してもらえませんか？`
- `delivered`: 二回目正式納品後か不明。`差し戻しできますか？`
- `closed`: クローズ後の再発。`前のトークルームで続きできますか？`
- `closed`: クローズ後の追加作業。`おひねりで払えば直してもらえますか？`

### RE-2026-04-25-bugfix-10-closed-materials-and-work-boundary

- 目的: closed 後に確認材料を受け取ることと、実作業へ入ることの境界を検証する
- 件数: 6
- state_mix: closed 6
- risk_axes: external_share_escape, actual_work_before_quote, secret_handling, nonanswer, missing_next_path

入れる archetype:

- `closed`: `ログとスクショを送れば見てもらえますか？`
- `closed`: `ZIPでコードを送るので直して返してもらえますか？`
- `closed`: `100MBを超えるのでGoogle Driveで共有していいですか？`
- `closed`: `.envも入れた方が早いですか？`
- `closed`: `前回の続きなので無料で直してもらえますか？`
- `closed`: `新規見積りになるなら、先に原因だけ見てください`

## rule に戻す条件

次を満たすものだけ、platform-contract / renderer / validator へ戻す。

- 公式事実に基づく
- 同 batch 内または過去 batch で再発している
- buyer に誤解や不利益が出る
- 戻し先が明確
- 副作用が小さい

## reviewer_prompt に留める条件

- phase 未確定時の言い切り調整
- 前回修正との関係確認の深さ
- メッセージ上の説明と実作業の境界
- `結局どうなるか` の見え方

## やらないこと

- phase を細かく増やさない。
- 電話相談・定期購入の例外を混ぜない。
- 支払い方法別の返金 timing を返信 system に常駐させない。
- 非公式ブログやSNS投稿を hard rule にしない。
- closed 後問い合わせをすべて即新規見積りに飛ばさない。
- ファイル受領を全面禁止しない。確認材料の受領と実作業を分ける。
