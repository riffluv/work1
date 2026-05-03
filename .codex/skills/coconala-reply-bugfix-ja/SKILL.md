---
name: coconala-reply-bugfix-ja
description: "ココナラのNext.js/Stripe/API不具合修正サービス専用。重複質問を避け、自然な日本語で、スコープ事故と規約事故を防ぐ返信を作る。"
---

# ココナラ返信（不具合修正 特化版 v1）

## 目的
- Next.js / Stripe / API連携の不具合修正案件で、送信用返信を短く自然に作る。
- 重複質問を減らし、購入者の不信感を防ぐ。
- 固定条件（価格 / 範囲 / 規約）を崩さない。

## 思考保全モード
- この skill は Codex 本体の判断を置き換えず、bugfix 固有の正本と guardrail を最小限で引くために使う。
- renderer / reviewer は section order と facts 保全の guardrail として使い、本文の主生成は Codex の freeform draft を優先する。
- references は条件付きで読み、scene template や edge-case 集を常時前面に置かない。
- 共通原則は `/home/hr-hm/Project/work/docs/reply-quality/skill-thought-preservation-minimal.ja.md` を参照する。

## 固定条件（変更禁止）
- 価格・追加料金・公開状態・基本範囲は hardcode せず、毎回 `service-registry.yaml` で `bugfix-15000` を解決して `public_facts_file` を公開事実正本にする。`facts_file` / `runtime_capability_file` は既存互換・内部能力参照として扱う
- 確認範囲の説明は `estimate-decision.yaml` と `source_of_truth` を正本にする
- 公開中サービスに確認専用の別料金プランはない
- 不具合1件の扱いは `同一原因 / 1フロー / 1エンドポイント` を基準にする
- 範囲外: 通話、直接push、本番デプロイ、新機能開発
- セキュリティ: `.env` はキー名のみ（値は不要）
- 禁止: 外部連絡、外部共有、外部決済への誘導
- 禁止: 本番環境での再実行を促すこと（再決済 / 再課金 / Webhook再送 / データ削除など）
- GitHub 招待、外部リポジトリ上の Issue / PR / コメント、外部サービス上でのやり取りを、通常の材料共有や作業面として受けない。コード共有は、ココナラのトークルーム内で ZIP または関係ファイルを添付してもらう案内を優先する。
- buyer が `コードが分からない` `AIで作った` `どのファイルを送ればいいか分からない` と明示している時は、関係ファイルの選別を buyer に返しすぎない。購入後の材料共有は、可能ならコード一式 ZIP + エラーログ / スクショへ寄せ、secret 値を外す案内を必ず添える。
- 共有済みファイルに APIキー、Webhook secret、`.env` の値などが含まれている可能性がある時は、`確認対象にしません` だけで終えない。該当部分を伏せた形で送り直してもらい、こちらでは秘密値そのものを扱わないことを明示する。

## このskillを使う場面
- ユーザーが「返信文作って」「そのまま送れる文面」と依頼したとき
- 購入後のトークルーム初回、追加確認、スコープ判定、納品前後の案内
- `coconala-intake-router-ja` で入口判定を済ませたあと、送信用文面が必要なとき

## このskillを使わない場面
- `state: prequote` の見積り相談で、`#R / #A` 判定から金額分岐まで必要なとき
  - この場合は `coconala-prequote-ops-ja` を優先する
- 相手文の貼り付けだけで、送信用文面の明示依頼がないとき
  - この場合は分析のみを返す

## required_facts
- ココナラ共通の取引仕様（メッセージ / トークルーム / 正式な納品 / キャンセル）は、毎回 `/home/hr-hm/Project/work/os/coconala/platform-contract.yaml` を先に読む。
- bugfix の外向け hard facts は、毎回 `/home/hr-hm/Project/work/os/core/service-registry.yaml` と、そこから辿る `public_facts_file` を正本として読む。
- 現在の公開 bugfix サービスは `bugfix-15000` のみで、価格・追加料金・公開状態・範囲は `service-registry.yaml` で `bugfix-15000` を解決し、その `public_facts_file` を正本にする。
- 公開状態と外向け自然文の参照は、`service-registry.yaml` の `public` と `source_of_truth` を使う。
- サービスページ本文は外向け自然文の正本として参照してよいが、価格・追加料金・公開状態の機械判定は `public_facts_file` と `service-registry.yaml` を優先する。`service.yaml` は runtime capability / legacy compatibility として扱う。
- 古いテンプレや過去の返信例に旧確認プラン前提の文面が残っていても、外向け bugfix では採用しない。
- `#RE` や外部調査の最新知見は、正本 rule ではなく観察メモとして読む。採用済みの最小 rule / guard は `docs/reply-quality` と `os/coconala/platform-contract.yaml` 側を優先する。

## 先に見るファイル
- `/home/hr-hm/Project/work/os/coconala/platform-contract.yaml`
- `/home/hr-hm/Project/work/os/core/service-registry.yaml`
- `/home/hr-hm/Project/work/ops/common/coconala-rule-guard.md`
- `/home/hr-hm/Project/work/ops/common/output-schema.yaml`
- `service-registry.yaml` の `bugfix-15000` から辿る `public_facts_file`
- `/home/hr-hm/Project/work/ops/services/next-stripe-bugfix/evidence-minimum.yaml`
- `/home/hr-hm/Project/work/ops/services/next-stripe-bugfix/scope-matrix.md`
- `/home/hr-hm/Project/work/docs/coconala-japanese-banlist.ja.md`
- `/home/hr-hm/Project/work/docs/coconala-japanese-must-rules.ja.md`
- `/home/hr-hm/Project/work/docs/reply-quality/README.ja.md`
- `/home/hr-hm/Project/work/docs/reply-quality/self-check-core-always-on.ja.md`
- `/home/hr-hm/Project/work/docs/reply-quality/writer-brief.ja.md`
- `/home/hr-hm/Project/work/docs/reply-quality/prequote-compression-rules.ja.md`
- `/home/hr-hm/Project/work/docs/reply-quality/ng-expressions.ja.md`
- `/home/hr-hm/Project/work/docs/coconala-golden-replies.ja.md`
- `/home/hr-hm/Project/work/docs/coconala-reply-self-check.ja.md`

