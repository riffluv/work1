# reply-quality（reply-only）

## 目的
- ココナラ返信の品質を、個別添削ではなく運用ループで安定させる。
- `#RE` は通常 live の `bugfix-15000`、`#BR` は future-dual の境界訓練として分ける。
- 納品物本文ではなく、トークルーム返信の品質改善にだけ使う。

## 現行入口
- `self-check-core-always-on.ja.md`
  - Reviewer が常時見る最小チェック。
- `writer-brief.ja.md`
  - Writer に渡す最小原則。
- `acceptance-gate.ja.md`
  - 送る / 差し戻す / system に戻す通過条件。
- `failure-taxonomy.ja.md`
  - 失敗分類。
- `guidance-scoping.ja.md`
  - 改善を効かせる route / state / service を切る表。
- `adoption-policy.ja.md`
  - 指摘を恒久反映するか決める基準。
- `forbidden-moves-matrix.ja.md`
  - 止めるべき崩れの表。
- `ng-expressions.ja.md`
  - 再発させたくない悪い言い回し。
- `scorecard.ja.md`
  - 軽い採点表。
- `multi-turn-check.ja.md`
  - 連続したやり取りの停滞・矛盾を見るチェック。

## Service Grounding
- `service-pack-source-of-truth-policy.ja.md`
  - service-pack 内の正本 / 補助 / runtime asset の分離。
- `service-pack-runtime-interface.ja.md`
  - 共通 runtime が service facts を読む順序。
- `service-pack-v1-fixed-points.ja.md`
  - v1 として固定してよい構成。
- `service-facts-onboarding-template.ja.md`
  - 新サービス導入時の facts テンプレ。
- `service-page-change-checklist.ja.md`
  - サービスページ変更時に返信OSへ戻す場所を確認するチェックリスト。
- `service-grounding-audit-20260429.ja.md`
  - `bugfix-15000` の本丸が renderer / validator / regression へ接続されているかの棚卸し。
- `skill-noise-audit-20260429.ja.md`
  - 古い skill / docs / template が live へノイズを混ぜないかの棚卸し。

## State / Layering
- `state-schema-minimal-contract.ja.md`
  - multi-turn で最低限持つ state 項目。
- `self-check-l1-minimal-universal.ja.md`
  - サービス非依存の最小チェック。
- `self-check-l2-domain-minimal.ja.md`
  - 受託返信としての最小チェック。
- `seller-initiated-lane-minimal.ja.md`
  - こちら起点の進捗共有・補足・完了報告の最小構成。
- `skill-thought-preservation-minimal.ja.md`
  - skill が Codex の判断を邪魔しないための最小方針。
- `re-alignment-checklist-20260429.ja.md`
  - Pro の `#RE / #R` 生成経路ズレ指摘を、反映済み / 一部反映 / 未反映に分けた作業チェックリスト。
- `r-smoke-style-anchors-20260429.ja.md`
  - `#R` 実出力の自然な文体を、`#RE` writer candidate へ戻すための一時 style anchor。

## #RE
- `#RE` は、通常 live の `bugfix-15000` 返信品質確認。
- `handoff-25000` のサービス名・25,000円・購入導線は出さない。
- `#RE` の deterministic renderer 出力は `renderer_baseline` として扱う。自然さの人間監査を #R 本丸へ戻す前に、同じ fixture の `writer-brief` から作った writer candidate でも再現するかを確認する。
- `renderer_baseline` の違和感は `#RE only` の可能性があるため、すぐ共通 skill / rule へ戻さない。public leak / secret 値要求 / phase drift / price・scope 崩れは candidate_source に関係なく必須修正として扱う。
- markdown batch 内の `writer_candidate_manual` は `--candidate-batch-file` で同じ fixture / contract / lint に通してから監査に出す。
- 出力先:
  - `/home/hr-hm/Project/work/サービスページ/rehearsal/bugfix-15000-返信学習/返信監査_batch-01.md`
- 観察計画:
  - `question-type-batch-plan-20260425.ja.md`
  - `phase-contract-batch-plan-20260425.ja.md`
  - `external-research-observation-plan-20260425.ja.md`
- 現在の `#RE` は、固定 fixture を残しつつ、文章品質の監査対象を `#R` 相当の `writer_candidate` へ寄せる移行中。詳細は `re-alignment-checklist-20260429.ja.md` を見る。

## #BR
- `#BR` は `bugfix-15000 / handoff-25000` の境界ルーティングを鍛える shadow rehearsal。
- live 返信ではなく、`handoff-25000` を `training-visible / future-dual simulation` として扱う。
- `service-registry.yaml` の `handoff-25000 public:false` は変更しない。
- 通常 live / #RE には `handoff-25000` のサービス名・25,000円・購入導線を戻さない。
- 出力先:
  - `/home/hr-hm/Project/work/サービスページ/rehearsal/boundary-routing-返信学習/返信監査_batch-current.md`
- 監査プロンプト:
  - `/home/hr-hm/Project/work/サービスページ/rehearsal/boundary-routing-返信学習/監査プロンプト_codex-xhigh.md`
  - `/home/hr-hm/Project/work/サービスページ/rehearsal/boundary-routing-返信学習/監査プロンプト_claude.md`
- 正本メモ:
  - `boundary-routing-shadow-rehearsal.ja.md`
  - `rehearsal-shelf-20260429-br13-16.ja.md`

## 学習ループ
1. batch を作る。
2. 外部監査へ渡す。
3. 指摘を `failure-taxonomy` へ落とす。
4. `case_fix / pattern_candidate / rule_return_candidate / preference / reject` を切る。
5. `guidance-scoping` と `adoption-policy` で戻し先を決める。
6. 再発するものだけ skill / rule / validator / gold へ戻す。
7. 一回限りの好みは正本へ入れない。

## Gold
- `gold-replies/`
  - 温度感、情報量、質問数、次アクションの基準になる良い返信例。
- 古い gold が現行ルールと矛盾した場合は、良い例として残さない。

## Lens Notes
- `promise-consistency-lens-20260429.ja.md`
  - 留保・不可・条件付き回答を、後段の成果物・納期・料金・次アクションが上書きして見えないかを見る soft lens。
  - 現時点では #RE / #BR 監査プロンプト + Gold 37 で運用し、lint / renderer / common skill へは再発 subtype を確認してから戻す。
- `pro-analysis-queue-20260430.ja.md`
  - `promise_consistency` / `conditional_scope_clarity` / `ack_to_answer_bridge` / `permission_benefit_alignment` など、次に Pro へまとめて聞く候補を保持する一時キュー。
  - すぐ投げるプロンプトではなく、#RE / #BR / human audit の実例をためてから相談内容へ変換する。

## 固定ルール
- Writer に self-check 全文を常駐させない。
- Reviewer はまず `self-check-core-always-on.ja.md` を使い、必要な時だけ詳細へ降りる。
- `reply-only` の改善を、`common` 判定なしで納品物本文へ流用しない。
- 外部調査結果をそのまま rule / renderer / validator へ入れない。
