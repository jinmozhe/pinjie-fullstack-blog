import type { IApi } from "@umijs/max";

export default function htmlAccessibility(api: IApi) {
  api.modifyHTML(($) => {
    $("html").attr("lang", "zh-CN");
    $('meta[name="viewport"]').attr("content", "width=device-width, initial-scale=1.0");
    return $;
  });
}
