---
name: coconala-intake-router-ja
description: "ココナラ相談文の入口判定専用。相手文を、経路・状態・サービス適合・リスク・不足情報・次アクションへ構造化し、返信文生成の前段を固定する。"
---

# ココナラ入口ルーター

## 目的
- 相手文をいきなり返信文へせず、先に安全な判定結果へ落とす。
- 誤判定、聞きすぎ、規約事故、スコープ事故を減らす。
- 返信文作成 skill の前段として使う。

## このskillを使う場面
- 相手文を貼られて、まず何を返すべきか整理したいとき
- `#A` で分析のみ返したいとき
- プロフィール経由やメッセージ経由で、主力サービス適合を見たいとき
- 返信文を作る前に、リスクと不足情報を固定したいとき

## 最初に見るファイル
1. `/home/hr-hm/Project/work/ops/common/output-schema.yaml`
2. `/home/hr-hm/Project/work/ops/common/interaction-states.yaml`
3. `/home/hr-hm/Project/work/ops/common/risk-gates.yaml`
4. `/home/hr-hm/Project/work/ops/common/routing-table.yaml`
5. `/home/hr-hm/Project/work/ops/common/coconala-rule-guard.md`
6. `/home/hr-hm/Project/work/ops/services/next-stripe-bugfix/service.yaml`
7. `/home/hr-hm/Project/work/ops/services/next-stripe-bugfix/evidence-minimum.yaml`
8. `/home/hr-hm/Project/work/ops/services/next-stripe-bugfix/scope-matrix.md`

## 入力の最小形
- `src`: `service` / `profile` / `message` / `talkroom`
- `state`: `prequote` / `quote_sent` / `purchased` / `predelivery` / `delivered` / `closed`
- `reply`: `analysis_only` / `make_reply`
- `raw_message`: 相手文そのまま
- `service_hint`: 任意。分かるときだけ

## 標準ルート
1. 相手文から事実だけ抽出する。
2. 主力サービス適合を `high / medium / service_mismatch_but_feasible / low / unknown` で置く。
3. `risk-gates` に当てて、`allow / hold / decline` 相当の危険を拾う。
4. スコープを `same_cause_likely / different_cause_likely / undecidable / not_applicable` のどれかへ落とす。
5. 不足情報は、その状態で本当に必要なものだけ最大3点に絞る。
6. `next_action` を1つに絞る。
7. `reply` が明示されていない限り、送信用文面は作らない。

## 判定フロー
1. 相手文から事実だけ抽出する。
2. 主力サービス適合を `high / medium / service_mismatch_but_feasible / low / unknown` で置く。
3. `risk-gates` に当てて、`allow / hold / decline` 相当の危険を拾う。
4. スコープは `same_cause_likely / different_cause_likely / undecidable / not_applicable` のどれかへ落とす。
5. 不足情報は、その状態で本当に必要なものだけ出す。
6. 次アクションを1つに絞る。
7. `reply` が明示されていない限り、送信用文面は作らない。

## Gotchas
- 相手文が貼られただけなら分析のみで止める。自動で返信文を作らない。
- `service_mismatch_but_feasible` は売上都合で使わない。技術的現実性と実績上の検討余地が両方ある時だけ使う。
- `undecidable` の場面で、こちらの都合で無理に `same` / `different` を決めない。
- 価格や無料対応は、この段階で断定しない。
- 既出情報を質問として再パッケージしない。

## 出力ルール
- `output-schema.yaml` の項目名に沿って返す。
- 返信文ではなく、まず判定結果を返す。
- `missing_info` は最大3点までを優先する。
- 既出情報の聞き直しをしない。
- 主力サービスに素直には乗らないが、技術的には現実的で実績目的なら検討余地があるときは `service_mismatch_but_feasible` を使う。
- `service_mismatch_but_feasible` のときは、自動で断らず、人間判断へ上げる。
- 主力サービスに乗るか不明なときは、無理に受けず `undecidable` または `medium fit` で止める。

## 感情注意フラグの検知
相手文に以下のシグナルがある場合、出力に `emotional_caution: true` を含める。

### 高信頼シグナル（単体でフラグ）
- `直っていない` / `直ってない`
- `解決していない` / `解決してない`
- `お金を払ったのに` / `料金を払ったのに`
- `返金`
- `納得できない` / `納得いかない`

### 中信頼シグナル（文脈と組み合わせ）
- `また` + 過去取引への言及（例: `前回` `以前` `クローズ` `前にお願いした`）
- `前回` + 不満を示す接続（例: `のに` `けど` `だったはず`）
- `困る` + 要求（例: `してほしい` `してもらわないと` `対応してください`）
- `まだ` + 否定（例: `直らない` `反映されない` `変わらない`）

### フラグしない例
- `また連絡します`
- `前回の続きで`
- `困っています` だけの単純相談

### 判定ルール
- 高信頼シグナルは1つでもあれば `emotional_caution: true`
- 中信頼シグナルは組み合わせ条件を満たす場合のみ `emotional_caution: true`
- 迷ったら `true` に倒す（冷たい返信の方がリスクが高いため）

## replyが必要なとき
- このskill自身は長い送信用文面を主担当にしない。
- `reply: make_reply` かつ `risk_level` が高くない場合のみ、短い返信方針メモを付けてよい。
- 本文生成は `coconala-reply-bugfix-ja` へ渡す。

## 仕上げ前チェック
- 経路と状態を混同していないか
- 主力サービス適合を売上都合で上げていないか
- 価格や無料対応を断定していないか
- `next_action` が1つに絞れているか
- `service_mismatch_but_feasible` を、単なる売上欲しさではなく「技術的現実性 + 実績上の検討余地」で使っているか
