import { publicOrigin } from "@/lib/public-origin";
import { getPublicPosts, getTaxonomyPage } from "./data";

const xmlHeaders = {
  "Content-Type": "application/xml; charset=utf-8",
  "Cache-Control": "no-store",
  "X-Content-Type-Options": "nosniff",
};
function xml(value: string) {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}
function failure() {
  return new Response("站点地图暂时不可用", {
    status: 503,
    headers: {
      "Cache-Control": "no-store",
      "Content-Type": "text/plain; charset=utf-8",
    },
  });
}

export async function sitemapIndexResponse() {
  try {
    const origin = publicOrigin();
    const [posts, categories, tags] = await Promise.all([
      getPublicPosts({ page: 1, page_size: 100 }),
      getTaxonomyPage("categories", 1),
      getTaxonomyPage("tags", 1),
    ]);
    const groups = [
      { kind: "posts", pages: Math.max(1, posts.total_pages) },
      { kind: "categories", pages: categories.total_pages },
      { kind: "tags", pages: tags.total_pages },
    ];
    if (groups.reduce((sum, group) => sum + group.pages, 0) > 50000)
      throw new Error("站点地图索引超出协议上限");
    const entries = groups.flatMap(({ kind, pages }) =>
      Array.from(
        { length: pages },
        (_, i) =>
          `<sitemap><loc>${xml(new URL(`/sitemaps/${kind}/${i + 1}`, origin).href)}</loc></sitemap>`,
      ),
    );
    return new Response(
      `<?xml version="1.0" encoding="UTF-8"?><sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${entries.join("")}</sitemapindex>`,
      { headers: xmlHeaders },
    );
  } catch {
    return failure();
  }
}

export async function sitemapPageResponse(kind: string, rawPage: string) {
  if (
    !["posts", "categories", "tags"].includes(kind) ||
    !/^[1-9]\d{0,6}$/.test(rawPage) ||
    Number(rawPage) > 1000000
  )
    return new Response("站点地图不存在", {
      status: 404,
      headers: { "Cache-Control": "no-store" },
    });
  try {
    const origin = publicOrigin();
    const page = Number(rawPage);
    const rows =
      kind === "posts"
        ? await getPublicPosts({ page, page_size: 100 })
        : await getTaxonomyPage(
            kind === "categories" ? "categories" : "tags",
            page,
          );
    if (page > Math.max(1, rows.total_pages))
      return new Response("站点地图不存在", {
        status: 404,
        headers: { "Cache-Control": "no-store" },
      });
    const entries = rows.items.map(
      (item) =>
        `<url><loc>${xml(new URL(`/${kind}/${item.slug}`, origin).href)}</loc></url>`,
    );
    if (kind === "posts" && page === 1)
      entries.unshift(`<url><loc>${xml(origin.href)}</loc></url>`);
    return new Response(
      `<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${entries.join("")}</urlset>`,
      { headers: xmlHeaders },
    );
  } catch {
    return failure();
  }
}
