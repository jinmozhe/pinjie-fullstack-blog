"use client";

export default function GlobalError() {
  return (
    <html lang="zh-CN">
      <body>
        <main
          style={{
            maxWidth: 720,
            margin: "12vh auto",
            padding: 24,
            fontFamily: "system-ui, sans-serif",
            lineHeight: 1.8,
          }}
        >
          <h1>暂时无法读取站点</h1>
          <p>服务暂时不可用，请稍后重新加载。当前网址中的查询条件会保留。</p>
          <button
            type="button"
            style={{ padding: "12px 20px" }}
            onClick={() => window.location.reload()}
          >
            重新加载
          </button>
        </main>
      </body>
    </html>
  );
}
