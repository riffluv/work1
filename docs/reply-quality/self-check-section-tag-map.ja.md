# self-check 章タグ付け表

## 目的
- 現行の `/home/hr-hm/Project/work/docs/coconala-reply-self-check.ja.md` を、章単位で `L1 / L2 / L3 / compat-only` に分解する
- 実際にどの章から薄くしていくかの順番を固定する
- `self-check-recomposition-plan.ja.md` を実行に移すための中間表にする

## タグ定義

### `L1`
- service 固有知識なしで成立する universal check
- 会話品質、既出情報、主質問、promise 回収、thread continuity

### `L2`
- 受託返信としての進め方
- prequote / quote_sent / purchased / delivered / closed の運び
- 断り方、保留の出し方、進捗共有、buyer の判断段階

### `L3`
- service-pack を見ないと判定できないもの
- 価格、scope、public/private、route 固有、deliverables、service 固有 secondary disposition

### `compat-only`
- いまはモノリスに残すが、最終的には縮小・削除対象
- 旧ルールとの互換、移行中の safety net、章横断の残差

## 章ごとの判定

### 1. `## 最小5項目`
- 現状タグ:
  - `L1`: 主質問
  - `L3`: 価格・スコープ・秘密情報
  - `compat-only`: Ban 語の圧縮まとめ
- 方針:
  - この章は最終的に廃止寄り
  - `L1` は `self-check-l1-minimal-universal.ja.md`
  - `L3` は service-pack 参照 validator
  - 互換上の入り口説明だけ残す

### 2. `## 送信前チェック`
- 現状タグ:
  - `L1`: 主質問、既出情報、open loop、事実ズレ、slot-fill、ban、promise
  - `L2`: phase 運用、hold、buyer の判断段階、断り方、進捗、delivered / closed の防御回避
  - `L3`: bugfix / handoff 固有の価格、scope、public/private、routing、deliverables、boundary
  - `compat-only`: L1/L2/L3 が未分離のまま並んでいる統合チェック
- 方針:
  - 最重要の再編対象
  - この章は最終的に `L1 + L2 + L3 validator の統合入口` だけ残す
  - 個々の本文ルールは縮約

### 3. `## Ban チェック`
- 現状タグ:
  - `L1`: internal 語、空語、オウム返し、slot-fill の再発
  - `compat-only`: ban の具体列挙が monolith 側にも残っている点
- 方針:
  - 中核は `L1`
  - ban 一覧の source of truth は別ファイル
  - ここは `L1` の短い gate として残しやすい

### 4. `## ケース別チェック`
- 現状タグ:
  - この親見出し自体は `compat-only`
- 方針:
  - 段階的に空洞化する
  - 実体は下位節へ再配置

#### 4-1. `### 見積り初回`
- 現状タグ:
  - `L2`: prequote ask / answer order / hold の運び
  - `L3`: bugfix handoff の価格・scope・最小 ask・ZIP 抑制・高確度案件の扱い
  - `compat-only`: 移行途中の混在
- 方針:
  - 共通の prequote 運びは `L2`
  - bugfix / handoff 固有は `L3`
  - この節は大きく薄くできる

#### 4-2. `### 感情注意`
- 現状タグ:
  - `L1`: slot-fill、buyer 語彙、感情のなぞりすぎ回避
  - `L2`: angry / anxious / mixed に対する受託返信としての温度運用
  - `L3`: bugfix 固有の返金・保証・危険操作要求
- 方針:
  - かなり `L1 + L2` に分けられる
  - service 固有恐れ対応だけ `L3`

#### 4-3. `### quote_sent`
- 現状タグ:
  - `L2`: prequote に戻らない、価格了承後の運び
  - `L3`: fixed price、service 固有 price-answer shape、handoff 固有 scope confirm
- 方針:
  - phase 運用は `L2`
  - 定額範囲と購入導線は `L3`

#### 4-4. `### closed 後再発`
- 現状タグ:
  - `L2`: closed 後の進め方、再発時の返し方
  - `L3`: repeat / discount / refund / same-cause disposition
- 方針:
  - service 固有 playbook の比重が高い
  - `L3` へかなり逃がせる

#### 4-5. `### 範囲外`
- 現状タグ:
  - `L2`: 断る時の自然さ、閉じすぎ防止
  - `L3`: 何が hard no / service mismatch か
- 方針:
  - 断り方は `L2`
  - 対象外の中身は `L3`

#### 4-6. `### 境界ケース`
- 現状タグ:
  - `L2`: mixed case の会話運び、buyer に判断を返さない routing
  - `L3`: bugfix vs handoff、Stripe以外、public/private、サービス混在
- 方針:
  - ルーティング思想は `L2`
  - route label と service 固有 must-say は `L3`

#### 4-7. `### purchased / closed`
- 現状タグ:
  - `L2`: 進捗共有、保留、複数話題の優先順位、secondary の行き先
  - `L3`: purchased の related secondary、closed repeat/discount、service 固有保証/返金境界
- 方針:
  - phase 運びは `L2`
  - disposition と境界は `L3`

#### 4-8. `### handoff 系`
- 現状タグ:
  - `L2`: black-box 案件の運び、非エンジニア向け説明の運び、段階対応
  - `L3`: 25,000円、主要1フロー、`.md` 納品、private、修正別対応、deeper memo
- 方針:
  - handoff 固有知識の比率が高い
  - `L3` 抽出の優先節

## 削減優先順位

### 優先 1
- `### handoff 系`
- `### closed 後再発`
- `### quote_sent`
- 理由:
  - L3 比率が高く、service-pack へ逃がす効果が大きい

### 優先 2
- `### 見積り初回`
- `### purchased / closed`
- `### 境界ケース`
- 理由:
  - L2 と L3 の混在を剥がすと runtime がかなり見やすくなる

### 優先 3
- `### 感情注意`
- `### 範囲外`
- 理由:
  - L1 / L2 への還元が多く、最後に整理した方がきれい

### 優先 4
- `## 最小5項目`
- `## Ban チェック`
- 理由:
  - 最終形に近い短い gate にしやすいので、後から圧縮できる

## 最終イメージ

### `coconala-reply-self-check.ja.md`
- 統合入口
- `L1 / L2 / L3` の見る順
- residual compat check

### `self-check-l1-minimal-universal.ja.md`
- 会話品質の正本

### `self-check-l2-domain-minimal.ja.md`
- phase と受託返信運用の正本

### `service-pack/*`
- L3 の正本

## 次の実作業
1. `### handoff 系` から、本文知識と validator を切り分ける
2. `### closed 後再発` と `### quote_sent` を同様に薄くする
3. `送信前チェック` は最後に統合入口として縮約する
