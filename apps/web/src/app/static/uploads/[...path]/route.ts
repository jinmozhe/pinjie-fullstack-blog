import { NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const SEGMENT = /^[A-Za-z0-9._-]+$/;

async function proxy(_: Request, context: { params: Promise<{ path: string[] }> }) {
  const backendURL = process.env.BACKEND_INTERNAL_URL;
  if (!backendURL) return NextResponse.json({ message: "后端服务尚未配置" }, { status: 503 });
  const { path } = await context.params;
  if (path.length < 3 || path.some((segment) => !SEGMENT.test(segment) || segment === "." || segment === "..")) {
    return NextResponse.json({ message: "文件不存在" }, { status: 404 });
  }
  const target = new URL(`/static/uploads/${path.map(encodeURIComponent).join("/")}`, backendURL);
  try {
    const response = await fetch(target, { cache: "no-store", redirect: "manual" });
    const headers = new Headers();
    for (const name of ["cache-control", "content-length", "content-type", "etag", "last-modified"]) {
      const value = response.headers.get(name);
      if (value) headers.set(name, value);
    }
    headers.set("X-Content-Type-Options", "nosniff");
    return new NextResponse(response.body, { status: response.status, headers });
  } catch {
    return NextResponse.json({ message: "文件服务不可用" }, { status: 503 });
  }
}

export const GET = proxy;
export const HEAD = proxy;
