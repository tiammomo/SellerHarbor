import type { Metadata } from "next";
import Script from "next/script";
import "./globals.css";

const themeBootScript = `
(() => {
  try {
    var theme = localStorage.getItem('rp-theme');
    if (theme !== 'dark' && theme !== 'light') theme = 'light';
    var root = document.documentElement;
    root.setAttribute('data-theme', theme);
    root.classList.toggle('dark', theme === 'dark');
    root.style.colorScheme = theme;
  } catch (error) {}
})();
`;

const react19ArcoConsoleGuardScript = `
(() => {
  if (typeof window === 'undefined') return;
  if (window.__reviewPilotReact19ConsoleGuard) return;
  window.__reviewPilotReact19ConsoleGuard = true;

  var ignoredMessages = [
    'Accessing element.ref was removed in React 19. ref is now a regular prop'
  ];

  function shouldIgnore(args) {
    for (var i = 0; i < args.length; i += 1) {
      var value = args[i];
      if (typeof value !== 'string') continue;
      for (var j = 0; j < ignoredMessages.length; j += 1) {
        if (value.indexOf(ignoredMessages[j]) !== -1) return true;
      }
    }
    return false;
  }

  function patchConsole(method) {
    var fallback = typeof console[method] === 'function' ? console[method].bind(console) : function () {};
    var current = fallback;

    function guardedConsoleMethod() {
      var args = Array.prototype.slice.call(arguments);
      if (shouldIgnore(args)) return;
      return current.apply(console, args);
    }

    try {
      Object.defineProperty(console, method, {
        configurable: true,
        enumerable: true,
        get: function () {
          return guardedConsoleMethod;
        },
        set: function (next) {
          current = typeof next === 'function' ? next.bind(console) : fallback;
        }
      });
    } catch (error) {
      console[method] = guardedConsoleMethod;
    }
  }

  patchConsole('error');
  patchConsole('warn');
})();
`;

export const metadata: Metadata = {
  title: "SellerHarbor - 跨境卖家商品运营港",
  description: "面向 Temu、TikTok Shop 等跨境卖家的商品主数据、上架素材、海外仓库存、好评与热款追踪工作台",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh" data-theme="light" suppressHydrationWarning>
      <body>
        {process.env.NODE_ENV === "development" && (
          <Script id="react19-arco-console-guard" strategy="beforeInteractive">
            {react19ArcoConsoleGuardScript}
          </Script>
        )}
        <Script id="theme-boot" strategy="beforeInteractive">
          {themeBootScript}
        </Script>
        {children}
      </body>
    </html>
  );
}
