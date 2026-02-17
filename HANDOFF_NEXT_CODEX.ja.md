# HANDOFF_NEXT_CODEX.ja.md

最終更新: 2026-02-15

## 目的

このファイルは、`/home/hr-hm/Project/work` で新しく起動したCodexに、
現在の方針と運用状態を引き継ぐための恒久メモです。

セッションが切れても、このファイルを最初に読ませれば継続できます。

## 現在の最優先ミッション

1. ココナラ受託（Next.js / Stripe / API連携の不具合修正）を安定運用する
2. スコープ暴走を防ぎつつ、初案件を確実に完了させる
3. テキストのみで高品質納品できる運用を維持する

## 固定方針（変更しない前提）

- 連絡: テキストのみ（通話なし）
- 標準範囲外: 直接push / 本番デプロイ / 新機能開発
- 入口訴求: Next.js + Stripe + API連携（広め）
- 強み訴求: Stripe Webhook（署名検証・不達・重複処理）

### 価格・提供モデル（確定）

1. 基本料金: 15,000円（不具合1件の切り分け〜修正差分/適用手順）
2. 有料オプション: 追加修正1件 15,000円
3. 有料オプション: 追加調査30分 5,000円

## 参照ルート

- 仕事ワークスペース: `/home/hr-hm/Project/work`
- 実績参照（ゲーム）: `/home/hr-hm/Project/jomonsho`
- 実績参照（Stripeキット）: `/home/hr-hm/Project/stripe`

## 返信運用（固定）

- 相手文の貼り付けのみは「分析のみ」で返す（返信文は作らない）
- 「返信文作って」「返信書いて」など明示があるときだけ送信用文面を作る
- 送信用文面を作った場合は、毎回 `/home/hr-hm/Project/work/返信文_latest.txt` に同内容を保存する

## work配下の重要ファイル

- `AGENTS.md`
- `CLAUDE.md`
- `OPERATIONS.md`
- `README.md`
- `Next.js_Stripe不具合診断・修正.md`（現行サービス内容の正本）
- `docs/service-plan.ja.md`
- `docs/coconala-premium-roadmap.ja.md`（上位サービス派生ロードマップ）
- `docs/coconala-guide-market-ops.ja.md`（ココナラ公式段取りの運用メモ）
- `docs/coconala-seller-help-key-links.ja.md`（見積り機能・紐付け・受付設定の要点）
- `docs/coconala-message-templates-short.ja.md`（返信・見積り判定テンプレ）
- `docs/coconala-listing-checklist.md`
- `docs/README.ja.md`
- `TEMPLATES/*.md`
- `scripts/new-case.sh`
- `scripts/move-case.sh`

## 新しいCodexに最初に依頼する内容（コピペ可）

1. `AGENTS.md` と `docs/service-plan.ja.md` を先に読み、矛盾がないか確認
2. ココナラ出品文（タイトル/本文/FAQ/注意事項）を最終版にする
3. 初案件の受注〜納品手順を1ページで整理する
4. 提案文・ヒアリング文・納品文をテンプレから実運用版へ仕上げる

## 更新ルール（大事）

- セッションが終わる前に、このファイルの「更新履歴」に必ず追記する
- 追記するのは以下の3点だけ
  1. 何を決めたか
  2. 何を変更したか（ファイルパス）
  3. 次回の最優先タスク

## 更新履歴

### 2026-02-11
- `work` を恒久運用の案件ワークスペースとして整備
- テンプレを日本語化
- プラン価格を 15,000 / 30,000 / 60,000 で確定
- 履歴置き場を `cases/CLOSED` に統一（`archive` 廃止）

### 2026-02-11（追記）
- 何を決めたか: `AGENTS.md` と `docs/service-plan.ja.md` の方針は整合しており、初回作業は「出品文最終化・1ページ運用手順化・主要テンプレ実運用化」を採用
- 何を変更したか（ファイルパス）: `docs/coconala-listing-final.ja.md`, `docs/first-case-sop-1page.ja.md`, `TEMPLATES/proposal.md`, `TEMPLATES/intake.md`, `TEMPLATES/delivery.md`
- 次回の最優先タスク: 出品画面へ文面を反映し、公開前チェック（チェックリスト照合）を実施する

### 2026-02-12（追記）
- 何を決めたか: コードコメントは「AI臭を排除した自然な実務文」をデフォルト運用にする（毎回の個別指示不要）。
- 何を変更したか（ファイルパス）: `docs/code-comment-style.ja.md`, `AGENTS.md`, `CLAUDE.md`
- 次回の最優先タスク: 実案件で新規コメント追加時に同ルールを運用し、必要なら規約を微調整する

