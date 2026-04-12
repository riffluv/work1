# acceptance gate

## 目的
- 返信文を `送れる / 差し戻す / system へ戻す` の3段階で判断する
- 感覚ではなく、最低限の通過条件を固定する

## gate の順番
1. 事実 gate
2. phase gate
3. 会話 gate
4. 日本語 gate

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

## 判定
### send
- major fail なし
- minor fail も許容範囲

### revise
- 送る前に直せる軽微なズレがある
- 文面修正で終わる

### escalate-to-system
- 同型が再発した
- Router / Writer / Reviewer / Facts のどこに戻すか切れる
- 単発修正だけで終わらせるとまた出る

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
