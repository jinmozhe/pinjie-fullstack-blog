import { Search } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function SearchForm({ query = "" }: { query?: string }) {
  return (
    <form action="/search" role="search" className="relative">
      <Input
        name="q"
        type="search"
        maxLength={100}
        defaultValue={query}
        aria-label="搜索文章标题和摘要"
        placeholder="搜索文章"
        className="rounded-pill pr-12 text-ui"
      />
      <Button
        type="submit"
        variant="ghost"
        size="icon"
        aria-label="搜索文章"
        className="absolute right-0 top-0 rounded-pill"
      >
        <Search aria-hidden="true" />
      </Button>
    </form>
  );
}
