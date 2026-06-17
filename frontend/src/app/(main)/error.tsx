"use client";

import { useEffect } from "react";
import { Button } from "@arco-design/web-react";
import { IconHome, IconRefresh } from "@arco-design/web-react/icon";
import { useRouter } from "next/navigation";

export default function MainRouteError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const router = useRouter();

  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex min-h-[60vh] items-center justify-center px-4">
      <div className="w-full max-w-lg rounded-2xl border p-8 text-center" style={{ borderColor: "var(--border-color)", backgroundColor: "var(--color-bg-2)" }}>
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full" style={{ backgroundColor: "#ef44441a", color: "var(--color-danger)" }}>
          <IconRefresh style={{ fontSize: 28 }} />
        </div>
        <h2 className="mb-2 text-xl font-semibold" style={{ color: "var(--text-color-1)" }}>页面暂时不可用</h2>
        <p className="mb-6 text-sm leading-relaxed" style={{ color: "var(--text-color-3)" }}>
          页面渲染时遇到异常，可以重试当前页面或回到首页继续操作。
        </p>
        <div className="flex flex-col justify-center gap-3 sm:flex-row">
          <Button type="primary" icon={<IconRefresh />} onClick={reset}>
            重新加载
          </Button>
          <Button icon={<IconHome />} onClick={() => router.push("/dashboard")}>
            回到首页
          </Button>
        </div>
      </div>
    </div>
  );
}
