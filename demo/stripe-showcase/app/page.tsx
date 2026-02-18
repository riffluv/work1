const plans = [
  {
    id: "bug_fix",
    badge: "Current Model",
    title: "不具合修正デモ",
    price: "¥15,000",
    scope: "同一原因の不具合1件を想定",
    note: "修正サービスの説明素材として使える画面",
  },
  {
    id: "stripe_build",
    badge: "Future Service",
    title: "Stripe実装デモ",
    price: "¥50,000",
    scope: "Checkout + Webhook + 反映確認を想定",
    note: "将来の高単価サービス訴求用",
  },
] as const;

const proofPoints = [
  "トップ画面（プラン選択と価格）",
  "Stripe Checkout画面（テスト決済中）",
  "Success画面（Session ID / 金額 / ステータス）",
  "Webhookログ画面（checkout.session.completed受信）",
];

export default function HomePage() {
  return (
    <main className="mx-auto w-full max-w-6xl px-6 py-10 md:px-10 md:py-14">
      <section className="mb-7 grid gap-6 rounded-3xl border border-sky-200/25 bg-[#071127]/65 p-6 md:grid-cols-[1.3fr_0.9fr] md:p-8">
        <div>
          <p className="mb-3 text-xs font-semibold uppercase tracking-[0.22em] text-cyan-300">Next.js + Stripe Showcase</p>
          <h1 className="font-heading title-glow text-4xl font-black leading-tight md:text-5xl">
            決済フローを
            <br />
            目で見せるデモ
          </h1>
          <p className="fine mt-4 text-sm md:max-w-xl md:text-base">
            明日の出品に向けて、Checkout・Webhook・成功画面の証跡を一気に作るためのデモです。
            画像素材と短い動画素材を同時に回収できます。
          </p>
        </div>

        <div className="glass rounded-2xl p-4 md:p-5">
          <p className="mb-3 text-sm font-bold text-cyan-100">スクショ候補（この順で撮る）</p>
          <ol className="space-y-2 text-sm">
            {proofPoints.map((point, idx) => (
              <li key={point} className="flex gap-2">
                <span className="inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-cyan-300/20 text-xs font-bold text-cyan-100">
                  {idx + 1}
                </span>
                <span>{point}</span>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        {plans.map((plan) => (
          <article key={plan.id} className="glass rounded-3xl p-5 md:p-6">
            <p className="mb-3 inline-flex rounded-full border border-cyan-300/35 bg-cyan-300/10 px-3 py-1 text-xs font-bold text-cyan-100">
              {plan.badge}
            </p>
            <h2 className="font-heading text-2xl font-bold">{plan.title}</h2>
            <p className="mt-1 text-3xl font-black text-white">{plan.price}</p>
            <p className="fine mt-3 text-sm">{plan.scope}</p>
            <p className="fine mt-1 text-xs">{plan.note}</p>

            <form action="/api/checkout" method="post" className="mt-5">
              <input type="hidden" name="planId" value={plan.id} />
              <button
                type="submit"
                className="w-full rounded-full bg-cyan-300 px-4 py-2 text-sm font-black text-[#032029] transition hover:bg-cyan-200"
              >
                テスト決済へ進む
              </button>
            </form>
          </article>
        ))}
      </section>

      <section className="mt-7 grid gap-4 md:grid-cols-2">
        <a
          href="/events"
          className="glass rounded-2xl p-4 text-sm transition hover:border-emerald-300/40"
        >
          <p className="font-bold text-emerald-200">Webhookログ確認</p>
          <p className="fine mt-1">受信イベント一覧を表示します。スクショ素材にも使えます。</p>
        </a>

        <div className="glass rounded-2xl p-4 text-sm">
          <p className="font-bold text-amber-100">注意（出品文に載せる時）</p>
          <p className="fine mt-1">
            実装デモ画像を使う場合は「実装実績例」であることと、「現サービスは不具合修正が対象」の注記を併記してください。
          </p>
        </div>
      </section>
    </main>
  );
}
