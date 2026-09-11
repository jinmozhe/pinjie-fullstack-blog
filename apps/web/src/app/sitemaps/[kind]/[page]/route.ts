import { sitemapPageResponse } from "@/features/blog";

export const dynamic = "force-dynamic";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ kind: string; page: string }> },
) {
  const { kind, page } = await params;
  return sitemapPageResponse(kind, page);
}
