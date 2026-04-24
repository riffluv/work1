# skill thought preservation 最小メモ

## 目的

- skill 発火時に、Codex 本体の判断を止めない
- skill を `別の思考主体` ではなく、`正本の取り出し口 / guardrail` として使う
- 長い固定文脈や二重ルールで、返信骨格を上書きしない

## 基本原則

- 主判断は常に Codex 本体で行う
- skill は `正本を引く / 取り出し口を整える / 確認観点を足す` ところまでに留める
- skill 側で別思想を作らない
- 1回の起動で読む reference は、その場に必要な最小限に絞る
- 長い review ルールや template 群を、本文生成前にまとめて流し込まない
- service page と facts がある時は、template より先に正本を優先する

## 優先順

1. `service-registry.yaml`
2. `source_of_truth`
3. `facts_file`
4. service-pack / decision / evidence
5. skill references
6. 過去テンプレ / gold replies / mirror

## 役割分担

### Router

- 相手文を、状態・主質問・不足情報・次アクションへ薄く構造化する
- 文体や phrasing まで決め切らない

### Prequote Ops

- service facts と phase を固定する
- Writer に渡すのは最小 facts packet だけにする

### Reply Skills

- 必要な正本を引いたら、まず Codex が freeform に近く下書きする
- template は本文の代わりではなく、詰まった時の参照に留める
- naturalize は意味変更ではなく、語感調整に限定する

## やらないこと

- skill 内に長い固定プロンプトを足して、毎回同じ骨格を押し付ける
- 同じルールを service facts と skill の両方に重複保持する
- router / writer / reviewer の責務を1枚の skill に混ぜる
- `参考` を `必須の順番` に格上げする

## 採用判断

- skill の追加情報が、`再発防止 / 取り出しやすさ / facts 保全` のどれにも効かないなら足さない
- Codex が既に持っている一般知識は、skill に書き足さない
- 迷ったら、`短い guide + 必要時だけ reference` を選ぶ