### 2026-02-12（追記2）
- 何を決めたか: `codecomment調査.md` を反映し、コメント規約を確定版へ更新。運用は「Codex実装→Claudeレビュー→Codex最終決定」に固定。
- 何を変更したか（ファイルパス）: `docs/code-comment-style.ja.md`, `CLAUDE.md`, `AGENTS.md`
- 次回の最優先タスク: 実案件でレビュー手順を実運用し、禁止語リストやテンプレを必要最小限で調整する

### 2026-02-12（追記3）
- 何を決めたか: 収益化調査の元レポートは内部引用トークンが多いため、運用用は `docs` 側の clean 版を正本として扱う。
- 何を変更したか（ファイルパス）: `docs/20260212-coconala-monetization-deepresearch.clean.ja.md`
- 次回の最優先タスク: 出品文とFAQに、clean版の「成果物定義」「追加料金判定」「KPI週次運用」を反映する

### 2026-02-12（追記4）
- 何を決めたか: 英語READMEは廃止し、日本語ドキュメントを正本として一本化する。人間向けの docs 目次を新設する。
- 何を変更したか（ファイルパス）: `README.md`, `docs/README.ja.md`
- 次回の最優先タスク: `docs/README.ja.md` を入口に、出品準備の実作業（反映・チェック）を進める

### 2026-02-12（追記5）
- 何を決めたか: `WORKSPACE_MAP.ja.md` の内容を `README.md` に統合し、重複ドキュメントを削減する。
- 何を変更したか（ファイルパス）: `README.md`, `HANDOFF_NEXT_CODEX.ja.md`, `WORKSPACE_MAP.ja.md`（削除）
- 次回の最優先タスク: `README.md` と `docs/README.ja.md` を入口として、ドキュメント運用を一本化する

### 2026-02-12（追記6）
- 何を決めたか: `AGENTS.md` は英語混在をやめ、全項目を日本語で運用する。
- 何を変更したか（ファイルパス）: `AGENTS.md`
- 次回の最優先タスク: 他の運用ドキュメントで英語混在が残る箇所を必要に応じて日本語へ統一する

### 2026-02-12（追記7）
- 何を決めたか: `CLAUDE.md` の英語混在（後半の運用セクション）をやめ、全体を日本語へ統一する。
- 何を変更したか（ファイルパス）: `CLAUDE.md`
- 次回の最優先タスク: 運用ドキュメントの文言統一を維持し、必要な更新は `docs/README.ja.md` から辿れる形で管理する

### 2026-02-12（追記8）
- 何を決めたか: 出品モデルを「3プラン（LIGHT/STANDARD/PREMIUM）」から「基本15,000円 + 有料オプション（追加修正1件/追加調査30分）」へ統一する。
- 何を変更したか（ファイルパス）: `docs/coconala-listing-final.ja.md`, `docs/service-plan.ja.md`, `docs/coconala-listing-checklist.md`, `docs/first-case-sop-1page.ja.md`, `HANDOFF_NEXT_CODEX.ja.md`
- 次回の最優先タスク: ココナラ出品画面の実入力値と `docs/coconala-listing-final.ja.md` の一致確認を行い、差分があれば正本側を更新する

### 2026-02-13（追記9）
- 何を決めたか: サービス内容の現行正本を「基本15,000円で不具合1件対応 + 最終確認は依頼者環境（結果ログで追加調整）」として確定した。
- 何を変更したか（ファイルパス）: `Next.js_Stripe不具合診断・修正.md`, `docs/coconala-listing-final.ja.md`, `HANDOFF_NEXT_CODEX.ja.md`, `docs/README.ja.md`, `docs/service-plan.ja.md`, `AGENTS.md`, `CLAUDE.md`
- 次回の最優先タスク: 依頼相談への初回返信時に、現行正本の定義（不具合1件の範囲・最終確認フロー）で回答を統一する

### 2026-02-13（追記10）
- 何を決めたか: 返信運用を「貼り付けのみ=分析」「返信文作成明示時のみ送信用文面作成」に固定し、送信用文面は毎回 `返信文_latest.txt` に保存する。
- 何を変更したか（ファイルパス）: `SKILLS/coconala-reply-ja/SKILL.md`, `HANDOFF_NEXT_CODEX.ja.md`
- 次回の最優先タスク: 見積り相談の実案件で同運用を使い、返信速度と貼り付け作業時間を短縮する。

