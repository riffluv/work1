# #RE / #R Alignment Checklist

作成日: 2026-04-29

## 目的

- Pro の `返信OS品質監査4-29` を、実装と運用のチェックリストに落とす。
- `#RE` で見つけた自然さの違和感が、本丸 `#R` に効くものか、`#RE only` の癖かを分ける。
- renderer を全文返信生成器として太らせず、contract / safety / semantic slots / regression の役へ寄せる。

## 現時点の判断

- 骨格は維持する。
  - `service-registry.yaml`
  - `platform-contract.yaml`
  - service facts
  - public/private gate
  - secret safety
  - phase boundary
- 変えるのは `#RE / renderer / naturalizer` の接続。
- `#R` の実出力は、Codex の判断と `japanese-chat-natural-ja` により自然化が効いている可能性が高い。
- ただし、統合 renderer の自動 naturalizer はまだ `identity_only`。
- したがって、`#RE` の deterministic renderer 出力を、そのまま本丸 `#R` の文章品質として監査してはいけない。

## 反映済み

- [x] `#R` スモーク 5件を実施し、自然化が効いている標準文体を確認した。
- [x] `#R` スモークの良い文体を `r-smoke-style-anchors-20260429.ja.md` として保存した。
- [x] `返信監査_batch-01.md` を r7 とし、`#R` スモークの文体に寄せた `writer_candidate_manual` へ更新した。
- [x] r7 batch を `--candidate-batch-file` で検証した。
- [x] `render-coconala-reply.py` が `candidate_source / audit_target / contract_source / writer_used / naturalizer` を出せる。
- [x] `renderer_baseline` と `writer_candidate_manual` を区別できる。
- [x] `--writer-brief` で、同じ fixture から writer candidate 用の意味契約を出せる。
- [x] `--candidate-file` で、手動 `#R` 相当候補を同じ fixture / contract / lint に通せる。
- [x] `--candidate-batch-file` で、`#RE` markdown batch 内の返信候補をまとめて `writer_candidate_manual` として検証できる。
- [x] `closed_materials_check` に semantic slots を追加した。
- [x] HRC49-008 に `expected_semantics` を追加した。
- [x] 監査 prompt に `candidate_source` の見方を追加した。
- [x] `返信監査_batch-01.md` を r6 とし、監査対象を `writer_candidate_manual` に変更した。
- [x] full regression は通過済み。

## 一部反映

- [ ] `japanese-chat-natural-ja` には Deep Research / Pro の conversation flow rule が入っているが、統合 renderer の自動 naturalizer としてはまだ発火していない。
- [ ] `#R` は運用上、Codex が skill を読んで自然化するが、スクリプト上の writer stage としてはまだ自動化されていない。
- [ ] `#RE` batch は writer candidate として出せるようになったが、writer candidate 作成はまだ手動。
- [ ] naturalness warning は出るが、writer candidate 監査結果を `#R reproduced / #RE only / safety deterministic / preference` に機械集計するところまでは未実装。
- [ ] Gold は style anchor として使えるが、writer brief へ最小 few-shot として自動選定するところまでは未実装。

## 未反映

- [ ] 自動 LLM writer stage。
- [ ] `#RE fixture -> contract builder -> writer candidate -> final naturalizer -> validator` の完全自動 pipeline。
- [ ] `render-prequote-estimate-initial.py` / `render-post-purchase-quick.py` / `render-delivered-followup.py` の renderer shrink。
- [ ] `answer_brief / ask_text / direct_answer_line` を、完成文ではなく intent / semantic slot へ全面移行する作業。
- [ ] `#R` 実出力と `#RE writer_candidate` の差分比較レポート。
- [ ] 外部監査結果を `#R reproduced / #RE only` で戻し先分類する専用 log format。

## 次にやる順番

1. `#R` スモークを 3〜5 件だけ実施する。完了。
   - 金額＋納期
   - 原因不明相談
   - 購入後の受領確認
   - 短い進捗確認
   - closed 後の関係確認
