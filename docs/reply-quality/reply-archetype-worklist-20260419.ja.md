# Reply Archetype Worklist 2026-04-19

## 目的
- live 寄り 5 件のランダム監査を一旦止める
- generic fallback / scenario misroute が出た archetype を固定して潰す
- 単発修正ではなく、類型ごとに代表ケースで直してから再監査する

## 今回固定する archetype

### 1. service_selection_uncertainty
- 代表ケース: `CASE-005`
- buyer の核心:
  - `どちらのサービスが合うか`
  - `不具合なのか、そもそも実装途中なのか分からない`
- 欲しい返し:
  - bugfix から入るのが近いかを先に答える
  - buyer の症状を 1 回は拾う
  - handoff 非公開前提を壊さない

### 2. guarantee_or_refund_prequote
- 代表ケース: `CASE-006`
- buyer の核心:
  - `15,000円で確実に直る保証はあるか`
  - `直らなかった場合はどうなるか`
- 欲しい返し:
  - 保証の有無を先に答える
  - 調査だけで終わる進め方ではないことを示す
  - 返金/追加費用の扱いを buyer 向けに自然に説明する

### 3. progress_status_request
- 代表ケース: `CASE-012`
- buyer の核心:
  - `進捗はどうなっているか`
  - `今どこまで見ているか`
  - `以前待たされて不安`
- 欲しい返し:
  - 謝罪または受け止め
  - 具体的な現在地
  - 次にいつ何を返すか

### 4. delivered_self_deploy_anxiety
- 代表ケース: `CASE-014`
- buyer の核心:
  - `本番反映は自分でやる形か`
  - `何に気をつけるべきか`
- 欲しい返し:
  - Yes/No を先に答える
  - 気をつける点を 1 つか 2 つ具体化する
  - 差し戻し系 generic へ落とさない

## 進め方
1. 各 archetype の代表ケースを current fixture で固定する
2. 類型ごとに renderer / routing の最小修正を入れる
3. archetype 単位で再レンダする
4. archetype が通ってから live 5 件監査に戻る

## やらないこと
- ランダム 5 件を回しながらその場で都度修正する
- scenario / renderer をむやみに増やす
- 返信文の表層だけを撫でて原因未特定のまま先に進む
