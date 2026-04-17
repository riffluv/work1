# self-check L3 抽出候補（bugfix-15000）

## 目的
- `/home/hr-hm/Project/work/docs/coconala-reply-self-check.ja.md` に残っている `bugfix-15000` 固有の `L3` 文を、実際にどの asset へ移すかを具体的に固定する
- 抽象マップではなく、`どの行を / どこへ / どう薄くするか` の最初の抜き取り単位を作る

## 前提
- 対象サービス:
  - `/home/hr-hm/Project/work/ops/services/next-stripe-bugfix/service-pack/`
- ここで扱うのは `bugfix-15000` 固有の価格 / 境界 / route / state
- ban 表現、slot-fill、否定先置き、buyer 語彙保持のような会話品質は `L1/L2` 側に残す

## 抽出候補一覧

### 1. 15,000円に含む範囲
- self-check:
  - `223`
  - `235`
- 現在の意味:
  - `15,000円には原因切り分けと修正可否確認を含む`
  - `原因不明のまま15,000円だけ取られる` 不安への返し
- 移し先:
  - `facts.yaml`
  - 参照: `/home/hr-hm/Project/work/ops/services/next-stripe-bugfix/service-pack/facts.yaml`
- 薄くした後の self-check:
  - `価格不安への返答が、service facts の included scope と矛盾していないか`

### 2. 追加料金は自動発生しない
- self-check:
  - `19`
  - `46`
  - `241`
- 現在の意味:
  - 別原因や追加料金を、相手が不安視していない段階で前に出しすぎない
  - 出す時も `自動発生` に読ませない
- 移し先:
  - `boundaries.yaml`
  - `routing-playbooks.yaml`
- 薄くした後の self-check:
  - `追加料金境界の返しが、boundary_principles と route must_say を外していないか`

### 3. bugfix は同一原因1件で扱う
- self-check:
  - `207`
  - `363`
- 現在の意味:
  - bugfix を `1フロー整理` のサービスのように誤説明しない
  - `同一原因 / 別原因` の固い繰り返しを避けつつ境界は守る
- 移し先:
  - `facts.yaml`
  - `boundaries.yaml`
- 薄くした後の self-check:
  - `scope unit の説明が service facts と矛盾していないか`

### 4. 価格質問の三択
- self-check:
  - `215`
  - `218`
- 現在の意味:
  - `15,000円でいけるか` への返答は
    - `進められる`
    - `まだ言い切れないので1点確認`
    - `その料金では受けない`
    の3択に寄せる
- 移し先:
  - `routing-playbooks.yaml`
- 薄くした後の self-check:
  - `価格主質問への返答が、bugfix quote playbook の answer shape から外れていないか`

### 5. prequote で ZIP を前のめり要求しない
- self-check:
  - `25`
  - `127`
  - `129`
  - `130`
  - `244`
  - `271`
- 現在の意味:
  - prequote で ZIP やコード一式を当然視しない
  - 必要でも構成確認までに止める
- 移し先:
  - `facts.yaml`
  - `boundaries.yaml`
- 薄くした後の self-check:
  - `prequote の ask が、phase_rules.prequote.can_ask_for / must_not_do を踏み越えていないか`

### 6. prequote では画面・文言・日時までを最小 ask にする
- self-check:
  - `127`
  - `271`
- 現在の意味:
  - 見積り相談では、症状・環境・エラー文で判断できる限り軽い ask に寄せる
- 移し先:
  - `facts.yaml`
  - `routing-playbooks.yaml`
- 薄くした後の self-check:
  - `prequote ask が bugfix facts の minimum evidence と一致しているか`

### 7. bugfix 起点を崩さない boundary
- self-check:
  - `207`
  - `326`
- 現在の意味:
  - 現に不具合が出ていて修正希望なら bugfix 起点で扱う
  - 二重決済や重複処理では返金より先に停止・切り分けを返す
- 移し先:
  - `boundaries.yaml`
  - `routing-playbooks.yaml`
- 薄くした後の self-check:
  - `boundary routing が bugfix-first 原則と矛盾していないか`

### 8. quote_sent の範囲確認
- self-check:
  - `417`
  - `418`
  - `419`
- 現在の意味:
  - 公開 bugfix は定額前提で、`見積もりを返す` 文に戻さない
- 移し先:
  - `facts.yaml`
  - `routing-playbooks.yaml`
- 薄くした後の self-check:
  - `quote_sent の closing が bugfix public facts と矛盾していないか`

### 9. closed 後の repeat / discount
- self-check:
  - `433`
  - `435`
- 現在の意味:
  - 同サービス内の別不具合でも一律値引きしない
  - ただし再審査っぽい closing に戻さない
