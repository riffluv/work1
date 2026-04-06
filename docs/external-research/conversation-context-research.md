# #AR 調査結果 — 会話コンテキスト管理（マルチターン返信の一貫性）

## 調査対象
「ラリーの途中なのに毎回初対面トーンになる問題」の原因と、業界の解決パターン

## ソース
- Rasa CALM アーキテクチャ（会話ロジックの分離）
- LangGraph（長期状態管理）
- 複数の AI カスタマーサービス実装事例
- 論文:「Chain-of-States」「StateAct」「Affective State Dynamics」

---

## 1. 問題の正体

研究では **「Conversation Amnesia（会話健忘症）」** と呼ばれている。

```
正常:
  1通目: 「確認します」
  2通目: 「前回確認すると言った件、進捗として〜」

異常（amnesia）:
  1通目: 「確認します」
  2通目: 「ご連絡ありがとうございます。確認できます」
         ← 前回の自分の返信を覚えていない
         ← buyer から見ると「覚えてないの？」感
```

### なぜ起きるか

```
LLM は本質的に stateless（状態を持たない）
→ 毎回「新しい会話」として処理する
→ 前のラリーを明示的に渡さない限り、知らない
→ 前のラリーを渡していても、context window に入りきらないと消える
```

---

## 2. 業界が使っている解決パターン

### A. Thread State Summary（スレッド状態要約）★★★ 最有望

```
ラリーの各通の後に、構造化された「スレッド状態」を生成・更新する

thread_state:
  turn_count: 3
  current_phase: purchased
  previous_promises:
    - "原因を確認します"  # 1通目
    - "ログを確認中"      # 2通目
  open_threads:
    - "buyer は進捗を待っている"
    - "週明けの社内報告に使いたい"
  buyer_tone_history:
    - turn1: neutral
    - turn2: anxious
    - turn3: patient_but_urgent
  last_reply_summary:
    "確認中と伝えた。具体的な進捗は未共有。"

→ 次の返信を書くときに、この thread_state を renderer に渡す
→ renderer は「前回何を約束したか」「buyer のトーンの流れ」を知った状態で書く
```

### B. Dialogue State Tracking（対話状態追跡）★★

```
会話の中の「決定事項」「未解決事項」を構造化して追跡する

dialogue_state:
  resolved:
    - "scope は strong_fit"
    - "価格は 15,000円で合意"
  pending:
    - "原因の切り分け中"
    - "buyer は進捗を待っている"
  commitments:
    - what: "確認結果を共有する"
      when: "本日20:08まで"
      fulfilled: false  ← まだ果たしていない

→ commitments.fulfilled = false なのに「確認中です」と繰り返したら
   validator が検出できる
```

### C. Progressive Summarization（段階的要約）★

```
ラリーが長くなると context window に入りきらなくなる
→ 古いメッセージを要約して圧縮
→ 直近2-3通はそのまま残す
→ それ以前は要約に変換

例:
  [要約] 1-3通目: scope 確認 → bugfix 引き受け → 購入完了
  [原文] 4通目: buyer「ログ送りました」
  [原文] 5通目: あなた「確認します」
  [原文] 6通目: buyer「進捗ありましたか？」← 今ここ

→ 古い部分は要約、新しい部分はそのまま
→ 情報量を保ちつつ token を節約
```

### D. Promise Tracker（約束追跡）★★★

```
返信文の中に含まれる「約束」を自動抽出して追跡する

promise_tracker:
  - promise: "確認します"
    made_at: turn_1
    fulfilled: false
    
  - promise: "本日20:08までに共有"
    made_at: turn_2
    fulfilled: false

→ turn_3 の返信を書くとき:
   → promise_tracker を renderer に渡す
   → 「前回の約束がまだ果たされていない」と知った状態で書く
   → 「前回お伝えした確認の件ですが、〜」と自然に繋がる
```

---

## 3. 今のシステムに落とし込める改善案

### 最小構成（即実装可能）

```yaml
# 返信を書くたびに thread_state を更新する
thread_state:
  case_id: "..."
  turn_count: 3
  my_last_reply_summary: "確認中と伝えた。進捗未共有。"
  unfulfilled_promises:
    - "確認結果の共有"
  buyer_current_tone: "patient_but_urgent"
```

```
renderer への入力を変える:

今:    buyer の今の1通 → renderer → 返信文
改善:  buyer の今の1通 + thread_state → renderer → 返信文 + thread_state 更新

→ renderer は「前回何を返したか」を知っている
→ 「ご連絡ありがとうございます」ではなく「お待たせしています」と書ける
```

### validator への追加（Promise Tracker）

```yaml
promise_fulfillment_check:
  条件: thread_state.unfulfilled_promises が存在する
  チェック: output が unfulfilled_promises のいずれかに触れているか
  失敗例: 前回「確認します」と言ったのに、今回も「確認中です」だけ
  期待: 前回の約束の進捗を具体的に書く
```

---

## 4. 効果の予測

```
会話コンテキストが入ると:

  温度感:
    before: 毎回「初対面」トーン → buyer は冷たく感じる
    after:  ラリーの流れを踏まえたトーン → 自然

  空約束:
    before: 前回と同じ「確認中」を繰り返す
    after:  前回の約束の進捗を書く（or 遅れを謝る）

  信頼感:
    before: 「この人、前のやり取り覚えてる？」
    after:  「ちゃんと繋がってる」

  → 1通の品質だけでなく「ラリー全体の品質」が上がる
```

---

## 5. 実装の場所と順序

```
1. thread_state の構造を定義（ops/cases/ に保存）
2. 返信生成時に thread_state を renderer に渡す入口を追加
3. 返信生成後に thread_state を更新する出口を追加
4. validator に promise_fulfillment_check を追加
5. テストでラリーケースを追加（2-3往復のケース）
```

---

## 6. 注意点

```
- thread_state はあくまで「renderer の入力」
- thread_state が「こう書け」と指示するのではない
- 「前回こう言った」という事実を渡すだけ
- 書き方は renderer と Codex の判断に委ねる
- writer 化しない設計が重要
```
