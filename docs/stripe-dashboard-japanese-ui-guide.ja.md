# Stripeダッシュボード案内（日本語UI基準）

更新日: 2026-02-21

## 目的
- 次セッションのCodexが、Stripe案内を日本語UIで迷わず行える状態にする。
- 依頼者が「どこを開けばよいか」を最短で理解できる案内に統一する。

## 固定ルール
- Stripe画面の案内は**日本語UI名を優先**して書く。
- 英語名は必要時のみ補足で併記する（例: カスタマーポータル / Customer portal）。
- 先に「テスト環境か本番環境か」を確認してから案内する。
- 機密情報（`sk_...` の値など）は受け取らない。キー名・IDのみ扱う。

## まず確認すること（毎回）
1. 右上の「テスト環境」ON/OFF
2. 相談内容が「単発決済」か「定期課金」か
3. 依頼者が見ている画面が Checkout か Portal か

## よく使う日本語UIの場所

### 1) APIキー
- `開発者` > `APIキー`
- ここで扱う主なキー: `STRIPE_SECRET_KEY`（`sk_test_...` / `sk_live_...`）

### 2) 商品・価格（Price ID）
- `商品カタログ` > 対象商品 > 料金
- 定期課金では `price_...` が必須
- `prod_...`（商品ID）と混同しない

### 3) カスタマーポータル
- `設定` > `Billing` > `カスタマーポータル`
- ここで設定するのは「契約管理画面（Portal）」の挙動
- Checkout画面の入力項目とは別

## 直リンク（UIが見つからない時の補助）
- テスト環境カスタマーポータル  
  `https://dashboard.stripe.com/test/settings/billing/portal`
- 本番環境カスタマーポータル  
  `https://dashboard.stripe.com/settings/billing/portal`
- APIキー  
  `https://dashboard.stripe.com/test/apikeys`（テスト）  
  `https://dashboard.stripe.com/apikeys`（本番）

## 用語の切り分け（依頼者説明用）
- **Checkout**: 決済入力画面（カード入力して支払う）
- **Billing Portal**: 契約管理画面（解約/プラン変更/支払い方法更新）
- **Payment mode**: 単発課金
- **Subscription mode**: 定期課金

## ID早見表
- `sk_...`: Secret key（機密）
- `pk_...`: Publishable key（公開鍵）
- `whsec_...`: Webhook署名シークレット
- `price_...`: 価格ID（定期課金で必須）
- `prod_...`: 商品ID（価格IDとは別）
- `cs_...`: Checkout Session ID
- `sub_...`: Subscription ID
- `cus_...`: Customer ID
- `bpc_...`: Portal設定ID（通常の実装では直接使わない）

## 定期課金デモを通す最小チェック
1. `price_...`（月額/年額）を `.env.local` に設定
2. `stripe listen --forward-to localhost:3000/api/webhook` を起動
3. Subscriptionで決済完了
4. Success画面で `mode=subscription` を確認
5. 「契約を管理」からPortal遷移
6. Portalで「プラン変更 / キャンセル」を確認
7. `/events` で受信イベントを確認

## 依頼者への案内文（短文）
### 案内1: Portalの場所
設定 > Billing > カスタマーポータル を開いてください。  
今の画面が「Billingの概要」の場合は、設定画面ではないため項目が表示されません。

### 案内2: `prod_...` と `price_...`
表示されている `prod_...` は商品IDです。  
定期課金に必要なのは `price_...`（価格ID）なので、料金行に表示される `price_...` を共有してください。

### 案内3: CheckoutとPortalの違い
カード入力画面は Checkout です。  
解約やプラン変更は Checkout ではなく、決済後の Portal（契約管理）で行います。
