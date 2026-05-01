# 返信OSコア完成条件チェックリスト

更新日: 2026-05-01

## 位置づけ

このチェックリストは、ココナラ返信OSを「さらに #RE を回すか」ではなく、「コアとして完成に近いか」で判断するための正本です。

Pro 分析 `chatgptPro/ココナラ返信OS設計レビュー5-01.txt` の結論を受け、今後は同型 batch の量産ではなく、完成条件・coverage・失敗分類・運用停止条件を優先します。

## 現在の総評

- 返信生成コアは `機能コア完成圏`。
- ただし、完成判定に必要な meta layer がまだ不足している。
- いま不足しているのは「返信文をもっと直すこと」ではなく、何を検証済みとみなし、何を未検証として残すかを判断する仕組み。

## 完成条件

| 領域 | 完成条件 | 現在の正本 | 現状 | 次に見ること |
| --- | --- | --- | --- | --- |
| Service truth | 公開状態、価格、scope、成果物、禁止事項が一意に解決できる | `os/core/service-registry.yaml`, `サービスページ/bugfix-15000.live.txt`, `ops/services/next-stripe-bugfix/service-pack/facts.yaml` | ほぼ安定 | service page と service-pack facts の意味一致を定期確認する |
| Phase contract | `prequote / quote_sent / purchased / delivered / closed` ごとの可否と次アクションが分かれている | `ops/common/interaction-states.yaml`, `ops/common/routing-table.yaml`, `ops/common/coconala-rule-guard.md` | 安定 | ココナラ仕様変更時だけ再監査する |
| Reply decision | 主質問、answer_map、ask_map、required/forbidden moves が返信生成前に固定される | `ops/common/output-schema.yaml`, intake / bugfix skills | 安定 | #R と #RE の candidate 生成経路がズレていないかを見る |
| Evidence / grounding | 相手文にない技術語・原因候補・作業状況を足さない | `evidence-minimum.yaml`, service-pack evidence, sentries | 安定化中 | 実案件 stock で確認する |
| Secret safety | `.env` / APIキー / Webhook secret / DB接続文字列の生値を扱わない | `risk-gates.yaml`, service-pack boundaries | 安定 | zip 共有案内時の伏せ直し導線を維持する |
| Writer preservation | AI の思考を潰さず、Classifier / Writer / Reviewer を分ける | `writer-brief.ja.md`, `skill-thought-preservation-minimal.ja.md` | 良好 | Writer に監査プロンプト全文を背負わせない |
| Naturalizer safety | 日本語自然化が価格・scope・phase・secret・支払い導線を上書きしない | `japanese-chat-natural-ja`, `lens-taxonomy.yaml` | 良好 | `safe_connection` を gate として使う |
| Evaluation coverage | どの family が検証済みで、どこが薄いか見える | `ops/tests/fixture-coverage-map.yaml` | 新規整備中 | #RE は coverage が薄い family だけ回す |
| Learning loop | 指摘を rule / gold / lint / no-change に分けられる | `failure-taxonomy.yaml`, `lens-taxonomy.yaml`, `adoption-policy.ja.md` | 新規整備中 | soft lens を hard rule 化しすぎない |
| Multi-service readiness | ココナラ固有、サービス固有、日本語チャット汎用、AI返信汎用が分離されている | service pack, platform contract, naturalizer, common schema | 設計可能 | アプリ化前に memory / phase schema を固める |

## 完成判定ゲート

次をすべて満たしたら、`bugfix-15000` の返信コアは「v1 完成候補」とみなす。

1. `bugfix-15000` の public facts が service page / registry / service-pack で矛盾しない。
2. `handoff-25000` が public:false のまま live / #RE に漏れない。
3. phase ごとの forbidden move が deterministic test で落ちない。
4. #R と #RE の writer candidate が同じ contract packet から作られていることを確認できる。
5. #RE family ごとの saturation が coverage map に記録されている。
6. 3本以上の同 family batch で deterministic fail がなく、指摘が preference / acceptable_as_is に収まる。
7. soft lens の新規追加がなくても、human audit の違和感を taxonomy へ分類できる。
8. Pro / xhigh に投げる理由が routine ではなく、未知 failure / lens 昇格 / 公開前判定 / app 化判断のいずれかに説明できる。

## #RE を止める条件

同じ family で次を満たしたら、追加の #RE は一旦停止する。

- 3 batch 連続で必須修正なし。
- 軽微修正が case_fix / preference の範囲に収まる。
- 新規 hard rule / lint / renderer 修正が発生していない。
- local lint / regression / service-pack fidelity / sentry が green または既存 warning のみ。
- human audit が「好み差」「少し硬いが安全」の範囲と判断している。

## 次の優先順位

1. 同型 #RE を止め、coverage map で薄い領域だけを回す。
2. `failure-taxonomy.yaml` と `lens-taxonomy.yaml` を使い、指摘を分類してから戻す。
3. `reply-memory-schema.yaml` と `phase-contract-schema.yaml` でアプリ化前の contract packet を固める。
4. 実案件 stock を取り込み、synthetic では見えない business chat viability を検証する。
5. Pro / xhigh は節目だけに使う。

