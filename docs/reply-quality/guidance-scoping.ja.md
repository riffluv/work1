# 返信改善 Guidance Scoping（reply-only）

更新日: 2026-04-11

## 目的

- 返信改善を入れる前に、`どこにだけ効かせるか` を先に固定する
- 良い改善が別 route / 別 state / 別 service へ漏れてノイズになるのを防ぐ
- 監査で見つけた指摘を、`採用するか` だけでなく `適用域をどこまでにするか` で判断できるようにする

## 先に切る4軸

### 1. 反映レーン

- `reply-only`
  - トークルーム返信、見積り返信、途中共有、正式納品メッセージ
- `common`
  - 返信文と納品物本文の両方で再発する改善
- `delivery-only`
  - 添付納品物の見出し、結論文、確認/推定/未確認の整理

原則:
- 日本語の柔らかさや温度感の調整は、まず `reply-only`
- `delivery-only` へ自動流用しない

### 2. route

- `service`
  - サービスページから来た相談
- `profile`
  - プロフィール経由の相談
- `message`
  - メッセージ経由の相談
- `talkroom`
  - 購入後トークルーム

原則:
- 書き出しや受け方は route 依存が大きい
- route 依存ルールを共通化しすぎない

### 3. state

- `prequote`
- `quote_sent`
- `purchased`
- `predelivery`
- `delivered`
- `closed`

原則:
- 動詞、時制、約束、質問の重さは state 依存が大きい
- `phase漏れ` を止めるルールは、必ず state 指定で入れる

### 4. service / case_type

- 公開 bugfix
- 非公開 handoff
- boundary
- after_purchase
- after_close

原則:
- bugfix の範囲説明、handoff の資料案内、boundary の段階提案は混ぜない
- 非公開 service の導線や価格は、外向け共通ルールへ入れない

## 適用判断の順番

1. その指摘は `reply-only / common / delivery-only` のどれか
2. どの route で再発しているか
3. どの state でだけ危険か
4. どの service / case_type にだけ効かせるべきか

この4つが切れない改善は、いったん恒久反映しない。

## よくある改善の置き場所

### prequote だけに効かせるもの

- 未受領段階で `確認します` と書かない
- こちらから ZIP を標準要求しない
- `この内容は / この内容なら` を prequote 冒頭で固定しない
- 主質問が対応可否だけの時、価格を先頭へ出さない

戻し先:
- `prequote policy`
- `prequote ops`
- `self-check`

### purchased 以降にだけ効かせるもの

- `いま見ている範囲` の現在地を1文入れる
- 次回共有時刻を入れる
- 即答できる論点と確認後回答を分ける

戻し先:
- `reply-bugfix`
- `self-check`

### bugfix にだけ効かせるもの

- `不具合1件` の言い方
- `同一原因 / 1フロー / 1エンドポイント` の境界説明
- 価格・追加料金・別原因の扱い

戻し先:
- `service facts`
- `scope matrix`
- `reply-bugfix`

### handoff にだけ効かせるもの

- 一式資料の受け方
- 主要1フローの整理案内
- 非公開運用中の外向けクロージング

戻し先:
- handoff skill / docs

### 全 route に共通しうるもの

- 意味接続破綻
- 明らかな内部語漏れ
- テンプレ臭が強い固定語尾

戻し先:
- `NG表現`
- `naturalizer`
- `gold replies`

## 反映してよい改善の条件

- 再発性がある
- 実務ノイズを増やさない
- 主質問への直答を弱めない
- 既存の hard constraints と衝突しない
- 適用域を4軸で説明できる

## 反映を保留する改善

- 単発の好み
- ある1ケースだけで自然に見える言い換え
- 別 state へ漏れると壊れる可能性があるもの
- 外部AIの一般論だが、今の運用文脈では未検証なもの

## 例

### 例1

指摘:
- `APIの500エラーは確認できます`

分類:
- `QA-03 phase漏れ`

scope:
- `reply-only`
- `prequote`
- `bugfix`

戻し先:
- `coconala-prequote-commitment-policy.ja.md`
- `coconala-prequote-ops-ja`
- `coconala-reply-self-check.ja.md`

### 例2

指摘:
- `お問い合わせが増えている状況とのこと、この内容なら不具合1件として対応できます`

分類:
- `QA-05 意味接続破綻`

scope:
- `reply-only`
- route 共通
- 主に `prequote`

戻し先:
- `ng-expressions.ja.md`
- `japanese-chat-natural-ja`
- `self-check`

### 例3

指摘:
- 主質問が `お願いできますか` なのに、先頭で価格を出す

分類:
- `QA-02 余計情報差し込み`

scope:
- `reply-only`
- `prequote`
- 公開 bugfix

戻し先:
- `output-schema`
- `intake-router`
- `reply-bugfix`

## 固定したい運用

- 監査で良い指摘が出たら、まず `QA分類`
- 次にこの scoping で `どこにだけ効かせるか`
- その後で `skill / schema / self-check / NG / gold` の戻し先を決める

この順番を崩すと、良い改善でも OS 全体にノイズが入る。
