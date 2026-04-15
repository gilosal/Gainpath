import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow API calls to the FastAPI backend in Docker
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/:path*`,
      },
    ];
  },
  // Needed for standalone output when deploying via Docker
  output: process.env.NEXT_OUTPUT === "standalone" ? "standalone" : undefined,
};

export default nextConfig;
