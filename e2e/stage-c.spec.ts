import { expect, test } from "@playwright/test";

import {
  expectCookieProfile,
  expectNoClientTokenPersistence,
  expectPageQuality,
  uniqueUsername,
} from "./helpers";

const adminUsername = process.env.E2E_ADMIN_USERNAME ?? "stage-admin";
const adminPassword =
  process.env.E2E_ADMIN_PASSWORD ?? "stage-c-admin-password-2026";
const limitedAdminPassword = "stage-c-limited-password-2026";
const avatarPng = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9WlKz50AAAAASUVORK5CYII=",
  "base64",
);

test.describe("stage C cross-stack journeys", () => {
  test("Web provides anonymous reading and closes reader account routes", async ({
    page,
  }) => {
    test.skip(
      !test.info().project.name.startsWith("web"),
      "Web journey runs in Web projects",
    );
    await page.goto("/");
    await expect(page.getByRole("main")).toBeVisible();
    await expect(page.getByRole("link", { name: "登录" })).toHaveCount(0);
    await expect(page.getByRole("link", { name: /用户中心/ })).toHaveCount(0);
    await expectNoClientTokenPersistence(page);
    await expectPageQuality(page);
    for (const path of ["/login", "/register", "/account"]) {
      const response = await page.goto(path);
      expect(response?.status()).toBe(404);
      await expect(
        page.getByRole("heading", { name: "页面不存在" }),
      ).toBeVisible();
    }
  });

  test("Admin records privileged work and rejects an administrator without permissions", async ({
    page,
    request,
  }) => {
    test.skip(
      !test.info().project.name.startsWith("admin"),
      "Admin journey runs in Admin projects",
    );
    const limitedUsername = uniqueUsername("limited", test.info().project.name);
    await page.goto("/login");
    const origin = new URL(page.url()).origin;
    const loginResponse = await request.post(
      `${origin}/api/v1/admin/auth/login`,
      {
        headers: { Origin: origin },
        data: { username: adminUsername, password: adminPassword },
      },
    );
    expect(loginResponse.ok()).toBe(true);
    expect(loginResponse.headers()["content-type"]).toContain(
      "application/json",
    );
    expect(JSON.stringify(await loginResponse.json())).not.toMatch(
      /access_token|refresh_token/i,
    );
    await page.getByLabel("用户名").fill(adminUsername);
    await page.getByLabel("密码").fill(adminPassword);
    await page.getByRole("button", { name: /登\s*录/ }).click();
    await expect(
      page.getByRole("heading", { name: "欢迎使用 Pinjie Console" }),
    ).toBeVisible();

    const csrf = await expectCookieProfile(page, {
      access: "pinjie_blog_admin_access",
      refresh: "pinjie_blog_admin_refresh",
      csrf: "pinjie_blog_admin_csrf",
    });
    await expectNoClientTokenPersistence(page);
    await page.goto("/users");
    await expect(page.getByRole("heading", { name: "用户管理" })).toBeVisible();
    await expectPageQuality(page);

    await page.goto("/account/settings");
    const uploadResponsePromise = page.waitForResponse(
      (response) =>
        response.url().endsWith("/api/v1/assets/upload") &&
        response.request().method() === "POST",
    );
    await page.locator('input[type="file"]').setInputFiles({
      name: "avatar.png",
      mimeType: "image/png",
      buffer: avatarPng,
    });
    const uploadResponse = await uploadResponsePromise;
    expect(uploadResponse.ok()).toBe(true);
    const uploadedAsset = (await uploadResponse.json()).data as { url: string };
    const avatarPreview = page
      .getByRole("tabpanel")
      .locator(`img[src="${uploadedAsset.url}"]`);
    await expect(avatarPreview).toBeVisible();

    const profileResponsePromise = page.waitForResponse(
      (response) =>
        response.url().endsWith("/api/v1/admin/auth/profile") &&
        response.request().method() === "PATCH",
    );
    await page.getByRole("button", { name: "更新基本信息" }).click();
    expect((await profileResponsePromise).ok()).toBe(true);
    await page.waitForLoadState("domcontentloaded");
    await expect(avatarPreview).toBeVisible();
    await page.reload();
    await expect(avatarPreview).toBeVisible();

    for (const assetOrigin of [origin, "http://127.0.0.1:3100"]) {
      const assetResponse = await page.request.get(
        `${assetOrigin}${uploadedAsset.url}`,
      );
      expect(assetResponse.ok()).toBe(true);
      expect(assetResponse.headers()["content-type"]).toBe("image/png");
      expect(assetResponse.headers()["x-content-type-options"]).toBe("nosniff");
      expect((await assetResponse.body()).byteLength).toBeGreaterThan(0);
    }
    await expectPageQuality(page);

    const commonHeaders = { Origin: origin, "X-CSRF-Token": csrf };
    const createResponse = await page.request.post(
      `${origin}/api/v1/admin/admins`,
      {
        headers: commonHeaders,
        data: {
          username: limitedUsername,
          initial_password: limitedAdminPassword,
          display_name: "Limited E2E Admin",
          is_active: true,
          is_superuser: false,
          role_ids: [],
        },
      },
    );
    expect(createResponse.ok()).toBe(true);

    await page.goto("/security");
    await page.getByRole("tab", { name: "审计事件" }).click();
    await expect(page.getByText("admins:create").first()).toBeVisible();

    const logoutResponse = await page.request.post(
      `${origin}/api/v1/admin/auth/logout`,
      {
        headers: commonHeaders,
      },
    );
    expect(logoutResponse.ok()).toBe(true);
    await page.goto("/login");
    await page.getByLabel("用户名").fill(limitedUsername);
    await page.getByLabel("密码").fill(limitedAdminPassword);
    await page.getByRole("button", { name: /登\s*录/ }).click();
    await expect(
      page.getByRole("heading", { name: "欢迎使用 Pinjie Console" }),
    ).toBeVisible();
    await page.goto("/users");
    await expect(page.getByText("无权访问")).toBeVisible();

    const deniedResponse = await page.request.get(
      `${origin}/api/v1/admin/users`,
    );
    expect(deniedResponse.status()).toBe(403);
    expect((await deniedResponse.json()).code).toBe("PERMISSION_DENIED");
    await expectNoClientTokenPersistence(page);
  });
});
