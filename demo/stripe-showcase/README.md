# stripe-showcase

Next.js + Stripe Checkout + Webhook reception demo.

## 1. Setup

```bash
pnpm install
cp .env.example .env.local
```

`.env.local` に次を設定:

- `STRIPE_SECRET_KEY` (test key)
- `STRIPE_WEBHOOK_SECRET` (`stripe listen` で取得)
- `NEXT_PUBLIC_APP_URL` (任意)
- `STRIPE_PRICE_SUB_MONTHLY` (subscription用 recurring price)
- `STRIPE_PRICE_SUB_YEARLY` (subscription用 recurring price)

## 2. Start app

```bash
pnpm dev
```

## 3. Start Stripe webhook forwarding

別ターミナルで:

```bash
stripe login
stripe listen --forward-to localhost:3000/api/webhook
```

表示された `whsec_...` を `.env.local` の `STRIPE_WEBHOOK_SECRET` に設定。

## 4. Test flow

1. `http://localhost:3000` を開く
2. タブを選択
   - `One-time`: 単発決済 (`mode=payment`)
   - `Subscription`: 定期決済 (`mode=subscription`)
3. Checkoutに遷移してテスト決済
4. `/success` でセッション情報を確認
5. `/events` でWebhook受信ログを確認

### Test card

- Number: `4242 4242 4242 4242`
- Expiry: 任意の未来日
- CVC: 任意3桁
- ZIP: 任意

## 5. Screenshot pack (for listing)

- Top page (One-time tab)
- Top page (Subscription tab)
- Stripe Checkout screen
- Success screen (session + amount + status)
- Events screen (webhook received)

## Notes

- `data/webhook-events.json` に受信イベントを保存します。
- デモ用途のため、実運用前には認可・冪等性・監視を追加してください。
