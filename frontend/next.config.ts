import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Needed for standalone output when deploying via Docker
  output: process.env.NEXT_OUTPUT === "standalone" ? "standalone" : undefined,
};

export default nextConfig;
