# boundary-routing shadow rehearsal（#BR）

最終更新: 2026-04-29

## 目的

`#BR` は、`bugfix-15000` と `handoff-25000` の境界ルーティングを鍛えるための shadow rehearsal。

通常の `#RE` は、公開中の `bugfix-15000` 返信品質を検査する。  
`#BR` は、将来 `bugfix-15000` と `handoff-25000` を両方公開した時に、buyer の相談をどちらへ案内するかを先に検査する。

## 現在の公開状態

- `bugfix-15000`: public / live
- `handoff-25000`: private / ready / internal reference

`#BR` を実行しても、`handoff-25000` を live 扱いにしない。  
`service-registry.yaml` の `public: false` は変更しない。

## `#BR` 内での扱い

`#BR` では `handoff-25000` を `training-visible / future-dual simulation` として扱う。

これは、外向けにすぐ送る文面ではなく、将来の dual-service 状態を検査するための rehearsal である。通常の `#R` / `#RE bugfix` / live 返信へは直接混ぜない。

## 保存先

```text
/home/hr-hm/Project/work/サービスページ/rehearsal/boundary-routing-返信学習/返信監査_batch-current.md
```

完了済みの過去 batch は、必要な場合だけ `archive/` に退避する。外部監査へ渡すファイルは原則 `返信監査_batch-current.md` のみ。

## 検査する主なルート

### 1. bugfix-first

主目的が「今出ている不具合を止めたい」なら、まず `bugfix-15000` に寄せる。

例:

- 決済後に注文が作成されない
- Webhook が届かない
- 管理画面や購入履歴に反映されない
- コードは分からないが、今はエラーを直したい

守ること:

- 「コードが分からない」だけで handoff へ逃がさない
- 修正が主目的なら、整理より bugfix を先にする
- 15,000円の不具合1件を、整理や複数フロー調査へ広げない

### 2. handoff-first

主目的が「次の担当者が触れるように把握したい」「どこから直せばよいか整理したい」なら、handoff 側のルートに寄せる。

例:

- 前任者がいなくなり、Stripe連携の流れを誰も説明できない
- いま壊れているというより、次の外注先へ渡せるメモがほしい
- 主要1フローの関連ファイル、危険箇所、次の着手順を整理したい

守ること:

- handoff は修正を成果条件にしない
- 主要1フローを超える場合は追加フローとして切る
- 新機能追加やリポジトリ全体の網羅調査に広げない

### 3. bugfix / handoff bridge

相談文に「不具合」と「把握したい」が混在する場合は、buyer に選択を丸投げせず、主目的で順番を決める。

原則:

- まず止めたい不具合が明確なら bugfix-first
- 不具合が曖昧で、目的が引き継ぎ・把握なら handoff-first
- bugfix 後に整理が必要なら、別対応として相談
- handoff 後に修正が必要なら、修正は別対応として相談
- 支払い導線は route 判定と混ぜない。buyer が支払い方法を聞いていない限り、同じトークルーム内 / おひねり / 有料オプションを前面に出さない

## live 漏れの禁止

通常の外向け live 返信では、`handoff-25000` が `public:false` の間、次を出さない。

- `handoff-25000` のサービス名
- 25,000円 / 25000円 / 25,000円側
- handoff サービスページへの購入導線
- 「整理側のサービスを購入してください」のような外向け CTA

`#BR` の rehearsal batch では、監査対象として future-dual の内部ルーティングを明示してよい。ただし batch 冒頭で `training-visible / future-dual simulation` と明記する。

## 監査観点

- buyer の主質問は「直したい」か「把握したい」か
- 価格を混ぜていないか
- 15,000円の bugfix に、整理・主要1フロー調査・新機能追加を吸収していないか
- 25,000円の handoff に、修正完了を約束していないか
- buyer に「どっちを買えばいいですか？」を返していないか
- `今はまずこちら` と順番が見えるか
- live 返信へ private service の名称・価格・購入導線が漏れていないか

## `#BR` の実行単位

1 batch は 6〜8件を目安にする。

推奨 mix:

- bugfix-first: 2件
- handoff-first: 2件
- mixed / bridge: 2件
- price / scope boundary: 1件
- public leak sentinel: 1件

## 採用判断

`#BR` で見つかった指摘は、すぐ通常返信へ戻さない。

先に分類する:

- `boundary-route`: bugfix / handoff の順番判断
- `price-separation`: 15,000円 / 25,000円 / 追加フローの分離
- `public-leak`: public false サービスの名称・価格・導線漏れ
- `scope-absorption`: 整理や新機能を bugfix に吸収
- `handoff-overpromise`: handoff で修正完了を約束

通常 live に戻してよいのは、`bugfix-15000` だけでも再発する境界事故に限る。  
dual-service 固有の改善は、`handoff-25000` 公開前の shadow asset として保持する。

## batch-01 棚卸し（2026-04-28）

初回 #BR では、r0 で `default_bugfix` への吸収が強く出た。

### r0 で見えた主な失敗

- `handoff-first` が bugfix の旧テンプレートへ落ちる
- `neither / scope out` の新機能追加を bugfix / handoff へ吸収しようとする
- `整理中にバグが見つかったらそのまま直せるか` に対して、修正まで約束しそうになる
- `外注先と連絡が取れず` のような相手文にない context bleed が出る
- route 判定語が外向け文面へ出ると、分類を発表しているように見える

### batch-01 で残した gold

#### handoff-first

壊れている不具合ではなく、次の担当者へ渡すための整理が主目的なら、整理ルートへ寄せる。

外向け文面では、`これは handoff-first です` のような分類文を出さない。  
`この内容であれば、次の外注先が追えるように...整理する対応が合っています` のように、buyer の目的に沿って説明する。

購入前はコード一式や関係ファイルを強く求めない。対象フローだけ分かればよい。

#### bugfix-first

止まっている不具合が明確なら、コードが分からない・整理も気になる、という相談でも bugfix を先にする。

引き継ぎメモは別対応だが、修正に必要な範囲の関連ファイル確認は bugfix 内で行う。

#### scope boundary

15,000円の不具合修正には、修正に必要な範囲のファイル位置・変更箇所の説明は含められる。  
ただし、次の担当者へ渡すための引き継ぎメモや主要フロー整理は含めない。

#### handoff no repair promise

整理中に明らかなバグが見つかった場合でも、そのまま修正作業まで進めるとは約束しない。  
整理では、怪しい箇所・影響しそうな処理・次に直すべき候補をメモとして伝える。  
修正が必要なら、別対応として進め方を相談する。

#### neither / scope out

クーポン追加などの新機能追加は、15,000円の不具合修正にも、25,000円の整理にも吸収しない。  
既存決済が壊れているなら bugfix、流れを整理するなら handoff、新しく機能を入れるなら別対応として分ける。

### 通常 live へ戻さないもの

- `25,000円` の外向け案内
- `handoff` のサービス名・購入導線
- dual-service 前提の選択肢提示

### 通常 live に戻してもよい候補

- 新機能追加を不具合修正へ吸収しない
- 相手文にない事情を受領しない
- 目的が修正なら、コードが分からないだけで整理へ逃がさない

ただし、これらも `handoff-25000` 名や価格を出さず、bugfix-15000 の範囲内で表現する。

## batch-02 r0（2026-04-28）

保存先:

```text
/home/hr-hm/Project/work/サービスページ/rehearsal/boundary-routing-返信学習/返信監査_batch-current.md
```

fixture:

