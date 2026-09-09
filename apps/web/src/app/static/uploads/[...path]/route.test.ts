import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { GET } from "./route";

const context = (path: string[]) => ({ params: Promise.resolve({ path }) });

describe("uploaded asset proxy", () => {
  const fetchMock = vi.fn<typeof fetch>();

  beforeEach(() => {
    vi.stubEnv("BACKEND_INTERNAL_URL", "http://backend.test");
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    fetchMock.mockReset();
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
  });

  it("proxies a generated asset key and preserves safe content headers", async () => {
    fetchMock.mockResolvedValue(
      new Response("image", { status: 200, headers: { "content-type": "image/png", etag: "asset-etag" } }),
    );
    const response = await GET(
      new Request("http://127.0.0.1:3100/static/uploads/avatar/20260825/hash.png"),
      context(["avatar", "20260825", "hash.png"]),
    );

    expect(response.status).toBe(200);
    expect(response.headers.get("content-type")).toBe("image/png");
    expect(response.headers.get("x-content-type-options")).toBe("nosniff");
    const [target, init] = fetchMock.mock.calls[0] ?? [];
    expect(String(target)).toBe("http://backend.test/static/uploads/avatar/20260825/hash.png");
    expect(init).toEqual({ cache: "no-store", redirect: "manual" });
  });

  it("rejects invalid asset keys before contacting the backend", async () => {
    const response = await GET(
      new Request("http://127.0.0.1:3100/static/uploads/avatar/file.png"),
      context(["avatar", "file.png"]),
    );

    expect(response.status).toBe(404);
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
