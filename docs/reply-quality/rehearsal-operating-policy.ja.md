# #RE / #BR 運用ポリシー

更新日: 2026-05-01

## 目的

#RE / #BR を、無限に同じ型を回す作業ではなく、返信OSコアの coverage を埋める実験として扱う。

このポリシーは、外部 Codex xhigh / Pro の費用と時間を無駄打ちしないための運用正本です。

## #RE の3分類

| 種別 | 目的 | 外部 xhigh | 例 |
| --- | --- | --- | --- |
| Discovery #RE | 未知の failure class / 新 lens 候補を見つける | 使ってよい | 新しい違和感、実案件 stock、サービス公開前 |
| Regression #RE | 直した failure が戻っていないか確認する | 原則不要 | B06 case_fix の再確認、validator 変更後 |
| Stability smoke | 既に安定した family を軽く確認する | 不要 | #RE88〜94 の同型 practical chat / semantic grounding |

## #RE を回す条件

次のいずれかに当てはまる時だけ、新規 #RE を回す。

- coverage map で `saturation: low` または `medium` の family がある。
- 実案件 stock から、既存 fixture にない buyer 文が来た。
- 新しい soft lens を candidate から formal に上げる前。
- renderer / validator / naturalizer / service pack を変更した。
- #R と #RE の出力差が気になる。
- 公開前の launch check が必要。

## #RE を止める条件

同一 family で次を満たしたら停止する。

- 3 batch 連続で必須修正なし。
- 指摘が軽微 case_fix / preference / acceptable_as_is だけ。
- 新規 hard rule / lint / renderer 変更がない。
- local lint / regression / service-pack fidelity / sentry が green または既存 warning のみ。
- human audit が「意味は通るが好み差」「安全境界由来の硬さ」と判断している。

## xhigh 監査を使う条件

外部 Codex xhigh は次の時だけ使う。

- 新しい failure class が出た。
- soft lens を formal / gold / lint / rule へ昇格するか迷う。
- public launch 前の総合監査。
- handoff-25000 を public 化する前。
- #R と #RE の生成経路がズレた疑いがある。
- human audit と local audit の判断が割れた。
- 実案件 stock で高リスクな未知ケースが出た。

使わない場面:

- 同型 #RE の routine 採用確認。
- 既に saturation: high の family。
- 軽微 case_fix の再監査。
- 句点数、段落数、単語の好み差だけ。

## Pro に聞く条件

ChatGPT Pro は、batch そのものの採点より、設計判断に使う。

使う場面:

- 完成条件、停止条件、coverage 設計を見直す。
- 新しい lens が本当に formal に値するか判断する。
- ココナラ固有から汎用コアへ切り出す境界を見直す。
- アプリ化前の memory / phase / contract packet 設計を固める。
- 3〜5本の accepted batch から、次に薄い領域を判断する。

使わない場面:

- 同じ family の採用確認だけ。
- 1文の好み差。
- local で明らかな case_fix。

## 現在の停止判断

#RE88〜94 は、以下の family で `saturation: high` と扱う。

- purchased_current_status
- quote_sent_payment_after_share
- delivered_light_supplement
- closed_relation_check

この family は、次のどれかが出るまで routine #RE を止める。

- 実案件 stock で未知の崩れが出る。
- #R で再現する違和感が出る。
- service pack / phase contract / writer brief を変更する。
- Pro / human audit が未検証領域を指定する。