### 2026-02-14（追記11）
- 何を決めたか: ココナラ出品画面の確定文言（サービス本文・購入時お願い・FAQ・見積り時お願い）を docs 正本へ同期した。
- 何を変更したか（ファイルパス）: `docs/coconala-listing-final.ja.md`, `Next.js_Stripe不具合診断・修正.md`, `HANDOFF_NEXT_CODEX.ja.md`
- 次回の最優先タスク: 相談文の実案件運用で、確定文言どおりにスコープ判定と返信文作成を統一する。

### 2026-02-14（追記12）
- 何を決めたか: 現行15,000円サービス完走後に追加出品する「不具合修正プレミアム」のロードマップを作成した。
- 何を変更したか（ファイルパス）: `docs/coconala-premium-roadmap.ja.md`, `docs/README.ja.md`, `HANDOFF_NEXT_CODEX.ja.md`
- 次回の最優先タスク: 現行サービスの初回〜2件を完走し、実績ベースでプレミアム出品文ドラフトを作る。

### 2026-02-15（追記13）
- 何を決めたか: `guide_market` の公式段取り（購入時挨拶・滞留時連絡・正式納品）を運用メモ化し、次セッションでも参照可能にした。
- 何を変更したか（ファイルパス）: `docs/coconala-guide-market-ops.ja.md`, `docs/README.ja.md`, `HANDOFF_NEXT_CODEX.ja.md`
- 次回の最優先タスク: 実案件で4フェーズ運用を適用し、返信テンプレと段取りのズレを都度補正する。

### 2026-02-15（追記14）
- 何を決めたか: サービス出品者向けヘルプ（見積り機能セクション）の重要リンクと運用要点を1枚に統合し、次セッションで参照可能にした。
- 何を変更したか（ファイルパス）: `docs/coconala-seller-help-key-links.ja.md`, `docs/README.ja.md`, `HANDOFF_NEXT_CODEX.ja.md`
- 次回の最優先タスク: 実際の見積り相談が来たら、経路判定と「出品サービスに紐付ける」運用を必ず実行する。

### 2026-02-15（追記15）
- 何を決めたか: 見積り相談の判定は「不具合1件（同一原因 / 1フロー / 1エンドポイント）」で固定し、受注前の見積り返信テンプレを運用標準にした。
- 何を変更したか（ファイルパス）: `docs/coconala-message-templates-short.ja.md`, `docs/README.ja.md`, `HANDOFF_NEXT_CODEX.ja.md`
- 次回の最優先タスク: 実案件の見積り相談で、テンプレ10〜14を使って判定と追加料金説明のブレをなくす。

### 2026-02-15（追記16）
- 何を決めたか: DeepResearchの結果は鵜呑みにせず、自然文に効く要素（禁止語言い換え、具体語、依頼者タイプ別テンプレ）のみを採用する。
- 何を変更したか（ファイルパス）: `/home/hr-hm/.codex/skills/coconala-reply-ja/SKILL.md`, `/home/hr-hm/.codex/skills/coconala-reply-ja/references/style-rules.ja.md`, `/home/hr-hm/.codex/skills/coconala-reply-ja/references/message-patterns.ja.md`, `HANDOFF_NEXT_CODEX.ja.md`
- 次回の最優先タスク: 実案件の相談文で skill 使用/不使用のA/B比較を行い、自然さと返信率の高い文型を固定する。

### 2026-02-15（追記17）
- 何を決めたか: 返信文の初手は「安心文」を必須にし、ヒアリングは「必須3項目（本来の動き/実際の不具合/発生環境）+ 任意3項目（ログ/環境/納期）」へ分割する。
- 何を変更したか（ファイルパス）: `/home/hr-hm/.codex/skills/coconala-reply-ja/SKILL.md`, `/home/hr-hm/.codex/skills/coconala-reply-ja/references/style-rules.ja.md`, `/home/hr-hm/.codex/skills/coconala-reply-ja/references/message-patterns.ja.md`, `docs/coconala-message-templates-short.ja.md`, `HANDOFF_NEXT_CODEX.ja.md`
- 次回の最優先タスク: 実相談で「安心文あり」テンプレの返信率を確認し、必要なら初回文面の長さだけ微調整する。

