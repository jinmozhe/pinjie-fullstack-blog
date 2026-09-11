export function publicOrigin(): URL {
  const value = process.env.WEB_PUBLIC_ORIGIN;
  if (!value) throw new Error("Web 公开地址尚未配置");
  const url = new URL(value);
  if (
    !["http:", "https:"].includes(url.protocol) ||
    url.username ||
    url.password ||
    url.pathname !== "/" ||
    url.search ||
    url.hash
  ) {
    throw new Error("Web 公开地址配置无效");
  }
  return url;
}
