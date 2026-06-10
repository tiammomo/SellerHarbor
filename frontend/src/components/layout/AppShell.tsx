"use client";
import { useEffect, useState } from "react";
import Sidebar from "./Sidebar";
import Header from "./Header";
import MobileNav from "./MobileNav";
import { useAppStore } from "@/lib/stores/appStore";
import { useDataStore } from "@/lib/stores/dataStore";

export default function AppShell({ children }: { children: React.ReactNode }) {
  const hydratePreferences = useAppStore((s) => s.hydratePreferences);
  const initializeData = useDataStore((s) => s.initialize);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    hydratePreferences();
    initializeData();
  }, [hydratePreferences, initializeData]);

  useEffect(() => {
    const updateIsMobile = () => setIsMobile(window.innerWidth < 768);
    updateIsMobile();
    window.addEventListener("resize", updateIsMobile);
    return () => window.removeEventListener("resize", updateIsMobile);
  }, []);

  return (
    <div className="flex h-screen overflow-hidden">
      {!isMobile && <Sidebar />}
      <div className="flex flex-col flex-1 overflow-hidden">
        <Header />
        <main
          className="flex-1 overflow-y-auto p-4 md:p-6"
          style={{
            backgroundColor: "var(--bg-color-page)",
            paddingBottom: isMobile ? "calc(var(--mobile-nav-height) + 24px)" : undefined,
          }}
        >
          {children}
        </main>
      </div>
      {isMobile && <MobileNav />}
    </div>
  );
}
