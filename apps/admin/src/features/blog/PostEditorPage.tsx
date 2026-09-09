import type { PostCreate, PostRead } from "@pinjie/api-client";
import { ArrowLeftOutlined, BoldOutlined, CodeOutlined, DeleteOutlined, EyeOutlined, FileImageOutlined, ItalicOutlined, LinkOutlined, OrderedListOutlined, SaveOutlined, UploadOutlined } from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { history, useParams } from "@umijs/max";
import { Alert, Button, Form, Input, Space, Tabs, Upload, message } from "antd";
import { useRef, useState } from "react";
import type { ComponentRef } from "react";

import { PageFrame, QueryState } from "@/components/PageFrame";
import { StandardConfirmModal } from "@/components/StandardConfirmModal";
import { canAccess, useCurrentAdmin } from "@/features/auth";
import { adminApi } from "@/lib/api/admin";
import { blogApi } from "@/lib/api/blog";
import { errorMessage } from "@/lib/api/http";

import { TaxonomySelect } from "./TaxonomySelect";
import { formatBlogTime } from "./time";
import { useUnsavedChanges } from "./useUnsavedChanges";
import "./blog.css";

const EMPTY_POST: PostCreate = { title: "", slug: "", summary: "", markdown: "", category_id: null, tag_ids: [], cover_asset_id: null };

export default function PostEditorPage() {
  const { postId } = useParams<{ postId?: string }>();
  const current = useCurrentAdmin();
  const canRead = canAccess(current, "posts:read");
  const canWrite = canAccess(current, postId ? "posts:update" : "posts:create");
  const query = useQuery({ queryKey: ["blog", "post", postId], queryFn: () => blogApi.post(postId ?? ""), enabled: Boolean(postId) && canRead, refetchOnWindowFocus: false });
  if (!canRead || !canWrite) return <PageFrame title="文章编辑" description="撰写并发布文章。"><Alert type="warning" title="没有相应的文章查看或写入权限" /></PageFrame>;
  if (!postId) return <PostEditor key="new" />;
  if (!query.data) return <PageFrame title="文章编辑" description="读取文章当前内容。"><QueryState loading={query.isLoading} error={query.isError ? errorMessage(query.error) : undefined} onRetry={() => void query.refetch()} /></PageFrame>;
  return <PostEditor key={postId} initial={query.data} />;
}

