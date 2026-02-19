import { NextResponse } from "next/server";
import { getStripe } from "@/lib/stripe";

type Plan = {
  id: string;
  name: string;
  amount: number;
  description: string;
};

const plans: Record<string, Plan> = {
  monthly: {
    id: "monthly",
    name: "Billing Platform Monthly Plan",
    amount: 2980,
    description: "月額課金プラン（サブスク）",
  },
  yearly: {
    id: "yearly",
    name: "Billing Platform Yearly Plan",
    amount: 29800,
    description: "年額課金プラン（サブスク）",
  },
};

export async function POST(request: Request) {
  const formData = await request.formData();
  const planId = String(formData.get("planId") ?? "");
  const plan = plans[planId];

  if (!plan) {
    return NextResponse.json({ error: "Invalid plan selected." }, { status: 400 });
  }

  const stripe = getStripe();
  const origin =
    request.headers.get("origin") ||
    process.env.NEXT_PUBLIC_APP_URL ||
    "http://localhost:3000";

  const session = await stripe.checkout.sessions.create({
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
      planId: plan.id,
      planName: plan.name,
    },
  });

  if (!session.url) {
    return NextResponse.json({ error: "No checkout url returned." }, { status: 500 });
  }

  return NextResponse.redirect(session.url, 303);
}
