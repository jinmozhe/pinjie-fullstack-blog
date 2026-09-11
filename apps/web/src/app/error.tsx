"use client";

import { Button } from "@/components/ui/button";

export default function ErrorPage({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="mx-auto flex min-h-dvh max-w-[720px] flex-col items-start justify-center px-page py-12">
      <div role="alert">
        <p className="mb-4 text-meta text-error-foreground">加载失败</p>
        <h1 className="text-home-title font-semibold">暂时无法读取内容</h1>
        <p className="mt-4 leading-relaxed text-muted-foreground">
          服务暂时不可用。当前网址中的搜索和分页条件已保留，请稍后重试。
        </p>
      </div>
      <Button type="button" className="mt-8" onClick={reset}>
        重新加载
      </Button>
    </main>
  );
}