```text
/home/hr-hm/Project/work/ops/tests/quality-cases/active/boundary-routing-shadow-br02.yaml
```

狙い:

- bugfix-first でも handoff 希望が混ざるケース
- 壊れていない handoff-first ケース
- 修正後に handoff を希望する bridge ケース
- bugfix に軽いファイル説明を含められるか
- handoff の主要1フローとリポジトリ全体の境界
- 新機能追加 + handoff 希望の neither 判定

r0 では手修正せず、current renderer の出力を監査対象にする。監査後に、`boundary-route / price-separation / scope-absorption / neither-route / context-bleed` のどこへ戻すかを判断する。

### r1 手反映

Codex監査を受け、`返信監査_batch-current.md` を r1 へ更新した。

- B01: bugfix-first。注文作成不具合を先に直し、引き継ぎ整理は別対応
- B02: handoff-first。壊れていない危険箇所整理を 主要1フロー整理へ戻す
- B03: bugfix-first + handoff later。二重メール送信を先に直し、整理は修正後に別対応
- B04: handoff-first。非エンジニア向けの決済から権限付与までの流れ整理
- B05: bugfix-first + light explanation boundary。修正関係ファイル/変更箇所説明は可、引き継ぎメモは別
- B06: handoff one-flow boundary。25,000円整理はリポジトリ全体やStripe全処理ではなく主要1フロー
- B07: neither。返金ボタン追加は新機能追加で、bugfix / handoff に吸収しない

この batch の主な失敗は、`handoff-first` と `neither` が `default_bugfix` へ吸収されること、軽い説明と引き継ぎメモの境界、相手文にない事情の context bleed。

### r2 軽微修正

Codex再監査で必須修正なし。軽微として、B04 は handoff-first の次アクションを `対象フローを「決済からユーザー権限付与まで」に絞って進めます` へ明確化した。B07 は neither 判定で `この2つの出品では対応範囲外です` を追加し、bugfix / handoff のどちらにも含めない着地を強めた。

### r3 user監査

B02 で、buyer はすでに「修正ではなく、危険箇所と関連ファイルのメモを作ってほしい」と決め打ちで依頼している。  
この場面で `整理する内容が合っています` と返すと、buyer が迷っていないのにこちらが route 判定を発表しているように見える。

修正方針:

- buyer が迷っていない依頼では、`こちらが合っています` のような適合診断を出さない
- `決済自体は動いていて、次の担当者へ渡す前に...整理したい、という内容ですね` のように、依頼内容を自然に受ける
- その後に、対象範囲・価格・次アクションを出す

外部のビジネス文例では `対応可能です` や `お引き受けいたします` は可否回答として使えるが、今回の違和感は敬語表現ではなく、buyer が迷っていない依頼に対して route 判定語を置いたことにある。したがって、禁止語追加ではなく、`decided request` と `route uncertainty` を分ける自然化観点として保持する。

### route state の分岐

`#BR` では、buyer の主目的だけでなく、buyer がすでに route を選んでいるかも見る。

#### 1. route_match_decided

buyer がすでに選んでいる route と、実際に案内すべき route が合っている状態。

例:

- `修正ではなく、危険箇所と関連ファイルのメモを作ってほしい`
- `今は壊れていないが、次の担当者へ渡せるように整理したい`

この場合は、`整理する内容が合っています` のような診断文を出さない。  
依頼内容を自然に受け、価格・範囲・次アクションへ進める。

良い流れ:

```text
決済自体は動いていて、次の担当者へ渡す前にStripeまわりの危険箇所と関連ファイルを整理したい、という内容ですね。

主要1フローの整理として、25,000円で対応できます。
```

#### 2. route_mismatch_decided

buyer がすでに何かを選んでいるが、実際の主目的と route がズレている状態。

例:

- 今止まっている不具合を直したいのに、整理側で頼もうとしている
- 新機能追加を、bugfix または handoff の範囲に入れようとしている
- リポジトリ全体の網羅調査を、主要1フロー整理として頼もうとしている

この場合は、受け流さずに誘導する。  
`今回は不具合修正からが近いです`、`これは新機能追加になるため、この2つの出品では対応範囲外です` のように、ズレを短く正す。

#### 3. route_uncertain

buyer がどちらに頼むべきか迷っている状態。

例:

- `修正と整理のどちらからお願いすればよいですか`
- `コードが分からないので、まず整理した方がいいですか`

この場合は、buyer に丸投げせず、主目的から順番を提案する。  
止まっている不具合が明確なら bugfix-first、壊れていない整理・引き継ぎが主目的なら handoff-first にする。

この3分岐は新しい監査レンズではなく、`boundary-route` の下位判定として扱う。

## batch-03 r0/r1（2026-04-28）

保存先:

```text
/home/hr-hm/Project/work/サービスページ/rehearsal/boundary-routing-返信学習/返信監査_batch-current.md
```

fixture:

```text
/home/hr-hm/Project/work/ops/tests/quality-cases/active/boundary-routing-shadow-br03.yaml
```

狙い:

- `route_match_decided`: buyer が正しい route をすでに選んでいる時、診断調にしない
- `route_mismatch_decided`: buyer の選択が主目的とズレている時、正しい入口へ誘導する
- `route_uncertain`: buyer が迷っている時、主目的から順番を提案する
- bridge: まず修正、後で整理を分ける
- neither: 新機能追加 + メモ希望を bugfix / handoff に吸収しない

r0 では、B01/B04 の handoff 決め打ち依頼、B06 の新機能追加、B07 の handoff + 修正境界が default bugfix へ吸収された。B02/B03/B05 は bugfix-first の方向は近いが、25,000円整理との順番や後続整理への回答が不足した。

### r1 手反映

Codex監査を受け、`返信監査_batch-current.md` を r1 へ更新した。

- B01: route_match_decided / handoff-first。壊れていない整理依頼を自然に受け、主要1フロー整理へ戻した
- B02: route_mismatch_decided / bugfix-first。buyer が整理側を候補にしていても、止まっている注文反映不具合を先に直す導線へ誘導した
- B03: route_uncertain / bugfix-first。buyer に選択を丸投げせず、まず15,000円の不具合修正から進める順番を提示した
- B04: route_match_decided / handoff-first。buyer が明示した「決済成功からユーザー権限付与まで」の1フロー整理として受けた
- B05: bugfix-first + later handoff。注文作成二重実行を先に直し、Webhook周辺の整理は修正後の別対応に分けた
- B06: neither / scope out。請求書CSVボタン追加は新機能追加として、この2つの出品では対応範囲外とした
- B07: handoff-first + no repair promise。整理は可能だが、小さいバグでもその場で修正作業までは含めないと明示した

この batch での学びは、`route_match_decided` は受け、`route_mismatch_decided` は誘導し、`route_uncertain` は順番提案する、という3分岐を #BR の gold として持つこと。

### r2 軽微修正

Codex再監査で必須修正なし。軽微として、B02/B03 は送信用の自然さを整え、B07 は handoff の対象を `1フロー` に絞る表現を追加した。

- B02: `整理より...入口が近いです` を `まずは注文反映が止まっている不具合修正から進めるのがよさそうです` へ変更
- B03: `15,000円内で` を `15,000円の範囲で` へ変更
- B07: `対象にする流れを1つに絞って` を追加し、25,000円整理が Stripe 連携全体の網羅に見えないようにした

handoff-25000 を #BR 内で扱う時は、`Stripe連携の流れ` や `決済まわり` のような広い表現だけで終えず、主要1フローに絞ることをできるだけ明示する。

