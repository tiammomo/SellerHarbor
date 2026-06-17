"use client";
import { useRouter } from "next/navigation";
import { Button } from "@arco-design/web-react";
import {
  IconRight,
  IconArrowRise,
  IconThumbUp,
  IconCheckCircle,
  IconStorage,
  IconSafe,
  IconApps,
  IconDashboard,
} from "@arco-design/web-react/icon";
import type { ReactNode } from "react";

/* ── Data ──────────────────────────────────────────────────── */

const features: Array<{
  title: string;
  desc: string;
  icon: ReactNode;
  color: string;
  gradient: string;
  route: string;
}> = [
  {
    title: "商品主数据",
    desc: "统一维护 SKU、变体、卖点、图片、平台字段和上架准备度",
    icon: <IconArrowRise />,
    color: "#f97316",
    gradient: "var(--gradient-primary)",
    route: "/products",
  },
  {
    title: "跨平台上架",
    desc: "围绕 Temu、TikTok Shop 准备标题、描述、类目和素材",
    icon: <IconThumbUp />,
    color: "#10b981",
    gradient: "var(--gradient-success)",
    route: "/generate",
  },
  {
    title: "海外仓库存",
    desc: "按仓库、SKU 和平台分配可售库存，识别低库存和断货风险",
    icon: <IconStorage />,
    color: "#3b82f6",
    gradient: "var(--gradient-info)",
    route: "/review",
  },
  {
    title: "好评热款追踪",
    desc: "结合销量、评分、反馈和库存状态识别热款、潜力款和风险款",
    icon: <IconArrowRise />,
    color: "#f59e0b",
    gradient: "var(--gradient-warning)",
    route: "/knowledge",
  },
  {
    title: "内容与合规",
    desc: "保留评价邀请、客服回访、详情页口碑素材和审核导出能力",
    icon: <IconSafe />,
    color: "#06b6d4",
    gradient: "var(--gradient-cyan)",
    route: "/settings",
  },
  {
    title: "数据看板",
    desc: "商品、上架、仓库、库存预警和热款动作集中呈现",
    icon: <IconDashboard />,
    color: "#ea580c",
    gradient: "var(--gradient-danger)",
    route: "/dashboard",
  },
];

const steps = [
  { num: "1", title: "建立商品主档", desc: "先把 SKU、卖点、平台目标和素材统一收口", icon: <IconApps />, route: "/products" },
  { num: "2", title: "配置平台与仓库", desc: "维护 Temu / TikTok Shop 上架状态和海外仓库存", icon: <IconStorage />, route: "/products" },
  { num: "3", title: "追踪热款与素材", desc: "根据销量、评价和库存信号处理下一步运营动作", icon: <IconCheckCircle />, route: "/dashboard" },
];

const LOGO_GRADIENT = "linear-gradient(135deg, #f97316 0%, #f59e0b 58%, #d97706 100%)";

/* ── Page ──────────────────────────────────────────────────── */

