---
name: coconala-reply-bugfix-ja
description: "ココナラのNext.js/Stripe/API不具合修正サービス専用。重複質問を避け、自然な日本語で、スコープ事故と規約事故を防ぐ返信を作る。"
---

# ココナラ返信（不具合修正 特化版 v1）

## 目的
- Next.js / Stripe / API連携の不具合修正案件で、送信用返信を短く自然に作る。
- 重複質問を減らし、購入者の不信感を防ぐ。
- 固定条件（価格 / 範囲 / 規約）を崩さない。

## 固定条件（変更禁止）
- 価格・追加料金・公開状態・基本範囲は hardcode せず、毎回 `service-registry.yaml` で `bugfix-15000` を解決して `facts_file` を正本にする
- 確認範囲の説明は `estimate-decision.yaml` と `source_of_truth` を正本にする
- 公開中サービスに確認専用の別料金プランはない
- 不具合1件の扱いは `同一原因 / 1フロー / 1エンドポイント` を基準にする
- 範囲外: 通話、直接push、本番デプロイ、新機能開発
- セキュリティ: `.env` はキー名のみ（値は不要）
- 禁止: 外部連絡、外部共有、外部決済への誘導
- 禁止: 本番環境での再実行を促すこと（再決済 / 再課金 / Webhook再送 / データ削除など）

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
- bugfix の hard facts は、毎回 `/home/hr-hm/Project/work/os/core/service-registry.yaml` と、そこから辿る `facts_file` を正本として読む。
- 現在の公開 bugfix サービスは `bugfix-15000` のみで、価格・追加料金・公開状態・範囲は `service-registry.yaml` で `bugfix-15000` を解決し、その `facts_file` を正本にする。
- 公開状態と外向け自然文の参照は、`service-registry.yaml` の `public` と `source_of_truth` を使う。
- サービスページ本文は外向け自然文の正本として参照してよいが、価格・追加料金・公開状態の機械判定は `service.yaml` を優先する。
- 古いテンプレや過去の返信例に旧確認プラン前提の文面が残っていても、外向け bugfix では採用しない。

## 先に見るファイル
- `/home/hr-hm/Project/work/os/coconala/platform-contract.yaml`
- `/home/hr-hm/Project/work/os/core/service-registry.yaml`
- `/home/hr-hm/Project/work/ops/common/coconala-rule-guard.md`
- `/home/hr-hm/Project/work/ops/common/output-schema.yaml`
- `service-registry.yaml` の `bugfix-15000` から辿る `facts_file`
- `/home/hr-hm/Project/work/ops/services/next-stripe-bugfix/evidence-minimum.yaml`
- `/home/hr-hm/Project/work/ops/services/next-stripe-bugfix/scope-matrix.md`
- `/home/hr-hm/Project/work/docs/coconala-japanese-banlist.ja.md`
- `/home/hr-hm/Project/work/docs/coconala-japanese-must-rules.ja.md`
- `/home/hr-hm/Project/work/docs/reply-quality/README.ja.md`
- `/home/hr-hm/Project/work/docs/reply-quality/ng-expressions.ja.md`
- `/home/hr-hm/Project/work/docs/coconala-golden-replies.ja.md`
- `/home/hr-hm/Project/work/docs/coconala-reply-self-check.ja.md`

## 標準ルート
1. 可能なら先に `coconala-intake-router-ja` を使い、経路・状態・`case_type`・`certainty`・`reply_stance`・`reply_contract` を確定する。
2. モードを判定する。
   - UI進行タグ（`#$0` / `#$1` / `#$2` / `#$3`）があるか
   - 文末タグ（`#R` / `#A` / `#D` / `#P`）があるか
   - `#R 受領返信` などのショート指示があるか