## batch-04 r0/r1（2026-04-28）

保存先:

```text
/home/hr-hm/Project/work/サービスページ/rehearsal/boundary-routing-返信学習/返信監査_batch-current.md
```

fixture:

```text
/home/hr-hm/Project/work/ops/tests/quality-cases/active/boundary-routing-shadow-br04.yaml
```

狙い:

- handoff-first で、説明メモ・主要1フロー整理へ自然に入れるか
- active production defect を handoff に逃がさず bugfix-first にできるか
- active defect がない把握相談を bugfix にしないか
- 25,000円整理で Stripe全体 / DB全部の網羅を受けすぎないか
- handoff 中の軽微修正を吸収しないか
- 新機能追加 + メモ希望を neither にできるか
- bugfix 内の軽い変更箇所説明と、正式な引き継ぎ資料を分けられるか

r0 では、B01/B03/B04/B05/B06 が default bugfix へ強く吸収された。B07 は route は近いが、相手文にない `外注先と連絡が取れず` の context bleed が出た。

### r1 手反映

Codex監査を受け、`返信監査_batch-current.md` を r1 へ更新した。

- B01: handoff-first。壊れていない説明メモ依頼を、Stripe決済からユーザー権限付与までの主要1フロー整理として受けた
- B02: bugfix-first。buyer が整理側を候補にしていても、本番で購入履歴が作られない不具合を先に直す導線へ戻した
- B03: handoff-first。今すぐエラーがなく、次の外注先へ渡す前の把握が主目的なら整理から始めるとした
- B04: handoff scope boundary。25,000円整理は Stripe連携全体やDB全部の網羅ではなく、主要1フロー整理だと明示した
- B05: handoff no repair promise。整理中に軽微なバグが見つかっても、その場で修正作業までは含めないと切った
- B06: neither。月額プラン変更機能は新機能追加として、bugfix / handoff のどちらにも含めない
- B07: bugfix-first + light explanation boundary。修正後の変更ファイル・確認順の軽い説明は可、本格的な引き継ぎ資料は別とした

この batch での学びは、handoff-first は `壊れていない整理` だけでなく、`今すぐエラーはないが全体像を知りたい` 相談にも使うこと。ただし、25,000円整理は常に主要1フローまでであり、全体網羅や修正作業は含めない。

### r2 軽微修正

Codex再監査で必須修正なし。軽微として、handoff-first の文末導線を2件だけ補強した。

- B01: `Stripe決済からユーザー権限付与まで` に対象フローを絞って進めること、コード一式は購入後でよいことを追加
- B05: サブスク変更フローを1つに絞って整理することを最後に追加

この batch での追加学びは、handoff-first でも最後を `対象1フロー` / `購入後にコード共有` / `修正は含まない` のどれかで閉じると、buyer の次アクションが迷子になりにくいこと。

### r3 軽微修正

user監査で、B02 の `まず購入履歴が作られない不具合修正から` が、修正後に整理サービスへ進む前提を匂わせると指摘された。

B02 は buyer が整理メモを明確に欲しがっているのではなく、`コードが読めないので整理の方がいいのか` と迷っている状態。そこで、`まず` と `修正後に別対応` を弱め、`今回の目的が購入履歴が作られない状態を止めたいことなら、15,000円の不具合修正で対応する内容` とした。

この batch での追加学びは、route_mismatch_decided で正しい route に誘導する時も、`まず` を不用意に置くと後続サービス前提・追加購入前提に見えること。buyer が整理を本当に希望しているのか、単に不安で route を迷っているのかを分ける。

## batch-05 r0/r1（2026-04-28）

保存先:

```text
/home/hr-hm/Project/work/サービスページ/rehearsal/boundary-routing-返信学習/返信監査_batch-current.md
```

fixture:

```text
/home/hr-hm/Project/work/ops/tests/quality-cases/active/boundary-routing-shadow-br05.yaml
```

狙い:

- active defect なのに、コードが読めないため 25,000円整理へ迷う相談を bugfix-first に戻せるか
- buyer が明確に handoff を選んでいる整理依頼を bugfix に吸収しないか
- active defect がないリスク整理相談を handoff-first にできるか
- 25,000円整理で2フローを両方含めないか
- bugfix 内の軽い変更ファイル説明と本格 handoff を分けられるか
- 新機能追加 + 処理メモを neither にできるか
- handoff 中の小さいバグ修正を吸収しないか

r0 では、B02/B03/B04/B06/B07 が default bugfix へ吸収された。B05 は route は近いが、相手文にない `外注先と連絡が取れず` の context bleed が出た。

### r1 手反映

Codex監査を受け、`返信監査_batch-current.md` を r1 へ更新した。

- B01: bugfix-first。buyer が整理に迷っていても、主目的が注文ステータス未反映なら 15,000円の不具合修正で対応する内容とした。後続 handoff 前提は出さない
- B02: handoff-first。決済完了から注文作成までの主要1フロー整理として受け、修正作業は含まないとした
- B03: handoff-first。今すぐ壊れている不具合ではなく、危険箇所と関連ファイルを次の担当者へ渡す整理として受けた
- B04: handoff scope boundary。Checkout とサブスク変更は別フローなので、同じ25,000円内で両方まとめる前提にはしないと切った
- B05: bugfix-first + light explanation boundary。修正後の変更ファイルと確認順の軽い説明は可、本格的な引き継ぎ資料は別とした
- B06: neither。返金ボタン追加は新機能追加として、bugfix / handoff のどちらにも含めない
- B07: handoff no repair promise。整理中に小さいバグが見つかっても、その場で修正作業までは含めないと切った

この batch での学びは、`コードが読めないから整理の方がよいか` は必ず handoff 希望ではなく、active defect の解消が主目的なら bugfix-first に戻すこと。一方で、`今は壊れていない / 修正ではなく整理 / 主要1フロー` が明示されている時は handoff-first として受ける。

### r2 軽微修正

Codex再監査で必須修正なし。軽微として、B02/B04 の handoff 文末導線を補強した。

- B02: 対象フローを `決済完了から注文作成まで` に絞って進めることを最後に追加
- B04: 2フロー両方が必要な場合は、まず1フローを整理したうえで追加分として相談することを追加

この batch での追加学びは、handoff 側で可否や範囲を切った後に、`対象1フロー` と `追加フロー扱い` の着地を短く置くと、buyer が次に何を選べばよいか分かりやすいこと。

## batch-06 r0/r1（2026-04-28）

保存先:

```text
/home/hr-hm/Project/work/サービスページ/rehearsal/boundary-routing-返信学習/返信監査_batch-current.md
```

fixture:

```text
/home/hr-hm/Project/work/ops/tests/quality-cases/active/boundary-routing-shadow-br06.yaml
```

狙い:

- buyer が bugfix と handoff の両方を明示した時に、一括化せず分けられるか
- active defect がある時は bugfix-first にできるか
- active defect がない時は handoff-first にできるか
- セット割・一括価格を約束しないか
- 25,000円整理へ、複数フロー・正式仕様書・修正作業を吸収しないか
- 新機能追加と既存不具合を同じ入口にしないか
- bugfix 内の軽い変更ファイル説明と、本格 handoff 資料を分けられるか

r0 では、B01/B02/B04/B05/B07 が default bugfix へ吸収された。B03 は相手文にない `外注先と連絡が取れず` の context bleed が出た。B06 は請求書CSV出力の新機能追加を neither に落とせず、既存不具合の bugfix へ吸収した。

### r1 手反映

Codex監査を受け、`返信監査_batch-current.md` を r1 へ更新した。