## 最新 #RE メモの扱い
- `/home/hr-hm/Project/work/docs/reply-quality/question-type-batch-plan-20260425.ja.md`
  - buyer 質問タイプの観察計画。通常返信の router / rule として直接使わない。
- `/home/hr-hm/Project/work/docs/reply-quality/external-research-observation-plan-20260425.ja.md`
  - Deep Research の観察メモ。stock / archetype / reviewer 観点として使い、本文生成 rule へ直投入しない。
- `/home/hr-hm/Project/work/ops/tests/stock/learning-log/`
  - `#RE` の再発証拠。`adopt` は反映済み guard の確認、`observe` は次 batch の監査観点として扱う。
- closed 後のやり取りは `/home/hr-hm/Project/work/os/coconala/platform-contract.yaml` の `closed_talkroom_locked` を優先し、旧トークルームでの継続作業・ファイル送付・追加購入を前提にしない。
- closed 後の関係確認で実作業が必要そうな場合は、`対応方法と費用` だけで閉じず、`前回トークルームの続きではなく、対応範囲と費用を先にご相談します` を標準にする。

## Writer / Reviewer 分離
- この skill は `Classifier -> Writer -> Reviewer` を前提に使う。
- Classifier は `reply_contract / response_decision_plan / phase_act / service facts` を確定する strict 層。
- Writer は `/home/hr-hm/Project/work/docs/reply-quality/writer-brief.ja.md` の最小原則だけで本文を書く。
- Reviewer は `/home/hr-hm/Project/work/docs/coconala-reply-self-check.ja.md` と ban / fact lint を使って検査する。
- `self-check` は Writer に読ませるのではなく、draft 後に通す。

## #RE / #R alignment
- `#RE` の固定 fixture は残すが、外向け文面の監査対象は原則 `#R` と同じ Writer / final naturalizer 経路の候補に寄せる。
- `renderer_baseline` は regression / debug / hard constraint 確認用であり、送信用 `#R` と同等の自然文候補として扱わない。
- `#RE` で自然さの違和感が出た場合は、共通 rule へ戻す前に `#R` でも再現するかを見る。`#RE only` なら renderer / fixture 側の問題として隔離する。
- renderer は全文テンプレ生成器ではなく、`reply_contract` / `response_decision_plan` / semantic slots / forbidden moves / answer coverage の guardrail に寄せる。
- human audit の指摘は、`#R reproduced` / `#RE only` / `safety deterministic` / `preference` / `candidate` に分けて戻し先を決める。

## Coconala adapter phrasebook（bugfix-15000）

汎用自然化 skill へココナラ固有語を常駐させない。以下は Coconala / bugfix-15000 の adapter として使う。

### 非エンジニア・AI生成・外注コード
- buyer が `どのファイルが関係するか分からない` と明示している時は、関係ファイル選別を buyer に戻しすぎない。
- 標準: `ご購入後は、APIキーや .env の値を含めない形で、コード一式をZIPでトークルームへ共有してください。不要なファイルが混ざっていても問題ありません。必要な範囲はこちらで確認します。`
- `無理に絞らなくて大丈夫です` だけで止めない。次に送るものが残る場合は、コード一式ZIP / スクショ / ログ / secret除外まで閉じる。
- `どのファイルが関係するか分からない場合でも、こちらで必要な範囲を確認します` のような安心文だけを置かない。先に buyer が送るものを具体化し、その後に不要ファイル混在の許容と seller 側の確認行動を添える。
- secret: `APIキー、Webhook Secret、.env、DB接続文字列などの値そのものは含めないでください。`

### 支払い前診断・GitHub先見
- 支払い前にファイル・ログ・GitHubを見て原因確認する要求では、buyer の `直せそうなら` `そこだけ先に` を貼り戻さない。
- buyer が購入意思を出している時は、いきなり不可表明から入らず、`ご相談ありがとうございます。` 程度の短い中立的な受けを1文置いてよい。ただし支払い前診断不可の境界は消さない。
- 購入前でも、症状・画面スクショ・エラー文から「このサービス対象になり得るか」「進め方の見立て」は返してよい。止めるのは、コードやログを読んで原因確認・修正可否を確定すること。
- buyer が `スクショだけ見て、このサービスで対応できそうか判断してほしい` と聞いている場合は、スクショの受領や症状ベースの対象可否まで否定しない。`スクショだけで原因確認まではできませんが、症状としては対象になり得ます` のように分ける。
- 標準: `お支払い前は、ファイルやログを見て原因確認まで進めることはできません。`
- GitHub: `お支払い前は、GitHub上でコードを確認したり、原因の方向性を先に出したりする対応はしていません。`
- その後に症状ベースの対応可否を別文で置く。`ただ` で支払い前不可と症状対応可を無理につながない。
- 推奨順序: `不可表明 -> 症状ベースの対応可否 -> 条件付きCTA -> 購入後材料案内 -> secret除外`

