import Link from "next/link";

export default function Page() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center px-6">
      <div className="text-center">
        <h1 className="mb-3 text-xl font-semibold" style={{ color: "var(--text-color-1)" }}>
          商品机会已整合到商品主档
        </h1>
        <p className="mb-6 text-sm" style={{ color: "var(--text-color-3)" }}>
          请从商品主档查看资料完整度、平台状态和下一步动作。
        </p>
        <Link
          href="/products"
          className="inline-flex h-10 items-center rounded-lg px-4 text-sm font-medium text-white"
          style={{ backgroundColor: "var(--color-primary)" }}
        >
          前往商品主档
        </Link>
      </div>
    </div>
  );
}