- B01: bugfix-first + optional handoff。不具合修正は15,000円、修正後の決済から注文作成までの整理メモは必要なら別途25,000円の主要1フロー整理として分けた
- B02: handoff-first。今すぐ止まっているエラーがないため、決済完了から注文作成までの主要1フロー整理から入り、修正が必要なら別対応として相談するとした
- B03: separate scopes / no discount promise。購入履歴が作られない不具合修正と、決済フロー引き継ぎメモは成果物が別なので、一括料金やセット値引きを約束しないとした
- B04: split multiple flows and bugfix。Checkout / サブスク変更 / 返金処理の3フローを25,000円整理にまとめず、整理は1フローに絞り、Checkout後メール不具合は別の不具合対応とした
- B05: bugfix-first with light explanation。不具合修正後の変更ファイルと確認順の軽い説明は15,000円修正内で可、本格引き継ぎ資料は別とした
- B06: neither + bugfix split。請求書CSV出力は新機能追加として scope out し、既存の注文反映バグだけなら15,000円の不具合修正とした
- B07: handoff deliverable boundary。25,000円整理は正式仕様書や設計書ではなく、主要1フローの引き継ぎメモまでとした

### batch-06 の gold

#### bugfix + handoff 両方明示

buyer が両方を明示した場合は、片方へ潰さない。  
`順番`、`価格`、`成果物` を分けて返す。

- active defect が明確なら bugfix-first
- handoff は必要なら別途主要1フロー整理
- 15,000円修正と25,000円整理を一括料金にしない
- セット割や値引きを約束しない
- `まず bugfix、その後 handoff 必須` のような後続サービス前提にしない

#### handoff-first then possible bugfix

今すぐ止まっている不具合がなく、主要フロー整理が主目的なら handoff-first。  
整理中に壊れている箇所が見つかっても、修正をそのまま含めない。

良い骨格:

- 主要1フロー整理として受ける
- 修正が必要な箇所が見つかったら、整理の範囲に含めず別途相談
- コード一式は購入後でよい
- 見積り時点では対象フローだけ分かればよい

#### bundle discount pressure

`両方頼むので安く` への回答は、値引き可否より先に成果物分離を説明する。

- 不具合修正と引き継ぎメモは成果物が別
- 一括料金やセット値引きは約束しない
- 先に止めたい不具合があるなら bugfix-first

#### handoff scope and deliverable boundary

25,000円整理は主要1フローの引き継ぎメモまで。

含めないもの:

- 3フローまとめて整理
- Stripe連携全体やDB全部の網羅
- 正式仕様書・設計書レベルの資料作成
- ついでの不具合修正
- 新機能追加

外向けでは、`主要1フロー` と `対象フローを1つに絞る` をできるだけ明示する。

#### bugfix 内の軽い説明

修正後の変更ファイルと確認順だけで足りるなら、25,000円整理へ押し込まない。  
15,000円の不具合修正内で軽く伝えられる。

ただし、次担当者向けの本格的な引き継ぎメモや主要フロー整理は別対応。

#### neither plus existing bug

新機能追加と既存不具合が混ざった場合は、同じ入口にしない。

- 新機能追加はこの2つの出品には含めない
- 既存不具合だけなら bugfix で扱える
- 25,000円整理にも新機能追加を吸収しない

### 通常 live へ戻さないもの

- `25,000円` の外向け案内
- handoff の購入導線
- dual-service 前提のセット分離文

通常 live に戻してよいのは、`新機能追加を bugfix に吸収しない`、`相手文にない事情を出さない`、`修正後の軽い説明と本格引き継ぎ資料を分ける` など、bugfix 単体でも必要な境界だけ。

## batch-07 r0/r1（2026-04-28）

保存先:

```text
/home/hr-hm/Project/work/サービスページ/rehearsal/boundary-routing-返信学習/返信監査_batch-current.md
```

fixture:

```text
/home/hr-hm/Project/work/ops/tests/quality-cases/active/boundary-routing-shadow-br07.yaml
```

狙い:

- `25,000円整理で修正も含むか` という期待に対して、修正を handoff へ吸収しないか
- `15,000円修正枠で整理だけ見たい` という cheap-route mismatch を bugfix へ吸収しないか
- buyer が正しく handoff を選んでいる時、診断調や context bleed に崩れないか
- bugfix 後に handoff まで同日で続ける約束をしないか
- 新機能追加 + メモ希望を neither に落とせるか
- handoff の成果物を職種別資料・設計書レベルへ広げないか
- bugfix 内の軽い説明で足りるケースに handoff を押し込まないか

r0 では、B02/B03/B05/B06 が default bugfix へ吸収された。B03 は相手文にない `外注先と連絡が取れず` の context bleed が出た。B01/B04/B07 は bugfix-first の方向は近いが、主質問への直答と価格・成果物分離が不足した。

### r1 手反映

Codex監査を受け、`返信監査_batch-current.md` を r1 へ更新した。

- B01: route mismatch / active defect。25,000円整理には修正作業は含まれず、注文作成停止は15,000円の不具合修正として扱うと明示した
- B02: cheap-route mismatch。壊れていない危険箇所整理は15,000円修正枠ではなく、25,000円の主要1フロー整理として扱うとした
- B03: route_match_decided / handoff-first。正式仕様書ではない簡単な引き継ぎメモとして、25,000円の主要1フロー整理で受けた
- B04: bugfix plus later handoff。購入履歴不具合は15,000円修正、決済フローのメモは別成果物。同日対応は約束しないとした
- B05: neither。Customer Portal 導入は新機能追加として、15,000円修正にも25,000円整理にも含まれないとした
- B06: handoff audience boundary。エンジニア/デザイナー向けに分けた資料や設計書レベルまでは含まず、主要1フローの引き継ぎメモまでとした
- B07: bugfix only + light explanation。修正箇所と影響範囲だけで足りるなら、15,000円修正内の軽い説明で足り、25,000円整理は不要とした

### r2 軽微修正

Codex再監査で必須修正なし。軽微として、B05 の `別の新機能開発としてご相談ください` を `別の新機能開発として扱う必要があります` に弱めた。新機能側をこちらから受ける前提に見せないため。

### batch-07 の gold

#### handoff repair boundary

`25,000円整理を頼めば修正も含まれるか` には、修正は含まれないと明示する。  
active defect がある場合は、まず15,000円の不具合修正として扱う。

良い骨格:

- 25,000円整理には修正作業までは含まれない
- 止まっている不具合は15,000円修正
- 整理が必要なら別途主要1フロー整理
- 1回で両方をまとめて完了する前提にはしない

#### cheap-route mismatch

`15,000円修正枠で危険箇所だけ見たい` は bugfix へ吸収しない。  
今壊れていないなら、危険箇所・関連ファイル・次に見る順番の整理は handoff 側。

#### handoff decided without diagnostic wording

buyer が正しく handoff を選んでいる時は、`整理が合っています` のような route 診断ではなく、依頼内容を自然に受ける。

例:

```text
正式な仕様書までは不要で、次の外注先がStripe決済から注文作成までを追えるようにする引き継ぎメモですね。
```

#### no same-day promise

bugfix 後に handoff を同日で続けてほしいと言われても、同日対応を約束しない。  
修正内容と確認が終わってから、整理が必要かを分けて相談する。

#### handoff audience boundary

handoff は、主要1フローについての処理の流れ・関連ファイル・注意点・次に見る順番をまとめる引き継ぎメモまで。  
エンジニア向け/デザイナー向けの職種別資料や、設計書レベルの資料は含めない。

