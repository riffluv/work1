# 01_公開embedで概算表示からlead保存_引き継ぎメモ.md

## 1. 対象と目的
今回の対象は、公開 embed で概算結果を表示し、最後のステップで lead を保存する流れです。  
目的は、次の担当者が「表示側の入口」と「保存側の境界」を短時間で把握し、どこを触ると公開品質を崩しやすいかを先に掴める状態にすることです。

## 2. このフローの全体像
`/embed/[publicId]` で公開フォームを表示し、`embed-runtime.tsx` が設定読込・概算計算・最終ステップ制御を担い、最後に `/api/embed/[publicId]/lead` で lead 保存と通知を行う構成です。  
今回見た範囲では、入口は公開 embed の表示、出口は `leads` テーブル保存と通知失敗の記録までです。

## 3. 入口から完了までの流れ
1. `web/src/app/embed/[publicId]/page.tsx` が `publicId` を受け取り、`EmbedRuntime` を表示する
2. `web/src/components/embed-runtime.tsx` が `/api/embed/[publicId]/config` を呼び、公開設定とプラン状態を読む
3. 同コンポーネントが `calculateEstimate()` で概算結果を更新しながら、最終ステップまで進行を管理する
4. 最終ステップ到達後にだけ lead gate が表示され、メール入力後に `/api/embed/[publicId]/lead` へ POST する
5. `lead/route.ts` 側で payload を検証し、published 状態の calculator を再取得し、honeypot / rate limit / 月次上限を確認する
6. サーバー側で `calculateEstimate()` と `buildLeadBrief()` を再実行し、`leads` へ保存したうえで usage / event / 通知を処理する
7. 成功すると client 側で `unlocked` が `true` になり、`ProposalResult` が詳細結果を表示する

## 4. 関連ファイルと役割
- `web/src/app/embed/[publicId]/page.tsx`
  - 役割: 公開 embed 入口。`publicId` と言語を `EmbedRuntime` へ渡す
  - 備考: ここ自体は薄く、実処理は `EmbedRuntime` に寄っています
- `web/src/components/embed-runtime.tsx`
  - 役割: 設定読込、概算更新、ステップ制御、最終 gate、lead 送信、unlock 後の表示切替
  - 備考: 公開品質に直結する責務が多く、最初に追うべきファイルです
- `web/src/app/api/embed/[publicId]/config/route.ts`
  - 役割: published calculator の読込、view 上限チェック、view 加算、`embed_loaded` 記録
  - 備考: service role key や usage 行が崩れると、公開 embed 全体が読めなくなります
- `web/src/app/api/embed/[publicId]/lead/route.ts`
  - 役割: payload 検証、honeypot / rate limit / 月次上限チェック、lead 保存、usage 加算、event 記録、通知
  - 備考: 保存順序と部分成功の理解が必要です
- `web/src/lib/calculate.ts`
  - 役割: client / server 共通の概算計算
  - 備考: 表示結果と保存結果の両方に効くため、変更影響が広いです
- `web/src/lib/lead-brief.ts`
  - 役割: 保存される `lead_brief_json` を組み立てる
  - 備考: LP テンプレでは `followupHint` が営業文脈に直結します
- `web/src/lib/templates.ts`
  - 役割: `briefTemplate` と入力設定の分岐元
  - 備考: LP テンプレの見え方と保存される `lead_brief_json` の両方に影響します
- `web/src/lib/notifications.ts`
  - 役割: owner 宛の lead 通知メール送信
  - 備考: 通知失敗は lead 保存失敗にしない設計です

## 5. 確認できたこと
- 公開 embed は published calculator だけを読み、draft 状態をそのまま出さない構成です
- 詳細結果は最終ステップ到達後にだけ開き、lead 保存成功後に `ProposalResult` へ切り替わります
- lead API は client から渡された `outputs` を信用せず、サーバー側で `calculateEstimate()` を再実行しています
- 通知失敗は `lead_notification_failed` として記録されますが、lead 保存自体は成功扱いのまま進みます

## 6. 推定
- 根拠: `config/route.ts` は表示前に view を加算し、`lead/route.ts` は保存後に usage と通知を進めるため、負荷や外部依存の影響が公開品質へ出やすい構成です
- 影響: bot 的な閲覧で view guardrail が先に消耗したり、lead は残っているのに通知だけ届かない、といった運用差分が起きやすいです
- 根拠: `lead_brief.ts` はテンプレ key に依存して営業向け summary を組み立てます
- 影響: テンプレ設定を変えた時に `lead_brief_json` の中身だけ弱くなると、公開側の見た目より営業価値が先に落ちます

## 7. 未確認
- 足りない情報: 実際に publish 済みの `publicId`、Supabase の migration 適用状況、Resend 設定の有無、外部サイト埋め込み時の実機挙動
- 確認できる条件: 本番相当の環境変数、Supabase データ、公開 embed に対する実アクセス権限があること

## 8. 危険箇所
- 箇所: `web/src/components/embed-runtime.tsx`
  - なぜ危険か: 公開側の状態遷移、概算更新、lead gate、unlock 後表示、iframe resize が1か所に集まっています
  - 触る前に見るファイル: `web/src/app/embed/[publicId]/page.tsx`, `web/src/components/proposal-result.tsx`
  - 典型的な事故: 最終ステップ前に gate が出る、保存成功後に unlock されない、host site で高さが崩れる
- 箇所: `web/src/app/api/embed/[publicId]/lead/route.ts`
  - なぜ危険か: 検証・制限・保存・usage 加算・通知が1ハンドラに集まっており、部分成功の境界を読み違えやすいです
  - 触る前に見るファイル: `web/src/lib/usage.ts`, `web/src/lib/notifications.ts`, `web/src/lib/rate-limit.ts`
  - 典型的な事故: lead は保存されたのに通知だけ来ない、または usage だけずれて月次上限判定が荒れる
- 箇所: `web/src/lib/calculate.ts` / `web/src/lib/lead-brief.ts`
  - なぜ危険か: 公開画面の概算と営業側へ届く案件概要が、同じ入力設定から別々の出力へ展開されています
  - 触る前に見るファイル: `web/src/lib/templates.ts`
  - 典型的な事故: 価格帯は自然なのに `lead_brief_json` の summary や follow-up hint だけ弱くなる

## 9. 次の着手順
- 目的: まず「公開側の見え方」と「保存側の事実」が同じ流れとしてつながっているかを確認する
- 最初に開くファイル: `web/src/components/embed-runtime.tsx`
- 確認する条件: 最終ステップ前に lead gate が出ないこと、`submitLead()` 成功時だけ `unlocked` が切り替わること
- 次に進む基準: 公開側が妥当なら `web/src/app/api/embed/[publicId]/lead/route.ts` で保存順序と部分成功の扱いを見る
- その次に見ること: `web/src/lib/templates.ts` の LP テンプレ1本を選び、`buildLeadBrief()` の summary と follow-up hint が営業文脈として使えるか確認する

## 10. 引き継ぎ時の注意
このメモは「CalcEmbed 全体の仕様書」ではなく、最も product value に近い `public embed -> quote range -> lead保存` を短時間で追うための引き継ぎメモです。  
billing / publish / editor 側へ広げる前に、まずこの end-to-end が一貫しているかを確認する前提で使ってください。
