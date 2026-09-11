import {
  getSiteProfileApiV1SystemSiteProfileGet,
  publicPostsApiV1BlogPostsGet,
  publicPostApiV1BlogPostsSlugGet,
  publicTaxonomiesApiV1BlogTaxonomyKindGet,
  publicTaxonomyApiV1BlogTaxonomyKindSlugGet,
} from "@pinjie/api-client";
import type {
  PublicPostsApiV1BlogPostsGetData,
  PublicTaxonomyCount,
  TaxonomyKind,
} from "@pinjie/api-client";
import { createClient } from "@pinjie/api-client/client";
import { notFound } from "next/navigation";
import { cache } from "react";

function serverClient() {
  if (typeof window !== "undefined")
    throw new Error("公开内容只能从服务端读取");
  const baseURL = process.env.BACKEND_INTERNAL_URL;
  if (!baseURL) throw new Error("后端服务尚未配置");
  return createClient({
    baseURL,
    timeout: 10000,
    maxRedirects: 0,
    headers: { "Cache-Control": "no-store" },
  });
}

function missingOrFailure(status: number): never {
  if (status === 404) notFound();
  throw new Error("文章服务暂时不可用");
}

export const getBlogSite = cache(async () => {
  const result = await getSiteProfileApiV1SystemSiteProfileGet({
    client: serverClient(),
    throwOnError: true,
  });
  return result.data.data;
});

export const getPublicPost = cache(async (slug: string) => {
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug) || slug.length > 120) notFound();
  const result = await publicPostApiV1BlogPostsSlugGet({
    client: serverClient(),
    path: { slug },
  });
  if (!result.data) missingOrFailure(result.response?.status ?? 503);
  return result.data.data;
});

const fetchPostPage = cache(
  async (
    page: number,
    pageSize: number,
    q: string,
    category?: string,
    tag?: string,
  ) => {
    const result = await publicPostsApiV1BlogPostsGet({
      client: serverClient(),
      query: { page, page_size: pageSize, q, category, tag },
      throwOnError: true,
    });
    return result.data.data;
  },
);

export function getPublicPosts(
  query: PublicPostsApiV1BlogPostsGetData["query"],
) {
  return fetchPostPage(
    query?.page ?? 1,
    query?.page_size ?? 12,
    query?.q ?? "",
    query?.category ?? undefined,
    query?.tag ?? undefined,
  );
}

export const getPublicTaxonomy = cache(
  async (kind: TaxonomyKind, slug: string) => {
    if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug) || slug.length > 120)
      notFound();
    const result = await publicTaxonomyApiV1BlogTaxonomyKindSlugGet({
      client: serverClient(),
      path: { kind, slug },
    });
    if (!result.data) missingOrFailure(result.response?.status ?? 503);
    return result.data.data;
  },
);

export async function getTaxonomyPage(kind: TaxonomyKind, page: number) {
  const result = await publicTaxonomiesApiV1BlogTaxonomyKindGet({
    client: serverClient(),
    path: { kind },
    query: { page, page_size: 100 },
    throwOnError: true,
  });
  return result.data.data;
}

const getAllTaxonomy = cache(async (kind: TaxonomyKind) => {
  const first = await getTaxonomyPage(kind, 1);
  const items: PublicTaxonomyCount[] = [...first.items];
  for (let page = 2; page <= first.total_pages; page += 1) {
    items.push(...(await getTaxonomyPage(kind, page)).items);
  }
  return items;
});

export const getBlogNavigation = cache(async () => {
  const [categories, tags] = await Promise.all([
    getAllTaxonomy("categories"),
    getAllTaxonomy("tags"),
  ]);
  return { categories, tags };
});