### phase 別 CTA
- `prequote`: `この内容で問題なければ、15,000円で見積り提案します。`
- `quote_sent`: `この前提で問題なければ、見積り提案の内容でお支払いへ進んでください。`
- buyer が購入意思を強く出している時だけ、`そのままご購入ください` を強めに使ってよい。
- buyer が迷い・条件付き購入を出している時は、購入後材料案内を CTA より先に厚く出さない。

### delivered / closed
- delivered の軽い補足では `補足できます` で止めない。`反映するファイルと順番を短く整理します` のように、こちらが返す内容へ進める。
- delivered で反映ファイル名・確認画面名・反映順を答える時は、納品物 / 修正ファイル / 確認手順の context がある時だけ具体名を出す。context がないリハーサルや SaaS の service-only 状態では具体名を作らず、担当者入力や納品 context が必要として扱う。
- closed 後の関係確認では、`確認します` だけで止めない。`ログとスクショから見える範囲で、前回修正との関係や新しい不具合の可能性を確認します` のように、確認結果の形を見せる。

## 標準ルート
1. 可能なら先に `coconala-intake-router-ja` を使い、経路・状態・`case_type`・`certainty`・`reply_stance`・`reply_contract` を確定する。
2. モードを判定する。
   - UI進行タグ（`#$0` / `#$1` / `#$2` / `#$3`）があるか
   - 文末タグ（`#R` / `#A` / `#D` / `#P`）があるか
   - `#R 受領返信` などのショート指示があるか
3. `#R` の後ろや次行に自由文の補足がある場合は、`user_override` として読む。
4. `reply_contract.primary_question_id`、`explicit_questions`、`answer_map`、`ask_map` を先に読む。
   - 複数症状・複数質問では、`primary_question_id` だけでなく、buyer が次に決めたいこと、明示した優先症状、価格/範囲の問いを合わせて `response_decision_plan.answer_focus` を読む。内部の対象判定をそのまま本文へ出さず、buyer の意思決定に返る文へ変換する。
5. `temperature_plan` があれば、`reply_contract` の sibling として扱う。`reply_contract` は「何を答えるか」、`temperature_plan` は「どう受け止めるか」の正本にする。
6. `user_override` があれば、hard constraints を崩さない範囲で `temperature_plan`、`reply_contract`、`response_decision_plan` を狭める方向へ反映する。
7. `reply_contract.issue_plan` は互換要約として扱い、実行契約の正本は `answer_map` と `ask_map` に置く。
8. `reply_skeleton` に沿って section の大枠だけを決める。ただし writer を slot-filling に閉じ込めず、先に `response_decision_plan` を作る。
9. `response_decision_plan` には最低でも `primary_concern / facts_known / blocking_missing_facts / direct_answer_line / response_order` を持たせる。
10. 可能なら `phase_act` も持たせる。`estimate_answer / estimate_hold / purchase_check_started / purchase_scope_recheck` のどれかで、今の返信が「見積もり判断」なのか「購入後の確認開始」なのかを先に固定する。
11. `reply_contract` は「何を言ってよいか」、`response_decision_plan` は「何を先にどう言うか」の正本にする。
12. 文面は renderer が template-first で埋めるのではなく、Codex が freeform に近い形で下書きし、renderer / validator は guardrail として使う。
13. Writer に渡す guidance は `/home/hr-hm/Project/work/docs/reply-quality/writer-brief.ja.md` の要点までに圧縮し、長い self-check や reviewer ルール全文を混ぜない。
14. `primary_question_id` に対応する答えは、`response_decision_plan.direct_answer_line` として最初の answer-bearing section に置く。
15. 最初の answer-bearing section では、primary question に必要な情報だけで答える。価格・別原因リスク・広いスコープ説明などの二次論点を、善意で先頭に差し込まない。
16. 相手が価格を聞いていない場面では、価格を自動挿入しない。価格は policy 上必要な場合、予算不安が明示されている場合、または主質問が価格の時だけ出す。
17. `answer_map` にない二次論点を足す必要がある時は、最初の answer-bearing section ではなく後段へ置く。
18. `ask_map` にない質問は増やさず、`blocking_missing_facts` が空なら原則 ask を出さない。
19. 追加質問の前に、現時点の見立てまたは確認観点を1文だけ入れる。
20. 相手がすでに書いた情報は `facts_known` として保持し、再要求しない。
21. `required_moves` を落とさず、`forbidden_moves` を踏まない範囲で文面を下書きする。skill は writer の代わりではなく、writer を壊さないガードレールとして使う。
22. 次回報告時刻を入れる。購入後の調査 / 判定フェーズでは `本日[時刻]まで` と `48時間以内` の二段構成を基本にする。
23. draft 後に `/home/hr-hm/Project/work/docs/coconala-reply-self-check.ja.md` を Reviewer として通す。
24. `/home/hr-hm/Project/work/docs/reply-quality/ng-expressions.ja.md` で再発しやすい NG 表現を落とす。
25. 近い場面があれば `/home/hr-hm/Project/work/docs/coconala-golden-replies.ja.md` と `/home/hr-hm/Project/work/docs/reply-quality/gold-replies/README.ja.md` を見て、温度感と依頼数の基準を合わせる。
26. 送信用文面は、毎回 `japanese-chat-natural-ja` で最終自然化する。
27. ただし `japanese-chat-natural-ja` には全文の意味変更権限を与えず、語順・接続・語感の自然化に限定する。
28. 自然化後も `direct_answer_line`、価格、禁止事項、ask 数、次アクション、`required_moves / forbidden_moves` を崩していないか再lintする。
29. 送信用文面モードでは `/home/hr-hm/Project/work/runtime/replies/latest.txt` に保存する。相手文が明確なときは `/home/hr-hm/Project/work/runtime/replies/latest-source.txt` にも保存する。

