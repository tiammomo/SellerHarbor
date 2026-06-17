"use client";
import { useState } from "react";
import { Button, Dropdown, Avatar, Badge, Tooltip } from "@arco-design/web-react";
import {
  IconMenu,
  IconSun,
  IconMoon,
  IconUser,
  IconPoweroff,
  IconNotification,
  IconSearch,
} from "@arco-design/web-react/icon";
import { useAppStore } from "@/lib/stores/appStore";
import { useRouter } from "next/navigation";

export default function Header() {
  const { toggleSidebar, theme, setTheme } = useAppStore();
  const router = useRouter();

  const toggleTheme = () => {
    setTheme(theme === "light" ? "dark" : "light");
  };

  return (
    <div
      className="flex items-center justify-between px-6 border-b glass"
      style={{ height: 64, borderColor: "var(--border-color)" }}
    >
      {/* Left side */}
      <div className="flex items-center gap-4">
        <Button
          type="text"
          icon={<IconMenu />}
          onClick={toggleSidebar}
          className="arco-btn-icon-only"
          style={{ fontSize: 20 }}
        />
      </div>

      {/* Right side */}
      <div className="flex items-center gap-2">
        {/* Search */}
        <Tooltip content="搜索">
          <Button
            type="text"
            icon={<IconSearch />}
            className="arco-btn-icon-only"
            style={{ color: "var(--text-color-3)" }}
          />
        </Tooltip>

        {/* Notification */}
        <Tooltip content="通知">
          <Badge count={3} dot>
            <Button
              type="text"
              icon={<IconNotification />}
              className="arco-btn-icon-only"
              style={{ color: "var(--text-color-3)" }}
            />
          </Badge>
        </Tooltip>

        {/* Theme toggle */}
        <Tooltip content={theme === "light" ? "切换暗色" : "切换亮色"}>
          <Button
            type="text"
            icon={theme === "light" ? <IconMoon /> : <IconSun />}
            onClick={toggleTheme}
            className="arco-btn-icon-only"
            style={{ color: "var(--text-color-3)" }}
          />
        </Tooltip>

        {/* Divider */}
        <div className="w-px h-6 mx-2" style={{ backgroundColor: "var(--border-color)" }} />

        {/* User dropdown */}
        <Dropdown
          droplist={
            <div className="py-1" style={{ minWidth: 160 }}>
              <div className="px-4 py-2 border-b" style={{ borderColor: "var(--border-color)" }}>
                <div className="font-medium" style={{ color: "var(--text-color-1)" }}>运营人员</div>
                <div className="text-xs" style={{ color: "var(--text-color-3)" }}>admin@sellerharbor.local</div>
              </div>
              <div
                className="flex items-center gap-2 px-4 py-2 cursor-pointer hover:bg-black/5 dark:hover:bg-white/5"
                onClick={() => router.push("/settings")}
              >
                <IconUser style={{ color: "var(--text-color-3)" }} />
                <span style={{ color: "var(--text-color-2)" }}>个人设置</span>
              </div>
              <div className="flex items-center gap-2 px-4 py-2 cursor-pointer hover:bg-black/5 dark:hover:bg-white/5 text-red-500">
                <IconPoweroff />
                <span>退出登录</span>
              </div>
            </div>
          }
          trigger="click"
        >
          <div className="flex items-center gap-3 cursor-pointer py-1 px-2 rounded-lg hover:bg-black/5 dark:hover:bg-white/5 transition-colors">
            <Avatar size={36} style={{ backgroundColor: "#f97316", borderRadius: 10 }}>👤</Avatar>
            <div className="hidden md:block">
              <div className="text-sm font-medium" style={{ color: "var(--text-color-1)" }}>运营人员</div>
            </div>
          </div>
        </Dropdown>
      </div>
    </div>
  );
}