### 2026-02-15（追記18）
- 何を決めたか: 「再現手順（番号で）」の曖昧表現を廃止し、「操作の順番を1,2,3で」に統一。期待結果/実際結果を併記する回収方式へ更新した。
- 何を変更したか（ファイルパス）: `/home/hr-hm/.codex/skills/coconala-reply-ja/SKILL.md`, `/home/hr-hm/.codex/skills/coconala-reply-ja/references/style-rules.ja.md`, `/home/hr-hm/.codex/skills/coconala-reply-ja/references/message-patterns.ja.md`, `docs/coconala-message-templates-short.ja.md`, `HANDOFF_NEXT_CODEX.ja.md`
- 次回の最優先タスク: 初回相談で「操作順1,2,3 + 期待/実際」テンプレの回収率を確認し、記入しづらい項目があれば文言をさらに短くする。

### 2026-02-15（追記19）
- 何を決めたか: ログインなし/単発障害など再現不可のケースでは、番号手順を強制せず「発生直前の操作 + 発生時刻」を回収する。
- 何を変更したか（ファイルパス）: `/home/hr-hm/.codex/skills/coconala-reply-ja/SKILL.md`, `/home/hr-hm/.codex/skills/coconala-reply-ja/references/style-rules.ja.md`, `/home/hr-hm/.codex/skills/coconala-reply-ja/references/message-patterns.ja.md`, `docs/coconala-message-templates-short.ja.md`, `HANDOFF_NEXT_CODEX.ja.md`
- 次回の最優先タスク: 実相談で再現不可ケースにこの回収方式を適用し、初回返信の離脱率を下げる。

### 2026-02-15（追記20）
- 何を決めたか: プロフィール文・出品本文・FAQ専用に、新skill `coconala-listing-ja` を作成し、固定条件を維持した自然文リライト運用を開始した。
- 何を変更したか（ファイルパス）: `/home/hr-hm/.codex/skills/coconala-listing-ja/SKILL.md`, `/home/hr-hm/.codex/skills/coconala-listing-ja/references/fixed-facts.ja.md`, `/home/hr-hm/.codex/skills/coconala-listing-ja/references/listing-style-rules.ja.md`, `HANDOFF_NEXT_CODEX.ja.md`
- 次回の最優先タスク: 現行のプロフィール文と出品本文に `coconala-listing-ja` を適用し、標準トーンの最終版を正本へ反映する。

### 2026-02-16（追記21）
- 何を決めたか: 不具合ヒアリングは「初回の最小3点（環境/操作と現象/証拠）→実装前の必須5点（期待/実際/再現/ログ/環境）」の2段階運用に固定した。再現不可時のみ日時回収を使う。
- 何を変更したか（ファイルパス）: `/home/hr-hm/.codex/skills/coconala-reply-ja/SKILL.md`, `/home/hr-hm/.codex/skills/coconala-reply-ja/references/style-rules.ja.md`, `/home/hr-hm/.codex/skills/coconala-reply-ja/references/message-patterns.ja.md`, `/home/hr-hm/.codex/skills/coconala-reply-ja/references/intake-flow.ja.md`, `HANDOFF_NEXT_CODEX.ja.md`
- 次回の最優先タスク: 実際の見積り相談で2段階ヒアリングを使い、初回返信率と必要情報の回収率（最小3点→必須5点）を確認して微調整する。

### 2026-02-16（追記22）
- 何を決めたか: 会話破綻を防ぐため、返信文生成に「整合性ガード」を追加し、宣言と実体の不一致（3点/5点の数ズレ、番号例の書き漏れ）を出力前に必ず検査する運用に固定した。
- 何を変更したか（ファイルパス）: `/home/hr-hm/.codex/skills/coconala-reply-ja/SKILL.md`, `/home/hr-hm/.codex/skills/coconala-reply-ja/references/consistency-guard.ja.md`, `/home/hr-hm/.codex/skills/coconala-reply-ja/references/message-patterns.ja.md`, `/home/hr-hm/.codex/skills/coconala-reply-ja/references/style-rules.ja.md`, `HANDOFF_NEXT_CODEX.ja.md`
- 次回の最優先タスク: 実相談の返信文を3件連続で整合性ガード適用し、項目数ズレ/例書き漏れがゼロか確認する。

### 2026-02-16（追記23）
- 何を決めたか: 環境ヒアリングの用語は `本番/プレビュー/ローカル` に固定し、`開発環境` は曖昧語として単独使用しない運用にした。
- 何を変更したか（ファイルパス）: `/home/hr-hm/.codex/skills/coconala-reply-ja/SKILL.md`, `/home/hr-hm/.codex/skills/coconala-reply-ja/references/style-rules.ja.md`, `/home/hr-hm/.codex/skills/coconala-reply-ja/references/message-patterns.ja.md`, `/home/hr-hm/.codex/skills/coconala-reply-ja/references/intake-flow.ja.md`, `/home/hr-hm/.codex/skills/coconala-reply-ja/references/consistency-guard.ja.md`, `HANDOFF_NEXT_CODEX.ja.md`
- 次回の最優先タスク: 実相談で環境を `本番/プレビュー/ローカル` の3択で回収し、回答率と誤解発生の有無を確認する。

