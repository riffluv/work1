# 2026-04-29 #BR 棚卸し BR13〜16

## 結論

今回の棚卸しは `reply-only`。
納品物本文には戻さない。

BR13〜16 で見えた学びは、`handoff-25000` 公開前の shadow asset と、通常 live / #RE に戻してよい汎用境界に分ける。
骨格は維持する。新しい大きな router / renderer は作らない。

## 対象 batch

| batch | 主題 | 外部監査結果 |
| --- | --- | --- |
| BR13 | neither 厚め。FAQ / 操作手順書 / 正式仕様書 / secret値 / 全体監査 / diagnosis-only / repair absorption | 採用圏 |
| BR14 | valid handoff と作業面境界。環境構築 / GitHub work-surface / 設計レビュー / bundle pressure | 採用圏 |
| BR15 | service boundary と payment route 分離。同じトークルーム / おひねり / closed 後導線 | 採用圏 |
| BR16 | Pro 4/29 後確認走行。public-private separation / delivered-closed micro-state | 採用圏 |

## 通常 live / #RE に戻してよいもの

`handoff-25000` の名前・25,000円・購入導線を含まない汎用境界だけ戻す。

### G1. active defect は bugfix-first

buyer が `コードが分からない` `整理も気になる` と言っても、今止まっている不具合を直したいなら、まず不具合修正から見る。
外向けでは未公開サービス名や価格比較を出さず、`今止まっている不具合を先に見ます` と返す。

戻し先:

- `question-type-batch-plan`
- `self-check`
- 既存 `fix_vs_structure_first` gold / validator の運用

### G2. bugfix 内の軽い説明と、本格資料を分ける

修正ファイル、変更箇所、確認順の軽い説明は bugfix 内で足りる。
正式仕様書、操作マニュアル、顧客FAQ、運用マニュアル、次担当者向けの本格資料は bugfix に吸収しない。

戻し先:

- `question-type-batch-plan`
- `normal boundary routing` gold の観察候補

### G3. operation docs / customer docs は code work ではない

Stripe関連でも、スタッフ向けの管理画面操作手順書、顧客対応FAQ、返答案テンプレートは、コード不具合修正ではない。
冷たく切らず、`既存コードの不具合修正とは別の運用資料です` と短く理由を出す。

戻し先:

- `question-type-batch-plan`
- reviewer 観点

### G4. raw secret は扱わない

APIキー、Webhook secret、DB接続文字列、`.env` の値そのものは扱わない。
必要な場面でも、キー名、設定箇所、用途、確認すべき場所までに留める。

戻し先:

- 既存 secret / secure share rules
- `question-type-batch-plan` の `秘密情報・共有方法型`

### G5. diagnosis-only / cheap trial を作らない

active defect で `原因だけ安く` `軽く診断だけ` の入口を作らない。
不具合修正は、原因確認から修正済みファイル返却まで進める前提として返す。

戻し先:

- `question-type-batch-plan`
- 既存 completion gate / price anxiety gold

### G6. service boundary と payment route を分ける

何を引き受けるかと、どう支払うかを同じ文脈に混ぜない。
buyer が支払い方法を聞いていない時は、同じトークルーム内 / おひねり / 有料オプションを先回りしない。
prequote では、まだ存在しないトークルーム内追加作業を約束しない。

戻し先:

- `phase-contract-batch-plan`
- `self-check`
- platform contract / reviewer 観点

### G7. delivered と closed を分ける

delivered は正式納品後・クローズ前。
承諾前なら、今回の修正との関係があるかを軽く確認できる。
closed 後は、ログやスクショなど確認材料の受領と、実作業開始を分ける。

戻し先:

- `phase-contract-batch-plan`
- `delivery-completion-bugfix40` regression
- delivered / closed gold

### G8. context bleed guard

相手文にない外注先事情、コード引き継ぎ背景、支払い事情を足さない。
route 判定を補強したくても、buyer の文章にない物語で埋めない。

戻し先:

- reviewer 観点
- `self-check`

## shadow asset に留めるもの

次は通常 live / #RE へ戻さない。

- `25,000円`
- `handoff-25000`
- `主要1フロー整理サービス` への購入導線
- dual-service 前提の `どちらのサービス` 案内
- handoff の成果物説明を、bugfix live の本文へ流用すること
- 追加フロー価格や handoff オプションの外向け案内

## validator に今すぐ戻さないもの

- `neither` の自然な切り方全般
- `含めにくい` と `含まれません` の語感差
- 取引状態に応じたおひねり説明の細かい文言
- valid handoff の言い回し
- `buyer がすでに正しい route を選んでいる時に診断調にしない` の全般

理由:

- 文脈依存が強い
- hard fail 化すると自然な短文まで落とす
- 現時点では外部監査で採用圏が続いている

## 今回反映した正本

- `question-type-batch-plan-20260425.ja.md`
  - BR13〜16 から通常 #RE へ戻す観察候補を追加
- `phase-contract-batch-plan-20260425.ja.md`
  - service boundary と payment route、delivered / closed micro-state の観察を補強
- `README.ja.md`
  - BR13〜16 棚卸しメモを reply-quality の索引へ追加
- `self-check-core-always-on.ja.md`
  - 公開状態、支払い導線先回り、delivered / closed 誤認の常時チェックを最小補強

## #RE bugfix41 で renderer に戻したもの

外部監査で r0 の generic bugfix 吸収が見つかったため、次の項目は `post-br-live-boundary-bugfix41.yaml` と `estimate_initial` renderer に戻した。

- active defect では、コード全体整理を先に挟まなくてよい
- 操作手順書・顧客FAQは、不具合修正に含めない
- 原因だけ安く / 診断メモだけの入口を作らない
- APIキー、Webhook secret、`.env`、DB接続文字列の値そのものは扱わない
- prequote では、取引中のおひねり追加を前提にしない

引き続き、`25,000円` / `handoff-25000` / 主要1フロー整理の購入導線は通常 live / #RE に戻さない。

外部監査では r1 が採用圏となった。
軽微候補だった B06 の自然化と B07 の固定時刻回避だけ r2 で反映し、必須境界は維持した。

## 次の BR17 を回す条件

すぐ連続では回さない。
次のどれかが必要になった時に BR17 を作る。

- 通常 #RE で、public/private leak や payment route bleed が再発した
- handoff 公開前に、サービスページ final check が必要になった
- buyer が `どちらがお得か` `無料で軽く見て` `返金/値引き` を強く迫る edge を追加したい
- delivered / closed の追加相談で、今回の regression にない状態が出た

BR17 を作る場合の候補:

- 値引き・無料確認・返金圧
- handoff に見える運用代行 / 教育 / PM作業
- 複数サービス公開時の `どちらがお得ですか`
- 納品直前 / 承諾後 / closed 後の追加相談
- buyer が未公開側の価格を先に出す public / shadow 分離
