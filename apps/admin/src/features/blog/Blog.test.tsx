import type { AdminRead, PostCreate, TaxonomyImpact, TaxonomyRead } from "@pinjie/api-client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { ConfigProvider } from "antd";
import zhCN from "antd/locale/zh_CN";
import { http, HttpResponse } from "msw";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";

import { AdminContext } from "@/features/auth";
import { server } from "@/test/setup";

import PostEditorPage from "./PostEditorPage";
import { TaxonomyPage } from "./TaxonomyPage";
import { formatBlogTime } from "./time";

const { push, block } = vi.hoisted(() => ({ push: vi.fn(), block: vi.fn(() => vi.fn()) }));
vi.mock("@umijs/max", () => ({ history: { push, block }, useParams: () => ({}) }));
const base = "http://127.0.0.1:3101/api/v1/admin/blog";
const principal: AdminRead = { id: "01900000-0000-7000-8000-000000000001", username: "blog-admin", display_name: "管理员", is_active: true, is_superuser: true, roles: [], permissions: [], created_at: "2026-09-09T00:00:00Z", updated_at: "2026-09-09T00:00:00Z" };
const category: TaxonomyRead = { id: "01900000-0000-7000-8000-000000000002", name: "日常", slug: "daily", revision: 1, created_at: "2026-09-09T00:00:00Z", updated_at: "2026-09-09T00:00:00Z" };
const envelope = <T,>(data: T) => HttpResponse.json({ code: "OK", message: "成功", request_id: "blog-test", data });

function mount(children: ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(<ConfigProvider locale={zhCN}><QueryClientProvider client={client}><AdminContext.Provider value={principal}>{children}</AdminContext.Provider></QueryClientProvider></ConfigProvider>);
}

function emptyTaxonomy() {
  server.use(http.get(`${base}/categories`, () => envelope({ items: [], page: 1, page_size: 100, total: 0, total_pages: 0 })), http.get(`${base}/tags`, () => envelope({ items: [], page: 1, page_size: 100, total: 0, total_pages: 0 })));
}

describe("博客写作", () => {
  it("发布失败保留所有输入，编辑输入不会自动保存", async () => {
    emptyTaxonomy();
    const submitted: PostCreate[] = [];
    server.use(http.post(`${base}/posts`, async ({ request }) => {
      submitted.push(await request.json() as PostCreate);
      return HttpResponse.json({ code: "BLOG_IDENTITY_CONFLICT", message: "网址标识已被占用" }, { status: 409 });
    }));
    mount(<PostEditorPage />);
    fireEvent.change(screen.getByLabelText("标题"), { target: { value: "我的文章" } });
    fireEvent.change(screen.getByLabelText("文章网址标识"), { target: { value: "my-post" } });
    fireEvent.change(screen.getByLabelText("正文"), { target: { value: "# 正文\n\n保留这段文字" } });
    expect(submitted).toHaveLength(0);
    fireEvent.click(screen.getByRole("button", { name: /发布/ }));
    await waitFor(() => expect(submitted).toHaveLength(1));
    expect(await screen.findAllByText("网址标识已被占用")).not.toHaveLength(0);
    expect(screen.getByLabelText("正文")).toHaveValue("# 正文\n\n保留这段文字");
    expect(screen.getByLabelText("标题")).toHaveValue("我的文章");
  });

  it("分类删除预览和取消不删除，失败时保留原确认内容", async () => {
    let deletes = 0;
    const impact: TaxonomyImpact = { targets: [category], affected_posts: 3, confirmation: "a".repeat(64) };
    server.use(
      http.get(`${base}/categories`, () => envelope({ items: [category], page: 1, page_size: 20, total: 1, total_pages: 1 })),
      http.post(`${base}/categories/delete-impact`, () => envelope(impact)),
      http.post(`${base}/categories/delete-batch`, () => { deletes += 1; return HttpResponse.json({ code: "BLOG_DELETE_IMPACT_CHANGED", message: "受影响文章已变化，请重新确认" }, { status: 412 }); }),
    );
    mount(<TaxonomyPage kind="categories" />);
    await screen.findByText("日常");
    fireEvent.click(screen.getByRole("button", { name: /删除/ }));
    let dialog = await screen.findByRole("dialog");
    expect(within(dialog).getByText(/影响 3 篇文章/)).toBeInTheDocument();
    expect(deletes).toBe(0);
    fireEvent.click(within(dialog).getByRole("button", { name: /取消/ }));
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect(deletes).toBe(0);
    fireEvent.click(screen.getByRole("button", { name: /删除/ }));
    dialog = await screen.findByRole("dialog");
    fireEvent.click(within(dialog).getByRole("button", { name: /确定/ }));
    await screen.findByText("受影响文章已变化，请重新确认");
    expect(within(dialog).getByText(/影响 3 篇文章/)).toBeInTheDocument();
    expect(deletes).toBe(1);
  });

  it("时间显示固定为北京时间", () => {
    expect(formatBlogTime("2026-09-08T16:30:00Z")).toContain("2026年9月9日");
    expect(formatBlogTime("2026-09-08T16:30:00Z")).toContain("00:30");
  });
});