### 2026-02-16（追記24）
- 何を決めたか: 見積り設定UIの挙動を迷わないように、`見積り相談受付` と `購入前見積り必須` の関係を3行で確認できるチートシートを新設した。
- 何を変更したか（ファイルパス）: `docs/coconala-estimate-ui-cheatsheet.ja.md`, `docs/README.ja.md`, `HANDOFF_NEXT_CODEX.ja.md`
- 次回の最優先タスク: 出品設定確認時はチートシートを起点に、実画面のON/OFF値と固定運用（ON/OFF/ON）が一致しているか確認する。

### 2026-02-16（追記25）
- 何を決めたか: 見積り相談の返信品質を固定するため、`coconala-reply-ja` に経路別テンプレ（サービス経由 / プロフィール経由 / メッセージ経由）を追加し、初回は「必須3項目 + 任意3項目」で回収する運用に統一した。
- 何を変更したか（ファイルパス）: `/home/hr-hm/.codex/skills/coconala-reply-ja/SKILL.md`, `/home/hr-hm/.codex/skills/coconala-reply-ja/references/estimate-reply-flow.ja.md`, `/home/hr-hm/.codex/skills/coconala-reply-ja/references/message-patterns.ja.md`, `/home/hr-hm/.codex/skills/coconala-reply-ja/references/consistency-guard.ja.md`, `docs/coconala-message-templates-short.ja.md`, `HANDOFF_NEXT_CODEX.ja.md`
- 次回の最優先タスク: 実際の見積り相談で経路別テンプレを適用し、初回返信で必要情報が集まるか（必須3の回収率）を確認する。

### 2026-02-16（追記26）
- 何を決めたか: 文章の分かりづらさ再発を防ぐため、返信/出品文の両skillに「人間向け明瞭化（1文1意味、1文目で結論、対応内容と納品物を分離）」を最優先ルールとして追加した。
- 何を変更したか（ファイルパス）: `/home/hr-hm/.codex/skills/coconala-reply-ja/references/style-rules.ja.md`, `/home/hr-hm/.codex/skills/coconala-reply-ja/references/consistency-guard.ja.md`, `/home/hr-hm/.codex/skills/coconala-listing-ja/references/listing-style-rules.ja.md`, `HANDOFF_NEXT_CODEX.ja.md`
- 次回の最優先タスク: 返信文・FAQ作成時に「1文目で回答」「1文1意味」が守られているかを出力前チェックで確認する。

### 2026-02-16（追記27）
- 何を決めたか: 3つのDeepResearch結果は「部分採用」方針に固定し、自然文に効く要素のみskillへ反映した。具体的には、硬い定型の削除、ヒアリング順序の統一（必須3=期待/実際/環境）、支払い仕様ガード（見積り経由オプション不可・正式納品後はおひねり・クローズ後は新規依頼）を適用した。
- 何を変更したか（ファイルパス）: `/home/hr-hm/.codex/skills/coconala-reply-ja/SKILL.md`, `/home/hr-hm/.codex/skills/coconala-reply-ja/references/style-rules.ja.md`, `/home/hr-hm/.codex/skills/coconala-reply-ja/references/message-patterns.ja.md`, `/home/hr-hm/.codex/skills/coconala-reply-ja/references/estimate-reply-flow.ja.md`, `/home/hr-hm/.codex/skills/coconala-reply-ja/references/consistency-guard.ja.md`, `/home/hr-hm/.codex/skills/coconala-reply-ja/references/intake-flow.ja.md`, `/home/hr-hm/.codex/skills/coconala-listing-ja/references/fixed-facts.ja.md`, `/home/hr-hm/.codex/skills/coconala-listing-ja/references/listing-style-rules.ja.md`, `HANDOFF_NEXT_CODEX.ja.md`
- 次回の最優先タスク: 実際の見積り相談1件で新テンプレを運用し、(1) 初回返信での離脱有無 (2) 必須3回収率 (3) 文章の分かりやすさ指摘の有無を確認する。

