import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { GET } from "./route";

const context = (path: string[]) => ({ params: Promise.resolve({ path }) });

describe("settings media proxy", () => {
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

  it("proxies the fixed site logo with immutable revision caching", async () => {
    fetchMock.mockResolvedValue(new Response("image", { status: 200, headers: { "content-type": "image/png" } }));

    const response = await GET(
      new Request("http://127.0.0.1:3100/static/settings/site/logo.png?v=3"),
      context(["site", "logo.png"]),
    );

    expect(response.status).toBe(200);
    expect(response.headers.get("cache-control")).toBe("public, max-age=31536000, immutable");
    const [target] = fetchMock.mock.calls[0] ?? [];
    expect(String(target)).toBe("http://backend.test/static/settings/site/logo.png?v=3");
  });

  it("rejects unknown paths and missing revisions", async () => {
    const unknown = await GET(
      new Request("http://127.0.0.1:3100/static/settings/site/banner.png?v=1"),
      context(["site", "banner.png"]),
    );
    const unversioned = await GET(
      new Request("http://127.0.0.1:3100/static/settings/site/logo.png"),
      context(["site", "logo.png"]),
    );

    expect(unknown.status).toBe(404);
    expect(unversioned.status).toBe(404);
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
