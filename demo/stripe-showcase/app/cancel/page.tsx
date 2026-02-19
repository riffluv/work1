import Link from "next/link";

export default function CancelPage() {
  return (
    <main className="mx-auto min-h-screen w-full max-w-4xl px-6 py-12 md:px-10">
      <section className="glass rounded-2xl p-6 md:p-8">
        <p className="mb-3 text-xs font-semibold uppercase tracking-[0.2em]"
           style={{ color: "var(--warning)" }}>
          Payment Canceled
        </p>
        <h1 className="font-heading text-3xl font-extrabold md:text-4xl"
            style={{ color: "var(--foreground)" }}>
          決済はキャンセルされました
        </h1>
        <p className="fine mt-3 text-sm md:text-base">
          この画面もキャンセル導線の動作証跡としてスクショに使えます。
        </p>
        <Link
          href="/"
          className="mt-6 inline-flex rounded-xl px-5 py-2.5 text-sm font-bold transition"
          style={{
            border: "1px solid var(--line)",
            color: "var(--foreground)",
          }}
        >
          トップへ戻る
        </Link>
      </section>
    </main>
  );
}
