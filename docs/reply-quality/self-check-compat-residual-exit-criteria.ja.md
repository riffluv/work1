# self-check compat residual exit criteria

## 目的
- `/home/hr-hm/Project/work/docs/coconala-reply-self-check.ja.md` の `compat-only residual` について、
  - 最後まで残すもの
  - 次の互換整理で消せるもの
  を固定する
- これ以上 `monolith` を削る時に、毎回ゼロから判断しないようにする

## 現在の位置づけ
- `L1`
  - 会話品質
- `L2`
  - 受託返信の運び
- `L3`
  - service-pack 参照 validator
- `compat-only residual`
  - wording / finishing / 移行安全網

ここで残すのは、原則として `runtime の最後の保険` だけに限る。

## A. 最後まで残すもの

### 1. finishing / batch hygiene
- 時刻目安を入れたか
- 直近3件と同じ書き出し・末尾になっていないか
- 末尾の時刻コミットが同型ばかりになっていないか
- `2時間以内` を毎回固定の定型フッターとして入れていないか
- 同一バッチで `15,000円で進められます` が続きすぎていないか
- クロージングが `問題なければ` に固定しすぎていないか

理由:
- これは `L1 / L2 / L3` のどこか単体では拾いにくい
- バッチ単位の単調さや仕上げ運用は、compat layer に残す方が安全

### 2. wording の移行安全網
- `公開サービス` `この中で` `範囲で入る` のような内部スコープ語
- `整理` `全体の整理` を不要に前に出すこと
- `流用` のような内部寄りの業務語
- `可能性が高いです` のような内部メモ調の確信度
- `ここは優先して見ます` のような曖昧な指示語
- 金額を出しているのに同じ文面でヘッジしていること

理由:
- これらは service 固有というより「旧モノリス由来の悪い癖」
- 移行完了後も、最終防波堤として残す価値がある

### 3. final re-check
- 本文の中段も含めて Ban 表現が残っていないか
- naturalize 後にも、section order・価格・ask 数・hold reason・次アクション・forbidden claim を再チェックしたか

理由:
- これは runtime の最終ゲートであり、薄くしても消すべきではない

## B. 次の互換整理で消せるもの

### 1. audience calibration
- non_engineer 向けで内部語や強すぎる技術語が混ざっていないか
- 技術的に詳しい相手なのに、相手が出した具体語を1つも拾わずテンプレだけで返していないか
- 非技術者でも、観察情報を1つ拾える場面で落としていないか

出口条件:
- `L1` と `L2` の実バッチ監査で 5〜10 バッチ連続再発ゼロ
- seeds / gold replies 側で audience calibration が十分固定された時

### 2. fear wording
- 不安への返しで、相手が使っていない感情語や評価語を足していないか
- 相手が遠慮や不安を1行差し出した場面で、受領直後に1拍の受け止めがあるか

出口条件:
- angry / anxious / mixed の multi-turn クロステストで再発しない
- tone-profile に acknowledgment style が安定して持てる

### 3. certainty wording
- `可能性が高いです` のような内部メモ調の確信度
- `ここは優先して見ます` のような曖昧な指示語

出口条件:
- `L1` wording 側と `routing-playbooks` 側で十分に吸収される
- 通常 / 限界 / multi-turn で再発しない

## C. まだ動かさないもの
- `Ban チェック` 本体
- `naturalize 後の再チェック`
- batch hygiene

これらは、recomposition 完了後も `compat layer` の核として残す。

## 実務上の使い方
1. 新しい residual 項目が出たら、まず `L1 / L2 / L3` へ置けないかを見る
2. 置けないものだけ `compat-only residual` へ入れる
3. `compat-only residual` に入れた後も、3〜5バッチで再発ゼロなら再配置を検討する

## ゴール
- `compat-only residual` が「余り物の置き場」ではなく、
  - final gate
  - wording safety-net
  - batch hygiene
だけになること
