# multi-turn check

## 目的
- 1通ずつは良くても、会話全体で停滞や矛盾が出ていないかを見る
- 特に `purchased / delivered / closed` の品質を確認する

## 対象
- 同一 buyer の連続 3通を1単位で見る
- `prequote` だけの単発監査には無理に使わない

## 最小4項目
1. 前のターンで言った約束を次で履行しているか
2. 同じ保留表現を引き延ばしていないか
3. buyer が会話として前に進んでいるか
4. secondary thread の行き先が delivery / close で見えているか

## pass / fail の例
### 1. 約束履行
- pass:
  - `確認して返します` の次で、確認結果を返している
- fail:
  - 次の返信でも同じ `確認します` のまま止まる

### 2. 保留の引き延ばし
- pass:
  - 保留の後に `続きとして扱えるか` `追加対応か` など判定が前に出る
- fail:
  - 2ターン続けて `確認します` `見ます` だけで進まない

### 3. buyer の前進
- pass:
  - buyer が次にやること、もしくは受け取る判断が見える
- fail:
  - 返信後も `で、どうすれば？` で止まる

### 4. secondary thread の行き先
- pass:
  - `同じ原因かを正式納品前に返します`
  - `別ならその時点で新しい依頼になると先に伝えます`
  - `画面が分かれば納品前に判断を返します`
- fail:
  - `まだ確認中です` のまま closed へ進む
  - `あとで見ます` のまま buyer に催促されて初めて動く

## 記録形式
```yaml
conversation_ref:
turn_span: ""
state:
checks:
  commitment_fulfilled: pass
  no_stalled_hold: pass
  buyer_progress_visible: pass
  secondary_thread_disposition_visible: pass
notes:
```

## 使いどころ
- `purchased` の途中共有
- `delivered` 後の軽い差し戻し
- `closed` 後の再相談

## 注意
- まずは3項目だけで回す
- ここで fail が多い時だけ、Router / Writer / Reviewer のどこに戻すか切る
