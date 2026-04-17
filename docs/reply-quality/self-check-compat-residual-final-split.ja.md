# self-check compat residual 最終仕分け

## 目的
- `/home/hr-hm/Project/work/docs/coconala-reply-self-check.ja.md` の `compat-only residual` に残っている項目を、
  - 本当に compatibility layer として残すもの
  - `L3 service-pack` 参照へ再配置するもの
  に二分する
- 次の削減を、文面感覚ではなく置き場の判断で進められるようにする

## 仕分け基準

### compat-only に残すもの
- まだ `L1 / L2 / L3` のどこか1つにきれいに置き切れない
- 旧バッチ資産や既存監査運用との互換を守る安全網として残す価値がある
- wording / finishing / migration safety として機能する

### L3 へ再配置するもの
- bugfix / handoff / 公開状態 / fixed price / deliverables / repeat / refund / private state など、service 固有の前提が必要
- `facts / boundaries / routing-playbooks / state-schema / tone-profile` を参照する方が自然
- monolith に本文知識として残すと、移植性が落ちる

## A. compat-only に残すもの

### 1. 仕上げ運用
- 時刻目安を入れたか
- 直近3件と同じ書き出し・末尾になっていないか
- 末尾の時刻コミットが同型ばかりになっていないか
- `2時間以内` を毎回固定の定型フッターとして入れていないか
- `.env` 注意文のあとに結語が抜けていないか
- 同一バッチで `15,000円で進められます` が続きすぎていないか
- クロージングが `問題なければ` に固定しすぎていないか
- `切り分けたうえで対応します` が機械的な標準文になっていないか
- 本文の中段も含めて Ban 表現が残っていないか
- naturalize 後にも、section order・価格・ask 数・hold reason・次アクション・forbidden claim を再チェックしたか

### 2. wording の移行安全網
- `公開サービス` `この中で` `範囲で入る` のような内部スコープ語を前に出していないか
- 相手が聞いていない `整理` `全体の整理` を否定形でも持ち出していないか
- `流用` のような内部寄りの業務語が残っていないか
- `可能性が高いです` のような確信度表現が内部メモとして漏れていないか
- `ここは優先して見ます` のような曖昧な指示語が残っていないか
- 金額を出しているのに、同じ文面でヘッジしていないか

### 3. 互換上まだ残す cross-layer 項目
- non_engineer 向けで内部語や強すぎる技術語が混ざっていないか
- 技術的に詳しい相手なのに、相手が出した具体語を1つも拾わずテンプレだけで返していないか
- 非技術者でも、観察情報を1つ拾える場面で落としていないか
- 不安への返しで、相手が使っていない感情語や評価語を足していないか
- 相手が遠慮や不安を1行差し出している場面で、冒頭の受領直後に1拍の受け止めがあるか

## B. L3 へ再配置するもの

### 1. bugfix facts / phase_rules 参照へ寄せるもの
- `.envやAPIキーの値は不要です` を機械的に入れていないか
- bugfix の prequote ask が `phase_rules.prequote` を外していないか
- prequote の ask が `もの / 資料 / ファイル` に広がりすぎていないか
- Stripe不使用ケースなら、対応可能か対象外かを一言で明示したか

置き先:
- `/home/hr-hm/Project/work/ops/services/next-stripe-bugfix/service-pack/facts.yaml`
- 必要なら `tone-profile.yaml`

### 2. boundaries 参照へ寄せるもの
- purchased / closed で外部共有前提で進めていないか
- 外部共有を止める時に代替物まで示しているか
- 返金・設定変更・デプロイなどの操作に触れる時、誰が行うかが曖昧でないか

置き先:
- bugfix / handoff 両サービスの `boundaries.yaml`

### 3. routing-playbooks 参照へ寄せるもの
- UI状態の確認と、エラー内容の共有を混同していないか
- 資料依頼が `送れるか` `出せるか` のような能力確認っぽくなっていないか
- 相手が1テーマだけ書いているのに、条件分岐の受け方をしていないか
- `〜件でしたら、不具合1件として対応できます。` が残っていないか
- 相手が `決済とは関係ない` と明言しているのに scope を広く見せていないか
- buyer の主質問が対応可否で、その場で受けられる内容なのに、確信度報告へ逃げていないか
- scope 境界の根拠と料金結論を1文に直結していないか

置き先:
- bugfix / handoff の `routing-playbooks.yaml`

### 4. state-schema 参照へ寄せるもの
- delivered / closed 以降で unresolved thread の行き先が曖昧になっていないか
- 返金不安や secondary symptom を扱う時に current thread / next promised action が読めるか

置き先:
- bugfix / handoff の `state-schema.yaml`

## 先に動かす順番
1. bugfix facts / phase_rules に寄せるもの
2. boundaries に寄せるもの
3. routing-playbooks に寄せるもの
4. state-schema に寄せるもの
5. 最後に compat-only をもう一段圧縮する

## ゴール
- `compat-only residual` が、service 固有本文の置き場ではなく
  - 仕上げ運用
  - wording の移行安全網
  - ごく少数の互換保険
 だけになること
