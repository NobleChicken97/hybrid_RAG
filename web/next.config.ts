import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  async rewrites() {
    // Local-dev fallback for the relative `/api/*` client prefix (see
    // lib/api.ts): `npm run dev` proxies API calls to the backend without
    // needing NEXT_PUBLIC_BACKEND_URL. In compose prod this never fires —
    // Caddy intercepts /api/* first (see deploy/Caddyfile). Override the
    // target when the backend isn't on localhost:8000, e.g. port 8001 on
    // the Windows dev box where 8000 is taken by Docker/WSL.
    const target = process.env.BACKEND_INTERNAL_URL ?? "http://localhost:8000";
    return [{ source: "/api/:path*", destination: `${target}/:path*` }];
  },
};

export default nextConfig;
