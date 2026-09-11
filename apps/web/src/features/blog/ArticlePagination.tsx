import { ChevronLeft, ChevronRight } from "lucide-react";

import { Pagination, PaginationContent } from "@/components/ui/pagination";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { ReadingLink } from "./ReadingLink";
import { listUrl } from "./urls";

export function ArticlePagination({
  page,
  totalPages,
  path,
  query,
}: {
  page: number;
  totalPages: number;
  path: string;
  query?: string;
}) {
  if (totalPages <= 1) return null;
  const pages = [...new Set([1, page - 1, page, page + 1, totalPages])]
    .filter((n) => n > 0 && n <= totalPages)
    .sort((a, b) => a - b);
  const muted =
    "inline-flex min-h-11 items-center gap-1 px-3 text-ui text-muted-foreground";
  return (
    <Pagination className="mt-10">
      <PaginationContent>
        <li>
          {page > 1 ? (
            <ReadingLink
              href={listUrl(path, page - 1, query)}
              className={buttonVariants({ variant: "ghost" })}
            >
              <ChevronLeft size={16} aria-hidden="true" />
              上一页
            </ReadingLink>
          ) : (
            <span aria-disabled="true" className={muted}>
              <ChevronLeft size={16} aria-hidden="true" />
              上一页
            </span>
          )}
        </li>
        {pages.map((number, i) => (
          <li
            key={number}
            className={cn(
              "items-center gap-2",
              number === page ? "flex" : "hidden sm:flex",
            )}
          >
            {i > 0 && number - (pages[i - 1] ?? 0) > 1 && (
              <span aria-hidden="true">…</span>
            )}
            <ReadingLink
              href={listUrl(path, number, query)}
              aria-label={`第 ${number} 页`}
              aria-current={number === page ? "page" : undefined}
              className={cn(
                buttonVariants({
                  variant: number === page ? "default" : "ghost",
                }),
                "min-w-11 rounded-pill",
              )}
            >
              {number}
            </ReadingLink>
          </li>
        ))}
        <li>
          {page < totalPages ? (
            <ReadingLink
              href={listUrl(path, page + 1, query)}
              className={buttonVariants({ variant: "ghost" })}
            >
              下一页
              <ChevronRight size={16} aria-hidden="true" />
            </ReadingLink>
          ) : (
            <span aria-disabled="true" className={muted}>
              下一页
              <ChevronRight size={16} aria-hidden="true" />
            </span>
          )}
        </li>
      </PaginationContent>
    </Pagination>
  );
}
