import type { TaxonomyRead } from "@pinjie/api-client";
import { useInfiniteQuery } from "@tanstack/react-query";
import { Alert, Button, Select } from "antd";

import { blogApi, type TaxonomyKind } from "@/lib/api/blog";
import { errorMessage } from "@/lib/api/http";

type Props = {
  kind: TaxonomyKind;
  value?: string | string[] | null;
  onChange?: (value: string | string[] | undefined) => void;
  multiple?: boolean;
  disabled?: boolean;
  label?: string;
  selectedOptions?: TaxonomyRead[];
};

export function TaxonomySelect({ kind, value, onChange, multiple, disabled, label, selectedOptions = [] }: Props) {
  const query = useInfiniteQuery({
    queryKey: ["blog", kind, "options"],
    initialPageParam: 1,
    queryFn: ({ pageParam }) => blogApi.taxonomy(kind, pageParam, 100),
    getNextPageParam: (last) => last.page < last.total_pages ? last.page + 1 : undefined,
    enabled: !disabled,
  });
  const options = new Map(selectedOptions.map((item) => [item.id, item]));
  for (const page of query.data?.pages ?? []) for (const item of page.items) options.set(item.id, item);
  return <div className="blog-taxonomy-select">
    <Select
      aria-label={label ?? (kind === "categories" ? "分类" : "标签")}
      allowClear showSearch optionFilterProp="label" disabled={disabled}
      mode={multiple ? "multiple" : undefined} maxCount={multiple ? 20 : undefined}
      placeholder={kind === "categories" ? "可不选分类" : "可不选标签"}
      value={value ?? undefined} onChange={onChange} loading={query.isFetching}
      options={Array.from(options.values(), (item) => ({ label: item.name, value: item.id }))}
      onPopupScroll={(event) => {
        const target = event.currentTarget;
        if (target.scrollTop + target.clientHeight >= target.scrollHeight - 24 && query.hasNextPage && !query.isFetching) void query.fetchNextPage();
      }}
      popupRender={(menu) => <>{menu}{query.hasNextPage && <Button block type="link" loading={query.isFetchingNextPage} onClick={() => void query.fetchNextPage()}>加载更多</Button>}</>}
    />
    {query.isError && <Alert type="error" showIcon title={errorMessage(query.error)} action={<Button onClick={() => void query.refetch()}>重试</Button>} />}
  </div>;
}