#### bugfix light explanation enough

修正箇所と影響範囲だけで足りるなら、15,000円の不具合修正内の軽い説明で足りる。  
本格的な引き継ぎ資料や主要フロー整理が必要な時だけ、25,000円整理として分ける。

#### new feature plus memo

Customer Portal 導入などの新機能追加と、その処理メモは、15,000円修正にも25,000円整理にも含まれない。  
既存フローの整理ではなく、新しく追加する機能に付随する説明として扱う。

### 通常 live へ戻さないもの

- `25,000円` の外向け案内
- handoff の購入導線
- dual-service 前提の比較文

通常 live に戻してよい候補:

- 新機能追加を不具合修正へ吸収しない
- 修正後の軽い説明と本格的な引き継ぎ資料を分ける
- 相手文にない背景事情を足さない
- 同日対応や一括対応を安易に約束しない

## batch-11 r0/r1（2026-04-28）

保存先:

```text
/home/hr-hm/Project/work/サービスページ/rehearsal/boundary-routing-返信学習/返信監査_batch-current.md
```

fixture:

```text
/home/hr-hm/Project/work/ops/tests/quality-cases/active/boundary-routing-shadow-br11.yaml
```

狙い:

- active defect を、整理を先に挟む前提へ逃がさない
- handoff で secret / APIキー / DB接続URL / 接続先URL の値そのものを扱わない
- E2Eテスト、自動テスト、テスト仕様書を handoff に含めない
- 複数フローや Stripe 全体監査を 25,000円整理へ吸収しない
- 不具合修正と handoff メモの同日・一括完了を約束しない
- 社内向け対応フローや復旧手順書を handoff に含めない
- buyer が正しい handoff 依頼を決め打ちしている時、診断調にしない

r0 では、B02/B03/B06/B07 が default bugfix へ強く吸収された。B04 も不具合相談へ誤寄せされ、B05 は不具合修正側へ寄る一方で handoff メモとの成果物分離と同日約束の否定が不足した。

### r1 手反映

Codex監査を受け、`返信監査_batch-current.md` を r1 へ更新した。

- B01: bugfix-first。注文がDBに作られない active defect は15,000円の不具合修正で扱い、25,000円整理を先に挟む前提にしない
- B02: handoff-first + secret safety。キー名・場所・用途は整理できるが、secret / APIキー / DATABASE_URL / 接続先URLの値そのものは扱わない
- B03: neither。E2Eテスト・Webhook自動テスト・テスト仕様書は、25,000円整理に含めない
- B04: handoff-first + one-flow boundary。Checkout / Customer Portal / 返金 / サブスク変更を全部まとめず、優先する1フローに絞る
- B05: bugfix-first + handoff separate。不具合修正と次担当者向けメモは別成果物で、同日完了を約束しない
- B06: neither。社内向け対応フロー・復旧手順書・スタッフ運用資料は、コードの主要1フロー整理とは別
- B07: route_match_decided / handoff-first。buyer が修正ではなく整理を明示しているため、診断文を出さず依頼内容を受けて範囲・価格・次アクションへ進めた

### r2 軽微修正

外部 Codex 監査で必須崩れなし・採用圏。軽微として、B02 の文末を `対象フローを1つに絞って進めます` から、`たとえば「決済完了から注文作成まで」のように対象フローを1つに絞って進めます` へ変更した。

理由は、環境変数や接続先URLの整理依頼では、`対象フローを1つ` だけだと環境変数全体の棚卸しへ広がる余地があるため。新規 rule 追加はせず、batch 内の case_fix として扱う。

### batch-11 の gold

#### config / URL safety in handoff

handoff で扱えるのは、キー名・使われている場所・用途・確認すべき設定箇所まで。
secret、APIキー、DB接続URL、接続先URLの値そのものは扱わず、送付も求めない。

#### test and runbook spillover

テスト追加、テスト仕様書、社内向け対応フロー、復旧手順書、スタッフ運用資料は、主要1フローの引き継ぎメモに含めない。
Stripe関連というだけで handoff に吸収しない。

#### active defect sequencing

今止まっている不具合が主目的なら bugfix-first。
`コードの流れが分からない` は buyer の状態であり、25,000円整理を先に必須化する根拠ではない。

#### no same-day combined promise

不具合修正と handoff メモを同時に頼まれた場合でも、同日・一括完了は約束しない。
修正後の変更ファイルや確認手順の軽い説明と、次担当者向けの主要1フロー整理は分ける。

### 通常 live へ戻さないもの

- `25,000円` の外向け案内
- handoff の購入導線
- dual-service 前提の比較文

通常 live に戻してよい候補:

- secret / APIキー / DB接続URL / 接続先URL の値そのものを扱わない
- テスト追加や運用資料を不具合修正へ吸収しない
- 修正後の軽い説明と本格的な引き継ぎ資料を分ける
- 同日対応や一括対応を安易に約束しない

## batch-12 r0/r1（2026-04-28）

保存先:

```text
/home/hr-hm/Project/work/サービスページ/rehearsal/boundary-routing-返信学習/返信監査_batch-current.md
```

fixture:

```text
/home/hr-hm/Project/work/ops/tests/quality-cases/active/boundary-routing-shadow-br12.yaml
```

狙い:

- active defect は bugfix-first にしつつ、直接 push や本番デプロイまで約束しない
- handoff を GitHub PRコメントや外部リポジトリ上のレビュー作業へ広げない
- 月次監視、Slack通知、継続保守、一次対応を bugfix / handoff に吸収しない
- active defect でも、DB設計変更やマイグレーションまで15,000円内に約束しない
- 複数リポジトリでも、直接つながる1フローに限定する
- Stripe APIバージョン更新やNext.js移行を bugfix / handoff に含めない
- buyer が no-repair handoff を決め打ちしている時、診断文や不具合修正導線へ崩れない

r0 では、B02/B05/B07 の handoff-first が default bugfix へ吸収された。B03/B06 の neither も active defect 風の generic boundary へ流れた。B01/B04 は bugfix-first の方向は近いが、直接push・本番デプロイ・DB設計変更/マイグレーションを切る回答が不足した。

### r1 手反映

Codex監査を受け、`返信監査_batch-current.md` を r1 へ更新した。

- B01: bugfix-first + no direct push/deploy。決済後の有料プラン未反映は15,000円修正で扱うが、GitHub直接pushとVercel本番反映は含めない
- B02: handoff-first + memo not PR review。決済から注文作成までの危険箇所整理は可能だが、GitHub PRへ直接コメントするコードレビューではなく引き継ぎメモで返す
- B03: neither。月次確認、Slack通知監視、エラー時の一次対応は継続保守であり、bugfix / handoff に含めない
- B04: bugfix-first + migration boundary。注文作成不具合は修正対象だが、DB設計見直しや大きなマイグレーションは15,000円内で約束しない
- B05: handoff-first + multi-repo one-flow。3リポジトリでも直接つながる1フローなら候補。ただし3repo全体監査へ広げない
- B06: neither。Stripe APIバージョン更新や Pages Router から App Router への移行は、この2つの出品に含めない
- B07: route_match_decided / no-repair handoff。修正不要の設定・処理つながり整理を、secret値なしで主要1フロー整理として受ける

### r2 軽微修正

外部 Codex 監査で必須崩れなし・採用圏。軽微として、B06 の範囲外判定後の整理候補補足を短く締めた。

