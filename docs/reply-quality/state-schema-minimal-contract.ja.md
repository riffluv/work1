# State Schema Minimal Contract

## 目的
- multi-turn で崩れやすい `secondary thread` と `約束した次アクション` を、最小項目だけで保持する
- wording ではなく state の不足で起きる取りこぼしを減らす

## 最小で持つべきもの

### 1. primary symptom
- 今回いちばん先に解く論点

### 2. secondary thread
- 主論点とは別に会話へ入ってきた論点
- 最低でも次を持つ
  - `disposition`
  - `return_timing` または `required_input`

### 3. promised next action
- こちらが次に返すと約束したこと
- 最低でも次を持つ
  - `action`
  - `return_timing`

### 4. unresolved thread
- まだ閉じていない論点
- 最低でも次を持つ
  - `planned_resolution`
  - `return_timing`

## 判断原則
- `あとで見ます` だけでは state 不足
- `same_cause_check` だけでは state 不足
- `return_timing` がない約束は、delivery / close で宙浮きしやすい

## 実務上の最低ライン
- secondary thread が出たら、その場で `disposition` を付ける
- delivery に入る前に、secondary thread へ `return_timing` か `required_input` のどちらかを付ける
- close に進む前に、unresolved thread の `planned_resolution` と `return_timing` を空にしない

## playbook との接続
- `routing-playbooks` は、言い回しの型だけでなく `state_contract` を持つ
- `state_contract` では少なくとも次を固定する
  - `promised_next_action.action`
  - `promised_next_action.return_timing`
  - secondary thread が出やすい route では `default_disposition`
  - secondary thread を返すために要る `default_required_input`
- これにより、`same cause か確認する` のような文章ルールだけで終わらず、state の初期値まで route ごとに決められる
