import { NextResponse } from "next/server";
import { getStripe } from "@/lib/stripe";

type CheckoutMode = "payment" | "subscription";

type PaymentPlan = {
  id: "standard" | "premium";
  name: string;
  amount: number;
  description: string;
};

type SubscriptionPlan = {
  id: "monthly" | "yearly";
  name: string;
  description: string;
  priceEnvKey: "STRIPE_PRICE_SUB_MONTHLY" | "STRIPE_PRICE_SUB_YEARLY";
};

const paymentPlans: Record<PaymentPlan["id"], PaymentPlan> = {
  standard: {
    id: "standard",
    name: "Standard",
    amount: 2980,
    description: "単発決済パターン（標準金額）",
  },
  premium: {
    id: "premium",
    name: "Premium",
    amount: 29800,
    description: "単発決済パターン（高額）",
  },
};

const subscriptionPlans: Record<SubscriptionPlan["id"], SubscriptionPlan> = {
  monthly: {
    id: "monthly",
    name: "Monthly",
    description: "月額サブスクリプション",
    priceEnvKey: "STRIPE_PRICE_SUB_MONTHLY",
  },
  yearly: {
    id: "yearly",
    name: "Yearly",
    description: "年額サブスクリプション",
    priceEnvKey: "STRIPE_PRICE_SUB_YEARLY",
  },
};

function resolveMode(rawMode: string): CheckoutMode {
  return rawMode === "subscription" ? "subscription" : "payment";
}

export async function POST(request: Request) {
  const formData = await request.formData();
  const planId = String(formData.get("planId") ?? "");
  const mode = resolveMode(String(formData.get("mode") ?? "payment"));

  const stripe = getStripe();
  const origin =
    request.headers.get("origin") ||
    process.env.NEXT_PUBLIC_APP_URL ||
    "http://localhost:3000";

  let session;

  if (mode === "subscription") {
    const plan = subscriptionPlans[planId as SubscriptionPlan["id"]];
    if (!plan) {
      return NextResponse.json({ error: "Invalid subscription plan selected." }, { status: 400 });
    }

    const priceId = process.env[plan.priceEnvKey];
    if (!priceId) {
      return NextResponse.json(
        { error: `Missing ${plan.priceEnvKey}. Set recurring price id in .env.local.` },
        { status: 500 },
      );
    }

    session = await stripe.checkout.sessions.create({
      mode: "subscription",
      payment_method_types: ["card"],
      line_items: [{ price: priceId, quantity: 1 }],
      success_url: `${origin}/success?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${origin}/cancel`,
      metadata: {
        mode: "subscription",
        planId: plan.id,
        planName: plan.name,
      },
      subscription_data: {
        metadata: {
          planId: plan.id,
          planName: plan.name,
        },
      },
    });
  } else {
    const plan = paymentPlans[planId as PaymentPlan["id"]];
    if (!plan) {
      return NextResponse.json({ error: "Invalid payment plan selected." }, { status: 400 });
    }

    session = await stripe.checkout.sessions.create({
      mode: "payment",
      payment_method_types: ["card"],
      line_items: [
        {
          quantity: 1,
          price_data: {
            currency: "jpy",
            unit_amount: plan.amount,
            product_data: {
              name: plan.name,
              description: plan.description,
            },
          },
        },
      ],
      success_url: `${origin}/success?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${origin}/cancel`,
      metadata: {
        mode: "payment",
        planId: plan.id,
        planName: plan.name,
      },
    });
  }

  if (!session.url) {
    return NextResponse.json({ error: "No checkout url returned." }, { status: 500 });
  }

  return NextResponse.redirect(session.url, 303);
}
