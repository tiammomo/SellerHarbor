"use client";
import { useEffect, useState, useMemo, type ReactNode } from "react";
import { useRouter, usePathname } from "next/navigation";
import { Avatar } from "@arco-design/web-react";
import {
  IconDashboard,
  IconFile,
  IconSettings,
  IconMenuFold,
  IconMenuUnfold,
  IconDown,
  IconRight,
  IconStorage,
  IconCheckCircle,
  IconMessage,
  IconArrowRise,
  IconThumbUp,
} from "@arco-design/web-react/icon";
import { useAppStore } from "@/lib/stores/appStore";

type MenuGroup = {
  label: string;
  items: Array<{ key: string; label: string; icon: ReactNode }>;
};

const menuGroups: MenuGroup[] = [
  {
    label: "工作台",
    items: [
      { key: "/dashboard", label: "数据看板", icon: <IconDashboard /> },
    ],
  },
  {
    label: "商品运营",
    items: [
      { key: "/products", label: "商品主档", icon: <IconArrowRise /> },
      { key: "/feedback", label: "评价反馈", icon: <IconMessage /> },
    ],
  },
  {
    label: "口碑运营",
    items: [
      { key: "/generate", label: "生成工作台", icon: <IconThumbUp /> },
      { key: "/review", label: "审核中心", icon: <IconCheckCircle /> },
      { key: "/history", label: "生成记录", icon: <IconFile /> },
    ],
  },
  {
    label: "知识库",
    items: [
      { key: "/knowledge", label: "品牌与话术", icon: <IconStorage /> },
    ],
  },
  {
    label: "系统",
    items: [
      { key: "/settings", label: "系统设置", icon: <IconSettings /> },
    ],
  },
];

const sidebarOpenGroupsStorageKey = "rp-sidebar-open-groups";

const getSelectedGroupKey = (groups: MenuGroup[], selectedKey: string) =>
  groups.find((g) => g.items.some((item) => item.key === selectedKey))?.label || groups[0]?.label || "工作台";

const readStoredOpenGroups = (groups: MenuGroup[], fallback: string[]) => {
  if (typeof window === "undefined") return fallback;
  const raw = localStorage.getItem(sidebarOpenGroupsStorageKey);
  if (!raw) return fallback;
  try {
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return fallback;
    const validKeys = new Set(groups.map((g) => g.label));
    const stored = parsed.filter((v): v is string => typeof v === "string" && validKeys.has(v));
    return stored.length ? stored : fallback;
  } catch {
    return fallback;
  }
};