3. `#R` の後ろや次行に自由文の補足がある場合は、`user_override` として読む。
4. `reply_contract.primary_question_id`、`explicit_questions`、`answer_map`、`ask_map` を先に読む。
5. `temperature_plan` があれば、`reply_contract` の sibling として扱う。`reply_contract` は「何を答えるか」、`temperature_plan` は「どう受け止めるか」の正本にする。
6. `user_override` があれば、hard constraints を崩さない範囲で `temperature_plan`、`reply_contract`、`response_decision_plan` を狭める方向へ反映する。
7. `reply_contract.issue_plan` は互換要約として扱い、実行契約の正本は `answer_map` と `ask_map` に置く。
8. `reply_skeleton` に沿って section の大枠だけを決める。ただし writer を slot-filling に閉じ込めず、先に `response_decision_plan` を作る。
9. `response_decision_plan` には最低でも `primary_concern / facts_known / blocking_missing_facts / direct_answer_line / response_order` を持たせる。
10. `reply_contract` は「何を言ってよいか」、`response_decision_plan` は「何を先にどう言うか」の正本にする。
11. 文面は renderer が template-first で埋めるのではなく、Codex が freeform に近い形で下書きし、renderer / validator は guardrail として使う。
12. `primary_question_id` に対応する答えは、`response_decision_plan.direct_answer_line` として最初の answer-bearing section に置く。
13. `ask_map` にない質問は増やさず、`blocking_missing_facts` が空なら原則 ask を出さない。
14. 追加質問の前に、現時点の見立てまたは確認観点を1文だけ入れる。
15. 相手がすでに書いた情報は `facts_known` として保持し、再要求しない。
16. `required_moves` を落とさず、`forbidden_moves` を踏まない範囲で文面を下書きする。skill は writer の代わりではなく、writer を壊さないガードレールとして使う。
17. 次回報告時刻を入れる。購入後の調査 / 判定フェーズでは `本日[時刻]まで` と `48時間以内` の二段構成を基本にする。
18. `/home/hr-hm/Project/work/docs/reply-quality/ng-expressions.ja.md` で再発しやすい NG 表現を落とす。
19. 近い場面があれば `/home/hr-hm/Project/work/docs/coconala-golden-replies.ja.md` と `/home/hr-hm/Project/work/docs/reply-quality/gold-replies/README.ja.md` を見て、温度感と依頼数の基準を合わせる。
20. 送信用文面は、毎回 `japanese-chat-natural-ja` で最終自然化する。
21. ただし `japanese-chat-natural-ja` には全文の意味変更権限を与えず、語順・接続・語感の自然化に限定する。
22. 自然化後も `direct_answer_line`、価格、禁止事項、ask 数、次アクション、`required_moves / forbidden_moves` を崩していないか再lintする。
23. 送信用文面モードでは `/home/hr-hm/Project/work/runtime/replies/latest.txt` に保存する。相手文が明確なときは `/home/hr-hm/Project/work/runtime/replies/latest-source.txt` にも保存する。

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
- `temperature_plan` は interaction の実行契約として扱う。`opening_move` `ack_style` `ack_anchor` `warmth_cap` `tone_constraints` は renderer / naturalize / lint の共通入力にする。
- `issue_plan` は、明示質問や実質別論点をどう処理するかの互換要約として使う。
- `answer_now` の論点だけを即答し、`answer_after_check` の論点は理由つきで保留する。
- `ask_client` は、`ask_map` にある最小証跡だけを依頼する。
- `decline` は、規約・公開状態・範囲の理由がある時だけ使う。
- `required_moves` にある動きは必ず文面へ反映する。
- `forbidden_moves` にある動きは、理由が分かっていても本文へ出さない。
- `reply_stance.answer_timing` は要約値に留め、実際に何を答えるかは `answer_map` を優先する。
- `ack_style: brief_specific` の時は、冒頭1文で buyer の具体的な行動・労力・結果・好意のどれかに触れる。`ありがとうございます。` だけで終えない。
- 具体的に触れる時も、褒め言葉に広げない。`動作確認までありがとうございます。` `評価まで入れていただけて助かります。` 程度で止める。
- `warmth_cap: one_sentence` なら、温度のある受けは1文で止めて、2文目から結論や次アクションへ入る。
- 情報収集フェーズで `opening_move: action_first` の時は、温度より先に `何を見るか / 何を送ってほしいか` を短く置く。
- `tone_constraints` に `no_groundless_reassurance` がある時は、`大丈夫です` `よくある症状です` `心配いりません` のような根拠のない安心を足さない。
- `tone_constraints` に `no_sycophancy` がある時は、buyer の認識違いを迎合せず、境界や価格も弱めない。

## skeleton ごとの固定骨格
- `estimate_initial`: 受け止め -> 結論 -> 根拠 -> 価格/購入導線 or 最小質問 -> 次アクション
- `estimate_followup`: 結論 -> 追加情報 -> 次アクション
- `post_purchase_receipt`: 受領確認 -> 確認対象 -> 時刻コミット
- `post_purchase_quick`: 短い反応 -> 今答えること -> 確認後に返すこと -> 最小依頼 -> 時刻
- `post_purchase_report`: 現状 -> 判明事項 -> 次ステップ -> 時刻コミット
- `delivery`: 確認依頼 -> 確認ポイント -> 次ステップ

