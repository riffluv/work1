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

1. `http://localhost:3000` でプランを選択
2. Checkoutに遷移してテスト決済
3. `/success` でセッション情報を確認
4. `/events` で `checkout.session.completed` を確認

### Test card

- Number: `4242 4242 4242 4242`
- Expiry: 任意の未来日
- CVC: 任意3桁
- ZIP: 任意

## 5. Screenshot pack (for listing)

- Top page (pricing + CTA)
- Stripe Checkout screen
- Success screen (session + amount + status)
- Events screen (webhook received)

## Notes

- `data/webhook-events.json` に受信イベントを保存します。
- デモ用途のため、実運用前には商品IDや在庫・認可チェックを追加してください。