function PostEditor({ initial: loaded }: { initial?: PostRead }) {
  // Freeze the edit revision together with the form values until explicit navigation.
  const [initial] = useState(loaded);
  const current = useCurrentAdmin();
  const queryClient = useQueryClient();
  const [form] = Form.useForm<PostCreate>();
  const [dirty, setDirty] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [removeCover, setRemoveCover] = useState(false);
  const [coverUrl, setCoverUrl] = useState<string | null>(initial?.cover_url ?? null);
  const [tab, setTab] = useState("write");
  const [preview, setPreview] = useState<{ source: string; html: string } | null>(null);
  const submitting = useRef(false);
  const uploadLock = useRef(false);
  const textarea = useRef<ComponentRef<typeof Input.TextArea>>(null);
  const values = initial ? { title: initial.title, slug: initial.slug, summary: initial.summary, markdown: initial.markdown, category_id: initial.category?.id ?? null, tag_ids: initial.tags.map((tag) => tag.id), cover_asset_id: initial.cover_asset_id } : EMPTY_POST;
  const markdown = Form.useWatch("markdown", form) ?? values.markdown;
  const save = useMutation({
    mutationFn: (input: PostCreate) => {
      const { slug, ...content } = input;
      return initial ? blogApi.updatePost(initial.id, { ...content, revision: initial.revision }) : blogApi.createPost({ ...content, slug });
    },
  });
  const render = useMutation({ mutationFn: blogApi.preview });
  const busy = save.isPending || uploading;
  const allowNavigation = useUnsavedChanges(dirty, busy);
  const submit = async () => {
    if (submitting.current || uploadLock.current) return;
    submitting.current = true;
    try {
      const input = await form.validateFields();
      await save.mutateAsync({ ...input, category_id: input.category_id || null, tag_ids: input.tag_ids ?? [], cover_asset_id: input.cover_asset_id || null });
      allowNavigation(); setDirty(false);
      message.success(initial ? "文章已保存" : "文章已发布");
      await queryClient.invalidateQueries({ queryKey: ["blog"] });
      history.push("/blog/posts");
    } catch (error) { if (error instanceof Error) message.error(errorMessage(error)); }
    finally { submitting.current = false; }
  };
  const insert = (before: string, after = "", placeholder = "文字") => {
    const input = textarea.current?.resizableTextArea?.textArea;
    const source = form.getFieldValue("markdown") ?? "";
    const start = input?.selectionStart ?? source.length;
    const end = input?.selectionEnd ?? start;
    const selection = source.slice(start, end) || placeholder;
    form.setFieldValue("markdown", source.slice(0, start) + before + selection + after + source.slice(end));
    setDirty(true);
    window.requestAnimationFrame(() => { input?.focus(); input?.setSelectionRange(start + before.length, start + before.length + selection.length); });
  };
  const upload = async (file: globalThis.File, isCover: boolean) => {
    if (uploadLock.current || submitting.current) return;
    uploadLock.current = true; setUploading(true);
    try {
      const asset = await adminApi.uploadAsset(file, "article");
      if (isCover) { form.setFieldValue("cover_asset_id", asset.id); setCoverUrl(asset.url); }
      else { form.setFieldValue("markdown", `${form.getFieldValue("markdown") ?? ""}\n\n![图片说明](${asset.url})\n`); }
      setDirty(true);
    } catch (error) { message.error(errorMessage(error)); }
    finally { uploadLock.current = false; setUploading(false); }
  };
  const refreshPreview = async () => {
    const source = form.getFieldValue("markdown") ?? "";
    try { const result = await render.mutateAsync(source); setPreview({ source, html: result.html }); }
    catch (error) { message.error(errorMessage(error)); }
  };
  if (initial?.deleted_at) return <PageFrame title="文章编辑" description="回收站文章不能直接编辑。"><Alert type="warning" title="请先到回收站恢复文章" /></PageFrame>;
  return <PageFrame title={initial ? "编辑文章" : "写文章"}
    description={initial ? `当前${initial.status === "public" ? "公开" : "隐藏"}，保存立即生效并保持此状态。首次发布：${formatBlogTime(initial.published_at)}。` : "填写完成后点击发布才会保存到服务器。未保存内容仅保留在当前页面。"}
    action={<Space wrap><Button icon={<ArrowLeftOutlined />} disabled={busy} onClick={() => history.push("/blog/posts")}>返回列表</Button><Button type="primary" icon={<SaveOutlined />} loading={save.isPending} disabled={uploading} onClick={() => void submit()}>{initial ? "保存" : "发布"}</Button></Space>}>
    {save.isError && <Alert showIcon type="error" title={errorMessage(save.error)} description="当前输入已保留。若提示内容冲突，请先复制需要保留的文字，再重新加载文章。" />}
    <Form<PostCreate> form={form} initialValues={values} layout="vertical" disabled={busy} onValuesChange={() => setDirty(true)}>
      <div className="blog-editor-grid">
        <div>
          <Form.Item name="title" label="标题" rules={[{ required: true, whitespace: true, message: "请输入标题" }]}><Input maxLength={200} showCount /></Form.Item>
          <Form.Item name="slug" label="文章网址标识" extra="标题修改不会改变网址，发布后不可修改。" rules={[{ required: true }, { pattern: /^[a-z0-9]+(?:-[a-z0-9]+)*$/, message: "使用小写字母、数字和连字符" }]}><Input addonBefore="/posts/" disabled={Boolean(initial) || busy} maxLength={120} placeholder="my-first-post" /></Form.Item>
          <Form.Item name="summary" label="摘要"><Input.TextArea rows={2} maxLength={500} showCount /></Form.Item>
          <Tabs activeKey={tab} onChange={(value) => { setTab(value); if (value === "preview") void refreshPreview(); }} items={[
            { key: "write", label: "Markdown 编辑", forceRender: true, children: <>
              <div className="blog-editor-toolbar">
                <Button icon={<BoldOutlined />} onClick={() => insert("**", "**")}>加粗</Button>
                <Button icon={<ItalicOutlined />} onClick={() => insert("*", "*")}>斜体</Button>
                <Button onClick={() => insert("\n## ", "\n", "小标题")}>标题</Button>
                <Button icon={<OrderedListOutlined />} onClick={() => insert("\n1. ", "\n", "列表内容")}>列表</Button>
                <Button icon={<CodeOutlined />} onClick={() => insert("\n```text\n", "\n```\n", "代码")}>代码块</Button>
                <Button icon={<LinkOutlined />} onClick={() => insert("[", "](https://example.com)", "链接文字")}>链接</Button>
                <Upload accept="image/png,image/jpeg,image/webp,image/gif" showUploadList={false} disabled={busy} beforeUpload={(file) => { void upload(file, false); return false; }}><Button icon={<FileImageOutlined />} loading={uploading}>插入图片</Button></Upload>
              </div>
              <Form.Item className="blog-editor-textarea" name="markdown" label="正文" rules={[{ required: true, whitespace: true, message: "请输入正文" }]}><Input.TextArea ref={textarea} rows={22} maxLength={200000} showCount /></Form.Item>
            </> },
            { key: "preview", label: "预览", children: <>
              <Button icon={<EyeOutlined />} loading={render.isPending} onClick={() => void refreshPreview()}>刷新预览</Button>
              {render.isError && <Alert type="error" showIcon title={errorMessage(render.error)} />}
              {preview && preview.source !== markdown && <Alert type="info" title="正文已修改，请刷新预览" />}
              {preview && <article className="blog-preview" dangerouslySetInnerHTML={{ __html: preview.html }} />}
            </> },
          ]} />
        </div>
        <aside>
          <Form.Item name="category_id" label="分类"><TaxonomySelect kind="categories" selectedOptions={initial?.category ? [initial.category] : []} disabled={busy || !canAccess(current, "categories:read")} /></Form.Item>
          <Form.Item name="tag_ids" label="标签（最多 20 个）"><TaxonomySelect kind="tags" multiple selectedOptions={initial?.tags} disabled={busy || !canAccess(current, "tags:read")} /></Form.Item>
          <Form.Item name="cover_asset_id" hidden><Input /></Form.Item>
          <div className="blog-cover">
            <p>封面图片（可选）</p>
            {coverUrl && <img src={coverUrl} alt="文章封面" />}
            <Space wrap>
              <Upload accept="image/png,image/jpeg,image/webp,image/gif" showUploadList={false} disabled={busy} beforeUpload={(file) => { void upload(file, true); return false; }}><Button icon={<UploadOutlined />} loading={uploading} disabled={busy}>{coverUrl ? "更换封面" : "上传封面"}</Button></Upload>
              {coverUrl && <Button danger icon={<DeleteOutlined />} disabled={busy} onClick={() => setRemoveCover(true)}>移除封面</Button>}
            </Space>
          </div>
          <Alert type="info" showIcon title="图片使用说明" description="支持 PNG、JPEG、WebP、GIF，单张最大 5 MB。隐藏或删除文章后，已知图片地址仍可访问。在用图片不能从文件资产中删除。" />
        </aside>
      </div>
    </Form>
    <StandardConfirmModal open={removeCover} title="移除文章封面" description="只解除当前文章的封面选择，保存文章后生效；图片资产会保留。" loading={false} onCancel={() => setRemoveCover(false)} onConfirm={async () => { form.setFieldValue("cover_asset_id", null); setCoverUrl(null); setDirty(true); setRemoveCover(false); }} />
  </PageFrame>;
}
