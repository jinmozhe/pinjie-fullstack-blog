import type { Metadata } from "next";

import { SearchReadingPage, type ReadingSearchParams } from "@/features/blog";

export const dynamic = "force-dynamic";
export const metadata: Metadata = {
  title: "搜索文章",
  description: "搜索公开文章的标题与摘要。",
  robots: { index: false, follow: true },
};

export default async function SearchPage({
  searchParams,
}: {
  searchParams: Promise<ReadingSearchParams>;
}) {
  return <SearchReadingPage searchParams={await searchParams} />;
}