## renderer の固定
- 最初に renderer 化するのは `estimate_initial` と `post_purchase_quick` の2つだけに絞る。
- renderer は section の有無、順序、ask 上限、主質問を扱う位置を固定する guardrail として使う。
- writer を slot 埋めに閉じ込めない。文章生成は Codex の reasoning を残した freeform draft を優先し、renderer は過剰な template-first を避ける。
- `estimate_initial` では、最初の answer-bearing section で `primary_question_id` に対する結論を出す。
- `post_purchase_quick` では、`answer_now` を先に、`answer_after_check` は理由つき保留として後段に置く。
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
- Yes/No へ直答が必要でも、先頭の1語を機械的に `はい、` に固定しない。`確認できます。` `可能です。` `15,000円の方が近いです。` のように、結論文そのものを先に置いてよい。
- 受領の言い方は `ありがとうございます。` `承知しました。` `確認できます。` などに散らす。
- 外向け返信で内部ラベルの `bugfix` `handoff` をそのまま書かない。`不具合修正` `主要1フローの整理` `このサービス` に言い換える。
- 相手が `高い` `予算が厳しい` のように価格への引っかかりを率直に出している時は、説明へ入る前に短い受け止めを1文だけ置いてよい。弁明には広げない。
- 怒りや催促が強い相手への途中共有では、技術語の粒度を少し落として現在地を返す。`切り分けの軸は〜` より `だいぶ絞れてきています` を優先する。
- 比較説明や価格差の返答で、`差額の説明だけすると` のような事務的な前置きを入れない。
- 追加料金や追加フローの支払い方法を案内する時は、`追加支払いの形をご案内します` のような曖昧な名詞止めを避ける。buyer に見える状態語を使って、`トークルームがまだ開いていればこの中でご案内します` `クローズ後ならメッセージから改めてご相談ください` のように書く。
- 追加対応や別対応への切り分けで、`この場で勝手に進めず` のような防御的な言い方を使わない。`先にご相談したうえで進めます` `進める前にご相談します` を優先する。
- buyer の冒頭文をそのまま返しておうむ返しにしない。`先日はありがとうございました` `ありがとうございます` など相手と同一の書き出しが直後に続くなら、`こちらこそありがとうございました` `前回の件が安定していてよかったです` のように少しずらす。
- 納期や見通しの返答で、`まだ確定できない` と `ここまでは返せる` が同時にある時は、先に `返せること` を置く。`見立てまでは返せます。そのうえで、症状を見ないまま日数は確定していません` の順を基本にする。
- buyer が `ちょっとだけ` `5分で終わる` `CSS1行だけ` のように作業量を根拠に広げてきても、範囲判断は作業量ではなく分類で返す。`1行かどうかに関係なく、今回はデザイン調整なので範囲外です` のように書いてよい。
- 低評価や不満をにおわせる圧力には、その言葉をなぞって返さない。まず `進み方が見えにくい状態にしてしまってすみません` のように、こちらが直せる事実へ受けを寄せてから、次回共有時刻と今見る点を書く。
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
- 追加料金や追加フローの支払い方法を聞かれた場面で、`追加支払いの形` のような曖昧な案内で止まらず、`トークルームがまだ開いていれば / クローズ後なら` のような buyer に見える状態語で案内できているか
- 別対応や追加料金の説明で、`勝手に進めず` のような防御的な語が残っていないか
- buyer の冒頭文をそのまま返すおうむ返しになっていないか
- 比較説明や価格差の返答で、`差額の説明だけすると` のような事務的な前置きが残っていないか
- `/home/hr-hm/Project/work/docs/reply-quality/ng-expressions.ja.md` の NG 表現が残っていないか
- Ban表現ヒット0件を確認したか
- `prequote` で本来 `coconala-prequote-ops-ja` に寄せるべき場面を、このskillで無理に処理していないか
- テンプレを使った場合でも、相手の文脈に合わせて調整したか
- 公開 bugfix で確認専用の別料金案内が再発していないか
- naturalize 後にも、section order・ask 数・価格・hold reason・次アクション・forbidden claim を再lintしたか
