import type { ComponentProps } from "react";
import Link from "next/link";

import { cn } from "@/lib/utils";
import { buttonVariants } from "./button";

export function Pagination({ className, ...props }: ComponentProps<"nav">) {
  return (
    <nav
      aria-label="文章分页"
      className={cn("flex justify-center", className)}
      {...props}
    />
  );
}

export function PaginationContent({
  className,
  ...props
}: ComponentProps<"ul">) {
  return (
    <ul
      className={cn(
        "flex flex-wrap items-center justify-center gap-2",
        className,
      )}
      {...props}
    />
  );
}

export function PaginationLink({
  isActive,
  className,
  ...props
}: ComponentProps<typeof Link> & { isActive?: boolean }) {
  return (
    <Link
      aria-current={isActive ? "page" : undefined}
      className={cn(
        buttonVariants({ variant: isActive ? "default" : "ghost" }),
        "min-w-11 rounded-pill",
        className,
      )}
      {...props}
    />
  );
}
