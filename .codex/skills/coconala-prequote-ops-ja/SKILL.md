---
name: coconala-prequote-ops-ja
description: "ココナラ見積り相談の前段専用。相手文を、入口判定 -> 15,000円/保留/断る の分岐 -> 返信文生成まで一貫処理し、送信用返信文・内部判定メモ・補足提案の3点セットで返す。"
---

# ココナラ見積り相談オペレーター

## 目的
- 見積り相談の判断順序を固定する
- `service / phase / scope / forbidden_moves` を前段で固める
- 本文生成では Codex の自然な文章力を残し、事故防止は Reviewer 側で担保する

## この skill を使う場面
- `state: prequote` の見積り相談
- サービス経由 / プロフィール経由 / メッセージ経由の購入前返信
- `#R` で送信用返信文を作る時
- `#A` で判定メモだけ返す時

## この skill を使わない場面
- `state` が `purchased` 以降
- トークルーム購入後の受領返信、進捗返信、納品前後の案内
- `#$0` `#$1` `#$2` `#$3` の UI進行タグが付いた購入後会話

購入後は `coconala-reply-bugfix-ja` を直接使う。

## 先に見る正本
1. `/home/hr-hm/Project/work/os/core/service-registry.yaml`
2. `/home/hr-hm/Project/work/os/coconala/platform-contract.yaml`
3. `/home/hr-hm/Project/work/ops/common/output-schema.yaml`
4. `/home/hr-hm/Project/work/ops/common/interaction-states.yaml`
5. `/home/hr-hm/Project/work/ops/common/coconala-rule-guard.md`
6. `/home/hr-hm/Project/work/ops/common/routing-table.yaml`
7. `service-registry.yaml` で解決した live service の `facts_file`
8. `/home/hr-hm/Project/work/docs/reply-quality/writer-brief.ja.md`
9. `/home/hr-hm/Project/work/docs/reply-quality/prequote-compression-rules.ja.md`
10. `/home/hr-hm/Project/work/docs/coconala-reply-self-check.ja.md`
11. `/home/hr-hm/Project/work/docs/coconala-prequote-commitment-policy.ja.md`
12. `/home/hr-hm/Project/work/docs/coconala-handoff-prequote-mini-contract.ja.md`
13. `references/phase-vocabulary-guard.ja.md`
14. `references/bugfix-boundary-rules.ja.md`
15. `references/handoff-boundary-rules.ja.md`

## 公開状態の扱い
- 外向け live は `bugfix-15000` のみ
- `handoff-25000` は private。外向け返信でサービス名・価格・購入導線を出さない
- buyer が private 側の価格を先に書いていても、こちらから繰り返さない

## 3段構成

### 1. Classifier
- `coconala-intake-router-ja` で入口判定する
- `phase / route / service_fit / certainty / scope_judgement / next_action` を先に固定する
- `estimate-decision.yaml` で `accept_15k / hold / decline` を決める

### 2. Writer
- Writer に渡すのは `/home/hr-hm/Project/work/docs/reply-quality/writer-brief.ja.md` の7原則だけ
- Writer は分類しない。前段の facts packet をもとに自然文を書く
- Writer に self-check 全文や長い lint を渡さない

### 3. Reviewer
- `/home/hr-hm/Project/work/docs/coconala-reply-self-check.ja.md` を正本にして draft を検査する
- `phase / public-private / 価格 / scope / 禁止語 / 空語 / next action` を止める
- 最後に `japanese-chat-natural-ja` を通し、再度 facts 崩れがないか確認する

## facts packet の最小要素
- buyer 原文
- route / state / service / certainty
- `reply_contract.primary_question_id`
- `explicit_questions`
- `answer_map`
- `ask_map`
- `required_moves`
- 最小限の `forbidden_moves`
- service facts
- 近い例 2〜3 件まで

## 判定の基本

### `accept_15k`
- 公開 live の `bugfix-15000` で受けられる
- 同一原因の1件として見られる
- 必要最小限の情報で見積り判断できる

### `hold`
- 情報不足で判定不能
- 追加質問は1回までを基本にする
- 2回目も曖昧なら辞退か人手確認へ倒す

### `decline`
- 範囲外
- 新規実装 / 新機能
- 別原因が多すぎる
- 幅が広すぎる

## 実行フロー
1. `coconala-intake-router-ja` で入口判定する
2. `prequote` 以外ならこの skill を使わない
3. live service と service facts を正本から解決する
4. `accept_15k / hold / decline` を決める
5. facts packet を作る
6. Writer Brief だけで draft を作る
7. Self-check / lint / phase guard で止める
8. `japanese-chat-natural-ja` で最終自然化する
9. `latest.txt` と `latest-source.txt` に保存する

## Writer でやらないこと
- `対象候補です` `見積もり判断できます` のような内部語で返す
- prequote なのに購入後フェーズの動詞へ進める
- buyer がまだ判断段階なのに、こちらの情報回収へ前のめりに進む
- private service の価格や導線を外へ出す

## Reviewer で必ず見ること
- 主質問に最初の answer-bearing section で答えているか
- buyer の語彙や観測事実を少なくとも1点拾えているか
- `対象候補 / 見積もり判断 / 進め方 / ご案内 / この不具合として` のような内部語・空語が戻っていないか
- prequote なのに `確認を進めます / 見ます / 切り分けます` のような購入後動詞になっていないか
- buyer の判断段階と次アクションが合っているか
- 外部共有や秘密情報の扱いが platform と security に合っているか

## 詳細ルールの置き場
- prequote の語彙・phase guard:
  - `references/phase-vocabulary-guard.ja.md`
- bugfix / boundary の詳細:
  - `references/bugfix-boundary-rules.ja.md`
- handoff / private-boundary の詳細:
  - `references/handoff-boundary-rules.ja.md`
- 圧縮と closing:
  - `/home/hr-hm/Project/work/docs/reply-quality/prequote-compression-rules.ja.md`
- 最終 lint:
  - `/home/hr-hm/Project/work/docs/coconala-reply-self-check.ja.md`

この main SKILL に細かい phrasing 禁止を増やさない。細かい再発表現は Reviewer 側へ寄せる。

## 出力

### `#A`
- 判定メモ
- 次アクション

### `#R`
- 送信用返信文
- 判定メモ
- 必要なら補足提案

## 保存
- 送信用文面: `/home/hr-hm/Project/work/runtime/replies/latest.txt`
- 相手文: `/home/hr-hm/Project/work/runtime/replies/latest-source.txt`

## 最後の原則
- strict に持つのは `facts / phase / scope / forbidden_moves`
- 本文は Writer Brief の原則で自然に書かせる
- おかしな言い回しを Writer に覚えさせず、Reviewer で止める
