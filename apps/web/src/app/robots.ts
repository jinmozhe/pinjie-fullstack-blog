import type { MetadataRoute } from "next";

import { publicOrigin } from "@/lib/public-origin";

export const dynamic = "force-dynamic";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: { userAgent: "*", allow: "/", disallow: "/api/" },
    sitemap: new URL("/sitemap.xml", publicOrigin()).href,
  };
}
