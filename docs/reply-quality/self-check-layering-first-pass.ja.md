# self-check L1/L2/L3 棚卸し（初版）

## 目的
- `/home/hr-hm/Project/work/docs/coconala-reply-self-check.ja.md` に集まっている暗黙知を、`L1 / L2 / L3` へ切り分ける
- `reply runtime` と `service-pack` を分離しやすくする
- 全文を書き換える前に、`どの層へ移すべきか` の判断基準を固定する

## 定義
- `L1: Universal`
  - 会話文と thread 状態だけ見れば判定できるもの
  - サービス固有知識を必要としない
- `L2: Domain`
  - 受託返信 / サポート返信というドメイン共通の運び方
  - 特定サービスの価格・範囲・禁止事項は不要
- `L3: Service`
  - 価格、範囲、禁止事項、個別 route、固有運用など、特定サービス knowledge が必要

## 判定基準
1. 会話だけで pass/fail を切れる -> `L1`
2. 受託返信の craft が必要だが、サービス固有 facts は不要 -> `L2`
3. price / scope / proper noun / route / hard no が必要 -> `L3`

補足:
- `L3` に本文知識を重複記述しない
- `L3` は service-pack を参照する validator に寄せる
- `tone` は layer ではなく別 asset として持つ

## 既存 self-check の見立て

### 送信前チェック
主成分:
- `L1`

理由:
- 主質問への直答
- 既出情報の聞き直し回避
- multi-turn 不整合
- AI感の強い反復
- buyer 名詞の事実ズレ
- open loop の放置

L3 へ寄せる候補:
- 価格・スコープ・規約・public/private 公開状態に依存する箇所
- `handoff` 未公開時の案内禁止
- `15,000円` 固定で返すべき場面

### 見積り初回
主成分:
- `L2`

理由:
- prequote で重い ask をしない
- buyer の判断段階に合わせる
- 価格や可否を先に返す
- 追加質問は最小限

L3 へ寄せる候補:
- `bugfix-15000` 固有の価格説明
- `ZIP は購入後` などサービス運用由来のルール
- `handoff` 公開状態に依存する境界処理

### 感情注意
主成分:
- `L1`

理由:
- slot-fill 回避
- buyer が使っていない感情語を足さない
- 防御・弁解の抑制
- 温度感の過不足

L2 へ寄せる候補:
- 緊急案件での返し方
- delivered / closed の不満への引き取り方

### quote_sent
主成分:
- `L2`

理由:
- quote_sent で prequote 的 ask に戻らない
- yes/no へ直答
- 購入判断を前に進める

L3 へ寄せる候補:
- 価格確定の仕方
- 固有サービスの追加対応境界

### closed 後再発
主成分:
- `L2`

理由:
- 再発か新規かを先に切る
- 一律保証を約束しない
- 追加料金説明を急がない

L3 へ寄せる候補:
- 「今回の続き」として扱う判定軸
- 同一原因 / 別原因の具体運用

### 範囲外
主成分:
- `L2`

理由:
- 断る時に講義調にしない
- 代替導線を1文で示す
- 外部共有 / Zoom / 直接操作を止める時の会話運び

L3 へ寄せる候補:
- 具体的な hard no
- platform / service 固有の禁止事項

### 境界ケース
主成分:
- `L3`

理由:
- `bugfix` と `handoff` の routing
- 公開状態
- どのサービスへ振るか
- `Stripe 以外` を受ける条件

移し先:
- `routing-playbooks`
- `boundaries`
- `facts`

### purchased / closed
主成分:
- `L2`

理由:
- 進捗共有
- 追加症状の disposition
- 保留を長引かせない
- `secondary symptom` の行き先明示

L3 へ寄せる候補:
- 同一原因として扱う条件
- 追加料金の固有境界

### handoff 系
主成分:
- `L3`

理由:
- `handoff-25000` 固有の運用
- private / live の扱い
- handoff 固有の納品物・進め方・価格説明

移し先:
- `handoff` service-pack 側

## 先に外へ出すべき高優先ルール
次の4系統は、self-check prose に置き続けるより asset 化した方がよい。

1. `価格・範囲・追加対応境界`
- 理由: もっとも service 固有で、L3 そのもの

2. `routing / playbook`
- 理由: `どういう相談に何を返すか` は rule ではなく route 設計

3. `state continuity`
- 理由: multi-turn の穴は prose rule ではなく state で持つべき

4. `hard no`
- 理由: 断り方は L2、断る対象そのものは L3

## 当面の運用
- 既存 self-check はすぐ分解しない
- まず、以下を並行で持つ
  - `現行 self-check`
  - `この棚卸し表`
  - `service-pack`

## 次の実作業
1. `bugfix-15000` の service-pack を source of truth として固定
2. `self-check` の L3 相当を、asset 参照に書き換える候補を洗い出す
3. `handoff-25000` も同じ pack 形式へ揃える
4. `L1` だけを抜いた最小 universal check の叩き台を作る

## ゴール
- self-check が「暗黙知の塊」ではなく
  - `L1/L2 の runtime check`
  - `L3 の asset validator`
 へ分かれている状態