`既存フローを整理するだけであれば25,000円の整理候補になりますが` は、neither 判定後に少し横へ広がるため、`既存フローの整理だけが目的であれば別の整理対象になりますが` へ変更した。新規 rule 追加はせず、batch 内の case_fix として扱う。

### batch-12 の gold

#### bugfix work-surface boundary

active defect は bugfix-first でよいが、GitHub への直接 push、本番デプロイ、外部リポジトリ上での作業完了までは含めない。
修正済みファイル、変更内容、適用手順、確認手順を返し、本番反映は依頼者側で行う。

#### handoff memo vs repository review

handoff は、主要1フローの関連ファイル・処理の流れ・危険箇所・次に見る順番をメモとして返す。
GitHub PRへの直接コメント、外部リポジトリ上でのレビュー作業、正式なコードレビュー運用には広げない。

#### monitoring and migration are neither

月次監視、Slack通知監視、継続保守、エラー時一次対応、APIバージョン更新、フレームワーク移行は、bugfix / handoff のどちらにも含めない。

#### bugfix with possible design change

active defect の原因が広い設計変更やDBマイグレーションに及びそうな場合でも、最初から15,000円内で進めるとは約束しない。
既存実装の中で確認し、広い変更が必要なら作業前に進め方と費用の有無を相談する。

### 通常 live へ戻さないもの

- `25,000円` の外向け案内
- handoff の購入導線
- dual-service 前提の比較文

通常 live に戻してよい候補:

- 直接push・本番デプロイを約束しない
- 継続監視や外部チャンネル運用を不具合修正へ吸収しない
- 大きなDB設計変更やフレームワーク移行を15,000円修正へ吸収しない
- secret 値を求めず、設定名・用途・場所までに留める

## BR13 以降の重点（neither 強化）

前 Codex からの引き継ぎとして、BR13 以降は `handoff に見えるが実は neither` 系を厚めに鍛える。

優先して当てる境界:

- 顧客対応FAQ / スタッフ操作マニュアル / 社内運用マニュアル
- 正式仕様書 / 設計書 / 職種別資料
- Stripe管理画面の操作手順書
- 新機能追加後の説明メモ
- secret / APIキー / env の値そのものをまとめたい相談
- 複数repo / 複数フロー / DB全部 / Stripe全体を 25,000円に入れたい相談
- `原因だけ安く` `軽く見て` `診断だけ` など、bugfix を安価な diagnosis-only に崩す相談
- `整理中に小さいバグが見つかったら直せるか` など、handoff に修正を吸収させる相談

狙いは、bugfix / handoff の二択を強めることではなく、どちらにも入れないものを冷たくならず自然に切ること。

## 通常 live / #RE へ戻す候補

通常 live / `#RE` に戻してよいのは、`handoff-25000` の名前・25,000円・購入導線を含まない汎用境界だけ。

戻してよい候補:

- 新機能追加は bugfix に吸収しない
- 顧客対応FAQ / スタッフ操作マニュアルは不具合修正に含めない
- secret / APIキー / Webhook secret の生値は扱わない。キー名・設定箇所・用途まで
- active defect がある場合、原因だけ安く見る入口は作らない
- bugfix 内で許されるのは、修正ファイル・変更箇所・確認順の軽い説明まで
- 本格的な引き継ぎ資料、仕様書、運用マニュアルは bugfix に含めない
- 相手文にない外注先事情・コード引き継ぎ背景を足さない

通常 live / `#RE` に戻さないもの:

- `25,000円`
- `handoff-25000`
- 主要1フロー整理サービスへの購入導線
- dual-service 前提の `どちらのサービス` 案内

## 次回 Pro 分析の論点候補

すぐに Pro へ投げず、BR13〜BR15 くらいまで回してからが理想。渡す時は BR10〜BR15 の r0/r1 の差分と、採用された gold をまとめる。

見るべき論点:

- `#BR` の route taxonomy は十分か
  - bugfix-first
  - handoff-first
  - bridge
  - neither
  - diagnosis-only pressure
  - cheap-route mismatch
  - bundle pressure
  - deliverable boundary
- neither の分類が広すぎ/狭すぎないか
- 25,000円の主要1フロー境界は自然か
- handoff-first で `修正は含まない` と言う文面が硬すぎないか
- bugfix-first から handoff を必要以上に売り込んでいないか
- `#BR` の学びを通常 live / `#RE` に戻す候補と、shadow asset に留める候補の線引き
- route 判定を外向け文面に出しすぎて bot 感が出ていないか

## batch-13 r0/r1（2026-04-28）

保存先:

```text
/home/hr-hm/Project/work/サービスページ/rehearsal/boundary-routing-返信学習/返信監査_batch-current.md
```

fixture:

```text
/home/hr-hm/Project/work/ops/tests/quality-cases/active/boundary-routing-shadow-br13.yaml
```

狙い:

- 顧客対応FAQや返答案テンプレートを、コード handoff に吸収しない
- Stripe管理画面の操作手順書を、主要1フロー整理へ吸収しない
- 正式仕様書・設計書・職種別資料を、25,000円整理へ含めない
- 新機能追加後の説明メモを、bugfix / handoff に吸収しない
- secret / APIキー / env / DB接続文字列の値そのものを扱わない
- 複数repo / DB全部 / Stripe全体を、25,000円の1フロー整理に入れない
- active defect を `原因だけ安く` `診断だけ` の入口へ崩さない
- handoff 中に見つかった小さいバグ修正を、25,000円整理へ吸収しない

r0 では、B01〜B05/B08 の neither / handoff boundary が default bugfix や generic boundary へ強く吸収された。B01 は相手文にない `外注先と連絡が取れず` の context bleed も出た。B06 は複数箇所の不具合修正相談のように誤読され、B07 は bugfix-first の方向は近いが diagnosis-only 圧力への直答が不足した。

### r1 手反映

Codex監査を受け、`返信監査_batch-current.md` を r1 へ更新した。

- B01: neither。顧客対応FAQ / 返答案テンプレートはコードの主要1フロー整理に含めない
- B02: neither。Stripe管理画面のスタッフ向け操作手順書は handoff に含めない
- B03: neither。正式仕様書・設計書・職種別資料は25,000円整理に含めない
- B04: neither。紹介クーポン自動付与の新機能追加と、その説明メモは bugfix / handoff に含めない
- B05: neither / secret safety。secret値そのものの台帳作成は扱わず、主要1フローに関係するキー名・場所・用途までに留める
- B06: handoff-first + not full audit。外注先へ渡す整理目的は handoff に近いが、複数repo・DB全部・Stripe全体監査は25,000円に含めない
- B07: bugfix-first / not diagnosis-only。active defect を原因だけ安く見る入口へ崩さず、原因確認から修正済みファイル返却までの料金として返す
- B08: handoff-first / no repair absorption。整理中に見つかった小さいバグを25,000円整理へ吸収せず、候補メモと別対応に分ける

### r1 外部監査

batch 13 / r1 revised は必須崩れなし・採用圏。対象名ズレもなし。

FAQ、操作手順書、正式仕様書、新機能説明メモ、secret値台帳、全体監査、diagnosis-only pressure、handoff repair absorption を、bugfix / handoff へ誤吸収せずに切れている。

B06 の `目的自体は主要1フロー整理に近いです` は少し診断調だが、全体監査要求を対象1フローへ戻す前置きとして許容範囲。preference 扱いで本文修正は行わず、r1 accepted とする。新規 rule 追加は不要。

### batch-13 の gold

#### neither without coldness

