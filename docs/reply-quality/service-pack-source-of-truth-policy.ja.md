# Service-Pack Source-of-Truth Policy

## 目的
- `service-pack` の中で、何がサービス理解の正本で、何が運用補助なのかを固定する
- `service page -> service-pack -> reply` で意味が落ちた時に、どこを直すべきか切り分けやすくする

## 優先順位
0. `service-registry.yaml` の `public` と `source_of_truth`
1. 公開サービスページ
2. `facts.yaml` / `boundaries.yaml`
3. `decision-contract.yaml` / `evidence-contract.yaml`
4. `routing-playbooks.yaml` / `state-schema.yaml`
5. `seeds.yaml` / `tone-profile.yaml`

## 層ごとの役割

### 0. service-registry
- 外向けに出してよい service かどうかの最上位
- `public:false` の service は、source_of_truth が存在しても外向け返信で service 名・価格・購入導線を出さない
- 価格、納品物、FAQ、公開約束に疑義がある時は、`service-registry.yaml` の `source_of_truth` をたどって確認する

### 1. 公開サービスページ
- buyer に公開している契約本文の正本
- 価格、納品物、FAQ、回答例、公開約束はここが最上位
- pack がこれと矛盾したら、まず page を基準に直す

### 2. facts / boundaries
- 公開ページから直接引ける事実と境界
- `何を売るか`
- `何を売らないか`
- `何を断るか`
を保持する

### 3. decision / evidence
- 公開ページだけでは平文でしか存在しない判断ルールを構造化する
- `どう判断するか`
- `どこで止まるか`
- `何を最低限聞くか`
を保持する
- L3 validator は、この層を service 理解の核として優先参照する

### 4. routing / state
- 会話運用の補助
- `どう返すか`
- `どの route で進めるか`
- `secondary thread をどう保持するか`
を持つ
- これは source-of-truth ではなく、契約を返信運用へ落とすための中間層

### 5. seeds / tone
- runtime asset
- `どういう言い回しにするか`
- `どういう温度感で出すか`
を持つ
- semantic fidelity の正本ではない
- service page と矛盾したら、先に seeds / tone を直す

## 修正先の判断

### page を直す
- 公開文面・FAQ・回答例の意味自体が曖昧
- public contract に主張が存在しない

### facts / boundaries を直す
- 価格、納品物、禁止事項、公開状態の保持が弱い

### decision / evidence を直す
- same-cause 判定
- 原因不明時の gate
- final confirmation owner
- phase ごとの minimum ask
のどれかが曖昧

### routing / state を直す
- 返し方は合っているのに、secondary thread が浮く
- promised next action の timing が崩れる
- route ごとの初期 state が弱い

### seeds / tone を直す
- 契約意味は合っているのに、言い回しがずれる
- style に引っ張られて判断が弱くなる

## 運用ルール
- `service 理解` と `reply スタイル` を混ぜない
- `routing / state` は buyer 向け契約の正本にしない
- `seeds / tone` は監査対象に含めてもよいが、契約判断の根拠にはしない
- 公開前サービスでは、public false の前提が page より先に外へ漏れないようにする