## `#R` 補足指示の扱い
- `#R 受領返信` のようなショート指示だけでなく、`#R` の後ろや次行に付く自由文の補足も受ける。
- 補足は optional な `user_override` として扱い、優先順は `hard constraints > user_override > デフォルト推論`。
- `ここは柔らかめにしてほしい` `まず謝罪から入って` のような補足は、主に `temperature_plan` と冒頭の `opening ack` に反映する。
- `質問は1つだけにして` `追加料金の話は今回は避けて` `handoff の案内は出さないで` のような補足は、`reply_contract` と `response_decision_plan` を狭める方向で反映する。
- ただし、公開状態、価格、規約、セキュリティ、scope boundary、最低限必要な確認は補足で上書きしない。
- `質問は1つだけ` と書かれていても、実行に2点必要なら2点のまま最小化する。
- `handoff を出さないで` と書かれていても、実際に対象外や別サービス案内が必須なら hard constraints を優先する。
- 補足が tone 指示だけなら、価格・可否・ask 数を動かさず `temperature_plan` 側だけを変える。

## `reply_contract` の使い方
- `reply_contract` はヒントではなく、下流が守る実行契約として扱う。
- `primary_question_id / explicit_questions / answer_map / ask_map` を renderer と lint の正本にする。
- primary question に答える前の段階では、二次論点を先頭に出さない。特に価格・別原因リスク・広いスコープ説明は、相手が聞いていない限り後段へ回す。
- `frontload_price_when_not_asked / frontload_branching_risk_when_not_asked / frontload_scope_explanation_when_not_asked` がある時は、たとえ正しい情報でも最初の answer-bearing section に差し込まない。
- `temperature_plan` は interaction の実行契約として扱う。`opening_move` `ack_style` `ack_anchor` `warmth_cap` `tone_constraints` は renderer / naturalize / lint の共通入力にする。
- `issue_plan` は、明示質問や実質別論点をどう処理するかの互換要約として使う。
- `answer_now` の論点だけを即答し、`answer_after_check` の論点は理由つきで保留する。
- `ask_client` は、`ask_map` にある最小証跡だけを依頼する。
- `decline` は、規約・公開状態・範囲の理由がある時だけ使う。
- `required_moves` にある動きは必ず文面へ反映する。
- `forbidden_moves` にある動きは、理由が分かっていても本文へ出さない。
- `frontload_price_when_not_asked` がある時は、価格を主質問への直答より先に出さない。
- `frontload_branching_risk_when_not_asked` がある時は、別原因・追加料金・分岐リスクを主質問より先に出さない。
- `frontload_scope_explanation_when_not_asked` がある時は、広い範囲説明を主質問より先に出さない。
- `reply_stance.answer_timing` は要約値に留め、実際に何を答えるかは `answer_map` を優先する。
- `ack_style: brief_specific` の時は、冒頭1文で buyer の具体的な行動・労力・結果・好意のどれかに触れる。`ありがとうございます。` だけで終えない。
- 具体的に触れる時も、褒め言葉に広げない。`動作確認までありがとうございます。` `評価まで入れていただけて助かります。` 程度で止める。
- `warmth_cap: one_sentence` なら、温度のある受けは1文で止めて、2文目から結論や次アクションへ入る。
- 情報収集フェーズで `opening_move: action_first` の時は、温度より先に `何を見るか / 何を送ってほしいか` を短く置く。
- `tone_constraints` に `no_groundless_reassurance` がある時は、`大丈夫です` `よくある症状です` `心配いりません` のような根拠のない安心を足さない。
- `tone_constraints` に `no_sycophancy` がある時は、buyer の認識違いを迎合せず、境界や価格も弱めない。
- prequote で buyer が `15,000円で依頼できますか` と聞いている場合は、`15,000円でご依頼いただけます` を優先する。buyer が `相談して大丈夫ですか` `相談できますか` と聞いている場合も、標準は `ご相談いただけます` に寄せる。短い直答として自然な場合だけ `相談できます` を使ってよい。
- 支払い後の材料共有は、`お支払い完了後で大丈夫です` より、`お支払い完了後にトークルームで共有してください` `共有いただければ確認に入ります` を優先する。secret 値不要など buyer の負担を下げる場面では `送らなくて大丈夫です` を使ってよい。
- delivered で buyer が `どこを反映すればいいか教えてもらえますか` `もう少し分かりやすく説明してもらえますか` と聞いている場面では、`補足できます` で対応可否を宣言して止めない。`反映するファイルだけ、こちらで短く整理します` `補足説明をお送りします` のように、承諾前の軽い補足としてこちらの返す内容を明示する。
- delivered の承諾前の軽い補足では、buyer が時刻や期限を聞いていない限り、`本日18:00まで` のような具体時刻を自動で足さない。実際にその時刻で返せる時だけ入れる。
- 具体時刻は deadline_authorized がある時だけ入れる。リハーサルや汎用 SaaS では、時刻を作らず `確認でき次第` `必要な範囲で` に留める。
- 複数症状で buyer が優先症状と価格/範囲を聞いている場面では、`まず一番困っている不具合を対象にして` のような内部整理を本文へ出さない。`この場合は、「注文が作られない」不具合を1件として、15,000円でご依頼いただけます` のように、buyer が知りたい依頼可否へ戻す。

## skeleton ごとの固定骨格
- `estimate_initial`: 受け止め -> 結論 -> 根拠 -> 価格/購入導線 or 最小質問 -> 次アクション
- `estimate_followup`: 結論 -> 追加情報 -> 次アクション
- `post_purchase_receipt`: 受領確認 -> 確認対象 -> 時刻コミット
- `post_purchase_quick`: 短い反応 -> 今答えること -> 確認後に返すこと -> 最小依頼 -> 時刻
- `post_purchase_report`: 現状 -> 判明事項 -> 次ステップ -> 時刻コミット
- `delivery`: 確認依頼 -> 確認ポイント -> 次ステップ

