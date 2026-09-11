import type { PublicTaxonomyCount } from "@pinjie/api-client";
import { FolderOpen, Hash, Library } from "lucide-react";

import { cn } from "@/lib/utils";
import { ReadingLink } from "./ReadingLink";
import { SearchForm } from "./SearchForm";

export type NavigationProps = {
  categories: PublicTaxonomyCount[];
  tags: PublicTaxonomyCount[];
  category?: string;
  tag?: string;
  query?: string;
};

export function Navigation({
  categories,
  tags,
  category,
  tag,
  query,
}: NavigationProps) {
  const itemClass = (active: boolean) =>
    cn(
      "flex min-h-11 items-center gap-3 rounded-pill px-4 py-2 text-ui transition-colors duration-hover [overflow-wrap:anywhere]",
      active
        ? "bg-primary text-primary-foreground focus-visible:ring-2 focus-visible:ring-background"
        : "hover:bg-accent",
    );
  return (
    <div className="space-y-8">
      <SearchForm query={query} />
      <nav aria-label="文章分类">
        <h2 className="mb-3 px-4 text-meta font-semibold text-muted-foreground">
          文章分类
        </h2>
        <ul className="space-y-1">
          <li>
            <ReadingLink
              href="/"
              aria-current={!category && !tag && !query ? "page" : undefined}
              className={itemClass(!category && !tag && !query)}
            >
              <Library size={16} aria-hidden="true" className="shrink-0" />
              全部文章
            </ReadingLink>
          </li>
          {categories.map((item) => (
            <li key={item.slug}>
              <ReadingLink
                href={`/categories/${item.slug}`}
                aria-current={category === item.slug ? "page" : undefined}
                className={itemClass(category === item.slug)}
              >
                <FolderOpen size={16} aria-hidden="true" className="shrink-0" />
                <span className="min-w-0 flex-1">{item.name}</span>
                <span className="shrink-0 text-meta">{item.post_count}</span>
              </ReadingLink>
            </li>
          ))}
        </ul>
      </nav>
      {tags.length > 0 && (
        <nav aria-label="全部标签">
          <h2 className="mb-4 flex items-center gap-2 px-4 text-meta font-semibold text-muted-foreground">
            <Hash size={16} aria-hidden="true" />
            全部标签
          </h2>
          <ul className="flex flex-wrap gap-2 px-1">
            {tags.map((item) => (
              <li className="min-w-0 max-w-full" key={item.slug}>
                <ReadingLink
                  href={`/tags/${item.slug}`}
                  aria-current={tag === item.slug ? "page" : undefined}
                  className={cn(
                    "block rounded-pill px-3 py-2 text-ui transition-colors duration-hover [overflow-wrap:anywhere]",
                    tag === item.slug
                      ? "bg-primary text-primary-foreground"
                      : "bg-background hover:bg-accent",
                  )}
                >
                  {item.name}
                </ReadingLink>
              </li>
            ))}
          </ul>
        </nav>
      )}
    </div>
  );
}
