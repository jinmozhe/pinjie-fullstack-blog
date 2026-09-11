import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ArticleCard } from "./ArticleCard";
import { ArticlePagination } from "./ArticlePagination";
import { MobileNavigation } from "./MobileNavigation";
import { Navigation } from "./Navigation";
import { ReadingLink } from "./ReadingLink";
import { formatPublished, listUrl, pageNumber, serializeJsonLd } from "./urls";

describe("公开阅读组件", () => {
  it("keeps title, taxonomy links and a missing cover independent", () => {
    const { container } = render(
      <ArticleCard
        post={{
          title: "很长的文章标题",
          slug: "article",
          summary: "摘要",
          category: { name: "分类", slug: "category" },
          tags: [{ name: "标签", slug: "tag" }],
          cover_url: null,
          published_at: "2026-09-10T18:00:00Z",
          updated_at: "2026-09-10T18:00:00Z",
        }}
      />,
    );
    expect(
      screen.getByRole("link", { name: "很长的文章标题" }),
    ).toHaveAttribute("href", "/posts/article");
    expect(screen.getByRole("link", { name: "分类" })).toHaveAttribute(
      "href",
      "/categories/category",
    );
    expect(screen.getByRole("link", { name: "标签" })).toHaveAttribute(
      "href",
      "/tags/tag",
    );
    expect(container.querySelector("a a, a button")).toBeNull();
    expect(container.querySelector("img")).toBeNull();
    expect(screen.getByText("2026年9月11日")).toBeVisible();
  });

  it("retains all tags and the submitted search term", () => {
    render(
      <Navigation
        categories={[]}
        tags={[{ name: "中文标签", slug: "chinese", post_count: 1 }]}
        tag="chinese"
        query="搜索词"
      />,
    );
    expect(screen.getByRole("searchbox")).toHaveValue("搜索词");
    expect(screen.getByRole("link", { name: "中文标签" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(screen.getByRole("navigation", { name: "全部标签" })).toBeVisible();
  });

  it("keeps queries when paging and disables unavailable previous navigation", () => {
    render(
      <ArticlePagination
        page={1}
        totalPages={3}
        path="/search"
        query="中文 & 空格"
      />,
    );
    expect(screen.queryByRole("link", { name: "上一页" })).toBeNull();
    const url = new URL(
      screen.getByRole("link", { name: "下一页" }).getAttribute("href") ?? "",
      "http://localhost",
    );
    expect(url.searchParams.get("q")).toBe("中文 & 空格");
    expect(url.searchParams.get("page")).toBe("2");
  });

  it("names the mobile dialog, closes on Escape and restores focus", async () => {
    vi.stubGlobal("matchMedia", () => ({
      matches: false,
      addEventListener() {},
      removeEventListener() {},
    }));
    try {
      const user = userEvent.setup();
      render(
        <MobileNavigation name="测试博客">
          <ReadingLink href="/">全部文章</ReadingLink>
        </MobileNavigation>,
      );
      const trigger = screen.getByRole("button", { name: "打开导航" });
      await user.click(trigger);
      expect(screen.getByRole("dialog", { name: "测试博客" })).toBeVisible();
      await user.keyboard("{Escape}");
      expect(screen.queryByRole("dialog")).toBeNull();
      expect(trigger).toHaveFocus();
    } finally {
      vi.unstubAllGlobals();
    }
  });
});

describe("阅读地址与安全元信息", () => {
  it("rejects invalid pages instead of silently changing the requested page", () => {
    expect(pageNumber(undefined)).toBe(1);
    for (const value of ["0", "-1", "1.2", "01", "1000001", ["1", "2"]])
      expect(pageNumber(value)).toBeNull();
    expect(listUrl("/categories/python", 1)).toBe("/categories/python");
  });
  it("escapes script closing tags without corrupting structured data", () => {
    const original = { headline: "</script><script>alert(1)</script>\u2028" };
    const encoded = serializeJsonLd(original);
    expect(encoded).not.toContain("<");
    expect(JSON.parse(encoded)).toEqual(original);
  });
  it("uses the Shanghai calendar date", () => {
    expect(formatPublished("2026-09-10T18:00:00Z")).toBe("2026年9月11日");
  });
});
