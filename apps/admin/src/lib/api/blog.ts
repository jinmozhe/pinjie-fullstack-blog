import type {
  BlogBatchResult, ListPostsApiV1AdminBlogPostsGetData, MarkdownPreview,
  PageResultPostSummary, PageResultTaxonomyRead, PostBatch, PostCreate, PostRead,
  PostStatusUpdate, PostUpdate, TaxonomyCreate, TaxonomyDelete, TaxonomyImpact,
  TaxonomyRead, TaxonomyUpdate,
} from "@pinjie/api-client";

import { apiRequest, jsonBody } from "./http";

export type TaxonomyKind = "categories" | "tags";
export type PostFilters = NonNullable<ListPostsApiV1AdminBlogPostsGetData["query"]>;
const root = "/api/v1/admin/blog";

export const blogApi = {
  posts: (filters: PostFilters) => {
    const query = new URLSearchParams();
    for (const [key, value] of Object.entries(filters)) {
      if (value !== undefined && value !== null && value !== "") query.set(key, String(value));
    }
    return apiRequest<PageResultPostSummary>(`${root}/posts?${query}`);
  },
  post: (id: string) => apiRequest<PostRead>(`${root}/posts/${id}`),
  createPost: (input: PostCreate) => apiRequest<PostRead>(`${root}/posts`, { method: "POST", body: jsonBody(input) }),
  updatePost: (id: string, input: PostUpdate) => apiRequest<PostRead>(`${root}/posts/${id}`, { method: "PUT", body: jsonBody(input) }),
  updateStatus: (id: string, input: PostStatusUpdate) => apiRequest<PostRead>(`${root}/posts/${id}/status`, { method: "PATCH", body: jsonBody(input) }),
  lifecycle: (action: "delete" | "restore", input: PostBatch) => apiRequest<BlogBatchResult>(`${root}/posts/${action}-batch`, { method: "POST", body: jsonBody(input) }),
  preview: (markdown: string) => apiRequest<MarkdownPreview>(`${root}/preview`, { method: "POST", body: jsonBody({ markdown }) }),
  taxonomy: (kind: TaxonomyKind, page = 1, pageSize = 20) => apiRequest<PageResultTaxonomyRead>(`${root}/${kind}?page=${page}&page_size=${pageSize}`),
  createTaxonomy: (kind: TaxonomyKind, input: TaxonomyCreate) => apiRequest<TaxonomyRead>(`${root}/${kind}`, { method: "POST", body: jsonBody(input) }),
  updateTaxonomy: (kind: TaxonomyKind, id: string, input: TaxonomyUpdate) => apiRequest<TaxonomyRead>(`${root}/${kind}/${id}`, { method: "PUT", body: jsonBody(input) }),
  deleteImpact: (kind: TaxonomyKind, targetIds: string[]) => apiRequest<TaxonomyImpact>(`${root}/${kind}/delete-impact`, { method: "POST", body: jsonBody({ target_ids: targetIds }) }),
  deleteTaxonomy: (kind: TaxonomyKind, input: TaxonomyDelete) => apiRequest<BlogBatchResult>(`${root}/${kind}/delete-batch`, { method: "POST", body: jsonBody(input) }),
};
