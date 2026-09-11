import type { Metadata } from "next";
import { notFound } from "next/navigation";
import type { TaxonomyKind } from "@pinjie/api-client";

import { publicOrigin } from "@/lib/public-origin";
import { ArticleBody } from "./ArticleBody";
import { ArticleList } from "./ArticleList";
import { BlogShell } from "./BlogShell";
import { CoverImage } from "./CoverImage";
import {
  getBlogSite,
  getPublicPost,
  getPublicPosts,
  getPublicTaxonomy,
} from "./data";
import { ReadingLink } from "./ReadingLink";
import { SearchForm } from "./SearchForm";
import {
  formatPublished,
  listUrl,
  pageNumber,
  serializeJsonLd,
  type ReadingSearchParams,
} from "./urls";

function requirePage(params: ReadingSearchParams): number {
  const page = pageNumber(params.page);
  if (page === null) notFound();
  return page;
}

export async function homeMetadata(
  params: ReadingSearchParams,
): Promise<Metadata> {
  const site = await getBlogSite();
  const page = requirePage(params);
  const data = await getPublicPosts({ page });
  if (page > 1 && page > data.total_pages) notFound();
  return {
    title: {
      absolute:
        page === 1 ? site.title : `全部文章 · 第 ${page} 页 | ${site.name}`,
    },
    description: site.description,
    alternates: { canonical: listUrl("/", page) },
    openGraph: {
      title: site.title,
      description: site.description,
      url: listUrl("/", page),
      type: "website",
    },
  };
}

export async function HomeReadingPage({
  searchParams,
}: {
  searchParams: ReadingSearchParams;
}) {
  const page = requirePage(searchParams);
  const [site, data] = await Promise.all([
    getBlogSite(),
    getPublicPosts({ page }),
  ]);
  if (page > 1 && page > data.total_pages) notFound();
  return (
    <BlogShell>
      <header className="mb-8 flex min-h-0 flex-col justify-center py-4 lg:min-h-[160px]">
        <p className="mb-3 text-meta font-semibold text-link">
          文字 · 记录 · 分享
        </p>
        <h1 className="font-serif text-home-title [overflow-wrap:anywhere]">
          {page === 1 ? site.title : "全部文章"}
        </h1>
        {page === 1 && site.description && (
          <p className="mt-4 max-w-[720px] leading-relaxed text-muted-foreground [overflow-wrap:anywhere]">
            {site.description}
          </p>
        )}
      </header>
      <ArticleList data={data} path="/" />
    </BlogShell>
  );
}

export async function taxonomyMetadata(
  kind: TaxonomyKind,
  slug: string,
  params: ReadingSearchParams,
): Promise<Metadata> {
  const taxonomy = await getPublicTaxonomy(kind, slug);
  const page = requirePage(params);
  const label = kind === "categories" ? "分类" : "标签";
  const data = await getPublicPosts({
    page,
    ...(kind === "categories" ? { category: slug } : { tag: slug }),
  });
  if (page > 1 && page > data.total_pages) notFound();
  const title = `${taxonomy.name} · ${label}${page > 1 ? ` · 第 ${page} 页` : ""}`;
  const description = `浏览${label}“${taxonomy.name}”下的公开文章。`;
  const url = listUrl(`/${kind}/${taxonomy.slug}`, page);
  return {
    title,
    description,
    alternates: { canonical: url },
    openGraph: { title, description, url, type: "website" },
  };
}

export async function TaxonomyReadingPage({
  kind,
  slug,
  searchParams,
}: {
  kind: TaxonomyKind;
  slug: string;
  searchParams: ReadingSearchParams;
}) {
  const page = requirePage(searchParams);
  const taxonomy = await getPublicTaxonomy(kind, slug);
  const filters = kind === "categories" ? { category: slug } : { tag: slug };
  const data = await getPublicPosts({ page, ...filters });
  if (page > 1 && page > data.total_pages) notFound();
  return (
    <BlogShell {...filters}>
      <header className="mb-8">
        <p className="mb-3 text-meta text-link">
          {kind === "categories" ? "文章分类" : "文章标签"}
        </p>
        <h1 className="text-home-title font-semibold [overflow-wrap:anywhere]">
          {taxonomy.name}
        </h1>
        <ReadingLink
          href="/"
          className="mt-4 inline-block min-h-11 py-2 text-ui text-link underline underline-offset-4"
        >
          浏览全部文章
        </ReadingLink>
      </header>
      <ArticleList data={data} path={`/${kind}/${slug}`} filtered />
    </BlogShell>
  );
}