export default function Sidebar() {
  const router = useRouter();
  const pathname = usePathname();
  const { sidebarCollapsed, toggleSidebar } = useAppStore();
  const allItems = menuGroups.flatMap((g) => g.items);

  const selectedKey = allItems.find((item) => pathname.startsWith(item.key))?.key || "/dashboard";
  const selectedGroupKey = getSelectedGroupKey(menuGroups, selectedKey);
  const defaultOpenKeys = useMemo(
    () => [menuGroups[0]?.label || "工作台", selectedGroupKey].filter((v, i, l) => l.indexOf(v) === i),
    [selectedGroupKey]
  );
  const [openGroupKeys, setOpenGroupKeys] = useState(defaultOpenKeys);
  const validGroupKeys = useMemo(() => new Set(menuGroups.map((g) => g.label)), []);

  useEffect(() => {
    setOpenGroupKeys((current) => readStoredOpenGroups(menuGroups, current.length ? current : defaultOpenKeys));
  }, [defaultOpenKeys]);
  const effectiveOpenKeys = useMemo(() => {
    const sanitized = openGroupKeys.filter((k) => validGroupKeys.has(k));
    return sanitized.includes(selectedGroupKey) ? sanitized : [...sanitized, selectedGroupKey];
  }, [openGroupKeys, selectedGroupKey, validGroupKeys]);

  const toggleGroup = (groupKey: string) => {
    setOpenGroupKeys((current) => {
      const sanitized = current.filter((k) => validGroupKeys.has(k));
      const next = sanitized.includes(groupKey) ? sanitized.filter((k) => k !== groupKey) : [...sanitized, groupKey];
      if (typeof window !== "undefined") {
        localStorage.setItem(sidebarOpenGroupsStorageKey, JSON.stringify(next));
      }
      return next;
    });
  };

  return (
    <div
      className="h-full flex flex-col border-r glass"
      style={{
        width: sidebarCollapsed ? 76 : 272,
        borderColor: "var(--border-color)",
        transition: "width 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
      }}
    >
      {/* Logo */}
      <div className="flex items-center justify-between border-b px-4" style={{ height: 68, borderColor: "var(--border-color)" }}>
        {!sidebarCollapsed && (
          <div className="flex items-center gap-3">
            <div
              className="w-11 h-11 rounded-xl flex items-center justify-center text-lg font-bold text-white shadow-sm"
              style={{ background: "linear-gradient(135deg, #f97316 0%, #f59e0b 58%, #d97706 100%)" }}
            >
              S
            </div>
            <div>
              <div className="font-bold text-lg" style={{ color: "var(--text-color-1)" }}>SellerHarbor</div>
              <div className="text-xs" style={{ color: "var(--text-color-3)" }}>跨境卖家港</div>
            </div>
          </div>
        )}
        {sidebarCollapsed && (
          <div
            className="w-11 h-11 rounded-xl flex items-center justify-center text-lg font-bold text-white mx-auto shadow-sm"
            style={{ background: "linear-gradient(135deg, #f97316 0%, #f59e0b 58%, #d97706 100%)" }}
          >
            S
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-3">
        <div className="space-y-3">
          {menuGroups.map((group) => (
            <div key={group.label} className="space-y-1">
              {!sidebarCollapsed ? (
                (() => {
                  const isGroupActive = group.label === selectedGroupKey;
                  const isGroupOpen = effectiveOpenKeys.includes(group.label);
                  return (
                    <button
                      type="button"
                      aria-expanded={isGroupOpen}
                      onClick={() => toggleGroup(group.label)}
                      className="group/section mb-1 flex h-8 w-full cursor-pointer items-center justify-between rounded-lg border-0 bg-transparent px-2 text-left outline-none transition-all hover:bg-black/[0.025] dark:hover:bg-white/[0.04]"
                      style={{ color: isGroupActive ? "var(--color-primary-dark)" : "var(--text-color-3)" }}
                    >
                      <span className="flex min-w-0 items-center gap-2">
                        <span className="h-4 w-0.5 rounded-full transition-colors" style={{ backgroundColor: isGroupActive ? "var(--color-primary)" : "transparent" }} />
                        <span className="min-w-0 truncate text-sm font-semibold tracking-normal">{group.label}</span>
                      </span>
                      <span className="ml-2 flex shrink-0 items-center gap-1.5 text-xs">
                        <span
                          className="grid h-5 min-w-5 place-items-center rounded-full px-1.5"
                          style={{
                            backgroundColor: isGroupActive ? "rgba(249, 115, 22, 0.11)" : "var(--color-fill-1)",
                            color: isGroupActive ? "var(--color-primary-dark)" : "var(--text-color-3)",
                          }}
                        >
                          {group.items.length}
                        </span>
                        <span className="grid h-5 w-5 place-items-center rounded-full" style={{ color: isGroupActive ? "var(--color-primary-dark)" : "var(--text-color-4)" }}>
                          {isGroupOpen ? <IconDown /> : <IconRight />}
                        </span>
                      </span>
                    </button>
                  );
                })()
              ) : (
                <div className="my-1.5 border-t" style={{ borderColor: "var(--border-color-light)" }} />
              )}
              {(sidebarCollapsed || effectiveOpenKeys.includes(group.label)) && (
                <div className="space-y-1">
                  {group.items.map((item) => {
                    const isActive = selectedKey === item.key;
                    return (
                      <button
                        key={item.key}
                        type="button"
                        title={sidebarCollapsed ? item.label : undefined}
                        aria-current={isActive ? "page" : undefined}
                        onClick={() => router.push(item.key)}
                        className="group relative flex h-11 w-full cursor-pointer items-center rounded-2xl border-0 bg-transparent px-2.5 text-left outline-none transition-all hover:bg-black/[0.025] dark:hover:bg-white/[0.04]"
                        style={{
                          color: isActive ? "var(--color-primary-dark)" : "var(--text-color-2)",
                          backgroundColor: isActive ? "rgba(249, 115, 22, 0.115)" : "transparent",
                          boxShadow: isActive ? "inset 0 0 0 1px rgba(249, 115, 22, 0.16), 0 8px 18px rgba(234, 88, 12, 0.08)" : "none",
                        }}
                      >
                        <span className="absolute left-0 top-1/2 h-6 w-1 -translate-y-1/2 rounded-r-full transition-all" style={{ backgroundColor: isActive ? "var(--color-primary)" : "transparent" }} />
                        <span
                          className="grid h-8 w-8 shrink-0 place-items-center rounded-xl transition-all"
                          style={{
                            backgroundColor: isActive ? "var(--color-primary)" : "rgba(100, 116, 139, 0.08)",
                            color: isActive ? "#ffffff" : "var(--text-color-3)",
                            fontSize: 18,
                          }}
                        >
                          {item.icon}
                        </span>
                        {!sidebarCollapsed && <span className="ml-3 truncate text-sm font-medium tracking-normal">{item.label}</span>}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          ))}
        </div>
      </nav>

      {/* Collapse button */}
      <div className="p-2 border-t" style={{ borderColor: "var(--border-color)" }}>
        <button
          onClick={toggleSidebar}
          className="flex h-9 w-full cursor-pointer items-center justify-center gap-2 rounded-xl border-0 bg-transparent px-3 transition-all hover:bg-black/5 dark:hover:bg-white/5"
          style={{ color: "var(--text-color-3)" }}
        >
          {sidebarCollapsed ? <IconMenuUnfold /> : <IconMenuFold />}
          {!sidebarCollapsed && <span className="text-sm">收起菜单</span>}
        </button>
      </div>

      {/* User info */}
      {!sidebarCollapsed && (
        <div className="p-3 border-t" style={{ borderColor: "var(--border-color)" }}>
          <div className="flex items-center gap-3">
            <Avatar size={36} style={{ backgroundColor: "#f97316", borderRadius: 12 }}>👤</Avatar>
            <div className="flex-1 min-w-0">
              <div className="font-medium text-sm truncate" style={{ color: "var(--text-color-1)" }}>运营人员</div>
              <div className="text-xs truncate" style={{ color: "var(--text-color-3)" }}>admin@sellerharbor.local</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
