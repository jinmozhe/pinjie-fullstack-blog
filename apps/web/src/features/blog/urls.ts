export type ReadingSearchParams = Record<string, string | string[] | undefined>;

export function pageNumber(
  value: string | string[] | undefined,
): number | null {
  if (value === undefined) return 1;
  if (typeof value !== "string" || !/^[1-9]\d{0,6}$/.test(value)) return null;
  const page = Number(value);
  return page <= 1000000 ? page : null;
}

export function listUrl(path: string, page: number, query = ""): string {
  const params = new URLSearchParams();
  if (query) params.set("q", query);
  if (page > 1) params.set("page", String(page));
  const suffix = params.toString();
  return suffix ? `${path}?${suffix}` : path;
}

export function formatPublished(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    timeZone: "Asia/Shanghai",
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(new Date(value));
}

export function serializeJsonLd(value: unknown): string {
  return JSON.stringify(value)
    .replace(/</g, "\\u003c")
    .replace(/\u2028/g, "\\u2028")
    .replace(/\u2029/g, "\\u2029");
}
