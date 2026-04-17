# self-check 再編方針

## 目的
- 現行の `/home/hr-hm/Project/work/docs/coconala-reply-self-check.ja.md` を、`L1 / L2 / L3` 前提の構造へ段階的に再編する
- 既存の返信品質を落とさず、`service-pack` を前提にした runtime へ移行する
- `self-check` を「知識の保存場所」から「品質判定と asset 参照の validator」へ変える

## 前提
- `L1`
  - universal な会話品質
- `L2`
  - 受託返信としての運び方
- `L3`
  - サービス固有知識。`service-pack` で持つ

関連ファイル:
- `/home/hr-hm/Project/work/docs/reply-quality/self-check-l1-minimal-universal.ja.md`
- `/home/hr-hm/Project/work/docs/reply-quality/self-check-l2-domain-minimal.ja.md`
- `/home/hr-hm/Project/work/docs/reply-quality/self-check-l3-extraction-map.ja.md`
- `/home/hr-hm/Project/work/ops/services/next-stripe-bugfix/service-pack/`
- `/home/hr-hm/Project/work/ops/services/handoff-25000/service-pack/`

## 目標の終状態

### 1. `coconala-reply-self-check.ja.md` に残すもの
- `L1` と `L2` に還元できない residual check
- `L3` asset を正しく参照しているかの validator
- migration 途中の互換用メモ

### 2. `coconala-reply-self-check.ja.md` から抜くもの
- 価格の固定値そのもの
- サービス固有の scope 説明本文
- hard no の具体列挙本文
- route ごとの must-say の本文
- 納品物の具体名
- service 固有の fear handling の本文

### 3. 正本の役割分担
- `L1`
  - 会話品質の最小 gate
- `L2`
  - phase / hold / refusal / progress の運び
- `L3`
  - service-pack 参照 validator
- `service-pack`
  - facts / boundaries / routing-playbooks / state-schema / seeds / tone-profile

## 再編の原則

### 原則 1. 知識本文を runtime に残さない
- `self-check` が価格や scope を直接説明し続けない
- 本文知識は `service-pack` に置く

### 原則 2. runtime は判定だけを担う
- `self-check` は
  - 読む順
  - 落とし穴
  - asset 参照漏れ
を判定する

### 原則 3. 互換性を壊さず薄くする
- 一気に全置換しない
- まず `参照型` に置き換え、動作を見てから本文を削る

### 原則 4. multi-turn は prose で抱え込みすぎない
- `secondary_symptoms`
- `promised_next_action`
- `unresolved_threads`
は `state-schema` 前提で見る

## 移行フェーズ

### Phase 1. service-pack を受け皿にする
状態:
- 完了

内容:
- bugfix / handoff の `service-pack` を作る
- `L3` 抽出候補を切る

### Phase 2. self-check を参照型へ寄せる
状態:
- 進行中

内容:
- `bugfix` と `handoff` の主要 `L3` を `asset 参照 validator` に置き換える
- 本文知識を減らし、`facts / boundaries / routing / state` を見る形に寄せる

### Phase 3. L1 / L2 を独立読本として固定する
状態:
- 完了

内容:
- `L1 minimal universal`
- `L2 domain minimal`
を separate docs として固定する

### Phase 4. 現行 self-check を compatibility layer に縮約する
状態:
- 未着手

内容:
- `coconala-reply-self-check.ja.md` から、L1/L2 の重複説明を減らす
- `L3` 本文をさらに薄くし、参照漏れ確認に寄せる
- 位置づけを「巨大ルール集」から「統合 validator」へ変える

### Phase 5. legacy 依存を外す
状態:
- 未着手

内容:
- 新規運用は `L1 -> L2 -> L3` を正順で使う
- monolith は residual / compatibility 用に限定する

## 具体的に残すべきチェック

### 残す
- cross-layer の整合確認
  - `L1` は通るが `L3` で落ちる時の切り分け
- service-pack 参照漏れ
  - facts を見ずに価格を断定した
  - routing-playbook を見ずに secondary disposition を書いた
- migration 中の safety net
  - 旧パターンが再発していないか

### 減らす
- 「15,000円には〜を含む」のような本文説明
- 「25,000円では〜」のような handoff 固有文
- hard no の具体本文列挙
- `.md` 納品や private 運用の直接説明

## 実装順
1. bugfix / handoff の `L3` 参照化を完了させる
2. `coconala-reply-self-check.ja.md` 内の `L1/L2` 重複説明に印を付ける
3. `L1 / L2` docs 参照前提の短い統合前書きを作る
4. monolith 内の `L3` 本文をさらに削る
5. regression を 5件バッチ / limit / multi-turn で確認する

## exit 条件
- bugfix / handoff の主要 `L3` が `service-pack` 側にある
- `L1` と `L2` だけで、service 固有知識なしの監査が成立する
- `coconala-reply-self-check.ja.md` が pricing / scope / deliverables の本文を主に抱えていない
- multi-turn の unresolved thread を `state-schema` 前提で扱えている
- 新サービス導入時に、monolith を直接増築しなくても回せる

## 現時点の判断
- ここまでで、`service-pack` は受け皿として成立した
- `L1 / L2` も独立した
- 次の実作業は、現行 monolith を `compatibility layer` に縮約すること

## 次の一手
- `coconala-reply-self-check.ja.md` の章ごとに
  - `L1`
  - `L2`
  - `L3`
  - `compat-only`
のタグ付け表を作る
- その表をもとに、実際の削減順を切る