export default function HomePage() {
  const router = useRouter();

  return (
    <div className="hero-gradient" style={{ minHeight: "100vh" }}>
      {/* ── Top Nav ── */}
      <nav
        className="glass fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 border-b"
        style={{ height: 64, borderColor: "var(--border-color)" }}
      >
        <div className="flex items-center gap-3">
          <div
            className="w-9 h-9 rounded-xl flex items-center justify-center text-sm font-bold text-white"
            style={{ background: LOGO_GRADIENT }}
          >
            S
          </div>
          <span className="font-bold text-base" style={{ color: "var(--text-color-1)" }}>
            SellerHarbor
          </span>
        </div>
        <Button type="primary" size="small" onClick={() => router.push("/dashboard")}>
          开始使用
        </Button>
      </nav>

      {/* ── Hero ── */}
      <section className="relative flex flex-col items-center justify-center text-center px-6" style={{ paddingTop: 160, paddingBottom: 96 }}>
        {/* Floating orbs */}
        <div
          className="animate-float hidden md:block"
          style={{
            position: "absolute", top: 120, left: "10%", width: 120, height: 120,
            borderRadius: "50%", background: "rgba(249, 115, 22, 0.08)", filter: "blur(40px)",
          }}
        />
        <div
          className="animate-float-slow animate-float-delay-1 hidden md:block"
          style={{
            position: "absolute", top: 200, right: "12%", width: 160, height: 160,
            borderRadius: "50%", background: "rgba(59, 130, 246, 0.06)", filter: "blur(50px)",
          }}
        />
        <div
          className="animate-float animate-float-delay-2 hidden md:block"
          style={{
            position: "absolute", bottom: 80, left: "25%", width: 100, height: 100,
            borderRadius: "50%", background: "rgba(245, 158, 11, 0.07)", filter: "blur(35px)",
          }}
        />

        {/* Logo */}
        <div
          className="w-20 h-20 rounded-2xl flex items-center justify-center text-3xl font-bold text-white mx-auto mb-8 shadow-lg animate-fade-in"
          style={{ background: LOGO_GRADIENT }}
        >
          S
        </div>

        {/* Title */}
        <h1
          className="gradient-text font-bold mb-4 animate-fade-in"
          style={{ fontSize: "clamp(2.25rem, 5vw, 4rem)", lineHeight: 1.15, animationDelay: "100ms" }}
        >
          SellerHarbor
        </h1>

        {/* Tagline */}
        <p
          className="text-lg sm:text-xl font-medium mb-4 animate-fade-in"
          style={{ color: "var(--text-color-2)", animationDelay: "200ms" }}
        >
          跨境卖家的商品运营港
        </p>

        {/* Description */}
        <p
          className="text-sm sm:text-base max-w-xl mx-auto mb-10 leading-relaxed animate-fade-in"
          style={{ color: "var(--text-color-3)", animationDelay: "300ms" }}
        >
          面向 Temu、TikTok Shop 等跨境卖家，统一管理商品主档、上架素材、海外仓库存、
          好评反馈和热款追踪
        </p>

        {/* CTAs */}
        <div className="flex flex-wrap items-center justify-center gap-4 animate-fade-in" style={{ animationDelay: "400ms" }}>
          <Button
            type="primary"
            size="large"
            className="cta-pulse"
            icon={<IconRight />}
            onClick={() => router.push("/dashboard")}
            style={{ height: 48, paddingInline: 36, fontSize: 16, borderRadius: 12 }}
          >
            开始使用
          </Button>
          <Button
            size="large"
            onClick={() => router.push("/products")}
            style={{ height: 48, paddingInline: 36, fontSize: 16, borderRadius: 12 }}
          >
            了解更多
          </Button>
        </div>
      </section>

      {/* ── Features ── */}
      <section className="px-6" style={{ paddingTop: 48, paddingBottom: 80 }}>
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2
              className="font-bold mb-3"
              style={{ color: "var(--text-color-1)", fontSize: "clamp(1.5rem, 3vw, 2rem)" }}
            >
              核心能力
            </h2>
            <p className="text-sm sm:text-base" style={{ color: "var(--text-color-3)" }}>
              覆盖商品、上架、仓库、库存预警、评价反馈和热款追踪
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f, i) => (
              <div
                key={f.title}
                className={`feature-card animate-fade-in ${
                  f.gradient === "var(--gradient-primary)" ? "primary" :
                  f.gradient === "var(--gradient-success)" ? "success" :
                  f.gradient === "var(--gradient-info)" ? "info" :
                  f.gradient === "var(--gradient-warning)" ? "warning" :
                  f.gradient === "var(--gradient-cyan)" ? "cyan" : "primary"
                }`}
                style={{ animationDelay: `${i * 80 + 200}ms` }}
                onClick={() => router.push(f.route)}
              >
                <div
                  className="w-12 h-12 rounded-xl flex items-center justify-center text-xl text-white mb-5"
                  style={{ background: f.gradient }}
                >
                  {f.icon}
                </div>
                <h3 className="font-semibold text-base mb-2" style={{ color: "var(--text-color-1)" }}>
                  {f.title}
                </h3>
                <p className="text-sm leading-relaxed m-0" style={{ color: "var(--text-color-3)" }}>
                  {f.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Workflow ── */}
      <section className="px-6" style={{ paddingTop: 32, paddingBottom: 80 }}>
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-14">
            <h2
              className="font-bold mb-3"
              style={{ color: "var(--text-color-1)", fontSize: "clamp(1.5rem, 3vw, 2rem)" }}
            >
              如何使用
            </h2>
            <p className="text-sm sm:text-base" style={{ color: "var(--text-color-3)" }}>
              三步完成从商品收口到跨平台运营动作的闭环
            </p>
          </div>

          <div className="flex flex-col md:flex-row items-center md:items-start justify-center gap-10 md:gap-0">
            {steps.map((s, i) => (
              <div
                key={s.num}
                className={`flex flex-col items-center text-center animate-fade-in ${
                  i < 2 ? "workflow-connector" : ""
                }`}
                style={{
                  width: "100%",
                  maxWidth: 260,
                  animationDelay: `${i * 120 + 300}ms`,
                }}
              >
                {/* Step number badge */}
                <div
                  className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold text-white mb-4"
                  style={{ background: LOGO_GRADIENT }}
                >
                  {s.num}
                </div>
                {/* Icon */}
                <div
                  className="w-14 h-14 rounded-2xl flex items-center justify-center text-2xl mb-4"
                  style={{ backgroundColor: "rgba(249, 115, 22, 0.1)", color: "var(--color-primary)" }}
                >
                  {s.icon}
                </div>
                <h3 className="font-semibold text-base mb-2" style={{ color: "var(--text-color-1)" }}>
                  {s.title}
                </h3>
                <p className="text-sm leading-relaxed m-0" style={{ color: "var(--text-color-3)" }}>
                  {s.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Bottom CTA ── */}
      <section className="px-6" style={{ paddingBottom: 80 }}>
        <div
          className="max-w-3xl mx-auto rounded-2xl text-center border"
          style={{
            background: "var(--bg-color-card)",
            borderColor: "var(--border-color)",
            padding: "clamp(32px, 6vw, 56px) clamp(24px, 5vw, 48px)",
            boxShadow: "var(--shadow-lg)",
          }}
        >
          <h2
            className="font-bold mb-3"
            style={{ color: "var(--text-color-1)", fontSize: "clamp(1.25rem, 2.5vw, 1.75rem)" }}
          >
            准备好收口您的跨境商品运营了吗？
          </h2>
          <p className="text-sm sm:text-base mb-8" style={{ color: "var(--text-color-3)" }}>
            立即开始使用 SellerHarbor，让商品、仓库和平台运营进入同一个工作台
          </p>
          <Button
            type="primary"
            size="large"
            className="cta-pulse"
            icon={<IconRight />}
            onClick={() => router.push("/dashboard")}
            style={{ height: 48, paddingInline: 40, fontSize: 16, borderRadius: 12 }}
          >
            立即开始
          </Button>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="text-center pb-8 px-6">
        <p className="text-xs" style={{ color: "var(--text-color-4)" }}>
          © {new Date().getFullYear()} SellerHarbor. All rights reserved.
        </p>
      </footer>
    </div>
  );
}
