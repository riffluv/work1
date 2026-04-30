# acceptance gate

## 目的
- 返信文を `送れる / 差し戻す / system へ戻す` の3段階で判断する
- 感覚ではなく、最低限の通過条件を固定する

## gate の順番
1. 事実 gate
2. phase gate
3. 会話 gate
4. 日本語 gate
5. soft lens gate

## 1. 事実 gate
以下のどれかを外したら差し戻す。
- 公開していないサービス名や価格を外向けに出していない
- scope や価格の事実を勝手に変えていない
- meeting / direct push / prod login / secrets などの禁止事項を破っていない

## 2. phase gate
以下を外したら差し戻す。
- prequote で購入後の ask まで進みすぎていない
- quote_sent で prequote の generic ask に戻っていない
- purchased / delivered / closed で不自然に prequote の温度へ戻っていない
- `state` だけに頼りすぎず、相手文と返信文の phase が読者にもつながっている
- `quote_sent` でトークルームを現在の作業場所のように書いていない。ただし、`お支払い完了後にトークルームで共有してください` のような未来条件つきの購入後手順は許容する
- `prequote` で、まだ出していない見積り提案を前提に `見積り提案の内容で問題なければ` と書いていない
- purchased で既に購入済みの場面では、`ご購入後に...` のような未来導線に戻さず、`受け取っている材料` `いただいた内容` など現在地に合う表現を使う
- #RE の fixture では、相手文だけで state が読み取りにくい場合、`購入後です` `見積り提案ありがとうございます` `クローズ後です` など phase を明示する
- buyer が既に出した情報を同じ粒度で聞き直していない

## 3. 会話 gate
以下を満たさない場合は差し戻す。
- 主質問に先に答えている
- buyer の判断段階を飛ばしていない
- 断る時でも、代替か次の動きが見える
- 返信後に buyer が「で、次に何をすればいいの？」で止まらない

## 4. 日本語 gate
以下の再発癖があれば差し戻す。
- internal 語
- 空語
- ban 語
- 同じ結論の繰り返し
- 相手文の引用オウム返し
- 同一バッチでの冒頭完全固定

## 5. soft lens gate
soft lens は、送れる文を好みで差し戻すためではなく、実務上の誤読・AI感・buyer の停滞を見つけるために使う。

判定前に必ず確認する。

- primary lens は原則1つに絞っているか。
- soft lens の修正案で、価格・scope・phase・secret・public/private・payment route・作業可否が弱まらないか。
- 高リスク場面では、多少硬くても `acceptable_as_is` として残す方が安全ではないか。
- `はい`、`まずは`、`大丈夫です`、`相談できます`、`〜の件`、句点数、段落数を blanket NG にしていないか。
- hard fail にする場合は、soft lens 名ではなく、実際に壊れている deterministic guard 名で説明できるか。

soft lens の判定例:

- `fix_recommended`: 送信前に最小修正した方が実務上よい。
- `acceptable_as_is`: より自然な言い換えはあるが、境界保持のため現状でよい。
- `observe_only`: まだ再発性や副作用が見えないため、修正へ戻さない。
- `overfire_risk`: 直すと必要な境界や主質問が弱まるため、修正しない。

## 判定
### send
- major fail なし
- minor fail も許容範囲

### revise
- 送る前に直せる軽微なズレがある
- 文面修正で終わる
- soft lens 上は気になるが、hard guard への影響がなく、最小修正で buyer の理解が明確になる

### escalate-to-system
- 同型が再発した
- Router / Writer / Reviewer / Facts のどこに戻すか切れる
- 単発修正だけで終わらせるとまた出る
- soft lens の指摘が、複数 batch で同じ root cause として再発している

## major fail
- 主質問未回答
- phaseズレ
- public/private 事故
- scope 事故
- prohibited action を許している
- buyer の判断段階を飛ばして強引に進行している

## minor fail
- 逃げ語
- ask の言い回し固定
- 感情シグナルの受け止めが薄い
- 技術語の粒度が少しズレる
- opening / closing の単調さ

## 毎バッチ見る数値
- major_fail_count
- minor_fail_count
- new_pattern_count
- gold_reply_candidate_count

## 合格の目安
- major fail = 0
- new pattern が減少傾向
- 同じ fail が system 反映後に戻ってこない

## system へ戻す判断
- `service facts` を入れ替えても再発するなら共通資産
- 特定 service だけで再発するなら service-specific
- 1回限りなら文面修正止まり
