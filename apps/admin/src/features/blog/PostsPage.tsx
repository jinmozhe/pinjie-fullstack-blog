import type { PostBatch, PostSummary } from "@pinjie/api-client";
import { DeleteOutlined, EditOutlined, PlusOutlined, UndoOutlined } from "@ant-design/icons";
import { ProFormDateRangePicker, ProTable } from "@ant-design/pro-components";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { history } from "@umijs/max";
import { Alert, Button, Form, Select, Space, Switch, Tabs, Tag, message } from "antd";
import { useRef, useState } from "react";

import { PageFrame, QueryState } from "@/components/PageFrame";
import { StandardConfirmModal } from "@/components/StandardConfirmModal";
import { canAccess, useCurrentAdmin } from "@/features/auth";
import { blogApi, type PostFilters } from "@/lib/api/blog";
import { errorMessage } from "@/lib/api/http";

import { TaxonomySelect } from "./TaxonomySelect";
import { formatBlogTime } from "./time";
import "./blog.css";

export default function PostsPage() {
  const current = useCurrentAdmin();
  const queryClient = useQueryClient();
  const [filters, setFilters] = useState<PostFilters>({ page: 1, page_size: 20, deleted: false });
  const [selected, setSelected] = useState<string[]>([]);
  const [confirmation, setConfirmation] = useState<PostBatch | null>(null);
  const operationLock = useRef(false);
  const canRead = canAccess(current, "posts:read");
  const canUpdate = canAccess(current, "posts:update");
  const canDelete = canAccess(current, "posts:delete");
  const canRestore = canAccess(current, "posts:restore");
  const query = useQuery({ queryKey: ["blog", "posts", filters], queryFn: () => blogApi.posts(filters), enabled: canRead });
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["blog"] });
  const lifecycle = useMutation({
    mutationFn: ({ action, input }: { action: "delete" | "restore"; input: PostBatch }) => blogApi.lifecycle(action, input),
    onSuccess: async (_, variables) => {
      message.success(variables.action === "delete" ? "文章已移入回收站" : "文章已恢复为隐藏，请确认后重新公开");
      setConfirmation(null); setSelected([]); await invalidate();
    },
  });
  const status = useMutation({
    mutationFn: (post: PostSummary) => blogApi.updateStatus(post.id, { revision: post.revision, status: post.status === "public" ? "hidden" : "public" }),
    onSuccess: async () => { message.success("文章状态已更新"); await invalidate(); },
  });
  const busy = lifecycle.isPending || status.isPending || Boolean(confirmation);
  const changeFilters = (values: Partial<PostFilters>) => { setFilters((old) => ({ ...old, ...values, page: 1 })); setSelected([]); };
  const batch = (rows: PostSummary[]): PostBatch => ({ targets: rows.map((row) => ({ id: row.id, revision: row.revision })) });
  const selectedBatch = () => batch((query.data?.items ?? []).filter((row) => selected.includes(row.id)));
  const restore = async (input: PostBatch) => {
    if (operationLock.current) return;
    operationLock.current = true;
    try { await lifecycle.mutateAsync({ action: "restore", input }); }
    catch (error) { message.error(errorMessage(error)); }
    finally { operationLock.current = false; }
  };
  const toggle = async (post: PostSummary) => {
    if (operationLock.current) return;
    operationLock.current = true;
    try { await status.mutateAsync(post); }
    catch (error) { message.error(errorMessage(error)); }
    finally { operationLock.current = false; }
  };
  if (!canRead) return <PageFrame title="文章管理" description="管理文章和回收站。"><Alert type="warning" title="没有查看权限" /></PageFrame>;
  return <PageFrame title="文章管理" description="发布时间与日期筛选均使用北京时间。回收站只提供恢复，恢复后保持隐藏。">
    <Tabs activeKey={filters.deleted ? "deleted" : "current"} onChange={(key) => changeFilters({ deleted: key === "deleted" })} items={[{ key: "current", label: "文章" }, { key: "deleted", label: "回收站" }]} />
    <div className="blog-filters">
      <Select aria-label="公开状态" allowClear placeholder="全部状态" value={filters.status ?? undefined} options={[{ value: "public", label: "公开" }, { value: "hidden", label: "隐藏" }]} onChange={(value: "public" | "hidden" | undefined) => changeFilters({ status: value })} />
      <TaxonomySelect kind="categories" disabled={!canAccess(current, "categories:read")} value={filters.category_id} onChange={(value) => changeFilters({ category_id: typeof value === "string" ? value : undefined })} />
      <TaxonomySelect kind="tags" disabled={!canAccess(current, "tags:read")} value={filters.tag_id} onChange={(value) => changeFilters({ tag_id: typeof value === "string" ? value : undefined })} />
      <div className="blog-date-range">
        <Form component={false} fields={[{ name: "publishedRange", value: [filters.published_from ?? null, filters.published_to ?? null] }]}>
          <ProFormDateRangePicker
            name="publishedRange"
            noStyle
            placeholder={["开始日期", "结束日期"]}
            fieldProps={{
              "aria-label": "发布日期范围（北京时间）",
              variant: "filled",
              format: "YYYY-MM-DD",
              allowEmpty: [true, true],
              style: { width: "100%" },
              onChange: (_, dates) => changeFilters({ published_from: dates[0] || undefined, published_to: dates[1] || undefined }),
            }}
          />
        </Form>
      </div>
      <Button onClick={() => { setFilters({ page: 1, page_size: 20, deleted: filters.deleted }); setSelected([]); }}>重置筛选</Button>
    </div>
    <QueryState loading={query.isLoading} error={query.isError ? errorMessage(query.error) : undefined} onRetry={() => void query.refetch()} />
    {query.data && <ProTable<PostSummary>
      rowKey="id" className="responsive-data-table" cardProps={false} search={false} headerTitle={filters.deleted ? "回收站文章列表" : "文章列表"}
      dataSource={query.data.items} loading={query.isFetching}
      tableLayout="auto"
      options={{ reload: () => void query.refetch(), density: true, setting: true, fullScreen: true }}
      pagination={{ current: filters.page ?? 1, pageSize: 20, total: query.data.total, showSizeChanger: false, onChange: (page) => { setFilters((old) => ({ ...old, page })); setSelected([]); } }}
      rowSelection={(filters.deleted ? canRestore : canDelete) ? { selectedRowKeys: selected, onChange: (keys) => setSelected(keys.map(String)), getCheckboxProps: () => ({ disabled: busy }) } : false}
      tableAlertOptionRender={() => filters.deleted
        ? <Button icon={<UndoOutlined />} loading={lifecycle.isPending} disabled={busy} onClick={() => void restore(selectedBatch())}>批量恢复</Button>
        : <Button danger icon={<DeleteOutlined />} disabled={busy} onClick={() => setConfirmation(selectedBatch())}>批量删除</Button>}
      toolBarRender={() => [!filters.deleted && canAccess(current, "posts:create") && <Button key="create" type="primary" icon={<PlusOutlined />} disabled={busy} onClick={() => history.push("/blog/posts/new")}>写文章</Button>]}
      columns={[
        { title: "标题", dataIndex: "title", ellipsis: true, onCell: () => ({ style: { minWidth: 120, maxWidth: 0 } }) },
        { title: "分类", render: (_, row) => row.category?.name ?? "无分类", ellipsis: true, width: "12%", onCell: () => ({ style: { minWidth: 80, maxWidth: 0 } }) },
        { title: "标签", ellipsis: true, width: "16%", onCell: () => ({ style: { minWidth: 80, maxWidth: 0 } }), render: (_, row) => row.tags.map((tag) => tag.name).join("、") || "无标签" },
        { title: "状态", width: "1%", render: (_, row) => filters.deleted || !canUpdate
          ? <Tag color={row.status === "public" ? "green" : "default"}>{row.status === "public" ? "公开" : "隐藏"}</Tag>
          : <Switch checked={row.status === "public"} checkedChildren="公开" unCheckedChildren="隐藏" aria-label={`${row.status === "public" ? "隐藏" : "公开"}文章：${row.title}`} disabled={busy} loading={status.isPending && status.variables?.id === row.id} onChange={() => void toggle(row)} /> },
        { title: "首次发布", width: "1%", render: (_, row) => formatBlogTime(row.published_at) },
        { title: "更新时间", width: "1%", render: (_, row) => formatBlogTime(row.updated_at) },
        { title: "操作", width: "1%", render: (_, row) => <Space className="table-actions" wrap={false}>
          {!filters.deleted && canUpdate && <Button type="link" icon={<EditOutlined />} disabled={busy} onClick={() => history.push(`/blog/posts/${row.id}/edit`)}>编辑</Button>}
          {!filters.deleted && canDelete && <Button type="link" danger icon={<DeleteOutlined />} disabled={busy} onClick={() => setConfirmation(batch([row]))}>删除</Button>}
          {filters.deleted && canRestore && <Button type="link" icon={<UndoOutlined />} disabled={busy} onClick={() => void restore(batch([row]))}>恢复</Button>}
        </Space> },
      ]}
    />}
    <StandardConfirmModal open={Boolean(confirmation)} title="将文章移入回收站" loading={lifecycle.isPending}
      description={`将所选 ${confirmation?.targets.length ?? 0} 篇文章移入回收站，文章正文与图片引用会保留。恢复后为隐藏状态，需单独重新公开。`}
      onCancel={() => setConfirmation(null)} onConfirm={async () => { if (confirmation) await lifecycle.mutateAsync({ action: "delete", input: confirmation }); }} />
  </PageFrame>;
}
