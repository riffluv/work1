# Service Page Change Checklist

1. 公開サービスページの変更点を 1 行で要約する
2. その変更が `page` だけか、`facts / boundaries` まで及ぶかを切る
3. 判断ルールが変わるなら `decision-contract.yaml` を直す
4. minimum ask が変わるなら `evidence-contract.yaml` を直す
5. 返し方や timing が変わるなら `routing-playbooks.yaml` / `state-schema.yaml` を直す
6. wording だけなら `seeds.yaml` / `tone-profile.yaml` か `writer-brief.ja.md` だけを見る
7. `service-registry.yaml` の `public` / `source_of_truth` / `service_pack_root` に影響がないか確認する
8. FAQ / 回答例に関わる変更なら `ops/tests/regression/service_pack_fidelity_*/cases.yaml` を更新する
9. 変更後、`service-pack-source-of-truth-policy.ja.md` の優先順に反していないか確認する
10. 最後に、返信OSへ落とし込んだ対象を `page / facts / decision / evidence / routing / state / seeds / tone` のどこかで記録する