2. `#R` で自然化が効いている文を、style anchor として短く保存する。完了。
   - 目的はテンプレ化ではなく、writer 判断の基準化。
3. `返信監査_batch-01.md` の writer candidate を、`#R` スモークで見えた標準文体へ寄せる。完了。
4. `--candidate-batch-file` で batch 全体を検証する。完了。
5. その後に外部監査へ出す。

## 外部監査に出す前のチェック

- [ ] batch metadata が `candidate_source: writer_candidate_manual` になっている。
- [ ] `writer_candidate_batch_validation` が通っている。
- [ ] 通常 live / #RE に `handoff-25000` / `25,000円` / `主要1フロー整理` が出ていない。
- [ ] `#R` スモークで近いケースの文体が破綻していない。
- [ ] 自然さ指摘を共通 rule へ戻す前に、`#R reproduced` か `#RE only` かを判定する前提が監査 prompt に入っている。

## 戻し先の判断

- `safety deterministic`
  - public leak、secret 値要求、phase drift、price/scope 崩れ。
  - validator / lint / renderer contract へ戻す。
- `#R reproduced`
  - `#R` 実出力でも自然さの問題が再現する。
  - `japanese-chat-natural-ja` / writer brief / gold へ戻す候補。
- `#RE only`
  - renderer baseline や rehearsal 文面だけの癖。
  - renderer / fixture / batch candidate 側で扱い、共通 skill へ戻さない。
- `preference`
  - 好み差。単発修正または gold 候補に留める。

## 2026-05-01 同期チェック

- HRC94-003 で、`#RE` の `writer_candidate_manual` は自然だったが、`--writer-brief` が `generic_quote_sent` に落ち、支払い後 ZIP 共有の主質問を拾えていなかった。
- `after_payment_zip_share_timing` を追加し、`支払い後に関係ファイルをZIPでまとめて送ればよいか` と `不要なものが混ざる不安` を意味契約へ分けた。
- この種のズレは自然化 skill ではなく、`#R / #RE` の contract 接続不良として扱う。
- 確認済み:
  - `--writer-brief` が `after_payment_zip_share_timing` を返す
  - candidate batch lint OK
  - full role suites OK
- 追加確認:
  - HRC94-002 は `progress_anxiety` に接続し、購入後の「今どこを見ているか」を汎用 follow-up に落とさない。
  - HRC94-004 は `prepayment_zip_sufficiency_check` に接続し、購入前 ZIP 足りているか確認を `quote_sent` の支払い前作業境界として扱う。
  - HRC94-007 は `closed_materials_check` に接続し、closed 後の「前回修正との関係確認」を通常の関係確認として扱う。
  - ただし `返金` を含む closed 後の関係確認は `refund_request` を優先し、通常の `closed_materials_check` に吸収しない。
- #RE91〜93 の追加同期確認:
  - 購入後の `今の見立て`、`何から見ているか`、`優先して見ているところ` は `progress_anxiety` へ接続し、`generic_followup` に落とさない。
  - 見積り提案後の `支払い後にまとめて送れば進められるか` は `after_payment_zip_share_timing` へ接続し、軽い手順確認を `generic_quote_sent` に落とさない。
  - 見積り提案後の `支払い前にエラー画面/zip/スクショだけ見て直せそうか判断してほしい` は `prepayment_materials_before_payment` へ接続し、支払い前作業境界を維持する。
  - closed 後の `前回修正との関係だけ見てもらえるか` は `closed_materials_check` へ接続する。ただし返金/無料圧が含まれる場合は高リスク経路を優先する。

## やらないこと

- renderer に職人風の固定文を大量登録しない。
- `#RE` の不自然さを、確認なしに `#R` の skill へ戻さない。
- 句点、`はい`、`まずは`、`確認` を blanket NG にしない。
- 自然化のために、金額・scope・phase・secret・public/private・payment route を変えない。
- Pro / Deep Research の raw 文を、そのまま正本 rule にしない。
