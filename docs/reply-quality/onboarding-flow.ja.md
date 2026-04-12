# 導入フロー

## 目的
- 新しいサービスへ返信OSを導入する時の作業順を固定する
- `何からやれば使える状態になるか` を商品として説明できる形にする

## 全体フロー
1. サービス理解
2. service facts 化
3. route / phase / forbidden の確定
4. gold reply 初期セット作成
5. 5件バッチ監査
6. system 反映
7. 受け渡し

## 1. サービス理解
集めるもの:
- サービスページ
- FAQ
- 見積りでよく来る質問
- 購入後によく起きる相談
- 禁止事項

出力:
- 1行要約
- 何を解決するサービスか
- 何はやらないか

## 2. service facts 化
使うもの:
- [service-facts-onboarding-template.ja.md](/home/hr-hm/Project/work/docs/reply-quality/service-facts-onboarding-template.ja.md)

決めること:
- 公開してよい事実
- phase ごとの許容 ask
- forbidden moves
- boundary

## 3. route / phase / forbidden の確定
最低限確定する項目:
- prequote の入口
- quote_sent の扱い
- purchased / delivered / closed の戻り方
- 外部共有、meeting、direct push、prod login、secrets の扱い

## 4. gold reply 初期セット作成
最初に必要な型:
- 価格不安
- scope 境界
- 断る系
- purchased 追加症状
- delivered / closed の軽い不満

本数の目安:
- 2〜3本で開始
- 初回から増やしすぎない

## 5. 5件バッチ監査
やること:
- 実務に近い stock を5件回す
- Claude などでまとめ監査
- `major / minor / new` で記録する

ここで見るもの:
- 事故リスクがないか
- phase を外していないか
- buyer に返せているか
- 何が再発しそうか

## 6. system 反映
判断順:
1. 文面だけ直す
2. 再発なら Reviewer に戻す
3. さらに再発なら Writer / Router / Facts に戻す
4. 良例なら gold reply 化する

## 7. 受け渡し
最低限渡すもの:
- 運用の前提
- 使う service facts
- acceptance gate
- 初回 gold replies
- 禁止事項

## 導入完了の基準
- 5件バッチで major fail 0
- common な質問で routing が安定
- 断る系で事故らない
- gold reply が最低 3本ある
- acceptance gate が言語化されている

## 初回導入で無理にやらないこと
- 最初から全 phase を完璧に揃えること
- 自動評価基盤を重くしすぎること
- 単発の好みを system に入れすぎること

## 次の改善先
- 初回導入後は、5件バッチを回しながら
  - new pattern
  - common pattern
  - service-specific pattern
  を分けて育てる
