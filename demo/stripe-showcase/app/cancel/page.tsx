import Link from "next/link";

export default function CancelPage() {
  return (
    <main className="mx-auto min-h-screen w-full max-w-4xl px-6 py-12 md:px-10">
      <section className="glass p-6 md:p-8">
        <p className="mb-2 text-xs font-semibold uppercase tracking-widest"
           style={{ color: "var(--warning)" }}>
          Payment Canceled
        </p>
        <h1 className="font-heading text-3xl font-semibold md:text-4xl"
            style={{ color: "var(--foreground)" }}>
          決済がキャンセルされました
        </h1>
        <p className="fine mt-3 text-sm md:text-base">
          課金は発生していません。いつでも再開できます。
        </p>
        <Link
          href="/"
          className="mt-6 inline-flex cursor-pointer rounded-lg px-5 py-2.5 text-sm font-semibold transition-colors"
          style={{ border: "1px solid var(--line)", color: "var(--foreground)" }}
        >
          プランへ戻る
        </Link>
      </section>
    </main>
  );
}
