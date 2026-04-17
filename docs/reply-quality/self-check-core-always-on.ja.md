# Self-Check Core Always-On

## 目的
- Reviewer が毎回常駐で見る項目を、常時コアだけに絞る
- `coconala-reply-self-check.ja.md` 全文を毎回前面に置かずに済むようにする
- ケース別の深掘りは、必要時だけ本体リファレンスへ降りる

## 常時コア
1. 主質問に直接答えているか
2. phase がずれていないか
3. ask が重すぎず、既出情報を聞き直していないか
4. 価格 / scope / 公開状態が service-pack と矛盾していないか
5. `decision-contract.yaml` と `evidence-contract.yaml` に反する判断をしていないか
6. `routing-playbooks.yaml` と `state-schema.yaml` に反する行き先や timing を置いていないか
7. `見られるか` `形ではありません` `もっともです` など既知 NG が戻っていないか
8. buyer の不安やお礼を、必要な場面で1文だけ受けているか
9. next action が buyer に見えており、1つに絞れているか
10. multi-turn なら、secondary thread の行き先 / return timing / required input が見えているか

## ケース別リファレンスへ降りる条件
- bugfix / handoff の L3 判断が絡む
- same / different / undecidable が絡む
- 返金 / 保証 / 追加料金 / formal delivery gate が絡む
- secondary thread が delivery / close をまたぐ
- handoff の対象フロー / repair / deeper memo が絡む

## 降り先
- 共通の詳細:
  - `/home/hr-hm/Project/work/docs/coconala-reply-self-check.ja.md`
- Universal / Domain:
  - `/home/hr-hm/Project/work/docs/reply-quality/self-check-l1-minimal-universal.ja.md`
  - `/home/hr-hm/Project/work/docs/reply-quality/self-check-l2-domain-minimal.ja.md`
- service 理解:
  - 各 service-pack の `facts / boundaries / decision-contract / evidence-contract`

## 運用ルール
- 常時コアで止まるなら、それ以上は読まない
- ケース別リファレンスは、必要が出た時だけ参照する
- 新しい regression は、まず常時コアへ入れるべきか、ケース別に留めるべきかを判定する
