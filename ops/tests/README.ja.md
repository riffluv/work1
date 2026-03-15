# 運用テストケース運用

## 目的
- 実案件前に、見積り判定・返信文・感情注意・金額分岐の回帰確認をする。
- 新しいテンプレや skill 変更を入れた時に、主要ケースで崩れていないかを見る。

## 優先して使う入力
- 主ケース集: `/home/hr-hm/Project/work/ops/tests/prequote-test-cases.txt`
- 骨格ケース: `/home/hr-hm/Project/work/ops/tests/prequote-cases.yaml`
- エッジケース: `/home/hr-hm/Project/work/ops/tests/edge-cases.yaml`

## 役割の違い
- `prequote-test-cases.txt`
  - Claude 作成の自然文ケース集。
  - 実際の相談文に近い温度感で、手動テストや reply 品質確認に向く。
- `prequote-cases.yaml`
  - 代表ケースの期待判定メモ。
  - 15K / 5K / 保留 / 断る の基本分岐確認に使う。
- `edge-cases.yaml`
  - 金銭事故や状態遷移の谷間に寄せた確認用。
  - 値引き、5K→15K、quote_sent、closed 後などを見る。

## 使い方
1. `prequote-test-cases.txt` から 1件ずつ選ぶ
2. `route / state / raw_message / note` を Codex に貼る
3. 判定メモ / 返信文 / 補足提案が妥当かを見る
4. 必要ならテンプレ・skill・rule を修正する
5. 修正後は `prequote-cases.yaml` と `edge-cases.yaml` でも崩れていないかを見る

## 返信文の温度感をまとめて整えたいとき
- `/home/hr-hm/Project/work/ops/tests/rehearsal/README.ja.md` を使う
- 1件ずつではなく、カテゴリごとに 5件前後まとめて返信文を作る
- まとめた返信文を Claude に監査させ、共通する AI感 を skill に戻す

## 特に見る点
- 15,000円 / 5,000円 / 保留 / 断る の分岐が妥当か
- 感情注意フラグが過不足なく立つか
- 苦情寄りケースで冷たい文面になっていないか
- 見積り経路なのに有料オプション前提で書いていないか
- `closed` 後の相談で、既存トークルーム継続前提になっていないか

## 更新ルール
- 実案件で新しい危険パターンが出たら、まずは `edge-cases.yaml` に追加する。
- 自然文で再現したい場合は `prequote-test-cases.txt` と同形式で追記する。
- 代表ケースは増やしすぎず、回帰確認で毎回見る最小セットに保つ。