- 移し先:
  - `routing-playbooks.yaml`
- 薄くした後の self-check:
  - `closed repeat / discount の返答が bugfix playbook から外れていないか`

### 10. refund の扱い
- self-check:
  - `158`
  - `186`
  - `187`
  - `188`
  - `328`
  - `329`
  - `330`
  - `331`
- 現在の意味:
  - 返金をこちらが決めるように読ませない
  - 返金不安では `先に判断できること` を返す
- 移し先:
  - `routing-playbooks.yaml`
  - `boundaries.yaml`
- 薄くした後の self-check:
  - `返金の返しが、bugfix repeat / refund playbook の scope-first 原則を外していないか`

### 11. purchased secondary symptom の優先順位
- self-check:
  - `441`
- 現在の意味:
  - delivery / close までに、副症状の行き先を必ず明示する
- 移し先:
  - `state-schema.yaml`
  - 参照: `/home/hr-hm/Project/work/ops/services/next-stripe-bugfix/service-pack/state-schema.yaml`
- 薄くした後の self-check:
  - `unresolved_threads と secondary_symptoms の行き先が空のまま close へ進んでいないか`

### 12. delivered の影響不安
- self-check:
  - `441` に関連
  - delivered 文脈の `secondary symptom` / `影響確認` 全般
- 現在の意味:
  - 触っていない箇所でも、関連テンプレートや分岐で見え方が変わることを返す
- 移し先:
  - `routing-playbooks.yaml`
  - `seeds.yaml`
- 薄くした後の self-check:
  - `delivered impact check の route must_say を落としていないか`

### 13. hard no: 直接push / 本番デプロイ / 本番ログイン
- self-check:
  - hard-no 群のうち bugfix に直接効くもの
- 現在の意味:
  - bugfix での実務境界
- 移し先:
  - `boundaries.yaml`
- 薄くした後の self-check:
  - `scope/contract を断る内容が、boundaries.hard_no と矛盾していないか`

### 14. success-rate fear
- self-check:
  - `235`
  - 価格不安と `調べただけで終わる` 不安の接点
- 現在の意味:
  - 保証はしないが、15,000円で返る価値を先に示す
- 移し先:
  - `routing-playbooks.yaml`
  - `seeds.yaml`
- 薄くした後の self-check:
  - `成功率不安への返答が、bugfix success-rate playbook と canonical seed を外していないか`

### 15. purchased / delivered の open loop 回収
- self-check:
  - `441`
  - purchased / delivered の secondary symptom 一般
- 現在の意味:
  - `あとで見ます` のまま終わらせない
- 移し先:
  - `state-schema.yaml`
- 薄くした後の self-check:
  - `promised_next_action と unresolved_threads が close 前に空振りしていないか`

## 先に抜きやすい 10 個
- 1. 15,000円に含む範囲
- 2. 追加料金は自動発生しない
- 3. bugfix は同一原因1件で扱う
- 5. prequote で ZIP を前のめり要求しない
- 6. prequote 最小 ask
- 8. quote_sent の範囲確認
- 9. closed 後の repeat / discount
- 10. refund の扱い
- 11. purchased secondary symptom の優先順位
- 15. purchased / delivered の open loop 回収

理由:
- 既に `service-pack` 側へ置き場がある
- 既存 `routing-playbooks.yaml` と `state-schema.yaml` に近い形で受けられる
- self-check から直接文言を削っても regression を見やすい

## まだ self-check に残すもの
- `同一原因 / 別原因` の語の固さそのもの
- `形` `自然です` などの ban 表現
- buyer 語彙の保持
- 否定先置き
- slot-fill

理由:
- これらは service 固有知識ではなく、runtime quality の問題だから

## 次の実作業
1. 上の `先に抜きやすい 10 個` について、self-check 側の文を `asset 参照 validator` に書き換える
2. まずは bugfix だけで regression を見る
3. 問題なければ handoff 側にも同じ粒度で抽出候補を作る

## 実装済み（first pass）
次の項目は、すでに `self-check` を asset 参照型へ置き換えた。

- 1. 15,000円に含む範囲
- 2. 追加料金は自動発生しない
- 3. bugfix は同一原因1件で扱う
- 4. 価格質問の三択
- 5. prequote で ZIP を前のめり要求しない
- 6. prequote 最小 ask
- 8. quote_sent の範囲確認
- 9. closed 後の repeat / discount
- 10. refund の扱い
- 11. purchased secondary symptom の優先順位
- 15. purchased / delivered の open loop 回収

残りは、会話品質と混ざっている L2/L3 境界のものが中心。
