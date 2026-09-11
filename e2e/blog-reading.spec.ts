import { expect, test } from "@playwright/test";

import { expectPageQuality, uniqueUsername } from "./helpers";

test("public article, taxonomy, search and metadata disappear after hiding", async ({
  page,
  request,
}) => {
  test.skip(
    !test.info().project.name.startsWith("web"),
    "仅在公开 Web 项目执行",
  );
  const adminOrigin = process.env.E2E_ADMIN_ORIGIN ?? "http://127.0.0.1:3101";
  const suffix = uniqueUsername("reading", test.info().project.name);
  const login = await request.post(`${adminOrigin}/api/v1/admin/auth/login`, {
    headers: { Origin: adminOrigin },
    data: {
      username: process.env.E2E_ADMIN_USERNAME ?? "stage-admin",
      password: process.env.E2E_ADMIN_PASSWORD ?? "stage-c-admin-password-2026",
    },
  });
  expect(login.ok()).toBe(true);
  const csrf = (await request.storageState()).cookies.find(
    (cookie) => cookie.name === "pinjie_blog_admin_csrf",
  )?.value;
  expect(csrf).toBeTruthy();
  const headers = { Origin: adminOrigin, "X-CSRF-Token": csrf! };
  const createCategory = await request.post(
    `${adminOrigin}/api/v1/admin/blog/categories`,
    { headers, data: { name: suffix, slug: suffix } },
  );
  expect(createCategory.ok()).toBe(true);
  const category = (await createCategory.json()).data;
  const createTag = await request.post(
    `${adminOrigin}/api/v1/admin/blog/tags`,
    { headers, data: { name: suffix, slug: suffix } },
  );
  expect(createTag.ok()).toBe(true);
  const tag = (await createTag.json()).data;
  const createPost = await request.post(
    `${adminOrigin}/api/v1/admin/blog/posts`,
    {
      headers,
      data: {
        title: suffix,
        slug: suffix,
        summary: "公开阅读摘要",
        markdown: "## 阅读正文\n\n仅正文关键词，不能用于标题摘要搜索。",
        category_id: category.id,
        tag_ids: [tag.id],
      },
    },
  );
  expect(createPost.ok()).toBe(true);
  let post = (await createPost.json()).data;
  try {
    const response = await page.goto(`/posts/${suffix}`);
    expect(response?.status()).toBe(200);
    await expect(
      page.getByRole("heading", { name: suffix, exact: true }),
    ).toBeVisible();
    await expect(page.locator('meta[name="description"]')).toHaveAttribute(
      "content",
      "公开阅读摘要",
    );
    await expect(page.locator('link[rel="canonical"]')).toHaveAttribute(
      "href",
      new RegExp(`/posts/${suffix}$`),
    );
    await expectPageQuality(page);
    for (const kind of ["categories", "tags"]) {
      await page.goto(`/${kind}/${suffix}`);
      await expect(
        page.getByRole("heading", { name: suffix, exact: true, level: 1 }),
      ).toBeVisible();
      await expect(page.locator('link[rel="canonical"]')).toHaveAttribute(
        "href",
        new RegExp(`/${kind}/${suffix}$`),
      );
      await expect(
        page.locator(`main a[href="/posts/${suffix}"]`),
      ).toBeVisible();
    }
    await page.goto(`/search?q=${suffix}`);
    await expect(page.locator(`main a[href="/posts/${suffix}"]`)).toBeVisible();
    await expect(page.locator('meta[name="robots"]')).toHaveAttribute(
      "content",
      /noindex/,
    );
    const hide = await request.patch(
      `${adminOrigin}/api/v1/admin/blog/posts/${post.id}/status`,
      { headers, data: { revision: post.revision, status: "hidden" } },
    );
    expect(hide.ok()).toBe(true);
    post = (await hide.json()).data;
    for (const path of [
      `/posts/${suffix}`,
      `/categories/${suffix}`,
      `/tags/${suffix}`,
    ]) {
      const hidden = await page.goto(path);
      expect(hidden?.status()).toBe(404);
      await expect(
        page.getByRole("heading", { name: "页面不存在" }),
      ).toBeVisible();
      await expect(
        page.locator('meta[name="description"]'),
      ).not.toHaveAttribute("content", "公开阅读摘要");
    }
    await page.goto(`/search?q=${suffix}`);
    await expect(
      page.getByRole("heading", { name: "没有找到匹配的文章" }),
    ).toBeVisible();
  } finally {
    const remove = await request.delete(
      `${adminOrigin}/api/v1/admin/blog/posts/${post.id}?revision=${post.revision}`,
      { headers },
    );
    expect(remove.ok()).toBe(true);
    for (const [kind, id] of [
      ["categories", category.id],
      ["tags", tag.id],
    ]) {
      const impact = await request.post(
        `${adminOrigin}/api/v1/admin/blog/${kind}/delete-impact`,
        { headers, data: { target_ids: [id] } },
      );
      expect(impact.ok()).toBe(true);
      const confirmation = (await impact.json()).data.confirmation;
      const deleted = await request.post(
        `${adminOrigin}/api/v1/admin/blog/${kind}/delete-batch`,
        { headers, data: { target_ids: [id], confirmation } },
      );
      expect(deleted.ok()).toBe(true);
    }
  }
});
