import type { TaxonomyCreate, TaxonomyImpact, TaxonomyRead } from "@pinjie/api-client";
import { DeleteOutlined, EditOutlined, PlusOutlined } from "@ant-design/icons";
import { ProTable } from "@ant-design/pro-components";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Alert, Button, Form, Input, Modal, Space, message } from "antd";
import { useRef, useState } from "react";

import { PageFrame, QueryState } from "@/components/PageFrame";
import { StandardConfirmModal } from "@/components/StandardConfirmModal";
import { canAccess, useCurrentAdmin } from "@/features/auth";
import { blogApi, type TaxonomyKind } from "@/lib/api/blog";
import { errorMessage } from "@/lib/api/http";

import "./blog.css";

export function TaxonomyPage({ kind }: { kind: TaxonomyKind }) {
  const label = kind === "categories" ? "分类" : "标签";
  const current = useCurrentAdmin();
  const canRead = canAccess(current, `${kind}:read`);
  const canCreate = canAccess(current, `${kind}:create`);
  const canUpdate = canAccess(current, `${kind}:update`);
  const canDelete = canAccess(current, `${kind}:delete`);
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<string[]>([]);
  const [editing, setEditing] = useState<TaxonomyRead | "new" | null>(null);
  const [impact, setImpact] = useState<TaxonomyImpact | null>(null);
  const [form] = Form.useForm<TaxonomyCreate>();
  const submitting = useRef(false);
  const query = useQuery({ queryKey: ["blog", kind, page], queryFn: () => blogApi.taxonomy(kind, page), enabled: canRead });
  const hasRows = Boolean(query.data?.items.length);
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["blog"] });
  const save = useMutation({
    mutationFn: async (values: TaxonomyCreate) => {
      if (editing === "new") return blogApi.createTaxonomy(kind, values);
      if (!editing) throw new Error("编辑目标不存在");
      return blogApi.updateTaxonomy(kind, editing.id, { ...values, revision: editing.revision });
    },
    onSuccess: async () => { setEditing(null); message.success(`${label}已保存`); await invalidate(); },
  });
  const preview = useMutation({ mutationFn: (ids: string[]) => blogApi.deleteImpact(kind, ids), onSuccess: setImpact, onError: (error) => message.error(errorMessage(error)) });
  const remove = useMutation({
    mutationFn: (snapshot: TaxonomyImpact) => blogApi.deleteTaxonomy(kind, { target_ids: snapshot.targets.map((target) => target.id), confirmation: snapshot.confirmation }),
    onSuccess: async () => { setImpact(null); setSelected([]); message.success(`${label}已删除，文章已保留`); await invalidate(); },
  });
  const busy = save.isPending || preview.isPending || remove.isPending || Boolean(impact) || Boolean(editing);
  const submit = async () => {
    if (submitting.current) return;
    submitting.current = true;
    try { await save.mutateAsync(await form.validateFields()); }
    catch (error) { if (error instanceof Error) message.error(errorMessage(error)); }
    finally { submitting.current = false; }
  };
  if (!canRead) return <PageFrame title={`${label}管理`} description="维护文章的分类与标签。"><Alert type="warning" title="没有查看权限" /></PageFrame>;
  return <PageFrame title={`${label}管理`} description={`删除${label}会解除全部关联，包含回收站文章；文章本身会保留。`}>
    <QueryState loading={query.isLoading} error={query.isError ? errorMessage(query.error) : undefined} onRetry={() => void query.refetch()} />
    {query.data && <ProTable<TaxonomyRead>
      className="responsive-data-table" rowKey="id" cardProps={false} search={false}
      headerTitle={`${label}列表`} dataSource={query.data.items} loading={query.isFetching}
      options={{ reload: () => void query.refetch(), density: true, setting: true, fullScreen: true }}
      pagination={{ current: page, pageSize: 20, total: query.data.total, showSizeChanger: false, onChange: (next) => { setPage(next); setSelected([]); } }}
      scroll={hasRows ? { x: 650 } : undefined} tableLayout={hasRows ? "fixed" : "auto"}
      rowSelection={canDelete ? { selectedRowKeys: selected, onChange: (keys) => setSelected(keys.map(String)), getCheckboxProps: () => ({ disabled: busy }) } : false}
      tableAlertOptionRender={() => <Button danger icon={<DeleteOutlined />} disabled={busy} onClick={() => preview.mutate([...selected])}>批量删除</Button>}
      toolBarRender={() => [canCreate && <Button key="create" type="primary" icon={<PlusOutlined />} disabled={busy} onClick={() => { save.reset(); form.resetFields(); setEditing("new"); }}>新建{label}</Button>]}
      columns={[
        { title: "名称", dataIndex: "name", ellipsis: true },
        { title: "标识", dataIndex: "slug", ellipsis: true },
        { title: "操作", width: "1%", render: (_, row) => <Space className="table-actions" wrap={false}>
          {canUpdate && <Button type="link" icon={<EditOutlined />} disabled={busy} onClick={() => { save.reset(); setEditing(row); form.setFieldsValue({ name: row.name, slug: row.slug }); }}>编辑</Button>}
          {canDelete && <Button type="link" danger icon={<DeleteOutlined />} disabled={busy} onClick={() => preview.mutate([row.id])}>删除</Button>}
        </Space> },
      ]}
    />}
    <Modal open={Boolean(editing)} title={`${editing === "new" ? "新建" : "编辑"}${label}`} okText="保存" cancelText="取消" confirmLoading={save.isPending}
      closable={!save.isPending} maskClosable={!save.isPending} keyboard={!save.isPending} cancelButtonProps={{ disabled: save.isPending }}
      onCancel={() => { if (!submitting.current) setEditing(null); }} onOk={() => void submit()}>
      {save.isError && <Alert type="error" showIcon title={errorMessage(save.error)} />}
      <Form form={form} layout="vertical" disabled={save.isPending}>
        <Form.Item name="name" label="名称" rules={[{ required: true, whitespace: true }]}><Input maxLength={80} /></Form.Item>
        <Form.Item name="slug" label="网址标识" rules={[{ required: true }, { pattern: /^[a-z0-9]+(?:-[a-z0-9]+)*$/, message: "使用小写字母、数字和连字符" }]}><Input maxLength={120} placeholder="例如：daily-notes" /></Form.Item>
      </Form>
    </Modal>
    <StandardConfirmModal open={Boolean(impact)} title={`删除${label}`} loading={remove.isPending} onCancel={() => setImpact(null)}
      description={impact ? `将删除：${impact.targets.map((target) => target.name).join("、")}。影响 ${impact.affected_posts} 篇文章（包含回收站）。文章会保留，${kind === "tags" ? "其他标签不受影响；" : "关联分类会设为空；"}${label}本身无法从文章回收站恢复。` : ""}
      onConfirm={async () => { if (impact) await remove.mutateAsync(impact); }} />
  </PageFrame>;
}
