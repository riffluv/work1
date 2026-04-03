# 回帰確認メモ 2026-03-30

注記:
- 当時の plain text batch は `/home/hr-hm/Project/work/ops/tests/rehearsal/archive/raw-batches-2026-04-03.tar.gz` に圧縮退避済み
- 下記の `batch-*.txt` 表記は、当時の識別子を残すための履歴メモであり、現行の参照先ではない

## 対象
- `ops/tests/rehearsal/batch-EST-001-005-v2.txt`
- `ops/tests/rehearsal/batch-CLS-001-005-v2.txt`
- `ops/tests/rehearsal/batch-V6-BUG-001-005.txt`
- `ops/tests/rehearsal/batch-V6-CLS-018-020.txt`
- `ops/tests/rehearsal/batch-V6-BND-010-014.txt`
- `ops/tests/rehearsal/batch-V6-PURCLS-015-020.txt`

## 前提
- 履歴バッチは当時の rule を反映した記録であり、現行の正本ではない
- 現行の正本は `skill / judgment-flow / style-rules / self-check / golden-replies / test YAML`

## 確認結果

### 1. 構造 smoke
- `scripts/check-internal-os-flows.sh` は `OK`

### 2. 現行 rule と衝突した履歴表現
- `batch-EST-001-005-v2.txt`
  - `対応できる見込みです`
  - `本番環境で合っていますか`
- `batch-V6-CLS-018-020.txt`
  - `付ける形で進められます`
  - `別途ご案内する形になります`
  - `新規の整理依頼として見る形になります`
- `batch-V6-PURCLS-015-020.txt`
  - `付ける形で進められます`
  - `別途ご案内する形になります`
  - `新規の整理依頼として見る形になります`
- `batch-V6-BUG-001-005.txt`
  - `二重引き落とし` ケースで、被害拡大停止より先に切り分けへ入っている

### 3. 判定
- いずれも `現行 rule の穴` ではなく `履歴バッチの古さ`
- current public only / closed後 / duplicate handling / Ban 表現の修正方針は、現行の正本へすでに反映済み
- このため、履歴バッチ自体は `参考履歴` として残し、最新模範としては扱わない

## 今回の結論
- 追加の rule は不要
- 次の回帰確認は、履歴バッチの再解釈ではなく、現行 fixture を使った再生成で行う

## 現行 rule で再生成したバッチ
- `ops/tests/rehearsal/batch-EST-001-005-v3.txt`
- `ops/tests/rehearsal/batch-CLS-001-005-v3.txt`
- `ops/tests/rehearsal/batch-V6-BND-010-014-v2.txt`
- `ops/tests/rehearsal/batch-V6-BUG-001-005-v2.txt`

確認:
- `形になります`
- `見込みです`
- `追加料金の有無`
- `確認案件`
- `修正案件`

上記の drift 表現は、再生成バッチでは 0 件

### Claude 監査反映
- `batch-CLS-001-005-v3.txt`
  - `CLS-005` の `費用がかかる前提ではなく` を削除
- `batch-EST-001-005-v3.txt`
  - 書き出しと結語の同型連打を分散
- `batch-V6-BND-010-014-v2.txt`
  - 書き出しの同型連打を分散
  - `近いです` を `適しています` / `見られます` へ置換
- `batch-V6-BUG-001-005-v2.txt`
  - 書き出しの同型連打を分散
  - `近いです` を `進められます` へ置換

## 次段階で再生成したバッチ
- `ops/tests/rehearsal/batch-CHK-001-005-v3.txt`
- `ops/tests/rehearsal/batch-PRC-001-005-v3.txt`
- `ops/tests/rehearsal/batch-CMP-001-005-v2.txt`

確認:
- `形になります`
- `見込みです`
- `合っています`
- `返金をお約束できません`

上記の drift 表現は、追加した 3 バッチでも 0 件

意図:
- `CHK`: 旧確認案内の出し方を現行 rule に合わせる
- `PRC`: 値下げ可否へ価格そのもので直接答える
- `CMP`: 返金や苦情で、こちらが判断者に見えない順序へそろえる

## 次段階で再生成したバッチ 2
- `ops/tests/rehearsal/batch-MUL-001-005-v2.txt`
- `ops/tests/rehearsal/batch-SCP-001-005-v2.txt`
- `ops/tests/rehearsal/batch-QST-001-005-v2.txt`

確認:
- `形になります`
- `見込みです`
- `合っています`
- `近いです`

上記の drift 表現は、追加した 3 バッチでも 0 件

意図:
- `MUL`: 複数論点では、緊急度と同一原因の見込みで優先順を切る
- `SCP`: 1件にまとめない線引きと、purchased 中の追加別件の扱いをそろえる
- `QST`: quote_sent の直接質問に、制度説明で逃げず先に答える

