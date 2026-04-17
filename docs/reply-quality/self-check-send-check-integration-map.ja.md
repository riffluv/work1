# 送信前チェック 統合入口マップ

## 目的
- `/home/hr-hm/Project/work/docs/coconala-reply-self-check.ja.md` の `## 送信前チェック` を、巨大ルール集ではなく `L1 / L2 / L3` の統合入口として再編する
- 一気に削って regression を起こさず、何を残し何を外へ逃がすかを先に固定する

## 現状の問題
- `送信前チェック` に
  - universal な会話品質
  - 受託返信の phase 運用
  - bugfix / handoff 固有の価格・scope・公開状態
  - migration 中の safety net
が混在している
- そのため、`self-check` 自体が知識の保存場所になりやすい

## 終状態のイメージ

### `送信前チェック` に残すもの
- `L1` を見る前の入口
- `L2` を見る前の入口
- `L3` を見る前の入口
- cross-layer の整合
- migration 中の residual compat check

### `送信前チェック` から抜くもの
- bugfix / handoff の価格本文
- 具体的な納品物本文
- hard no の本文列挙
- route ごとの must-say 本文
- service 固有 anxiety handling 本文

## 入口として残すべき4ブロック

### 1. primary answer integrity
残す:
- 主質問に答えているか
- `primary_question_id` に対応しているか
- 最初の answer-bearing section がずれていないか
- explicit questions を落としていないか
- answer map と本文が一致しているか

位置づけ:
- `L1` 入口

### 2. phase integrity
残す:
- `phase_act` と文面骨格の整合
- prequote が購入後動詞へ滑っていないか
- purchased / delivered / closed が受付文面へ戻っていないか
- quote_sent が prequote に戻っていないか

位置づけ:
- `L2` 入口

### 3. evidence / ask integrity
残す:
- ask が本当に必要か
- ask 数が過剰でないか
- 既出情報の聞き直しがないか
- minimum evidence を壊していないか
- prequote の ask が重くなりすぎていないか

位置づけ:
- `L1 + L2` の橋渡し

### 4. asset reference integrity
残す:
- facts を見ずに価格や scope を断定していないか
- routing-playbook を見ずに route 固有の言い回しを出していないか
- state-schema を見ずに unresolved thread を閉じていないか
- public/private と矛盾していないか

位置づけ:
- `L3` 入口

## compat-only として当面残すもの
- 旧 ban 語の再発 safety net
- wording 崩れの保険
- 直近で問題になった運用癖の見張り

例:
- `もちろんです`
- `はい、`
- `形です`
- `この文面だけだと`
- `確認したいです`

理由:
- まだ `L1 / L2 / ng-expressions` 側だけで完全に回るとは言い切れないため

## 先に外へ逃がすもの

### facts / boundaries
- 価格の固定値
- base price の扱い
- deliverables
- hard no 本文
- public/private の具体説明

### routing-playbooks
- bugfix-first
- repeat / refund / discount
- handoff scope confirm
- purchased related secondary

### state-schema
- promised_next_action
- secondary_symptoms
- unresolved_threads
- repair_as_additional_work

## `送信前チェック` の再編順

### Step 1
- 冒頭に「L1 / L2 / L3 の順で見る統合入口」であることを明記する

### Step 2
- `primary answer integrity`
- `phase integrity`
- `evidence / ask integrity`
- `asset reference integrity`
の4ブロックへ整理する

### Step 3
- bugfix / handoff 固有の本文知識を削って、`service-pack と矛盾していないか` へ置き換える

### Step 4
- compat-only 項目を最後尾へ追いやり、残量を見ながら削る

## 削りすぎ防止ライン
- 主質問への直答チェックは薄くしない
- phase の逆戻りチェックは薄くしない
- unresolved thread の行き先チェックは薄くしない
- service-pack 参照漏れチェックは薄くしない

## ここでまだやらないこと
- `送信前チェック` 全文の一括リライト
- wording レベルの全面整理
- L1/L2 docs との完全重複除去

## 次の一手
1. `送信前チェック` 冒頭に、`L1 -> L2 -> L3 -> compat` の順で見ることを明記する
2. 本文の最初の 20〜30 行を、4ブロック構造へ寄せる
3. regression を見ながら後半を削る