### 2026-02-16（追記28）
- 何を決めたか: Claudeレビューの有効指摘のみ採用し、skill文面の自然さと可読性を追加改善した。特に、見積り初回の安心文統一、セクション番号逆順修正、曖昧語（テキストのみ）排除、再現手順の表現統一を反映した。
- 何を変更したか（ファイルパス）: `/home/hr-hm/.codex/skills/coconala-reply-ja/references/message-patterns.ja.md`, `/home/hr-hm/.codex/skills/coconala-reply-ja/references/estimate-reply-flow.ja.md`, `/home/hr-hm/.codex/skills/coconala-reply-ja/references/style-rules.ja.md`, `/home/hr-hm/.codex/skills/coconala-listing-ja/references/fixed-facts.ja.md`, `/home/hr-hm/.codex/skills/coconala-listing-ja/references/listing-style-rules.ja.md`, `HANDOFF_NEXT_CODEX.ja.md`
- 次回の最優先タスク: 実際の見積り相談1件で、(1) 返信の読みやすさ (2) 初回3点の回収率 (3) 不要な追質問の有無を確認し、必要ならテンプレをさらに短文化する。

### 2026-02-16（追記29）
- 何を決めたか: `skill-ux-review-2026-02-16.md` の提案を評価し、自然さと可読性に効く項目のみ採用した。採用対象は、初回返信の語彙平易化（切り分け→対応方針）、任意3項目の箇条書き化、スコープ説明の平易化、スラッシュ表現の除去、初回メッセージ型のラベル統一。
- 何を変更したか（ファイルパス）: `/home/hr-hm/.codex/skills/coconala-reply-ja/references/message-patterns.ja.md`, `/home/hr-hm/.codex/skills/coconala-reply-ja/references/estimate-reply-flow.ja.md`, `/home/hr-hm/.codex/skills/coconala-reply-ja/references/intake-flow.ja.md`, `/home/hr-hm/.codex/skills/coconala-listing-ja/references/fixed-facts.ja.md`, `HANDOFF_NEXT_CODEX.ja.md`
- 次回の最優先タスク: 実相談1件で「初回返信後の回答率」「任意3項目の回収率」「追加料金説明後の離脱有無」を観測し、必要ならテンプレをさらに短文化する。

### 2026-02-16（追記30）
- 何を決めたか: `skill-japanese-teacher-review.md` は実務に有効。採用は「自然さ/誤読防止に直結する最小修正」に限定し、価格・仕様変更系は不採用方針を維持した。
- 何を変更したか（ファイルパス）: `/home/hr-hm/.codex/skills/coconala-reply-ja/references/message-patterns.ja.md`, `/home/hr-hm/.codex/skills/coconala-reply-ja/references/estimate-reply-flow.ja.md`, `/home/hr-hm/.codex/skills/coconala-reply-ja/references/consistency-guard.ja.md`, `/home/hr-hm/.codex/skills/coconala-listing-ja/references/listing-style-rules.ja.md`, `HANDOFF_NEXT_CODEX.ja.md`
- 次回の最優先タスク: 実案件ログを1週間分採点表で評価し、返信率が落ちる文型（語尾固定・専門語先行）を追加で削る。

### 2026-02-16（追記31）
- 何を決めたか: Claudeレビューの3点は妥当と判断し、現行運用（基本15,000円 + 有料オプション）に合わせて最小修正する方針で反映した。`OPERATIONS.md` は日本語統一、caseテンプレは初動で埋める項目だけを持つ実用版に更新した。
- 何を変更したか（ファイルパス）: `scripts/new-case.sh`, `OPERATIONS.md`, `cases/_case-template/README.md`, `HANDOFF_NEXT_CODEX.ja.md`
- 次回の最優先タスク: `scripts/new-case.sh` で新規ケースを1件作成し、`CASE.md` と `cases/_case-template/README.md` の記入フローが実運用で過不足ないか確認する。

### 2026-02-16（追記32）
- 何を決めたか: 案件IDは長いslugをやめ、`case-001` 形式の連番へ統一した。`new-case.sh` は引数なしで自動採番を標準にし、必要時のみ `case-XXX`（または数字）指定で作成できる運用にした。
- 何を変更したか（ファイルパス）: `scripts/new-case.sh`, `scripts/move-case.sh`, `OPERATIONS.md`, `README.md`, `HANDOFF_NEXT_CODEX.ja.md`
- 次回の最優先タスク: 実際に `./scripts/new-case.sh`（引数なし）で `case-001` を作成し、受領zipの配置〜`move-case.sh` での状態移動までを1回通しで確認する。