## 次段階で再生成したバッチ 3
- `ops/tests/rehearsal/batch-EMO-001-005-v2.txt`
- `ops/tests/rehearsal/batch-CLO-001-005-v2.txt`
- `ops/tests/rehearsal/batch-FPO-001-005-v2.txt`
- `ops/tests/rehearsal/batch-OOS-001-005-v2.txt`
- `ops/tests/rehearsal/batch-V6-PUR-015-017-v2.txt`

確認:
- `形になります`
- `見込みです`
- `合っています`
- `近いです`
- `追加料金の有無`

上記の drift 表現は、追加した 5 バッチでも 0 件

意図:
- `EMO`: 感情が強い相談でも、受け止めは最小にして次アクションへ寄せる
- `CLO`: 再発・別件・新機能追加を、closed / 追加相談の境界で崩さない
- `FPO`: 前任や前回未返信の文脈を引きずらず、現症状から入口を切る
- `OOS`: 範囲外案内を `拒否 -> 提案 -> 再度拒否` にしない
- `V6-PUR`: purchased 中の外部API ずれ / 外部共有停止 / 別話題混入を現行 rule にそろえる

## 現時点で履歴扱いに留めるバッチ
- `ops/tests/rehearsal/batch-V6-HND-006-009.txt`
- `ops/tests/rehearsal/batch-V6-PURCLS-015-020.txt`

理由:
- `handoff` は未公開のため、外向け canonical batch として更新すると current-public-only と衝突しやすい
- `V6-PURCLS-015-020` の後半 (`018-020`) は、個別の golden reply と closed 後ルールで現行正本をすでに持っている
- このため、上記2本は履歴資産として残し、現行模範は `golden-replies` と個別の updated batch を優先する

## 次にやるなら
1. 現行 canonical batch を使った spot-check をもう1周回す
2. `edge-cases.yaml` と regenerated batch の対応漏れがないかだけ見る
3. `handoff` が公開状態へ変わった時だけ、`V6-HND` / `V6-PURCLS` を canonical 化する

## 最終 spot-check

### current canonical set
- `ops/tests/rehearsal/batch-CHK-001-005-v3.txt`
- `ops/tests/rehearsal/batch-CLO-001-005-v2.txt`
- `ops/tests/rehearsal/batch-CLS-001-005-v3.txt`
- `ops/tests/rehearsal/batch-CMP-001-005-v2.txt`
- `ops/tests/rehearsal/batch-EMO-001-005-v2.txt`
- `ops/tests/rehearsal/batch-EST-001-005-v3.txt`
- `ops/tests/rehearsal/batch-FPO-001-005-v2.txt`
- `ops/tests/rehearsal/batch-MUL-001-005-v2.txt`
- `ops/tests/rehearsal/batch-OOS-001-005-v2.txt`
- `ops/tests/rehearsal/batch-PRC-001-005-v3.txt`
- `ops/tests/rehearsal/batch-QST-001-005-v2.txt`
- `ops/tests/rehearsal/batch-SCP-001-005-v2.txt`
- `ops/tests/rehearsal/batch-V6-BND-010-014-v2.txt`
- `ops/tests/rehearsal/batch-V6-BUG-001-005-v2.txt`
- `ops/tests/rehearsal/batch-V6-PUR-015-017-v2.txt`

### grep 確認
- `形になります`
- `見込みです`
- `合っています`
- `近いです`
- `追加料金の有無`
- `handoff-25000`
- `25,000円`

上記は current canonical set で 0 件

### opening ローテーション
- 5件バッチはすべて `4/5` 以上の同一書き出しなし
- 3件バッチの `V6-PUR` も、`ありがとうございます。` `情報ありがとうございます。` `ご報告ありがとうございます。` に分散済み

### edge-cases coverage
- `EC-001` -> `short:§21`
- `EC-002` -> `short:§24`
- `EC-003` -> `short:§25`
- `EC-004` -> `short:§26`
- `EC-005` -> `short:§27`
- `EC-006` -> `golden:§53`
- `EC-007` -> `golden:§52`
- `EC-008` -> `golden:§46`

結論:
- `edge-cases.yaml` の 8 件は、現行の short template / golden reply に対応先あり
- public live (`bugfix-15000`) 側で使う rehearsal category は一通り現行 rule に寄せ直せた
- 残りは `handoff` 公開状態が変わるまで履歴資産のまま保持する

## 追加リハーサル
- `ops/tests/rehearsal/batch-PRF-001-005-v2.txt`
- `ops/tests/rehearsal/batch-MSG-001-005-v2.txt`

意図:
- `PRF`: profile 経由のざっくり相談で、medium fit / feasible / handoff未公開境界を崩さない
- `MSG`: message 経由の見積り相談で、15K / 5K / 保留の初手を現行 rule のまま出せるか確認する

確認:
- `形になります`
- `見込みです`
- `合っています`
- `近いです`
- `25,000円`

上記の drift 表現は、追加した 2 バッチでも 0 件

## 補足
- `§13-2` / `§13-3` は `docs/coconala-message-templates-short.ja.md` の参照
- `§46` `§52` `§53` などの代表文例は `docs/coconala-golden-replies.ja.md` の参照
