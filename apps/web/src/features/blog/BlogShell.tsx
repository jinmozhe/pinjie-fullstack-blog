import type { ReactNode } from "react";
import Image from "next/image";

import { getBlogNavigation, getBlogSite } from "./data";
import { MobileNavigation } from "./MobileNavigation";
import { Navigation } from "./Navigation";
import { ReadingLink } from "./ReadingLink";

export async function BlogShell({
  children,
  category,
  tag,
  query,
}: {
  children: ReactNode;
  category?: string;
  tag?: string;
  query?: string;
}) {
  const [site, navigation] = await Promise.all([
    getBlogSite(),
    getBlogNavigation(),
  ]);
  const nav = (
    <Navigation {...navigation} category={category} tag={tag} query={query} />
  );
  const brand = (
    <ReadingLink
      href="/"
      className="flex min-w-0 items-center gap-3 text-card-title font-semibold [overflow-wrap:anywhere]"
      aria-label={`${site.name}首页`}
    >
      {site.logo_url && (
        <Image
          src={site.logo_url}
          width={32}
          height={32}
          unoptimized
          alt=""
          className="shrink-0 rounded-control"
        />
      )}
      <span>{site.name}</span>
    </ReadingLink>
  );
  return (
    <div className="min-h-dvh lg:grid lg:grid-cols-[248px_minmax(0,1fr)]">
      <a
        href="#main-content"
        className="sr-only z-[60] rounded-control bg-card p-4 focus:not-sr-only focus:fixed focus:left-4 focus:top-4"
      >
        跳到正文
      </a>
      <aside className="sticky top-0 hidden h-dvh min-w-0 flex-col overflow-y-auto bg-sidebar px-5 py-8 lg:flex">
        <div className="mb-10 px-3">{brand}</div>
        {nav}
        <p className="mt-auto px-4 pt-12 text-meta text-muted-foreground">
          记录思考，分享所学。
        </p>
      </aside>
      <div className="min-w-0">
        <header className="flex min-h-16 items-center justify-between gap-4 border-b border-border bg-sidebar px-page py-3 lg:hidden">
          {brand}
          <MobileNavigation name={site.name}>{nav}</MobileNavigation>
        </header>
        <main
          id="main-content"
          tabIndex={-1}
          className="mx-auto w-full max-w-[1280px] min-w-0 px-page py-8 outline-none lg:py-10"
        >
          {children}
        </main>
        <footer className="mx-auto max-w-[1280px] px-page pb-8 text-meta text-muted-foreground">
          <div className="flex flex-wrap justify-between gap-3 border-t border-border pt-6">
            <span>{site.name}</span>
            <span>文字与时间，一起留下来。</span>
          </div>
        </footer>
      </div>
    </div>
  );
}
