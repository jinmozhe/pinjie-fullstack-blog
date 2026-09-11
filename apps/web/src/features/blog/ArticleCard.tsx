import type { PublicPostSummary } from "@pinjie/api-client";

import { CoverImage } from "./CoverImage";
import { ReadingLink } from "./ReadingLink";
import { formatPublished } from "./urls";

export function ArticleCard({ post }: { post: PublicPostSummary }) {
  return (
    <article className="flex min-w-0 flex-col rounded-card bg-card shadow-card">
      {post.cover_url && (
        <ReadingLink
          href={`/posts/${post.slug}`}
          aria-label={`阅读：${post.title}`}
          className="m-3 mb-0 block rounded-media"
        >
          <CoverImage src={post.cover_url} title={post.title} />
        </ReadingLink>
      )}
      <div className="flex flex-1 flex-col items-start p-card">
        {post.category && (
          <ReadingLink
            href={`/categories/${post.category.slug}`}
            className="mb-3 text-meta font-semibold text-link hover:underline [overflow-wrap:anywhere]"
          >
            {post.category.name}
          </ReadingLink>
        )}
        <h2 className="mb-3 text-card-title font-semibold [overflow-wrap:anywhere]">
          <ReadingLink
            href={`/posts/${post.slug}`}
            className="transition-colors duration-hover hover:text-link"
          >
            {post.title}
          </ReadingLink>
        </h2>
        {post.summary && (
          <p className="mb-5 line-clamp-3 text-ui leading-relaxed text-muted-foreground [overflow-wrap:anywhere]">
            {post.summary}
          </p>
        )}
        <div className="mt-auto w-full space-y-4 pt-3">
          {post.tags.length > 0 && (
            <ul aria-label="文章标签" className="flex flex-wrap gap-2">
              {post.tags.map((tag) => (
                <li key={tag.slug} className="min-w-0 max-w-full">
                  <ReadingLink
                    href={`/tags/${tag.slug}`}
                    className="block rounded-pill bg-background px-3 py-1 text-meta text-link transition-colors duration-hover hover:bg-accent [overflow-wrap:anywhere]"
                  >
                    {tag.name}
                  </ReadingLink>
                </li>
              ))}
            </ul>
          )}
          <time
            dateTime={post.published_at}
            className="block text-meta text-muted-foreground"
          >
            {formatPublished(post.published_at)}
          </time>
        </div>
      </div>
    </article>
  );
}
