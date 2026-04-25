# Service-Pack Runtime Interface

## 目的
- 共通 runtime が `service-pack` のどの層を、どの順で参照するかを固定する
- `service理解` と `reply スタイル` を混ぜず、reply 生成と reviewer 判定の責務を分ける
- `service page -> service-pack -> reply` のどこでズレたかを切り分けやすくする

## 適用対象
- `bugfix-15000`
- `handoff-25000`
- 今後追加する service-pack も同じ順序で読む

## runtime の読む順
1. `facts.yaml` / `boundaries.yaml`
2. `decision-contract.yaml` / `evidence-contract.yaml`
3. `routing-playbooks.yaml`
4. `state-schema.yaml`
5. `seeds.yaml` / `tone-profile.yaml`

補足:
- 公開サービスページは runtime が毎回直接読む前提ではない
- 公開ページを基準に pack を保守し、runtime は pack を読む
- 公開ページとの整合は fidelity 監査と regression source で確認する
- ただし、価格・公開状態・納品物・FAQ・公開約束に疑義がある場合は、`service-registry.yaml` の `public` と `source_of_truth` を最上位として確認する

## 層ごとの責務

### 1. facts / boundaries
- 価格
- scope unit
- deliverables
- public/private
- hard no
- 境界原則

runtime の使い方:
- `このサービスで売るものか`
- `この相談をここで止めるべきか`
- `外向けに出してよい内容か`
を判定する
- `public:false` の service は、内部比較には使えても、外向け返信で service 名・価格・購入導線を出さない

### 2. decision / evidence
- same / different / undecidable
- unknown cause gate
- additional work policy
- final confirmation owner
- phase ごとの minimum ask
- first-class evidence

runtime の使い方:
- `どう判断するか`
- `どこで止まるか`
- `何を最低限聞くか`
を決める

### 3. routing-playbooks
- よくある入口の route
- must_say
- ask_shape
- state_contract

runtime の使い方:
- `この相談なら何を先に返すか`
- `secondary thread をどう置くか`
- `promised next action を何にするか`
を決める

### 4. state-schema
- primary / secondary thread
- unresolved thread
- promised next action
- return timing
- required input

runtime の使い方:
- multi-turn で `何が未回収か`
- `いつ返す約束か`
- `何が足りないか`
を保持する

### 5. seeds / tone
- 言い回しの型
- 温度感
- brevity / directness / acknowledgment の傾向

runtime の使い方:
- 意味が決まったあとに、どう自然化するかだけに使う
- service理解や契約判断の根拠には使わない

## Writer が読む最小セット
- `facts.yaml`
- `boundaries.yaml`
- `decision-contract.yaml`
- `evidence-contract.yaml`
- 該当 route の `routing-playbooks.yaml`
- 現在 thread の必要 state
- `seeds.yaml`
- `tone-profile.yaml`

Writer の原則:
- facts / decision / evidence が先
- seeds / tone は後
- `seeds` に引っ張られて contract を曲げない

## Reviewer が読む最小セット
- `facts.yaml`
- `boundaries.yaml`
- `decision-contract.yaml`
- `evidence-contract.yaml`
- `routing-playbooks.yaml`
- `state-schema.yaml`
- 必要なら current state
- `L1 / L2 self-check`

Reviewer の原則:
- service 固有判断は `decision / evidence` を first-class に見る
- `routing / state` は補助
- `seeds / tone` は wording drift 確認に限る

## 典型的な切り分け

### page を直す
- 公開文面や FAQ 自体が曖昧
- public contract が不足している

### facts / boundaries を直す
- 価格、納品物、禁止事項、公開状態の保持が弱い

### decision / evidence を直す
- same-cause 判定がぶれる
- formal delivery gate がぶれる
- minimum ask がぶれる
- first-class evidence が足りない

### routing / state を直す
- route は合っているのに secondary thread が浮く
- promised next action の timing が崩れる

### seeds / tone を直す
- 契約意味は合っているのに wording がずれる
- runtime asset が buyer の温度に合っていない

## 最小運用ルール
- 新しい service-pack を入れたら、まず `facts / boundaries / decision / evidence` があるかを見る
- `routing / state` は、その契約を返信運用へ落とすためにだけ足す
- `seeds / tone` は最後に足す
- fidelity 監査は `service page -> decision / evidence -> reply` の意味落ちを見る

## 完了条件
- Writer が `service理解` のために `seeds / tone` を見なくてよい
- Reviewer が same / different / undecidable と minimum ask を `decision / evidence` だけで判定できる
- multi-turn の secondary thread を `state` と `routing state_contract` で回収できる