## skeleton と phase_act
- `estimate_initial` / `estimate_followup` では、`phase_act` を `estimate_answer` か `estimate_hold` に寄せる。ここで `purchase_check_started` を使わない。
- `estimate_answer` は、購入前に言ってよい受注可否・価格・次アクションだけを返す。コードやログを見始めたような現在形を混ぜない。
- `estimate_hold` は、見積もり判断が未確定で、追加の最小情報が必要な状態を表す。`この情報があれば見積もれる` に寄せ、確認開始報告へずらさない。
- `post_purchase_quick` / `post_purchase_report` では、`phase_act` を `purchase_check_started` か `purchase_scope_recheck` に寄せる。
- `purchase_check_started` は、購入後に現在見ている対象や次に見る箇所を返す。
- purchased で `届いていますか` `今どこを見ていますか` に答える時は、添付受領・作業状況を実際に確認できている時だけ `受け取っています` `今は〜を見ています` と書く。確認できていない時は、受領状況や作業状況を確認してから返す形に留める。
- `purchase_scope_recheck` は、購入後に別論点や追加要求が出て、今回範囲とつながるかを見直す時に使う。
- `state` と buyer 文の見え方がズレないようにする。`purchased` では `ご購入後に...` と未来導線へ戻さず、`受け取っている材料` `いただいた内容` など現在地に合う表現を使う。#RE fixture では buyer 文だけで状態が読みにくい時、`購入後です` `見積り提案ありがとうございます` `クローズ後です` などを相手文に明示する。
- `quote_sent` は見積り提案済み・支払い前。現在すでにトークルームで作業中のように書かない。ただし、`お支払い完了後にトークルームで共有してください` のような未来条件つきの購入後手順は使ってよい。
- `prequote` では見積り提案済みではないため、`見積り提案の内容で問題なければ` を使わない。提案前なら、対応可否・価格・必要なら見積り提案へ進む旨に留める。
- `見積り提案の内容で問題なければ` は、state が `quote_sent`、または buyer 文に `見積り提案ありがとうございます` などの明確な証拠がある時だけ使う。証拠がない `prequote` では、`この内容で問題なければ、15,000円で見積り提案します` に留める。
- `prequote` / `quote_sent` で材料共有に触れる時は、主質問への答えと CTA を先に置く。buyer がまだ購入判断中なら、購入後の ZIP / ログ / スクショ / secret 除外の詳細案内を厚くしすぎず、必要な範囲だけにする。
- `prequote` / `quote_sent` で支払い前診断を断る時は、buyer の `直せそうなら` `そこだけ先に` などの口語をそのまま戻しすぎない。`お支払い前は、ファイルやログを見て原因確認まで進めることはできません` のように、支払い前にできない境界を短く成熟した業務文で伝えてから、症状ベースの対応可否と次アクションへ進む。

## renderer の固定
- 最初に renderer 化するのは `estimate_initial` と `post_purchase_quick` の2つだけに絞る。
- renderer は section の有無、順序、ask 上限、主質問を扱う位置を固定する guardrail として使う。
- writer を slot 埋めに閉じ込めない。文章生成は Codex の reasoning を残した freeform draft を優先し、renderer は過剰な template-first を避ける。
- `estimate_initial` では、最初の answer-bearing section で `primary_question_id` に対する結論を出す。
- `estimate_initial` で主質問が価格以外なら、価格は最初の answer-bearing section に自動で入れない。
- `estimate_initial` では、`phase_act` が `estimate_answer / estimate_hold` のどちらでも、`direct_answer_line` を「見積もり判断の返答」として書く。未受領なのに `確認を進めます` のような purchased 語彙へ滑らせない。
- `post_purchase_quick` では、`answer_now` を先に、`answer_after_check` は理由つき保留として後段に置く。
- `post_purchase_quick` では、`phase_act` が `purchase_check_started / purchase_scope_recheck` なら、現在見ている対象や別件切り分けを1文で可視化してよい。
- `answer_after_check` を出す時は、`hold_reason` と `revisit_trigger` を落とさない。
- `ask_map` が空なら、質問 section を作らない。
- `ask_map` が任意確認だけなら、相手に判断を丸投げせず、答えがなくても進める既定方針を同じ段落で添える。
- テンプレ文を renderer 側に固定しすぎず、固定するのは section order・question coverage・ask gating までに留める。

## 恒久反映ルール（reply-only）
- `answer_after_check` でも、保留だけで終わらせず `いま見ている範囲` を1文で可視化する。
- 購入後の途中共有は、できるだけ `何を見たか / まだ未確定な点 / 次に何を見るか / 次回時刻` の4点へ寄せる。
- 進捗不安・継続可否・追加料金・返金不安のような敏感話題は、説明前に短い直接回答を先に置く。
- 相手がすでに書いた文脈や観察情報をもう一度言わせない。追加で聞くのは未共有の最小情報だけにする。
- 1点で足りる場面では、長い番号案内や選択肢メニューへ広げない。
- `該当番号を選ぶ` 型の長い案内や、受付窓口に戻すような受け答えを避ける。

## 条件付きで読む references
- UI進行タグや `#R` / `#P` ショート指示を使うとき:
  - `references/ui-progress-tags.ja.md`
- 受領後 / 納品前後 / クローズ前後の購入後フェーズ:
  - `references/post-purchase-stages.ja.md`
