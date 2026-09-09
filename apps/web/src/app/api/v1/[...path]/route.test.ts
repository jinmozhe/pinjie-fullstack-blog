import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { DELETE, GET, PATCH, POST, PUT } from "./route";

const context = (path: string[]) => ({ params: Promise.resolve({ path }) });
const proxyHandlers = { DELETE, GET, PATCH, POST, PUT };
const sessionId = "01900000-0000-7000-8000-000000000003";
type BrowserApiRoute = { method: keyof typeof proxyHandlers; path: readonly string[]; query?: string };

const browserApiRoutes: readonly BrowserApiRoute[] = [
  { method: "GET", path: ["system", "site-profile"] },
  { method: "POST", path: ["auth", "register"] },
  { method: "POST", path: ["auth", "login"] },
  { method: "POST", path: ["auth", "refresh"] },
  { method: "POST", path: ["auth", "logout"] },
  { method: "POST", path: ["assets", "upload"] },
  { method: "GET", path: ["users", "me"] },
  { method: "PATCH", path: ["users", "me"] },
  { method: "DELETE", path: ["users", "me"] },
  { method: "PUT", path: ["users", "me", "avatar"] },
  { method: "POST", path: ["users", "me", "password"] },
  { method: "GET", path: ["users", "me", "sessions"], query: "?page=1&page_size=100" },
  { method: "DELETE", path: ["users", "me", "sessions", sessionId] },
  { method: "POST", path: ["users", "me", "sessions", "revoke-others"] },
];

describe("Web API profile proxy", () => {
  const fetchMock = vi.fn<typeof fetch>();

  beforeEach(() => {
    vi.stubEnv("BACKEND_INTERNAL_URL", "http://backend.test");
    vi.stubEnv("WEB_PUBLIC_ORIGIN", "http://127.0.0.1:3100");
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    fetchMock.mockReset();
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
  });

  it("rejects admin API paths before contacting the backend", async () => {
    const response = await GET(
      new Request("http://127.0.0.1:3100/api/v1/admin/auth/me"),
      context(["admin", "auth", "me"]),
    );

    expect(response.status).toBe(404);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it.each(browserApiRoutes)("forwards Web browser API $method $path", async ({ method, path, query = "" }) => {
    fetchMock.mockResolvedValue(new Response(null, { status: 204 }));
    const routePath = [...path];
    const requestInit: RequestInit = {
      method,
      headers: method === "GET" ? undefined : { origin: "http://127.0.0.1:3100" },
    };
    if (!["GET", "HEAD"].includes(method)) requestInit.body = "{}";

    const response = await proxyHandlers[method](
      new Request(`http://127.0.0.1:3100/api/v1/${routePath.join("/")}${query}`, requestInit),
      context(routePath),
    );

    expect(response.status).toBe(204);
    expect(fetchMock).toHaveBeenCalledOnce();
    const [target] = fetchMock.mock.calls[0] ?? [];
    expect(String(target)).toBe(`http://backend.test/api/v1/${routePath.join("/")}${query}`);
  });

  it("rejects unsafe requests from another origin", async () => {
    const response = await POST(
      new Request("http://127.0.0.1:3100/api/v1/auth/login", {
        method: "POST",
        headers: { origin: "http://127.0.0.1:3101" },
        body: JSON.stringify({ username: "user", password: "secret" }),
      }),
      context(["auth", "login"]),
    );

    expect(response.status).toBe(403);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("fails closed when the authoritative Web origin is missing", async () => {
    vi.stubEnv("WEB_PUBLIC_ORIGIN", "");
    const response = await POST(
      new Request("http://127.0.0.1:3100/api/v1/auth/login", {
        method: "POST",
        headers: { origin: "http://127.0.0.1:3100" },
        body: JSON.stringify({ username: "user", password: "secret" }),
      }),
      context(["auth", "login"]),
    );

    expect(response.status).toBe(503);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("forwards only Web profile cookies for an allowed route", async () => {
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify({ code: "OK", data: { username: "user" } }), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );

    const response = await GET(
      new Request("http://127.0.0.1:3100/api/v1/users/me", {
        headers: {
          cookie: "pinjie_blog_web_access=web-access; pinjie_blog_admin_access=admin-access; other=value; pinjie_blog_web_csrf=web-csrf",
        },
      }),
      context(["users", "me"]),
    );

    expect(response.status).toBe(200);
    expect(fetchMock).toHaveBeenCalledOnce();
    const [, init] = fetchMock.mock.calls[0] ?? [];
    const headers = new Headers(init?.headers);
    expect(headers.get("cookie")).toBe("pinjie_blog_web_access=web-access; pinjie_blog_web_csrf=web-csrf");
    expect(headers.get("cookie")).not.toContain("pinjie_blog_admin_access");
  });

  it("allows only UUID session deletion paths", async () => {
    fetchMock.mockResolvedValue(new Response(null, { status: 204 }));
    const allowed = await DELETE(
      new Request(`http://127.0.0.1:3100/api/v1/users/me/sessions/${sessionId}`, {
        method: "DELETE",
        headers: { origin: "http://127.0.0.1:3100" },
      }),
      context(["users", "me", "sessions", sessionId]),
    );
    const rejected = await DELETE(
      new Request("http://127.0.0.1:3100/api/v1/users/me/sessions/not-a-uuid", {
        method: "DELETE",
        headers: { origin: "http://127.0.0.1:3100" },
      }),
      context(["users", "me", "sessions", "not-a-uuid"]),
    );

    expect(allowed.status).toBe(204);
    expect(rejected.status).toBe(404);
    expect(fetchMock).toHaveBeenCalledOnce();
  });

  it("streams an allowed multipart asset upload", async () => {
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify({ code: "OK", data: { url: "/static/uploads/avatar/test.png" } }), {
        status: 201,
        headers: { "content-type": "application/json" },
      }),
    );
    const boundary = "pinjie-test-boundary";
    const body = [
      `--${boundary}`,
      'Content-Disposition: form-data; name="scene"',
      "",
      "avatar",
      `--${boundary}`,
      'Content-Disposition: form-data; name="file"; filename="avatar.png"',
      "Content-Type: image/png",
      "",
      "png",
      `--${boundary}--`,
      "",
    ].join("\r\n");

    const response = await POST(
      new Request("http://127.0.0.1:3100/api/v1/assets/upload", {
        method: "POST",
        headers: {
          cookie: "pinjie_blog_web_access=web-access; pinjie_blog_admin_access=admin-access; pinjie_blog_web_csrf=web-csrf",
          "content-type": `multipart/form-data; boundary=${boundary}`,
          origin: "http://127.0.0.1:3100",
          "x-csrf-token": "web-csrf",
        },
        body,
      }),
      context(["assets", "upload"]),
    );

    expect(response.status).toBe(201);
    const [target, init] = fetchMock.mock.calls[0] ?? [];
    expect(String(target)).toBe("http://backend.test/api/v1/assets/upload");
    expect(new Headers(init?.headers).get("content-type")).toContain("multipart/form-data");
    expect((init as RequestInit & { duplex?: string })?.duplex).toBe("half");
  });
});
