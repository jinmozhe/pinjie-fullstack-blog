import { buttonVariants } from "@/components/ui/button";

export default function NotFound() {
  return (
    <main className="mx-auto flex min-h-dvh max-w-[720px] flex-col items-start justify-center px-page py-12">
      <p className="mb-4 text-meta text-muted-foreground">404</p>
      <h1 className="text-home-title font-semibold">页面不存在</h1>
      <p className="mt-4 leading-relaxed text-muted-foreground">
        这篇文章或页面暂不可访问，可以返回首页继续阅读。
      </p>
      <a href={String("/")} className={`${buttonVariants()} mt-8`}>
        返回首页
      </a>
    </main>
  );
}