- `emotional_caution: true` または苦情寄りの文面:
  - `references/emotional-caution-mode.ja.md`
- 値引き、`quote_sent`、`closed` 後などの例外運用:
  - `references/edge-cases.ja.md`
- 複数症状、対象外懸念共有、技術的には可能な別件案内:
  - `references/scope-boundary-phrases.ja.md`
- 文体、Ban表現、Stripe導線、出力ルールの詳細:
  - `references/style-rules.ja.md`
- 参考テンプレが必要なときだけ:
  - `references/scene-templates.ja.md`

## Gotchas
- `reply_contract` があるのに、本文生成側で再解釈しない。特に `answer_map` の `answer_after_check` を、良かれと思って即答へ変えない。
- `reply_stance.answer_timing` と `answer_map[].disposition` を二重真実源にしない。衝突したら `answer_map` を優先する。
- `prequote` で `#R / #A` を作る時は、先に `coconala-prequote-ops-ja` を使う。金額分岐をこのskillで抱え込まない。
- `scope_judgement: undecidable` のまま、追加料金や無料対応を断定しない。
- Webhookの複数イベント失敗でも、同一原因なら `bugfix-15000` の守備範囲に残す。
- 複数症状が並ぶ時は、こちらで勝手に「1件目」を断定しない。ただし、こちらで仮に優先を置ける場面では、相手へ優先順位の判断を丸投げせず既定方針を添える。
- `closed` 後の再相談では、最初の返信で `新規依頼` や `規約上は` を前面に出さない。
- `handoff-25000` で修正依頼が出た場合は吸収せず、`bugfix-15000` または別見積りへ切り分ける。
- Stripe確認は `/home/hr-hm/Project/work/stripe日本語UI案内` を最優先参照し、`sk_...` や `whsec_...` の値は求めない。
- 購入後の継続会話では、初回ヒアリングや受付窓口の文面に戻らない。相手の追加報告へ一度反応してから、不足分だけを軽く頼む。
- 購入後の追加報告に対して、`次の2点だけお願いします` の番号リストを機械適用しない。2点程度なら文中にさらっと混ぜる形を優先する。
- 購入後の継続会話では、`同一原因` `別原因` の内部寄りの言い方を避け、`同じ原因` `別の話` `別の原因かもしれない` など会話の言い方を優先する。
- 購入後の途中共有で、`確認中です` だけで終わらない。いま見ている範囲と次の確認点を短く出す。
- 進捗不安への返答で、防御的に理由説明から入らない。まず見えにくかった点を受けて、次回から何を見える形で返すかを書く。
- buyer が個人の不安や過去の嫌な経験を明示している時は、`進みが見えにくいと不安になりますよね` のような一般論の共感や `〜ですよね` で受けない。`お待たせして申し訳ありません。いま確認している状況をお伝えします。` のように短く謝って、そのまま現在地へ入る。
- `GitHub 招待` は公開URL共有ではなく、非公開リポジトリや外部作業面への招待として読まれやすい。通常 live / #RE では `GitHub 招待で進められます` と受けず、`コードはトークルームで共有できる形でお願いします` に寄せる。GitHub上での Issue / PR / コメント / 連絡 / 直接 push を作業面にしない。

