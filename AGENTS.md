# AGENTS.md（Internal OS Core）

## ミッション
この workspace は、ココナラ受託の返信・案件記録・実装・納品を、mode を切り替えながら長期運用する内部OSです。  
最優先は、購入後のコード分析・修正・実装でノイズを混ぜないことです。

## 起動正本
- 起動の単一正本は `/home/hr-hm/Project/work/docs/next-codex-prompt.txt`
- `HANDOFF_NEXT_CODEX.ja.md` は履歴専用。起動時の必読には使わない

## Core OS 固定
- 常時前面に置くのは `Core OS` だけ
- mode の正本は `/home/hr-hm/Project/work/runtime/mode.txt`
- active case の正本は `/home/hr-hm/Project/work/runtime/active-case.txt`
- 送信用返信の保存先は `/home/hr-hm/Project/work/runtime/replies/latest.txt`
- 直近の相手文の保存先は `/home/hr-hm/Project/work/runtime/replies/latest-source.txt`

## 公開状態ルール
- 公開状態の正本は `/home/hr-hm/Project/work/os/core/service-registry.yaml`
- 外向けに案内してよいのは `public: true` のサービスだけ
- 現時点の外向け live は `bugfix-15000` のみ
- `handoff-25000` は内部準備用の参照にとどめ、外向け返信でサービス名・価格・購入導線を出さない

## サービスページ正本
- サービスページ文面の正本は `service-registry.yaml` の `source_of_truth` を使う
- `bugfix-15000` の正本は `/home/hr-hm/Project/work/サービスページ/bugfix-15000.live.txt`
- `handoff-25000` の正本は `/home/hr-hm/Project/work/サービスページ/handoff-25000.ready.txt`
- Codex がサービスページ文面を確認・修正・監査する時は、必ず上記2ファイルを先に参照する
- Claude / Gemini に監査させる時も、まず上記2ファイルを直接参照させる
- `docs/coconala-listing-final.ja.md` などの mirror / 同期用ファイルは参照補助にとどめ、公開判断や文言監査の基準にしない

## 厳守する境界
- 通話・ビデオ会議は行わない
- 外部連絡、外部共有、外部決済へ誘導しない
- 契約に明記がない限り、依頼者リポジトリへの直接 push は行わない
- 契約に明記がない限り、本番デプロイは行わない
- `.env` / APIキー / Webhook秘密値など、生の秘密情報は扱わない
- 法務・税務の助言は行わない

## 実務の固定
- 事前知識より、ログ・コード・再現手順などの一次証跡を優先する
- スコープは固定し、新要件が出たら一旦停止して範囲変更として扱う
- 購入後の実装判断の正本は `ops/cases/open/{case_id}/README.md` と受領コードとログに置く
- 実装 mode では返信系 docs を主文脈に常駐させない
- 返信が必要な時だけ `Coconala OS` の lane に戻る
- Stripe案内は `/home/hr-hm/Project/work/stripe日本語UI案内` を最優先参照する
- コードコメントは `/home/hr-hm/Project/work/docs/code-comment-style.ja.md` を毎回デフォルト適用する
- Agent-Reach などの外部調査ツールは、ユーザーが明示した時だけ使う
- 外部調査ツールは OS 本体に常駐させず、外部調査レーンとして切り離して扱う
- 外部調査の結果はそのまま正本へ入れず、要約・選別した調査メモ経由で持ち込む

## 日本語品質の反映
- 送信用返信は毎回 `japanese-chat-natural-ja` を最終自然化として通す
- Codex は主軸として最終判断と正本反映を担うが、外部AIの案を優先的に退ける意味ではない
- 外部AIの提案は、出所ではなく妥当性・再発性・実務ノイズ・要点維持・既存ルールとの整合で採否を決める
- 外部AIの案がより妥当なら、Codex はそれを採用して workspace に統合してよい
- 外部レビューで妥当と判断した再発性のある自然化ルールは、その場の文面修正だけで終わらせず、関連する skill / prompt / guide の正本へ反映する
- 反映前に、その改善が `reply-only` / `common` / `delivery-only` のどれかを必ず判定する
- `reply-only`: 返信文・途中報告・正式納品メッセージなどトークルーム文面だけに反映する
- `common`: 返信文と納品物の両方で再発する日本語品質改善として反映する
- `delivery-only`: 添付する納品物本文・見出し・結論文・確認/推定/未確認の整理だけに反映する
- `reply-only` の改善を、`common` 判定なしで納品物正本へ入れない
- `delivery-only` の改善を、`common` 判定なしで返信文正本へ入れない
- 恒久反映してよいのは、次の条件を満たす指摘に限る
- 再発性がある
- 実務ノイズを増やさない
- 要点を薄めない
- 既存ルールと衝突しない
- 1回限りの好みではない
- `#CL` は、直近の相手文（`latest-source.txt`）と送信用返信文（`latest.txt`）を対象に、Claude向け監査プロンプトを作るショートカットとして扱う
- `#CL` の補足行や後続条件は、監査観点としてプロンプトへ反映する
- `#GE` は、直近の相手文（`latest-source.txt`）と送信用返信文（`latest.txt`）を対象に、Gemini向け監査プロンプトを作るショートカットとして扱う
- `#GE` の補足行や後続条件は、監査観点としてプロンプトへ反映する

## stock 運用
- 新しい文章 stock は `/home/hr-hm/Project/work/ops/tests/stock/inbox` に置く
- Codex へ stock 処理を依頼する時は、「返信文を書いて」ではなく「inbox の stock を取り込んで、seed / eval / holdout / edge に仕分けし、eval-sources に接続して、contract / renderer / lint / regression を回す」と伝える
- stock 処理の標準は、`inbox` 取り込み -> `seed / eval / holdout / edge` 仕分け -> `eval-sources.yaml` 接続 -> `check-coconala-reply-role-suites.py --save-report` 実行
- stock から見つかった再発パターンは、返信文の単発修正で終わらせず、`rule / renderer / lint` のどこに戻すかを判断して正本へ反映する
- 実ストックを最優先し、Claude / Gemini 生成文は不足領域の補完として扱う

## mode の使い分け
- `coconala`: 見積り相談、購入前後の返信、公開中サービスの案内
- `implementation`: 購入後のコード分析・修正・実装
- `delivery`: 納品物、正式納品、クローズ前後
- 購入後に case を開始したら `implementation` を主モードにする
- 納品物を整える段階で `delivery` へ切り替える

## script 正本
- `./scripts/os-check.sh`: Internal OS の起動整合確認
- `./scripts/case-open.sh`: `#S` の正本
- `./scripts/case-note.sh`: `#M` の正本
- `./scripts/case-phase.sh`: open case の phase / mode 切替
- `./scripts/case-switch.sh`: active case の明示切替
- `./scripts/case-close.sh`: `#C` の正本
- `./scripts/reply-save.sh`: 送信用返信の保存

## 納品の固定
- 標準納品物は `00_結論と確認方法.md` とコード納品物
- 納品は、何が壊れていたか / 何を変更したか / どう検証するか、の3点を証拠付きで示す
- 最終確認は依頼者環境で実施してもらう。合意内容と相違が残る場合は、トークルームの差し戻しで受ける
- 納品物本文で、結果共有・追加情報送付・継続前提の依頼をしない
- `japanese-chat-natural-ja` を通すのはトークルームに送る文面だけで、添付する納品物本文には適用しない
