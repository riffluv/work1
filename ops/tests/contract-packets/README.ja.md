# contract packet samples

## 目的

返信OSの `memory / phase / reply_contract / writer` の接続を、実装前に見える形で確認するためのサンプル置き場です。

ここに置くものは、送信用テンプレートではありません。Writer に自由に文章を書かせる前に、何を事実として渡し、何を禁止し、どの質問へ先に答えるかを固定するための最小 packet です。

## 現在のファイル

- `bugfix-15000-v1-samples.yaml`
  - `bugfix-15000` の v1 完成候補を前提にした、主要 phase 別の contract packet サンプル。
  - `prequote / quote_sent / purchased / delivered / closed` を1件ずつ収録。

## 使い方

- #R / #RE の生成経路がズレた時に、まず packet のどこが違うかを見る。
- アプリ化する時に、画面入力から作るべき最小データ構造の参考にする。
- Pro に v1 completion review を依頼する時に、返信文そのものだけでなく、返信前の判断単位として見せる。
- 形の確認は `./scripts/check-contract-packets.py` を使う。

## 注意

- Gold reply ではない。
- 文面テンプレートではない。
- `handoff-25000`、25,000円、主要1フロー整理は通常 live packet に入れない。
- `known_commitments` や `received_materials` にない事実を writer が補完してはいけない。