`この2つの出品では対応範囲外です` と切る場合でも、何が対象外か、なぜ handoff / bugfix ではないかを1〜2文で説明する。
FAQ、操作手順書、正式仕様書、職種別資料、新機能説明メモは、Stripe関連でもコードの主要1フロー整理ではない。

#### raw secret inventory

secret / APIキー / env / DB接続文字列の値そのものをまとめる台帳は扱わない。
主要1フロー内で整理できるのは、キー名、使われている場所、用途、次の担当者が確認すべき設定箇所まで。

#### full audit pressure

複数repo / DB全部 / Stripe全体を一通り見る相談は、25,000円の主要1フロー整理に吸収しない。
handoff として受ける場合も、優先する1フローに絞る。

#### diagnosis-only pressure

active defect では、`原因だけ安く` `診断メモだけ` の入口を作らない。
bugfix は原因確認から修正済みファイル返却までを含む料金として扱う。

#### repair absorption in handoff

handoff 中に小さいバグや直せそうな箇所が見つかっても、その場で修正作業まで進めるとは約束しない。
整理では怪しい箇所・影響しそうな処理・次に直すべき候補をメモし、修正が必要なら別対応として相談する。

### 通常 live へ戻さないもの

- `25,000円` の外向け案内
- handoff の購入導線
- dual-service 前提の比較文

通常 live に戻してよい候補:

- 顧客対応FAQ / スタッフ操作マニュアル / 正式仕様書 / 新機能追加は bugfix に吸収しない
- secret / APIキー / Webhook secret の生値は扱わない
- 原因だけ安く見る入口は作らない
- 修正後の軽い説明と、本格的な引き継ぎ資料・仕様書・運用マニュアルを分ける
- 相手文にない外注先事情・コード引き継ぎ背景を足さない

## batch-14 r0/r1/r2（2026-04-28）

保存先:

```text
/home/hr-hm/Project/work/サービスページ/rehearsal/boundary-routing-返信学習/返信監査_batch-current.md
```

fixture:

```text
/home/hr-hm/Project/work/ops/tests/quality-cases/active/boundary-routing-shadow-br14.yaml
```

狙い:

- コードが分からない buyer の active defect を、先に handoff が必要な形へ逃がさない
- buyer が有効な handoff を明示している時、診断調にせず受ける
- bugfix 内の軽い説明と、本格 handoff を分ける
- handoff をローカル環境構築、起動保証、README整備、サポートへ広げない
- handoff を GitHub Issue / PRコメント / ラベル付けなど外部repo作業へ広げない
- 広い設計レビュー・改善提案を25,000円の主要1フロー整理へ吸収しない
- 値を扱わない secret-safe settings map は、対象1フローに限って handoff として受ける
- 15,000円修正と25,000円整理を25,000円内のセット扱いにしない

r0 では、B02/B04/B05/B07 の handoff-first が default bugfix / code_handoff_bugfix_scope へ吸収された。B06 は具体的な active defect がない全体設計レビュー相談だが、原因不明の不具合相談のように誤読された。B01/B08 は bugfix-first の方向は近いが、handoff を必須にしないこと、bundle として吸収しないことの直答が不足した。

### r1 手反映

Codex監査を受け、`返信監査_batch-current.md` を r1 へ更新した。

- B01: bugfix-first / not required handoff。コードが分からなくても、注文作成停止の active defect は先に25,000円整理を挟まず15,000円修正から確認できる
- B02: handoff-first / decided request。動いている決済完了から注文作成までの1フロー整理を、診断調にせず25,000円整理として受ける
- B03: bugfix-first / light explanation not handoff。修正ファイルと確認手順の軽い説明は15,000円修正内で足りる
- B04: handoff-first / not environment setup support。1フロー整理は受けるが、環境構築手順、起動保証、README整備、起動できない時のサポートは含めない
- B05: handoff-first / memo not GitHub work-surface。危険箇所整理はメモで返し、GitHub Issue作成・PRコメント・ラベル付けは含めない
- B06: neither / architecture review mismatch。広い設計レビュー・改善提案は、bugfix / handoff のどちらにも吸収しない
- B07: handoff-first / secret-safe settings map。値そのものを扱わず、1フローに関係するキー名・設定箇所・用途だけ整理する
- B08: bugfix-first then separate handoff / no bundle discount。不具合修正と整理メモを25,000円内へまとめない

### r2 軽微修正

外部 Codex 監査で必須崩れなし・採用圏。軽微として、B02 の購入後共有物の表現だけ締めた。

`対象リポジトリまたは該当コード一式を共有してください` は、文脈上はコード共有の意味だが、GitHub招待や外部repo上作業を連想する余地があるため、`該当コード一式や関係ファイルを共有してください` へ変更した。新規 rule 追加はせず、batch 内の case_fix として扱う。

### batch-14 の gold

#### active defect with code confusion

buyer が `コードが分からない` `AIで作った` と言っていても、今止まっている不具合を直したいなら bugfix-first。
handoff を先に挟むことを必須にしない。

#### decided handoff without diagnosis

buyer が `修正不要` `次の担当者向け` `決済完了から注文作成まで` のように対象1フローを自然に決めている場合は、適合診断を返さず、範囲・成果物・価格・購入後共有へ進める。

#### light explanation boundary

bugfix の納品で、修正ファイル・変更箇所・確認手順を軽く説明するのは15,000円修正内で足りる。
本格的な引き継ぎメモ、主要1フロー整理、正式資料へ広げない。

#### handoff work-surface boundary

handoff は、対象1フローの関連ファイル、処理の流れ、注意点、次に見る順番をメモで返す。
ローカル環境構築、起動保証、README整備、継続サポート、GitHub Issue/PR/label作業には広げない。

#### architecture review mismatch

Stripe決済、サブスク、返金、管理画面、DB設計まで含む広い設計レビューや改善提案は、25,000円の主要1フロー整理ではない。
既存コードの対象1フロー整理と、全体設計コンサルを分ける。

#### bundle pressure

15,000円の不具合修正と25,000円の主要1フロー整理を、25,000円内の一括料金として約束しない。
active defect がある場合は、まず不具合修正を優先し、整理メモが必要なら別成果物として扱う。
支払い方法や同じトークルーム内で続けられるかは transaction / platform policy の話であり、#BR の route gold では前面に出さない。

### 通常 live へ戻さないもの

- `25,000円` の外向け案内
- handoff の購入導線
- dual-service 前提の比較文

通常 live に戻してよい候補:

- コードが分からない buyer でも、止まっている不具合は bugfix-first にする
- 修正ファイル・変更箇所・確認手順の軽い説明は bugfix 内で足りる
- ローカル環境構築、起動保証、README整備、GitHub Issue/PR作業を不具合修正へ吸収しない
- 広い設計レビュー・改善提案を不具合修正へ吸収しない
- secret 値を求めず、キー名・設定箇所・用途までに留める

## batch-15 r0/r1/r2（2026-04-29）

保存先:

```text
/home/hr-hm/Project/work/サービスページ/rehearsal/boundary-routing-返信学習/返信監査_batch-current.md
```

fixture:

```text
/home/hr-hm/Project/work/ops/tests/quality-cases/active/boundary-routing-shadow-br15.yaml
```

狙い:

- service boundary と payment route を混ぜない
- buyer が支払い方法を聞いていない時に、同じトークルーム内 / おひねり / 有料オプションを前面に出さない
- prequote で、まだ存在しないトークルーム内追加支払いを約束しない
- purchased / delivered で、buyer が支払い方法を明示した時だけ、状態に応じて支払い導線を返す
- closed で、旧トークルーム内のおひねりや追加購入へ誘導しない
- 15,000円修正と25,000円整理を、一括料金・セット割・同日保証へ寄せない
- handoff 中の修正を吸収せず、修正は別対応として分ける
- active defect を cheap trial や handoff 必須へ崩さない

