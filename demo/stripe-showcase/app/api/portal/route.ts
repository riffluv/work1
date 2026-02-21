import { NextResponse } from "next/server";
import { getStripe } from "@/lib/stripe";

export async function POST(request: Request) {
  const formData = await request.formData();
  const sessionId = String(formData.get("sessionId") ?? "");

  if (!sessionId) {
    return NextResponse.json({ error: "Missing sessionId." }, { status: 400 });
  }

  const stripe = getStripe();
  const checkoutSession = await stripe.checkout.sessions.retrieve(sessionId);

  if (checkoutSession.mode !== "subscription") {
    return NextResponse.json(
      { error: "Billing Portal is available for subscription mode only." },
      { status: 400 },
    );
  }

  const customerId =
    typeof checkoutSession.customer === "string"
      ? checkoutSession.customer
      : checkoutSession.customer?.id;

  if (!customerId) {
    return NextResponse.json(
      { error: "Customer is missing in checkout session." },
      { status: 400 },
    );
  }

  const origin =
    request.headers.get("origin") ||
    process.env.NEXT_PUBLIC_APP_URL ||
    "http://localhost:3000";

  const returnUrl =
    process.env.STRIPE_BILLING_PORTAL_RETURN_URL ||
    `${origin}/success?session_id=${checkoutSession.id}`;

  const portalSession = await stripe.billingPortal.sessions.create({
    customer: customerId,
    return_url: returnUrl,
  });

  if (!portalSession.url) {
    return NextResponse.json({ error: "No billing portal url returned." }, { status: 500 });
  }

  return NextResponse.redirect(portalSession.url, 303);
}
