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

function extractEventSnapshot(event: Stripe.Event) {
  if (event.type === "checkout.session.completed") {
    const session = event.data.object as Stripe.Checkout.Session;
    return {
      amountTotal: session.amount_total ?? null,
      currency: session.currency ?? null,
      customerEmail: session.customer_details?.email ?? session.customer_email ?? null,
      sessionId: session.id,
      metadata: toRecord(session.metadata),
    };
  }

  if (event.type === "invoice.paid" || event.type === "invoice.payment_failed") {
    const invoice = event.data.object as Stripe.Invoice;
    const subscriptionRef = (invoice as unknown as {
      subscription?: string | { id: string } | null;
    }).subscription;

    return {
      amountTotal: invoice.amount_paid ?? invoice.amount_due ?? null,
      currency: invoice.currency ?? null,
      customerEmail: invoice.customer_email ?? null,
      sessionId:
        typeof subscriptionRef === "string"
          ? subscriptionRef
          : subscriptionRef?.id ?? invoice.id,
      metadata: toRecord(invoice.metadata),
    };
  }

  if (event.type === "customer.subscription.deleted") {
    const subscription = event.data.object as Stripe.Subscription;
    return {
      amountTotal: null,
      currency: subscription.currency ?? null,
      customerEmail: null,
      sessionId: subscription.id,
      metadata: toRecord(subscription.metadata),
    };
  }

  const fallbackObject = event.data.object as { metadata?: Stripe.Metadata };
  return {
    amountTotal: null,
    currency: null,
    customerEmail: null,
    sessionId: null,
    metadata: toRecord(fallbackObject.metadata),
  };
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

  const snapshot = extractEventSnapshot(event);

  await appendWebhookEvent({
    id: event.id,
    type: event.type,
    createdAt: new Date().toISOString(),
    livemode: event.livemode,
    amountTotal: snapshot.amountTotal,
    currency: snapshot.currency,
    customerEmail: snapshot.customerEmail,
    sessionId: snapshot.sessionId,
    metadata: snapshot.metadata,
  });

  return NextResponse.json({ received: true });
}
