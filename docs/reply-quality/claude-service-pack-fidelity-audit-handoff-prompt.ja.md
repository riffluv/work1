あなたは設計レビュー担当です。日本語返信の添削役ではなく、「service-pack が公開サービス文面の意味を十分に保持できているか」を監査してください。
主軸は Codex で、採否判断と正本反映は Codex が行います。

今回は handoff-25000 の service-pack fidelity 監査です。

背景:
- `handoff-25000` は現時点では private / ready です
- ただし、商品化設計と service-pack の骨格整備のため、公開準備文面を source-of-truth として fidelity を監査したいです
- すでに bugfix-15000 では `かなり良い` まで改善済みで、今回は handoff 側が同じ水準に達しているかを見たいです

今回見てほしいこと:
1. 公開準備文面の意味が、service-pack に十分保持されているか
2. `facts / boundaries / decision-contract / evidence-contract / routing-playbooks / state-schema / seeds / tone-profile` という構成は妥当か
3. 特に handoff で重要な
   - `主要1フロー`
   - `整理だけで止められる`
   - `修正は別対応`
   - `どこから見ればいいか分からない`
   - `次の担当者へ渡せるメモ`
   - `非エンジニアでも読める`
   - `追加フロー`
   - `未公開状態`
   が service-pack から読めるか
4. `service page -> service-pack -> reply` の意味落ちが残っているなら、それが
   - public contract
   - decision / evidence
   - routing / state
   - runtime asset
   のどこに属するか
5. 今の handoff pack は
   - かなり良い
   - 中くらい
   - 危ない
   のどこか

特に強く見てほしい観点:
- `what it sells` だけでなく `how it decides` と `where it stops` が保持できているか
- `主要1フロー` が固定の1本に見えすぎず、広い相談でも今回の対象を1つ置く契約になっているか
- `修正は別対応` が hard no ではなく `整理のあとに追加対応として続けられる` 文脈で保持されているか
- `コードの中身が分からないだけでは handoff 送りの単独理由にしない` という境界が見えているか
- `seeds / tone` が source-of-truth のふりをしていないか

出力形式:
次の順で、短くてもいいので必ず埋めてください。

1. 総評
- 今の fidelity は `かなり良い / 中くらい / 危ない` のどれか
- 一言理由

2. 十分に保持できているもの
- 3〜7個

3. 落ちている / 弱いもの
- 3〜7個
- 各項目に、
  - `public contract`
  - `decision/evidence`
  - `routing/state`
  - `runtime asset`
  のどこが弱いかも付ける

4. ノイズになっているもの
- あれば 1〜5個

5. 今やるべき次の改善
- 優先順位つきで最大5個
- `なぜそれが先か` を一言ずつ

6. 判定
- handoff-25000 の service-pack を、
  - 一旦固めてよい
  - もう1回だけ修正した方がよい
  - まだ再設計が必要
  のどれかで結論づけてください

今回見てほしいファイル:
- /home/hr-hm/Project/work/サービスページ/handoff-25000.ready.txt
- /home/hr-hm/Project/work/os/core/service-registry.yaml
- /home/hr-hm/Project/work/ops/services/handoff-25000/service-pack/README.ja.md
- /home/hr-hm/Project/work/ops/services/handoff-25000/service-pack/facts.yaml
- /home/hr-hm/Project/work/ops/services/handoff-25000/service-pack/boundaries.yaml
- /home/hr-hm/Project/work/ops/services/handoff-25000/service-pack/decision-contract.yaml
- /home/hr-hm/Project/work/ops/services/handoff-25000/service-pack/evidence-contract.yaml
- /home/hr-hm/Project/work/ops/services/handoff-25000/service-pack/routing-playbooks.yaml
- /home/hr-hm/Project/work/ops/services/handoff-25000/service-pack/state-schema.yaml
- /home/hr-hm/Project/work/ops/services/handoff-25000/service-pack/seeds.yaml
- /home/hr-hm/Project/work/ops/services/handoff-25000/service-pack/tone-profile.yaml
- /home/hr-hm/Project/work/docs/reply-quality/service-pack-source-of-truth-policy.ja.md

補足:
- handoff-25000 は現時点では private / ready で、外向け公開前です
- 返信文そのものの自然さではなく、service-pack の fidelity を監査してください
- Codex は、今回の結果をもとに handoff pack を一旦固めるか、追加修正するかを決めます
