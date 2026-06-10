import { create } from "zustand";

type Theme = "light" | "dark";

interface AppState {
  sidebarCollapsed: boolean;
  theme: Theme;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setTheme: (theme: Theme) => void;
  hydratePreferences: () => void;
}

const isTheme = (value: string | null): value is Theme => value === "light" || value === "dark";

const applyTheme = (theme: Theme) => {
  if (typeof document === "undefined") return;
  const root = document.documentElement;
  root.setAttribute("data-theme", theme);
  root.classList.toggle("dark", theme === "dark");
  root.style.colorScheme = theme;
};

const readStoredTheme = (): Theme => {
  if (typeof window === "undefined") return "light";
  const value = localStorage.getItem("rp-theme");
  return isTheme(value) ? value : "light";
};

export const useAppStore = create<AppState>((set) => ({
  sidebarCollapsed: false,
  theme: readStoredTheme(),

  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
  setTheme: (theme) => {
    applyTheme(theme);
    if (typeof window !== "undefined") {
      localStorage.setItem("rp-theme", theme);
    }
    set({ theme });
  },
  hydratePreferences: () => {
    const theme = readStoredTheme();
    applyTheme(theme);
    set({ theme });
  },
}));
