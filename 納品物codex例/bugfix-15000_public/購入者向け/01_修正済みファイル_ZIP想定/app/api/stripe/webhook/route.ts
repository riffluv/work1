import { headers } from "next/headers";
import { NextRequest, NextResponse } from "next/server";
import Stripe from "stripe";

import { applySubscriptionUpdate } from "@/src/lib/billing/applySubscriptionUpdate";

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY ?? "", {
  apiVersion: "2025-02-24.acacia",
});

export async function POST(request: NextRequest) {
  const signature = headers().get("stripe-signature");

  if (!signature) {
    return NextResponse.json({ error: "missing_signature" }, { status: 400 });
  }

  // 署名検証は raw body が必要（json() で加工すると失敗する）
  const rawBody = await request.text();

  let event: Stripe.Event;

  try {
    event = stripe.webhooks.constructEvent(
      rawBody,
      signature,
      process.env.STRIPE_WEBHOOK_SECRET ?? "",
    );
  } catch (error) {
    // 署名不正は 400。Stripe の再試行では直らない
    return NextResponse.json(
      { error: "invalid_signature", detail: String(error) },
      { status: 400 },
    );
  }

  if (event.type !== "checkout.session.completed") {
    return NextResponse.json({ ok: true });
  }

  const session = event.data.object as Stripe.Checkout.Session;
  const customerId = typeof session.customer === "string" ? session.customer : null;

  if (!customerId) {
    return NextResponse.json({ error: "missing_customer_id" }, { status: 400 });
  }

  try {
    await applySubscriptionUpdate({
      eventId: event.id,
      customerId,
    });
  } catch (error) {
    // 500 は一時障害。後段の再試行で会員状態を回復させる
    return NextResponse.json(
      { error: "subscription_update_failed", detail: String(error) },
      { status: 500 },
    );
  }

  return NextResponse.json({ ok: true });
}
