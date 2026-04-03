# 2026-04-02 bugfix 需要・痛み表現調査（Agent-Reach）

## 目的
- `bugfix-15000` が、どの困り方に刺さるかを外部の相談文・Issue から確認する。
- 納品物の型ではなく、サービスページ・購入前相談に効く痛み表現を拾う。
- Stripe 特化に閉じすぎず、症状ベースでどこまで広く見せると強いかを判断する。

## 見たソース
- Reddit: How do you handle “payment succeeded but user not activated” cases with Stripe?
  - https://www.reddit.com/r/stripe/comments/1ro62zu/how_do_you_handle_payment_succeeded_but_user_not/
- Reddit: How do you handle “paid but not activated” issues in SaaS billing?
  - https://www.reddit.com/r/indiehackersindia/comments/1ro44nl/how_do_you_handle_paid_but_not_activated_issues/
- GitHub Issue: Failed to update subscription after Stripe payment
  - https://github.com/better-auth/better-auth/issues/7753
- GitHub Issue: Subscription Updates Not Persisting to Database
  - https://github.com/better-auth/better-auth/issues/4957
- GitHub Issue: Stripe webhook failing
  - https://github.com/vercel/nextjs-subscription-payments/issues/64
- Exa で拾った周辺候補
  - better-auth / get-convex / supabase / WooCommerce / Stack Overflow 周辺

## 1. いちばん強い痛み

### 1-1. 「支払いは成功したのに、アプリ側が反映されない」
- Reddit でも GitHub Issue でも、核の困り方はこれだった。
- 技術者の表現:
  - `payment succeeded but user not activated`
  - `subscription updates not persisting to database`
  - `active subscription, but app didn’t unlock`
- 非技術寄りの表現:
  - 払われたのに使えない
  - 有料プランを買ったのに Free のまま
  - 購入後も権限が変わらない

示唆:
- 売り文句は `Stripe webhook 修正` より `決済は通ったのに反映されない` の方が刺さる。

### 1-2. 「失敗が見えにくい」が強い不安
- Reddit の相談では、`the only reason we noticed was because the customer emailed support` という文が象徴的だった。
- つまり困り方は、単なるバグではなく
  - 気づきにくい
  - 売上と提供状態がズレる
  - 信用を落とす
 という運用事故。

示唆:
- `反映漏れ` だけでなく、`気づきにくい`、`サポートで初めて発覚する` を痛みとして見せると強い。

### 1-3. Webhook 単体の問題としては見られていない
- 相談文では、原因候補は
  - webhook
  - deploy 中断
  - DB 更新漏れ
  - checkout redirect 後の成功処理
  - entitlement / access state の不整合
 など複数にまたがっていた。

示唆:
- `Stripe特化` は専門性として有効だが、入口は `Webhook` 単語だけに寄せない方がよい。
- 強い入口は `決済後の反映漏れ` や `有料状態がアプリに反映されない`。

## 2. 困っている人が欲しがっているもの

### 2-1. 原因特定
- どこで止まっているか分からないこと自体がストレスになっている。
- 特に
  - Stripe は成功している
  - でも DB や UI が更新されない
 というズレが多い。

示唆:
- サービスの価値は「直す」だけでなく「どこで止まっているか切り分ける」にある。

### 2-2. 直ったと確認できること
- GitHub Issue も Reddit 相談も、単に修正方法だけでなく
  - どこを見れば直ったと言えるか
  - 再発をどう検知するか
 を気にしている。

示唆:
- サービスページでも `確認方法まで整理` はかなり強い。

### 2-3. 再発しにくい形
- Reddit では
  - reconciliation job
  - re-query Stripe APIs
  - internal monitoring dashboard
 が話題になっていた。
- つまり、利用者は応急処置だけでなく「次に同じことが起きにくいか」を気にしている。

示唆:
- 価格やスコープを広げずに言うなら、`反映漏れの原因切り分けと、確認しやすい形への整理` が刺さる。

## 3. `bugfix-15000` の見せ方への示唆

### 3-1. 入口は症状ベースの方が強い
- 強い言い方候補:
  - 決済は成功したのに反映されない
  - 有料プラン購入後も Free のまま
  - 支払い後に会員状態が更新されない
  - 払われたのにアプリ側が有効化されない

### 3-2. 中身で Stripe / Next.js / Webhook / DB を見られることを示す
- 購入者は最初から `Stripe が原因` と分かっているとは限らない。
- ただし、技術的に見られる範囲が広いことは安心材料になる。

示唆:
- 入口は症状
- 本文で `Stripe / Next.js / Webhook / DB更新 / UI反映` の切り分け対応を示す
がよさそう。

### 3-3. 「払われたのに反映されない」は事業インパクトが強い
- これは単なるエンジニアの不具合ではなく、
  - 売上は立つ
  - でも提供価値が届かない
  - サポート対応が発生する
  - 信用を落とす
という痛み。

示唆:
- サービスページで `決済後の反映漏れ` を前に出す価値は高い。

## 4. 今回の暫定判断

### 強い仮説
- `Stripe webhook 修正` より `決済後の反映漏れを直す` の方が広く刺さる
- `Stripe` は専門性の裏付けとして使い、入口は症状ベースにした方がよい
- `Next.js / DB / UI反映まで切り分ける` を示すと、Stripe 単独より買いやすい

### 今後サービスページで見たいもの
- タイトル・冒頭に、症状ベースの表現をどこまで出すか
- `Stripe` をどれくらい前に出すか
- `反映されない` だけでなく `気づきにくい` / `問い合わせで発覚する` をどこまで入れるか

## 5. 次にやると効くこと
- `bugfix-15000.live.txt` のタイトル・冒頭・見積り欄を、この調査結果に照らして点検する
- 必要なら `サービスページ/購入前見本` 側にも、症状ベースの見せ方が伝わるか確認する