export async function SearchReadingPage({
  searchParams,
}: {
  searchParams: ReadingSearchParams;
}) {
  const query = typeof searchParams.q === "string" ? searchParams.q.trim() : "";
  if (query.length > 100 || Array.isArray(searchParams.q))
    return (
      <BlogShell>
        <h1 className="mb-6 text-home-title">搜索文章</h1>
        <p role="alert" className="mb-6 text-error-foreground">
          请输入一个不超过 100 个字符的关键词。
        </p>
        <SearchForm query={query.slice(0, 100)} />
      </BlogShell>
    );
  const page = requirePage(searchParams);
  if (!query)
    return (
      <BlogShell>
        <h1 className="mb-4 text-home-title">搜索文章</h1>
        <p className="mb-8 text-muted-foreground">
          输入关键词，搜索文章标题和摘要。
        </p>
        <div className="max-w-[480px]">
          <SearchForm />
        </div>
      </BlogShell>
    );
  const data = await getPublicPosts({ page, q: query });
  if (page > 1 && page > data.total_pages) notFound();
  return (
    <BlogShell query={query}>
      <header className="mb-8">
        <p className="mb-3 text-meta text-link">标题与摘要搜索</p>
        <h1 className="text-home-title font-semibold [overflow-wrap:anywhere]">
          “{query}”的搜索结果
        </h1>
        <ReadingLink
          href="/"
          className="mt-4 inline-block min-h-11 py-2 text-ui text-link underline underline-offset-4"
        >
          清除搜索
        </ReadingLink>
      </header>
      <ArticleList data={data} path="/search" query={query} filtered />
    </BlogShell>
  );
}

export async function articleMetadata(slug: string): Promise<Metadata> {
  const post = await getPublicPost(slug);
  const description = post.summary || `阅读《${post.title}》。`;
  return {
    title: post.title,
    description,
    alternates: { canonical: `/posts/${post.slug}` },
    openGraph: {
      type: "article",
      title: post.title,
      description,
      url: `/posts/${post.slug}`,
      publishedTime: post.published_at,
      modifiedTime: post.updated_at,
      ...(post.cover_url ? { images: [{ url: post.cover_url }] } : {}),
    },
  };
}

export async function ArticleReadingPage({ slug }: { slug: string }) {
  const [post, site] = await Promise.all([getPublicPost(slug), getBlogSite()]);
  const url = new URL(`/posts/${post.slug}`, publicOrigin()).href;
  const structuredData = {
    "@context": "https://schema.org",
    "@type": "BlogPosting",
    headline: post.title,
    description: post.summary || `阅读《${post.title}》。`,
    datePublished: post.published_at,
    dateModified: post.updated_at,
    mainEntityOfPage: url,
    url,
    publisher: { "@type": "Organization", name: site.name },
    ...(post.cover_url
      ? { image: new URL(post.cover_url, publicOrigin()).href }
      : {}),
  };
  return (
    <BlogShell category={post.category?.slug}>
      <article className="mx-auto max-w-[720px]">
        <ReadingLink
          href="/"
          className="mb-8 inline-block min-h-11 py-2 text-ui text-link"
        >
          ← 返回全部文章
        </ReadingLink>
        <header className="mb-8">
          {post.category && (
            <ReadingLink
              href={`/categories/${post.category.slug}`}
              className="mb-4 inline-block text-meta text-link hover:underline"
            >
              {post.category.name}
            </ReadingLink>
          )}
          <h1 className="text-article-title font-semibold [overflow-wrap:anywhere]">
            {post.title}
          </h1>
          <div className="mt-5 flex flex-wrap gap-x-5 gap-y-2 text-meta text-muted-foreground">
            <span>
              发布于{" "}
              <time dateTime={post.published_at}>
                {formatPublished(post.published_at)}
              </time>
            </span>
            {post.updated_at !== post.published_at && (
              <span>
                更新于{" "}
                <time dateTime={post.updated_at}>
                  {formatPublished(post.updated_at)}
                </time>
              </span>
            )}
          </div>
          {post.summary && (
            <p className="mt-6 leading-relaxed text-muted-foreground [overflow-wrap:anywhere]">
              {post.summary}
            </p>
          )}
        </header>
        {post.cover_url && (
          <div className="mb-8">
            <CoverImage src={post.cover_url} title={post.title} priority />
          </div>
        )}
        <ArticleBody html={post.html} />
        {post.tags.length > 0 && (
          <footer className="mt-10 border-t border-border pt-6">
            <h2 className="mb-4 text-ui font-semibold">文章标签</h2>
            <ul className="flex flex-wrap gap-2">
              {post.tags.map((tag) => (
                <li key={tag.slug} className="min-w-0 max-w-full">
                  <ReadingLink
                    href={`/tags/${tag.slug}`}
                    className="block rounded-pill bg-sidebar px-4 py-2 text-ui text-link hover:bg-accent [overflow-wrap:anywhere]"
                  >
                    {tag.name}
                  </ReadingLink>
                </li>
              ))}
            </ul>
          </footer>
        )}
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: serializeJsonLd(structuredData) }}
        />
      </article>
    </BlogShell>
  );
}
