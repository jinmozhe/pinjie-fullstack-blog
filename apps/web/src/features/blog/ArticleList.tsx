import type { PageResultPublicPostSummary } from "@pinjie/api-client";
import { BookOpen } from "lucide-react";

import { ArticleCard } from "./ArticleCard";
import { ArticlePagination } from "./ArticlePagination";
import { ReadingLink } from "./ReadingLink";

export function ArticleList({
  data,
  path,
  query,
  filtered = false,
}: {
  data: PageResultPublicPostSummary;
  path: string;
  query?: string;
  filtered?: boolean;
}) {
  return (
    <section aria-label="文章列表">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3 border-b border-border pb-4 text-meta text-muted-foreground">
        <p role="status">
          共 {data.total} 篇文章
          {data.total_pages > 1 &&
            ` · 第 ${data.page} / ${data.total_pages} 页`}
        </p>
        <span>按首次发布时间排列</span>
      </div>
      {data.items.length ? (
        <div className="grid min-w-0 grid-cols-1 gap-grid md:grid-cols-2 xl:grid-cols-3">
          {data.items.map((post) => (
            <ArticleCard key={post.slug} post={post} />
          ))}
        </div>
      ) : (
        <div className="py-16 text-center">
          <BookOpen
            size={32}
            className="mx-auto mb-5 text-muted-foreground"
            aria-hidden="true"
          />
          <h2 className="text-card-title font-semibold">
            {filtered ? "没有找到匹配的文章" : "暂无文章"}
          </h2>
          <p className="mt-3 text-muted-foreground">
            {filtered
              ? "可以换个关键词，或浏览全部文章。"
              : "新的内容发布后，会出现在这里。"}
          </p>
          {filtered && (
            <ReadingLink
              href="/"
              className="mt-6 inline-block min-h-11 px-4 py-2 text-link underline underline-offset-4"
            >
              清除条件，浏览全部文章
            </ReadingLink>
          )}
        </div>
      )}
      <ArticlePagination
        page={data.page}
        totalPages={data.total_pages}
        path={path}
        query={query}
      />
    </section>
  );
}
