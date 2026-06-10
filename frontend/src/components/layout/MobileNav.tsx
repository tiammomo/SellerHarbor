"use client";
import { useRouter, usePathname } from "next/navigation";
import {
  IconHome,
  IconApps,
  IconEdit,
  IconCheckCircle,
  IconSettings,
} from "@arco-design/web-react/icon";

const navItems = [
  { key: "/dashboard", label: "看板", icon: <IconHome /> },
  { key: "/products", label: "商品", icon: <IconApps /> },
  { key: "/generate", label: "生成", icon: <IconEdit /> },
  { key: "/review", label: "审核", icon: <IconCheckCircle /> },
  { key: "/settings", label: "设置", icon: <IconSettings /> },
];

export default function MobileNav() {
  const router = useRouter();
  const pathname = usePathname();
  const selectedKey = navItems.find((item) => pathname.startsWith(item.key))?.key || "/dashboard";

  return (
    <div
      className="fixed bottom-0 left-0 right-0 border-t glass mobile-nav"
      style={{
        height: "var(--mobile-nav-height)",
        borderColor: "var(--border-color)",
        zIndex: 100,
      }}
    >
      <div className="flex items-center justify-around h-full">
        {navItems.map((item) => {
          const isActive = selectedKey === item.key;
          return (
            <button
              key={item.key}
              type="button"
              onClick={() => router.push(item.key)}
              className="flex flex-col items-center justify-center gap-1 border-0 bg-transparent cursor-pointer px-3 py-1"
              style={{ color: isActive ? "var(--color-primary)" : "var(--text-color-3)" }}
            >
              <span className="text-xl">{item.icon}</span>
              <span className="text-xs font-medium">{item.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
