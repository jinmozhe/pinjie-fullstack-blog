import { afterEach, describe, expect, it, vi } from "vitest";

import { adminApi } from "./admin";

const targetId = "01900000-0000-7000-8000-000000000041";

describe("admin API request shapes", () => {
  afterEach(() => vi.restoreAllMocks());

  it("sends uploads and uncovered bulk lifecycle requests", async () => {
    const bodies: Record<string, unknown> = {};
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.endsWith("/api/v1/assets/upload")) {
        const form = init?.body as globalThis.FormData;
        bodies.uploadScene = form.get("scene");
        bodies.uploadFile = form.get("file");
      } else if (url.endsWith("/api/v1/admin/settings/site/logo")) {
        const form = init?.body as globalThis.FormData;
        bodies.siteLogoRevision = form.get("revision");
        bodies.siteLogoFile = form.get("file");
      } else if (url.endsWith("/api/v1/admin/users/status/batch")) {
        bodies.userStatus = JSON.parse(String(init?.body));
      } else if (url.endsWith(`/api/v1/admin/users/${targetId}/restore`)) {
        bodies.restoredUserId = targetId;
      } else if (url.endsWith("/api/v1/admin/roles/status/batch")) {
        bodies.roleStatus = JSON.parse(String(init?.body));
      }
      return new Response(JSON.stringify({
        code: "OK",
        message: "操作成功",
        data: { id: targetId, completed_count: 1, target_ids: [targetId] },
        request_id: "api-test",
      }), { status: 200, headers: { "Content-Type": "application/json" } });
    });

    const file = new globalThis.File(["png"], "avatar.png", { type: "image/png" });
    await adminApi.uploadAsset(file);
    await adminApi.uploadSiteLogo(file, 7);
    await adminApi.setUserStatusBulk({ user_ids: [targetId], is_active: false });
    await adminApi.restoreUser(targetId);
    await adminApi.setRoleStatusBulk({ role_ids: [targetId], is_active: false });

    expect(bodies.uploadScene).toBe("avatar");
    expect(bodies.uploadFile).toBeInstanceOf(globalThis.File);
    expect(bodies.siteLogoRevision).toBe("7");
    expect(bodies.siteLogoFile).toBeInstanceOf(globalThis.File);
    expect(bodies.userStatus).toEqual({ user_ids: [targetId], is_active: false });
    expect(bodies.restoredUserId).toBe(targetId);
    expect(bodies.roleStatus).toEqual({ role_ids: [targetId], is_active: false });
  });
});
