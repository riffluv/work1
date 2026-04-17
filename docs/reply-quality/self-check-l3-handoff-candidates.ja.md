# self-check L3 抽出候補（handoff-25000）

## 目的
- `/home/hr-hm/Project/work/docs/coconala-reply-self-check.ja.md` に残っている `handoff-25000` 固有の `L3` 文を、どの `service-pack` asset へ移すかを具体的に固定する
- `handoff` 特有の価格 / 1フロー / 修正別対応 / 納品物 / private 状態の知識を、runtime の会話品質ルールから切り離す

## 前提
- 対象サービス:
  - `/home/hr-hm/Project/work/ops/services/handoff-25000/service-pack/`
- `handoff-25000` は現時点では `public: false`
- ここで抜くのは `handoff` 固有の価格・範囲・route・納品物・補足対応境界
- ban 表現、buyer 語彙保持、否定先置き、slot-fill は `L1/L2` に残す

## 抽出候補一覧

### 1. 25,000円の範囲と追加フロー
- self-check:
  - `81`
  - `241`
  - `436`
  - `441`
  - `443`
  - `444`
- 現在の意味:
  - `25,000円` に含むのは `主要1フロー`
  - `追加フロー` は別単位
  - `25,000円で全部` の質問には、範囲と理由を返す
- 移し先:
  - `facts.yaml`
  - `boundaries.yaml`
- 薄くした後の self-check:
  - `価格返答が handoff facts と boundary_principles に矛盾していないか`

### 2. 主要1フローの定義
- self-check:
  - `248`
  - `249`
  - `359`
- 現在の意味:
  - `主要1フロー` を、固定の1本ではなく
    `1つの起点から1つの目的に向かう処理のまとまり`
    として説明する
- 移し先:
  - `facts.yaml`
- 薄くした後の self-check:
  - `1フロー説明が scope_unit.explanation と矛盾していないか`

### 3. bugfix vs handoff の boundary routing
- self-check:
  - `254`
  - `380` 付近の `boundary で症状が明確な bugfix を逃がさない`
- 現在の意味:
  - 主目的が修正なら bugfix を先に勧める
  - `コードが分からない` だけで handoff へ送らない
- 移し先:
  - `boundaries.yaml`
  - `routing-playbooks.yaml`
- 薄くした後の self-check:
  - `boundary routing が handoff boundary_principles と矛盾していないか`

### 4. prequote でコード一式を前のめり要求しない
- self-check:
  - `241`
  - `267`
  - `272`
  - `273`
  - `274`
- 現在の意味:
  - 高確度案件では ZIP より先に購入導線
  - 資料依頼を出す時も見積り判断まで
- 移し先:
  - `facts.yaml`
  - `routing-playbooks.yaml`
- 薄くした後の self-check:
  - `handoff prequote ask が phase_rules.prequote.must_not_do と矛盾していないか`

### 5. ブラックボックス案件で buyer に判断を返さない
- self-check:
  - `244`
  - `245`
  - `246`
  - `247`
- 現在の意味:
  - `どこが一番困るか` を相手へ返しすぎない
  - こちらから最初の1フロー案を置く
- 移し先:
  - `routing-playbooks.yaml`
  - `state-schema.yaml`
- 薄くした後の self-check:
  - `handoff prequote の target_flow 仮置きが route / state と矛盾していないか`

### 6. 非エンジニアでも読めるか
- self-check:
  - `262`
- 現在の意味:
  - 納品物の名前だけでなく、どう読めるか・何に使えるかまで返す
- 移し先:
  - `routing-playbooks.yaml`
  - `seeds.yaml`
- 薄くした後の self-check:
  - `non-engineer 返答が handoff playbook must_say と canonical seed を外していないか`

### 7. 納品物と `.md` 形式
- self-check:
  - `400`
  - `435`
  - `442`
- 現在の意味:
  - `何がもらえるか` に対し、`00_結論と要点.md` と `01_[対象フロー名]_引き継ぎメモ.md` を曖昧化しない
- 移し先:
  - `facts.yaml`
  - `seeds.yaml`
- 薄くした後の self-check:
  - `handoff deliverables の説明が facts.deliverables と矛盾していないか`

### 8. 修正は別対応
- self-check:
  - `360`
  - `361`
  - `439`
  - `440`
- 現在の意味:
  - `修正は含まない`
  - ただし強すぎず、同トークルームで続けられる導線は残す
- 移し先:
  - `boundaries.yaml`
  - `routing-playbooks.yaml`
  - `state-schema.yaml`
- 薄くした後の self-check:
  - `handoff 本体と修正追加の thread を混線させていないか`

### 9. まず整理だけで止められる
- self-check:
  - `quote_sent` 文脈の `まず整理だけで止められる`
- 現在の意味:
  - 整理だけで止めて、後から修正判断できる
- 移し先:
  - `routing-playbooks.yaml`
- 薄くした後の self-check:
  - `quote_sent handoff の段階対応が route must_say と矛盾していないか`

### 10. deeper memo / 補足メモ
- self-check:
  - `delivered_handoff` 文脈
- 現在の意味:
  - 補足で足りるか、書き直しに近いかで費用境界が変わる
- 移し先:
  - `routing-playbooks.yaml`
  - `state-schema.yaml`
- 薄くした後の self-check:
  - `deeper memo の返答が delivered_handoff_deeper_memo route と矛盾していないか`

### 11. private / 未公開状態の扱い
- self-check:
  - `255`
- 現在の意味:
  - 未公開サービスの名前・価格・購入導線を外に出さない
- 移し先:
  - `facts.yaml`
  - ただし最終的には `service-registry` 参照も必要
- 薄くした後の self-check:
  - `handoff が private の間は、service facts をそのまま公開導線へ出していないか`

### 12. 仕様書を先回り否定しない
- self-check:
  - `379`
- 現在の意味:
  - 相手が言っていない `仕様書` を先回りで否定しない
- 移し先:
  - `seeds.yaml`
  - 一部は L2 に残す
- 薄くした後の self-check:
  - `handoff の価値説明が canonical seed を外していないか`

## 先に抜きやすい 8 個
- 1. 25,000円の範囲と追加フロー
- 2. 主要1フローの定義
- 3. bugfix vs handoff の boundary routing
- 4. prequote でコード一式を前のめり要求しない
- 6. 非エンジニアでも読めるか
- 7. 納品物と `.md` 形式
- 8. 修正は別対応
- 11. private / 未公開状態の扱い

理由:
- 既に `service-pack` 側に facts / boundaries / playbooks / state の置き場がある
- `handoff` で特にノイズになりやすい知識塊を先に外へ出せる
- 返信品質を壊さず slim 化しやすい

## まだ self-check に残すもの
- `形になります`
- `進め方`
- `合っています`
- buyer 語彙保持
- 過度な upsell 回避

理由:
- これらは `handoff` 固有知識というより、会話品質や writer の癖だから

## 次の実作業
1. 上の `先に抜きやすい 8 個` を `asset 参照 validator` に置き換える
2. bugfix と同様に、facts / boundaries / routing / state 参照へ薄くする
3. その後 `L1` だけ抜いた最小 universal check を作る
