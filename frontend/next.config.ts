import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  transpilePackages: ["@arco-design/web-react"],
};

export default nextConfig;
