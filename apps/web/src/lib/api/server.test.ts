import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const nextHeaders = vi.hoisted(() => ({ cookies: vi.fn() }));

vi.mock("next/headers", () => ({ cookies: nextHeaders.cookies }));

import { fetchAuthenticationState } from "./server";

const originalBackendURL = process.env.BACKEND_INTERNAL_URL;

describe("server authentication state", () => {
  beforeEach(() => {
    process.env.BACKEND_INTERNAL_URL = "http://backend.test";
    nextHeaders.cookies.mockResolvedValue({
      toString: () => "pinjie_blog_web_access=test-access; pinjie_blog_admin_access=admin-access; unrelated=value",
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    nextHeaders.cookies.mockReset();
    if (originalBackendURL === undefined) delete process.env.BACKEND_INTERNAL_URL;
    else process.env.BACKEND_INTERNAL_URL = originalBackendURL;
  });

  it("reports an authenticated user after the identity endpoint succeeds", async () => {
    const fetchMock = vi.fn().mockResolvedValue(Response.json({ data: { username: "test-user" } }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(fetchAuthenticationState()).resolves.toBe("authenticated");
    expect(fetchMock).toHaveBeenCalledWith(
      new URL("http://backend.test/api/v1/users/me"),
      expect.objectContaining({ headers: expect.objectContaining({ cookie: "pinjie_blog_web_access=test-access" }) }),
    );
    const [, init] = fetchMock.mock.calls[0] ?? [];
    expect((init?.headers as Record<string, string>).cookie).not.toContain("pinjie_blog_admin_access");
  });

  it("reports an anonymous visitor after the identity endpoint returns 401", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(null, { status: 401 })));

    await expect(fetchAuthenticationState()).resolves.toBe("anonymous");
  });

  it("reports an unavailable identity service for other HTTP failures", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(null, { status: 503 })));

    await expect(fetchAuthenticationState()).resolves.toBe("unavailable");
  });

  it("reports an unavailable identity service for network failures", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("connection failed")));

    await expect(fetchAuthenticationState()).resolves.toBe("unavailable");
  });
});
