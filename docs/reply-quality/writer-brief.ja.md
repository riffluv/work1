# Writer Brief（reply-only）

更新日: 2026-04-12

## 目的

- 返信本文を書く `Writer` に、必要最小限の指示だけを渡す
- `policy / self-check / lint` を Writer に背負わせず、Codex の自然な文章力を残す
- `分類は厳密、本文はもっと自由、最後に self-check` を実装レベルで固定する

## 前提

- 対象はココナラ返信の本文生成だけ
- `phase / service / scope / forbidden_moves` の判定は前段で済ませる
- Writer は分類しない。与えられた metadata と facts をもとに自然文を書く
- `self-check` は Writer に渡さず、Reviewer 専用にする

## Writer に渡してよいもの

- buyer の原文
- route / state / service / certainty
- `reply_contract.primary_question_id`
- `explicit_questions`
- `answer_map`
- `ask_map`
- `required_moves`
- 最小限の `forbidden_moves`
- service facts
- 近い few-shot 例 2〜3 件まで

## Writer に渡さないもの

- 420行級の self-check 全文
- reviewer 用の ban list 全文
- `why this is forbidden` の長い説明
- platform 契約の細部全文
- 恒久反映の履歴や監査議論

## Writer の固定原則

1. 主質問に先に答える
2. buyer の語彙や観測事実を 1 点は拾う
3. buyer が次に何をすればよいか分かる言葉で書く
4. 内部語を出さない
5. 次アクションは 1 つだけ置く
6. 聞かれていない説明を増やしすぎない
7. 次アクションは buyer の判断サイクルに合わせる

## Writer への短い指示テンプレ

以下の 7 行を Writer の既定とする。

```text
- 主質問に先に答える
- buyer の語彙や観測事実を1点は拾う
- buyer が次に何をすればよいか分かる言葉で書く
- 内部語や判定ラベルを書かない
- 次アクションは1つだけ置く
- 次アクションは buyer の判断サイクルに合わせる
- phase / service / forbidden_moves は守る
```

## 禁止形より価値観形を優先する

Writer には `内部判断を出すな` とだけ渡さない。

代わりに、次のように価値観で渡す。

- `buyer が読んで次の行動が分かる言葉で書く`
- `buyer の質問にそのまま返る言葉を優先する`
- `内部で使う分類語より、buyer が会話として読める語を優先する`
- `こちらが次に欲しいもの` より、`buyer が次に決めること` を優先する

## Reviewer の役割

Reviewer は本文を書かない。次だけを見る。

- phase 整合
- public / private 境界
- 価格 / scope facts
- forbidden_moves
- ban 表現
- closing の有無
- 空語
- 主質問への直答

## 適用の原則

- Writer で説明を足しすぎるより、Reviewer で止める
- `forbidden_moves` だけは Writer / Reviewer の両方で持ってよい
- Writer の guidance は 5〜10 行までに圧縮する
- few-shot は rules 100 行より優先してよい

## いまの実務への当て方

- `coconala-prequote-ops-ja`
  - intake と price/scope 判定は strict
  - 本文生成は本 brief を使う
  - self-check は draft 後に通す
- `coconala-reply-bugfix-ja`
  - `reply_contract` と `response_decision_plan` を前段で固定
  - 本文生成は本 brief を使う
  - `japanese-chat-natural-ja` は最終自然化だけ
