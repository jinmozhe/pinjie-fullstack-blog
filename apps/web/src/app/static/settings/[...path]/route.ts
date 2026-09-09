import { NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const LOGO_PATHS = new Set(["site/logo.png", "site/logo.jpg", "site/logo.webp"]);

async function proxy(request: Request, context: { params: Promise<{ path: string[] }> }) {
  const backendURL = process.env.BACKEND_INTERNAL_URL;
  if (!backendURL) return NextResponse.json({ message: "后端服务尚未配置" }, { status: 503 });
  const { path } = await context.params;
  const fileKey = path.join("/");
  if (!LOGO_PATHS.has(fileKey)) return NextResponse.json({ message: "文件不存在" }, { status: 404 });

  const source = new URL(request.url);
  const revision = source.searchParams.get("v");
  if (source.searchParams.size !== 1 || !revision || !/^[1-9]\d*$/.test(revision)) {
    return NextResponse.json({ message: "文件不存在" }, { status: 404 });
  }
  const target = new URL(`/static/settings/${fileKey}${source.search}`, backendURL);
  try {
    const response = await fetch(target, { cache: "no-store", redirect: "manual" });
    const headers = new Headers();
    for (const name of ["cache-control", "content-length", "content-type", "etag", "last-modified"]) {
      const value = response.headers.get(name);
      if (value && name !== "cache-control") headers.set(name, value);
    }
    headers.set("Cache-Control", "public, max-age=31536000, immutable");
    headers.set("X-Content-Type-Options", "nosniff");
    return new NextResponse(response.body, { status: response.status, headers });
  } catch {
    return NextResponse.json({ message: "站点媒体服务不可用" }, { status: 503 });
  }
}

export const GET = proxy;
export const HEAD = proxy;