### 2026-02-16（追記33）
- 何を決めたか: 見積り初回の3点回収文面は「安心文 + 平易語 + 回答例」を必須にする。必須3+任意3の構造は維持しつつ、任意3の3項目目に「画面スクショ + 利用技術（分かる範囲）」を含めて、判定精度を上げる運用にした。
- 何を変更したか（ファイルパス）: `/home/hr-hm/.codex/skills/coconala-reply-ja/references/estimate-reply-flow.ja.md`, `/home/hr-hm/.codex/skills/coconala-reply-ja/references/message-patterns.ja.md`, `docs/coconala-message-templates-short.ja.md`, `HANDOFF_NEXT_CODEX.ja.md`
- 次回の最優先タスク: 実見積り1件で新文面を適用し、(1) 初回返信率 (2) 追加質問回数 (3) スタック不明による往復有無を確認する。

### 2026-02-16（追記34）
- 何を決めたか: 見積り初回返信は「非エンジニア向け（標準）」と「エンジニア向け（要点重視）」の2パターンを固定テンプレ化した。必須3+任意3の構造は維持し、どちらも安心文と回答例を含める運用に統一した。
- 何を変更したか（ファイルパス）: `/home/hr-hm/.codex/skills/coconala-reply-ja/references/estimate-reply-flow.ja.md`, `docs/coconala-message-templates-short.ja.md`, `HANDOFF_NEXT_CODEX.ja.md`
- 次回の最優先タスク: 実相談で相手タイプに合わせてA/Bを使い分け、返信率と追加往復回数の差を記録して運用テンプレを1本化するか判断する。

### 2026-02-16（追記35）
- 何を決めたか: Claude再レビューの指摘4点を採用し、見積り初回文面の硬さと旧表現の残りを除去した。A版デフォルト運用は維持し、B版は補助テンプレとして継続する。
- 何を変更したか（ファイルパス）: `/home/hr-hm/.codex/skills/coconala-reply-ja/references/estimate-reply-flow.ja.md`, `docs/coconala-message-templates-short.ja.md`, `HANDOFF_NEXT_CODEX.ja.md`
- 次回の最優先タスク: 実相談でA版をデフォルト適用し、B版に切り替えたケースの成約率・追質問回数を1週間記録する。

### 2026-02-16（追記36）
- 何を決めたか: 最終レビューで残った軽微差分（B版の「対応可否」表現）を統一し、見積り初回テンプレの語調をA/Bで揃えた。
- 何を変更したか（ファイルパス）: `docs/coconala-message-templates-short.ja.md`, `HANDOFF_NEXT_CODEX.ja.md`
- 次回の最優先タスク: A版デフォルトで実運用し、相手の返信内容が技術寄りのときのみB版へ切り替える判断基準を案件メモに記録する。

### 2026-02-16（追記37）
- 何を決めたか: Claudeの全体レビュー（CONDITIONAL GO）で有効だった指摘を採用し、見積り初回以外の文面と出品正本の整合を強化した。特に、先走り判定の回避、`結果ログ` 表現の除去、見積りUI文面の「まず3点」統一を反映した。
- 何を変更したか（ファイルパス）: `/home/hr-hm/.codex/skills/coconala-reply-ja/references/message-patterns.ja.md`, `docs/coconala-listing-final.ja.md`, `HANDOFF_NEXT_CODEX.ja.md`
- 次回の最優先タスク: 実運用で「購入後初回テンプレ（セクション1）」と「見積り初回テンプレ（セクション10）」の使い分けミスがないかを1週間記録し、混同が出るならテンプレ名をさらに明確化する。

### 2026-02-16（追記38）
- 何を決めたか: Claude最終レビューで `最終GO` を取得。日本語の自然さ・分かりやすさ・実運用安定性・整合性がすべて5/5に到達したため、現行テンプレと出品正本を運用開始版として確定した。
- 何を変更したか（ファイルパス）: `HANDOFF_NEXT_CODEX.ja.md`
- 次回の最優先タスク: 実案件で `初回返信率` `追加往復回数` `技術不明による追質問有無` を1週間記録し、数値ベースで微調整判断を行う。

### 2026-02-17（追記39）
- 何を決めたか: 公開直前版として、実際の入力文面（`現在の製品ページとプロフィール`）を `docs/coconala-listing-final.ja.md` に同期した。以後は listing-final を正本として更新する。
- 何を変更したか（ファイルパス）: `docs/coconala-listing-final.ja.md`, `HANDOFF_NEXT_CODEX.ja.md`
- 次回の最優先タスク: 実画面へ反映後、表示崩れ（改行/FAQ順/200字欄）を確認し、差分があれば listing-final 側へ即時反映する。

