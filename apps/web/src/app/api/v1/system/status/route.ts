import { NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const backendURL = process.env.BACKEND_INTERNAL_URL;
  if (!backendURL) {
    return NextResponse.json(
      { code: "SERVICE_UNAVAILABLE", message: "后端服务尚未配置", request_id: request.headers.get("x-request-id") ?? "" },
      { status: 503 },
    );
  }
  try {
    const target = new URL("/api/v1/system/status", backendURL);
    const response = await fetch(target, { cache: "no-store", headers: { accept: "application/json" } });
    return new NextResponse(await response.text(), {
      status: response.status,
      headers: { "content-type": response.headers.get("content-type") ?? "application/json" },
    });
  } catch {
    return NextResponse.json(
      { code: "SERVICE_UNAVAILABLE", message: "后端服务不可用", request_id: request.headers.get("x-request-id") ?? "" },
      { status: 503 },
    );
  }
}
