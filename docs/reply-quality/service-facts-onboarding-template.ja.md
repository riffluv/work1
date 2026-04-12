# service facts 導入テンプレ

## 目的
- 新しいサービスへ返信OSを導入する時に、毎回ゼロから考え直さないための入力テンプレート
- `何をヒアリングし、何を facts 化し、何を forbidden にするか` を短時間で揃える

## 使い方
1. サービスページ、FAQ、見積り案内、納品方針を集める
2. 下のテンプレートを埋める
3. 埋まった内容を `Router / Writer / Reviewer` のどこに渡すか切る
4. 初回 5件バッチで不足を確認する

## テンプレート
```yaml
service_id:
public_name:
public: true

goal:
  one_line:
  user_problem_it_solves:

allowed_scope:
  - 

out_of_scope:
  - 

public_facts:
  price:
  deliverable:
  lead_time_if_any:
  what_is_included:
  what_is_not_included:

phase_rules:
  prequote:
    can_offer:
    can_ask_for:
    must_not_do:
  quote_sent:
    can_offer:
    can_ask_for:
    must_not_do:
  purchased:
    can_offer:
    can_ask_for:
    must_not_do:
  delivered:
    can_offer:
    can_ask_for:
    must_not_do:
  closed:
    can_offer:
    can_ask_for:
    must_not_do:

platform_constraints:
  external_share:
  direct_push:
  prod_login:
  secrets:
  meeting:

buyer_intents:
  common_questions:
    - 
  common_anxieties:
    - 
  common_misunderstandings:
    - 

routing:
  primary_entry_cases:
    - 
  boundary_with_other_services:
    - 
  what_should_be_prioritized_first:
    - 

forbidden_moves:
  - 

evidence_to_request_by_phase:
  prequote:
    - 
  purchased:
    - 
  delivered:
    - 

good_closing_shapes:
  prequote:
    - 
  quote_sent:
    - 
  purchased:
    - 
  delivered:
    - 
  closed:
    - 

language_notes:
  buyer_words_to_reuse:
    - 
  words_to_avoid:
    - 
  explanation_style:
```

## 何を facts 化するか
- 価格や納品物のような `事実`
- `この phase では何を言ってよくて、何を言ってはいけないか`
- buyer がよく迷う点
- scope の境界
- 断る時でも示せる代替行動

## 何を facts にしないか
- 単発の好み
- まだ再発していない言い回し
- Writer の表現自由まで潰す細かい禁止

## Router / Writer / Reviewer への振り分け
- Router:
  - route
  - state
  - service fit
  - primary question
  - forbidden moves
- Writer:
  - 主質問
  - buyer の語彙
  - phase に合う closing
  - 事実として答えるべき範囲
- Reviewer:
  - phase 違反
  - public/private 逸脱
  - forbidden 表現
  - ask 粒度違反
  - buyer が既に出した情報の聞き直し

## 導入時の最小セット
- サービスページ 1本
- FAQ or よく来る相談 5件
- 禁止事項 5〜10個
- gold reply 2〜3件
- 初回監査 5件

## 完了条件
- `価格 / scope / phase / 禁止事項` が YAML で埋まっている
- primary route が説明できる
- 初回 5件で major fail が出ない
