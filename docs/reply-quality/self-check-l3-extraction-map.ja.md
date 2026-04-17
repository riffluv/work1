# self-check L3 抽出マップ

## 目的
- `/home/hr-hm/Project/work/docs/coconala-reply-self-check.ja.md` に残っている `L3: Service` 相当のチェックを、どの `service-pack` asset へ移すかを固定する
- 先に抽出マップを作ることで、self-check を一気に壊さず段階的に slim 化する

## 前提
- `L1`: 会話文と thread state だけで判定できる
- `L2`: 受託返信の運び方として共通
- `L3`: 価格 / scope / hard no / route / proper noun など、サービス固有知識が必要

## 対象 service-pack
- bugfix:
  - `/home/hr-hm/Project/work/ops/services/next-stripe-bugfix/service-pack/`
- handoff:
  - `/home/hr-hm/Project/work/ops/services/handoff-25000/service-pack/`

## 抽出優先順位
1. price / scope / boundary
2. routing / playbook
3. hard no
4. state continuity の service 固有部分
5. handoff 固有の納品物・価格・境界

## 1. facts.yaml に寄せるもの
対象:
- 価格の固定値
- `15,000円` / `25,000円` の範囲説明
- phase ごとの `can_offer / can_ask_for / must_not_do`
- deliverables
- buyer anxieties の service 固有部分

代表例:
- `15,000円には原因の切り分けと修正可否の確認を含める`
- `公開 bugfix の定額案内で、お見積りをお返しします が残っていないか`
- `handoff の納品物を .md 形式まで答えているか`

移し方:
- self-check 本文に金額や納品物を再記述しない
- `facts.yaml の source_ref を参照しているか` を見る validator に寄せる

## 2. boundaries.yaml に寄せるもの
対象:
- in/out of scope
- hard no
- 追加料金が自動発生しない
- 同一原因 / 別原因のサービス固有境界

代表例:
- `通話・ビデオ会議`
- `直接push`
- `本番デプロイ代行`
- `別機能なら新しい依頼`
- `同じ原因なら今回の中で扱う`

移し方:
- 断り方の自然さは L2 に残す
- 何を断るか、何を含まないかは boundaries 側へ寄せる

## 3. routing-playbooks.yaml に寄せるもの
対象:
- `どの相談に、どの route で返すか`
- route ごとの must_say
- mixed symptom の disposition
- bugfix / handoff の境界 route

代表例:
- `今出ている不具合を止めるのが先なら、まずは不具合修正から`
- `まず整理だけで止められる`
- `追加で詳しいメモは可能`
- `返金不安では、まず再発か新規かを返す`

移し方:
- self-check には `must_say を落としていないか` だけ残す
- route 自体の本文説明は playbook 側で持つ

## 4. state-schema.yaml に寄せるもの
対象:
- secondary symptom
- promised_next_action
- unresolved_threads
- scope_status
- current_route

代表例:
- `secondary symptom の行き先を明示しないままクローズへ進んでいないか`
- `promise を次ターンで履行しているか`
- `multi-turn で同じ保留を引き延ばしていないか`

移し方:
- self-check prose ではなく、state の埋まり具合と遷移整合で見る
- service 固有の thread（例: `修正追加は別対応`）だけ L3 で残す

## 5. seeds.yaml に寄せるもの
対象:
- そのサービスで効く canonical reply
- live prompt に差し込む少数 exemplar
- eval gold

代表例:
- bugfix:
  - success rate fear
  - repeat discount
  - refund anxiety
- handoff:
  - non-engineer explanation
  - deeper memo supplement

移し方:
- self-check に「こう書け」を増やし続けない
- 良い型は seed 側へ送る

## 6. tone-profile.yaml に寄せるもの
対象:
- warmth
- directness
- politeness
- brevity
- acknowledgment style
- certainty calibration

代表例:
- `buyer の具体的な行動や観測事実を1点拾う`
- `長い共感を避ける`
- `制度説明を講義調にしない`

移し方:
- tone は layer ではなく asset
- `何を言うか` ではなく `どう聞こえるか` を管理する

## すぐ self-check から外しやすい L3 群
次の項目は、まず service-pack 参照へ移しやすい。

### bugfix 側
- 15,000円固定の価格説明
- 追加料金が自動発生しない
- prequote で ZIP を要求しない
- `同一原因 / 別原因 / 新しい依頼`
- bugfix 固有の mixed symptom disposition

### handoff 側
- 25,000円 / 追加1フロー 15,000円
- `.md` 納品
- 修正は別対応
- 主要1フローの説明
- private / ready 状態に依存する案内

## まだ self-check に残すもの
次は service 固有に見えても、しばらく self-check に残す。
- buyer の名詞を推測で差し替えない
- slot-fill の回避
- ban表現
- 否定先置き
- 既出情報の聞き直し回避
- open loop 放置

理由:
- これらは実際には会話品質や universal runtime の問題で、service 固有 asset に置くと再利用性が下がるため

## 次の実作業
1. `bugfix-15000` に関する L3 文を self-check から抜く候補を 10〜20 個抽出する
2. 候補ごとに `facts / boundaries / routing / state / seeds / tone` のどこへ置くかタグ付けする
3. 抜いた後も quality regression が起きないか、5件バッチで確認する

## ゴール
- self-check が「service 知識の本文」ではなく
  - `runtime quality checks`
  - `service-pack 参照 validator`
 へ変わっている状態
