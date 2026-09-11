import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";
import { getBlogSite } from "@/features/blog";
import { publicOrigin } from "@/lib/public-origin";

export const dynamic = "force-dynamic";

export async function generateMetadata(): Promise<Metadata> {
  const site = await getBlogSite();
  return {
    metadataBase: publicOrigin(),
    title: { default: site.title, template: `%s | ${site.name}` },
    description: site.description,
    ...(site.logo_url ? { icons: { icon: site.logo_url } } : {}),
  };
}

export default function RootLayout({
  children,
}: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
