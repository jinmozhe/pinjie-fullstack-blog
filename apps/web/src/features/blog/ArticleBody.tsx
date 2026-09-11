"use client";

import { useEffect, useRef } from "react";

export function ArticleBody({ html }: { html: string }) {
  const container = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const root = container.current;
    if (!root) return;
    for (const [index, node] of root.querySelectorAll("pre, table").entries()) {
      node.setAttribute("tabindex", "0");
      node.setAttribute(
        "aria-label",
        `${node.tagName === "PRE" ? "代码块" : "表格"} ${index + 1}，可横向滚动`,
      );
    }
  }, [html]);
  // HTML comes exclusively from the backend's shared Markdown renderer with raw HTML disabled.
  return (
    <div
      ref={container}
      className="article-prose"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