### 2026-02-17（追記40）
- 何を決めたか: `docs/coconala-listing-final.ja.md` は、運用用の見出し付き版ではなく「実画面コピペ完全一致フォーマット」を正本とする運用に変更した。
- 何を変更したか（ファイルパス）: `docs/coconala-listing-final.ja.md`, `HANDOFF_NEXT_CODEX.ja.md`
- 次回の最優先タスク: サービス編集後は `現在の製品ページとプロフィール` と `docs/coconala-listing-final.ja.md` の差分を都度ゼロに保つ。

### 2026-02-17（追記41）
- 何を決めたか: プロフィール文の最終軽微修正（UI残骸削除・禁止語の平易化・冒頭重複の緩和）を反映し、公開運用に移行できる状態へ更新した。
- 何を変更したか（ファイルパス）: `現在のプロフィール`, `HANDOFF_NEXT_CODEX.ja.md`
- 次回の最優先タスク: 実画面プレビューでプロフィールの表示順（ひとことアピールと自己紹介本文の重複感）を確認し、必要なら1文だけ短縮する。

### 2026-02-17（追記42）
- 何を決めたか: セッションが切れても納品形式の確認漏れが出ないよう、購入直後に「patch/diff か 修正済みZIP か」を必ず合意する運用を固定した。
- 何を変更したか（ファイルパス）: `docs/coconala-message-templates-short.ja.md`, `docs/coconala-guide-market-ops.ja.md`, `docs/README.ja.md`, `HANDOFF_NEXT_CODEX.ja.md`
- 次回の最優先タスク: 実案件1件で「納品形式の確認テンプレ（セクション15）」を使用し、案件メモに合意した納品形式が記録されているか確認する。

### 2026-02-17（追記43）
- 何を決めたか: 「特例対応しない？」への判断を毎回ぶらさないため、特例対応ポリシーを docs と skill の両方に固定した。基本料金の値引きは行わず、同一原因の軽微調整のみ短時間吸収、別原因は追加見積りに切り替える。
- 何を変更したか（ファイルパス）: `docs/coconala-special-case-policy.ja.md`, `docs/coconala-guide-market-ops.ja.md`, `docs/coconala-message-templates-short.ja.md`, `docs/README.ja.md`, `/home/hr-hm/.codex/skills/coconala-reply-ja/SKILL.md`, `/home/hr-hm/.codex/skills/coconala-reply-ja/references/consistency-guard.ja.md`, `/home/hr-hm/.codex/skills/coconala-reply-ja/references/message-patterns.ja.md`, `/home/hr-hm/.codex/skills/coconala-reply-ja/references/style-rules.ja.md`, `HANDOFF_NEXT_CODEX.ja.md`
- 次回の最優先タスク: 実案件で特例を使ったら案件メモに「理由（同一原因）/追加時間/当月累計」を必ず記録し、月次上限（実績5件未満: 月2件・30分）を超える前に追加見積りへ切り替える。

### 2026-02-17（追記44）
- 何を決めたか: 特例対応の上限管理を実運用で漏らさないため、案件テンプレに「納品形式の合意」「特例使用有無」「追加時間」「当月累計」を記録する欄を追加した。
- 何を変更したか（ファイルパス）: `cases/_case-template/README.md`, `HANDOFF_NEXT_CODEX.ja.md`
- 次回の最優先タスク: 新規案件作成時に `cases/_case-template/README.md` の新項目を必ず埋め、特例累計が閾値に達したら追加見積りへ切り替える。

### 2026-02-17（追記45）
- 何を決めたか: 特例対応の数値上限は固定しない方針へ変更した。今後は「同一原因の軽微調整か」「短時間で収束見込みがあるか」を都度判断し、文面フロー（同一原因は吸収案内 / 別原因は追加見積り案内）だけを固定する。追記43/44の月次閾値運用は廃止する。
- 何を変更したか（ファイルパス）: `docs/coconala-special-case-policy.ja.md`, `/home/hr-hm/.codex/skills/coconala-reply-ja/SKILL.md`, `/home/hr-hm/.codex/skills/coconala-reply-ja/references/consistency-guard.ja.md`, `cases/_case-template/README.md`, `HANDOFF_NEXT_CODEX.ja.md`
- 次回の最優先タスク: 特例を使った案件では「理由（同一原因）」「追加時間」「判断メモ」を案件メモに残し、数値閾値ではなくケース判断で次アクション（吸収/追加見積り）を決める。
