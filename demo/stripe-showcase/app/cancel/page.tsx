import Link from "next/link";

export default function CancelPage() {
  return (
    <main className="mx-auto min-h-screen w-full max-w-4xl px-6 py-12 md:px-10">
      <section className="glass rounded-3xl p-6 md:p-8">
        <p className="mb-3 text-xs font-semibold uppercase tracking-[0.2em] text-amber-300">Payment Canceled</p>
        <h1 className="font-heading text-3xl font-extrabold md:text-4xl">決済はキャンセルされました</h1>
        <p className="fine mt-3 text-sm md:text-base">
          この画面もキャンセル導線の動作証跡としてスクショに使えます。
        </p>
        <Link
          href="/"
          className="mt-6 inline-flex rounded-full border border-white/30 px-5 py-2 text-sm font-bold transition hover:bg-white/10"
        >
          トップへ戻る
        </Link>
      </section>
    </main>
  );
}
