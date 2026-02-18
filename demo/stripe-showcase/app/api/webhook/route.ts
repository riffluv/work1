import { NextResponse } from "next/server";
import Stripe from "stripe";
import { appendWebhookEvent } from "@/lib/event-store";
import { getStripe } from "@/lib/stripe";

export const runtime = "nodejs";

function toRecord(metadata: Stripe.Metadata | null | undefined): Record<string, string> | null {
  if (!metadata) return null;
  return Object.entries(metadata).reduce<Record<string, string>>((acc, [key, value]) => {
    if (typeof value === "string") acc[key] = value;
    return acc;
  }, {});
}

export async function POST(request: Request) {
  const signature = request.headers.get("stripe-signature");
  if (!signature) {
    return NextResponse.json({ error: "Missing stripe-signature" }, { status: 400 });
  }

  const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET;
  if (!webhookSecret) {
    return NextResponse.json({ error: "Missing STRIPE_WEBHOOK_SECRET" }, { status: 500 });
  }

  const payload = await request.text();

  let event: Stripe.Event;
  try {
    const stripe = getStripe();
    event = stripe.webhooks.constructEvent(payload, signature, webhookSecret);
  } catch (error) {
    return NextResponse.json(
      { error: `Webhook signature verification failed: ${String(error)}` },
      { status: 400 },
    );
  }

  const checkoutSession =
    event.type === "checkout.session.completed"
      ? (event.data.object as Stripe.Checkout.Session)
      : null;

  await appendWebhookEvent({
    id: event.id,
    type: event.type,
    createdAt: new Date().toISOString(),
    livemode: event.livemode,
    amountTotal: checkoutSession?.amount_total ?? null,
    currency: checkoutSession?.currency ?? null,
    customerEmail: checkoutSession?.customer_details?.email ?? null,
    sessionId: checkoutSession?.id ?? null,
    metadata: toRecord(checkoutSession?.metadata),
  });

  return NextResponse.json({ received: true });
}