r0 では、prequote 4件のうち B02 が handoff-first ではなく default bugfix へ吸収された。B01/B03/B04 は bugfix-first の方向は近いが、buyer が聞いている支払い導線、cheap trial、同じトークルーム/セット割圧力への直答が不足した。B05〜B08 は state edge のため renderer 対象外として手反映した。

### r1 手反映

Codex監査を受け、`返信監査_batch-current.md` を r1 へ更新した。

- B01: prequote / bugfix-first + no prequote ohineri promise。注文作成停止は15,000円修正。整理メモは別成果物。購入前に同じトークルーム内・おひねり追加を前提にしない
- B02: prequote / handoff-first + no payment route。壊れていない1フロー整理は25,000円整理として受け、怪しい箇所は次に直す候補メモまで。支払い導線は出さない
- B03: prequote / bugfix-first + no cheap trial。15,000円修正を安い診断試し枠にせず、25,000円整理への自動切替にも寄せない
- B04: prequote / split deliverables + no bundle。修正と整理を別成果物として分け、同じトークルームや一括化を理由にセット割を約束しない
- B05: purchased / state-allowed payment route。現在の bugfix を先に完了し、後続整理は別成果物。buyer が聞いているため、トークルームが開いている間の追加支払いを条件付きで案内する
- B06: purchased / handoff repair split。整理中の決済停止は修正として別threadに分け、追加料金は自動発生しない。作業前に進め方と費用を相談する
- B07: delivered / not closed payment route。正式納品後・クローズ前は追加相談自体は可能。ただし整理メモは今回納品と別成果物で、合意後に追加支払い
- B08: closed / no old talkroom ohineri。クローズ後は旧トークルーム内のおひねり追加不可。メッセージ上で確認し、新しい見積り提案または新規依頼へ戻す

### r2 軽微修正

外部 Codex 監査で必須崩れなし・採用圏。軽微として、B07 の支払い導線の断定だけ弱めた。

`合意後におひねり等の追加支払いで進める形になります` は、delivered / クローズ前の支払い導線としては妥当だが少し断定寄りのため、`合意後におひねり等の追加支払いで進められる場合があります` へ変更した。新規 rule 追加はせず、batch 内の case_fix として扱う。

### batch-15 の gold

#### service boundary vs payment route

`bugfix / handoff / neither` は、主目的・成果物・サービス範囲で先に決める。
`同じトークルーム内`、`おひねり`、`有料オプション`、`新規依頼` は、その後の取引状態に応じた支払い導線として扱う。

#### prequote payment route pressure

prequote で buyer が `同じトークルーム内` や `おひねり` を聞いても、まだ存在しない取引中の導線を約束しない。
`必要になった時点で、取引状態に合わせて進め方と費用を先に相談する` までに留める。

#### payment route only when asked

buyer が支払い方法を聞いていないなら、`別成果物`、`別対応`、`進め方と費用を先に相談` までで止める。
おひねり・有料オプション・同じトークルーム内導線は前面に出さない。

#### purchased / delivered state route

purchased / delivered で buyer が明示的に追加支払い方法を聞いた場合は、トークルームが開いている間の追加支払い導線を条件付きで案内してよい。
ただし、自動追加料金、後続サービス前提、同日保証、セット割にしない。

#### closed route

closed 後は、旧トークルーム内のおひねりや追加購入へ誘導しない。
メッセージ上で内容を確認し、実作業が必要なら新しい見積り提案または新規依頼へ戻す。

### 通常 live へ戻さないもの

- `25,000円` の外向け案内
- handoff の購入導線
- dual-service 前提の比較文

通常 live に戻してよい候補:

- 支払い導線とサービス境界を混ぜない
- buyer が支払い方法を聞いていない時に、おひねり・有料オプション・同じトークルーム内導線を先回りしない
- prequote でトークルーム内追加支払いを約束しない
- closed 後に旧トークルーム内のおひねりを案内しない

## batch-16 r0/r1（2026-04-29）

保存先:

```text
/home/hr-hm/Project/work/サービスページ/rehearsal/boundary-routing-返信学習/返信監査_batch-current.md
```

fixture:

```text
/home/hr-hm/Project/work/ops/tests/quality-cases/active/boundary-routing-shadow-br16.yaml
```

狙い:

- Pro 4/29 対応後に、source cleanup / public-private wording separation / payment-route isolation が効いているか確認する
- active defect を 25,000円整理へ逃がさない
- valid handoff で、支払い導線や修正成功を先回りしない
- bugfix 内の軽い説明と、主要1フロー整理を分ける
- handoff 中の修正候補を、25,000円内の修正作業へ吸収しない
- delivered と closed の micro-state を誤認しない
- closed 後に旧トークルーム内のおひねりへ誘導しない
- Stripe関連でも、操作手順書・顧客FAQを code handoff に吸収しない

### r0 手反映

Pro 4/29 後の確認走行として、`返信監査_batch-current.md` を r0 prepared として作成した。

- B01: active defect + 25,000円迷い。注文作成停止は bugfix-first とし、handoff 必須にしない
- B02: valid handoff。支払い導線を先回りせず、1フロー整理として受ける
- B03: bugfix light explanation。変更ファイルと確認順だけなら bugfix 内の軽い説明で足りる
- B04: handoff repair absorption。整理中の修正候補はメモに留め、修正作業は別対応に分ける
- B05: delivered before acceptance。承諾前確認と別件実作業を分ける
- B06: closed materials first。確認材料の受領と実作業開始を分ける
- B07: neither。Stripe関連でも、操作手順書・顧客FAQは code handoff に含めない
- B08: prequote same-room repair pressure。購入前に同じトークルーム内修正継続を約束しない

### r1 軽微修正

外部 Codex 監査で必須崩れなし・採用圏。軽微として、B07 の範囲外判定だけ締めた。

`25,000円の主要1フロー整理には含めにくいです` は、最終的に範囲外と言えているため hard fail ではないが、交渉余地がある言い方に見えるため、`25,000円の主要1フロー整理には含まれません` へ変更した。新規 rule 追加はせず、batch 内の case_fix として扱う。

### batch-16 の gold

#### post-Pro payment route confirmation

service boundary と payment route を分ける。prequote では、buyer が同じトークルーム内の後続修正を聞いても、まだ存在しない取引中導線を約束しない。

#### delivered / closed micro-state

delivered は closed ではない。承諾前なら、今回の修正との関係があるかを軽く確認できる。
closed 後は、ログやスクショの確認材料をメッセージ上で受けることはできるが、実作業は新しい見積り提案または新規依頼へ分ける。

#### neither boundary for operation docs

Stripe関連でも、スタッフ向けの管理画面操作手順書や顧客向けFAQは、既存コードの主要1フロー整理ではない。
`含めにくい` ではなく、必要な場面では `含まれません` と短く切る。

### 通常 live へ戻さないもの

- `25,000円` の外向け案内
- handoff の購入導線
- dual-service 前提の比較文

通常 live に戻してよい候補:

- delivered を closed へ早く戻しすぎない
- closed 後でも確認材料の受領と実作業は分ける
- 操作手順書・顧客FAQは code handoff / bugfix に吸収しない
- prequote で同じトークルーム内追加作業を約束しない