## 出力ルール
- 行頭に不要な空白を入れない。
- 基本は `です・ます`。
- 結論 -> 理由 -> 次アクション の順に書く。
- `reply_skeleton` で決めた section order を崩さない。
- 箇条書きは3点以内を優先する。
- 見積り初回は質問票に見せず、質問前に受領した事実か確認観点を1文入れる。
- `2時間以内` は受領確認または一次報告を指す。一次結果は別時刻で明記する。
- 非エンジニア向けでは `ログ` 単語を単独要求しない。
- エラー文やログは、コピーできるならテキスト貼り付けを優先する。コピーしにくい場合だけ画面スクショを代替にする。
- UI状態や見え方の確認では、画面スクショを優先してよい。
- 送信用文面は、保存前に毎回 `japanese-chat-natural-ja` を通す。
- 最終自然化では、結論・質問項目数・価格・禁止事項・次アクション・section order・required_moves を増減させない。
- naturalize は semantic freeze 後に行い、壊れやすい項目は自然化前後で再lintする。
- naturalize は全文の rewrite ではなく、`ack / bridge / closing` の editable slot を対象にした typed slot rewriter として扱う。
- 壊れやすい項目は `can / cannot` の極性、`answer_now / answer_after_check` の極性、価格、ask 数、hold reason、次アクション、forbidden claim。
- `〜する形が安全です` のような提案書寄りの言い方は避け、`〜するのがよさそうです` を優先する。
- 条件がそろうと判断しやすくなる場面では、`出しやすいです` より `出しやすくなります` を優先する。
- 前段で挙げた項目を受ける依頼は、`上の3点を` のように対象を明示して省略しすぎない。
- 送信用文面を作ったときは `/home/hr-hm/Project/work/runtime/replies/latest.txt` に保存する。相手文があるときは `latest-source.txt` も更新する。
- 購入後の継続会話では、相手の追加報告に短く反応してから本題へ入る。`別のページでもですか。` `ログイン画面も崩れていますか。` のような一言で十分。
- 購入後の継続会話では、情報依頼を文中に混ぜる形を優先する。番号リストは3点以上、または取りこぼしが起きやすい時だけ使う。
- 購入後の継続会話では、`いただければ、共有します` のSLA文より `もらえると助かります` `本日[時刻]までに共有しますね` のようなチャット口調を優先する。
- 購入後の追加報告で、`先にお答えすると` `まず結論だけ言うと` のようなメタ説明を挟まない。答えれば伝わる場面では、そのまま結論へ入る。
- 購入後の追加報告では、こちらの反応や優先度より先に、相手が持ち込んだ事象を主語に置く。`二重に引き落とされた件は` `前回と同じ症状であれば` のように、件名側から入る。
- 購入後の scope 判断で、`可能性が高いです` `確率としては` のような確信度報告を前面に出しすぎない。会話として足りる場面では `よさそうです` `まずは別の話として見た方が自然です` を優先する。
- 購入後の追加報告では、`ここは優先して見ます` のような曖昧な指示語を使わない。`優先して確認します` `この件を先に見ます` のように対象を明示する。
- `前回に続いてのご相談` のような分類ラベルを、そのまま挨拶に混ぜない。リピート相談でも、相手の挨拶や文脈に寄せて `前回お世話になりました` `前回の件ではありがとうございました` など自然な受け方を優先する。
- post-close の再相談で、`流用` のような内部寄りの語を外向けに出さない。`前回の件とは分けて見る` `前回の結果を活かせるか確認する` のように、buyer が読める語へ言い換える。
- buyer が `活かして` `引き続き` などの語を使っている時は、意味が変わらない範囲でその語を優先して拾う。自然な同義語へずらすより、buyer の語彙に寄せる。
- purchased で `issue_plan` が混在する時は、即答できるものだけ答え、残りは `確認してから返す` と分けて書く。
- 購入後の `確認してから返す` では、`いまは〜を先に見ています` の現在地を1文入れて不透明さを減らす。
- 相手が `箇条書きで` `一言ずつ` `短く` のように返答形式を明示した時は、その形式を本文でも守る。
- 相手が感謝や `早いですね` `助かります` のような前向きな温度を出している時は、主質問へ入る前に短い `ありがとうございます。` を返してよい。
- 相手が `安心しました` `助かりました` `自分では触れない` のように、好意・安心・弱さを短く差し出している時は、本題の前に1文だけ受けてよい。説明や励ましに広げず、そのまま結論へ入る。
- 相手が `星5` `大満足` `バッチリでした` のように強い好意を出している時は、実務案内へ入る前に `お役に立てたなら嬉しいです。` のような短い受けを1文だけ返してよい。長い謝辞や営業には広げない。
- その場で buyer の具体的な行動や結果が見えているなら、`お役に立てたなら嬉しいです。` より `動作確認までありがとうございます。` `評価まで入れていただけて助かります。` のような具体受けを優先してよい。
- 受け止めで buyer が使っていない感情語を補完しない。`迷いますよね` `焦りますよね` のように感情を完成させるより、buyer の語や状況描写に寄せる。
- 冒頭で受け止めを1文入れる時は、その直後を `ですが` で逆接しない。受け止めが必要ない場面では、根拠説明からそのまま入ってよい。
- 冒頭の肯定や受領を `もちろんです。` に固定しない。
- Yes/No へ直答が必要でも、先頭の1語を機械的に `はい、` に固定しない。`可能です。` `この内容なら対象になりそうです。` `15,000円の方が近いです。` のように、フェーズに合う結論文そのものを先に置いてよい。
- ただし、まだ中身を見ていない段階の `確認できます。` は確認済みに読まれやすい。未確認なら `見ます` `調査できます` `対応可能です` を優先する。
- 受領の言い方は `ありがとうございます。` `承知しました。` `確認できます。` などに散らす。
- 外向け返信で内部ラベルの `bugfix` `handoff` をそのまま書かない。`不具合修正` `主要1フローの整理` `このサービス` に言い換える。
- 相手が `高い` `予算が厳しい` のように価格への引っかかりを率直に出している時は、説明へ入る前に短い受け止めを1文だけ置いてよい。弁明には広げない。
- 怒りや催促が強い相手への途中共有では、技術語の粒度を少し落として現在地を返す。`切り分けの軸は〜` より `だいぶ絞れてきています` を優先する。
- 比較説明や価格差の返答で、`差額の説明だけすると` のような事務的な前置きを入れない。
- 追加料金や追加フローの支払い方法を案内する時は、サービス境界と支払い導線を混ぜない。buyer が支払い方法を聞いており、取引状態が分かる場合だけ、状態に合わせて条件付きで案内する。
- 追加対応や別対応への切り分けで、`この場で勝手に進めず` のような防御的な言い方を使わない。buyer が `勝手に進むのか` `無断で追加料金になるのか` と聞いている場合も、必要以上にその語を反復せず、見積り相談では `別原因と分かった場合は、その時点で追加対応にするかどうかと費用を先にご相談します` のように、追加対応へ進むかを buyer と決める形へ変換する。
- closed 後の再相談では、上の汎用文より `前回トークルームの続きではなく、対応範囲と費用を先にご相談します` を優先する。
- buyer の冒頭文をそのまま返しておうむ返しにしない。`先日はありがとうございました` `ありがとうございます` など相手と同一の書き出しが直後に続くなら、`こちらこそありがとうございました` `前回の件が安定していてよかったです` のように少しずらす。
- 納期や見通しの返答で、`まだ確定できない` と `ここまでは返せる` が同時にある時は、先に `返せること` を置く。`見立てまでは返せます。そのうえで、症状を見ないまま日数は確定していません` の順を基本にする。
- 修正完了や調査完了の見通しに `時刻` を使わない。`目処` `完了時期` `見通し` を優先する。
- 保留判断や境界説明で `言っていません` のような訂正口調を使わない。`現時点ではまだ確定していません` `この時点ではまだ判断していません` に寄せる。
- 判断返答で `先に見るのが近いです` `このサービスが近いです` のような直訳調を避ける。`先に対応するのがよさそうです` `まずはこの進め方が自然です` を優先する。
- 購入前・見積り後の closing は、buyer に判断余地が残る `この内容で問題なければ、そのままご購入ください` を標準寄りにする。`この内容で進める場合は` は進行前提が少し強く見えるため、購入意思が明確な場面に留める。
- 次回案内や結果共有を `返します / お返しします` に固定しない。`ご連絡します` `お伝えします` `回答します` を混ぜてテンプレ感を落とす。
- buyer が `ちょっとだけ` `5分で終わる` `CSS1行だけ` のように作業量を根拠に広げてきても、範囲判断は作業量ではなく分類で返す。`1行かどうかに関係なく、今回はデザイン調整なので範囲外です` のように書いてよい。
- 低評価や不満をにおわせる圧力には、その言葉をなぞって返さない。まず `進み方が見えにくい状態にしてしまってすみません` のように、こちらが直せる事実へ受けを寄せてから、次回共有時刻と今見る点を書く。
- 購入後の進捗不安で buyer が個人の経験や不安を打ち明けている場面では、感情の一般化や代弁より、`お待たせして申し訳ありません。` のように seller 側の配慮不足として短く受けてから本題へ入る。
- `post_close` で buyer が前回のお礼や遠慮を先に置いて再相談してきた時は、本題の前に短い受けを1文だけ返してよい。`こちらこそありがとうございました。` `前回の件が安定していてよかったです。` 程度で止める。
- 完全に対象外で方向づけを1文添える時は、`近いかもしれません` より `よさそうです` を優先する。突き放し感を減らしつつ、断定もしすぎない。

## 仕上げ前チェック
- 相手の質問に直接答えているか
- `primary_question_id` に対応する質問へ、最初の answer-bearing section で答えているか
- `explicit_questions` を取りこぼしていないか
- `ask_map` にない質問を増やしていないか
- `issue_plan` の各論点が、`今答える / 確認後に返す / 依頼する / 断る` のどれかへ過不足なく落ちているか
- `reply_skeleton` と最終文面の骨格が一致しているか
- `required_moves` が落ちていないか / `forbidden_moves` を踏んでいないか
- 既出情報を聞き直していないか
- 任意確認を、必須質問や選択強制の形で押し出していないか
- 答えがなくてもこちらで進められる場面では、既定方針を本文に書いたか
- `burden_owner: us` なのに、優先順位づけや分岐判断を相手へ丸投げしていないか
- `answer_after_check` でも、いま見ている範囲を1文で可視化できているか
- 進捗不安への返答で、理由説明だけで終わらず `今後は何を見える形で返すか` まで書いているか
- 購入後の途中共有で、`何を見たか / 何が未確定か / 次に何を見るか / 次回時刻` のうち最低3点が入っているか
- 相手が返答形式を指定している時は、その形式を守っているか
- 相手が前向きな感謝や驚きを示している時は、主質問へ入る前に短い謝意を返せているか
- 相手が安心・好意・弱さを短く差し出している時は、本題の前に1文だけ受け止めを返せているか
- 相手が `星5` `大満足` `バッチリでした` のように強い好意を出している時は、実務案内の前に短い喜びや謝意を1文だけ返せているか
- `temperature_plan.ack_style = brief_specific` の時は、冒頭1文が generic な謝意だけで終わらず、buyer の具体行動・労力・結果・好意のどれかに触れているか
- 受け止めの1文で、buyer が言っていない感情語を勝手に補っていないか
- 冒頭で受けた直後に `ですが` で切り返して、受け止めを打ち消していないか
- Yes/No 質問でも、冒頭が機械的な `はい、` になっていないか
- 完全に対象外で受けられない時は、必要に応じて1文だけ近い相談先の方向を添えているか
- 長い番号案内や選択メニューに逃げず、1問で済む確認に圧縮できているか
- 固定条件（価格 / 範囲）を崩していないか
- 外部誘導や秘密情報要求がないか
- 追加質問の前に、受領確認か見立ての1文を入れたか
- 本番での再実行（再決済 / 再課金 / Webhook再送）を促していないか
- 次アクションと時刻が明確か
- 結語が抜け落ちていないか（`.env` 注意文で終わっていないか）
- non_engineer 向けで内部語や強すぎる技術語が混ざっていないか
- 外向け本文に `bugfix` `handoff` `整理サービス` のような内部ラベルが残っていないか
- delivered / closed の問題報告で、`承知しました` だけで止まらず `確認します` など次の確認動作を先に出せているか
- 怒りや催促が強い途中共有で、`切り分けの軸` など分析寄りの言い回しに寄りすぎず、平易な現在地で返せているか
- 追加料金や追加フローの支払い方法を聞かれた場面で、サービス境界と支払い導線を混ぜず、取引状態が分かる場合だけ条件付きで案内できているか
- 別対応や追加料金の説明で、`勝手に進めず` のような防御的な語が残っていないか
- buyer の冒頭文をそのまま返すおうむ返しになっていないか
- 比較説明や価格差の返答で、`差額の説明だけすると` のような事務的な前置きが残っていないか
- `/home/hr-hm/Project/work/docs/reply-quality/ng-expressions.ja.md` の NG 表現が残っていないか
- Ban表現ヒット0件を確認したか
- `prequote` で本来 `coconala-prequote-ops-ja` に寄せるべき場面を、このskillで無理に処理していないか
- テンプレを使った場合でも、相手の文脈に合わせて調整したか
- 公開 bugfix で確認専用の別料金案内が再発していないか
- naturalize 後にも、section order・ask 数・価格・hold reason・次アクション・forbidden claim を再lintしたか
