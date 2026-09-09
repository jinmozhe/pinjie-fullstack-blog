import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response

from app.api.dependencies import BlogServiceDependency, require_admin_csrf, require_permission
from app.core.context import current_request_id
from app.core.response import ResponseModel, success_response
from app.domains.admin.permissions import PermissionCode

from .schemas import (
    BlogBatchResult,
    MarkdownPreview,
    MarkdownPreviewInput,
    PostBatch,
    PostCreate,
    PostListQuery,
    PostPage,
    PostRead,
    PostStatusUpdate,
    PostUpdate,
    RevisionInput,
    TaxonomyCreate,
    TaxonomyDelete,
    TaxonomyImpact,
    TaxonomyPage,
    TaxonomyRead,
    TaxonomyTargets,
    TaxonomyUpdate,
)


def no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"


router = APIRouter(
    prefix="/admin/blog",
    tags=["博客管理"],
    dependencies=[Depends(no_store)],
    responses={
        401: {"description": "需要管理员认证"},
        403: {"description": "权限或 CSRF 校验失败"},
        404: {"description": "目标不存在"},
        409: {"description": "标识或状态冲突"},
        412: {"description": "修订号或删除影响已变化"},
        503: {"description": "内容服务暂时不可用"},
    },
)


@router.get(
    "/posts",
    response_model=ResponseModel[PostPage],
    summary="分页查看文章或回收站",
    dependencies=[Depends(require_permission(PermissionCode.POSTS_READ))],
)
async def list_posts(
    service: BlogServiceDependency, query: Annotated[PostListQuery, Query()]
) -> ResponseModel[PostPage]:
    return success_response(data=await service.list_posts(query), request_id=current_request_id())


@router.post(
    "/posts",
    response_model=ResponseModel[PostRead],
    status_code=201,
    summary="创建并发布文章",
    dependencies=[Depends(require_admin_csrf), Depends(require_permission(PermissionCode.POSTS_CREATE))],
)
async def create_post(payload: PostCreate, service: BlogServiceDependency) -> ResponseModel[PostRead]:
    return success_response(
        data=await service.create_post(payload), request_id=current_request_id(), message="文章已发布"
    )


@router.post(
    "/preview",
    response_model=ResponseModel[MarkdownPreview],
    summary="预览 Markdown，不保存草稿",
    dependencies=[Depends(require_admin_csrf), Depends(require_permission(PermissionCode.POSTS_READ))],
)
async def preview_markdown(
    payload: MarkdownPreviewInput, service: BlogServiceDependency
) -> ResponseModel[MarkdownPreview]:
    return success_response(data=await service.preview(payload.markdown), request_id=current_request_id())


@router.post(
    "/posts/delete-batch",
    response_model=ResponseModel[BlogBatchResult],
    summary="批量将文章移入回收站",
    dependencies=[Depends(require_admin_csrf), Depends(require_permission(PermissionCode.POSTS_DELETE))],
)
async def delete_posts(payload: PostBatch, service: BlogServiceDependency) -> ResponseModel[BlogBatchResult]:
    return success_response(
        data=await service.change_lifecycle(payload, action="delete"),
        request_id=current_request_id(),
        message="文章已移入回收站",
    )


@router.post(
    "/posts/restore-batch",
    response_model=ResponseModel[BlogBatchResult],
    summary="批量恢复文章并保持隐藏",
    dependencies=[Depends(require_admin_csrf), Depends(require_permission(PermissionCode.POSTS_RESTORE))],
)
async def restore_posts(payload: PostBatch, service: BlogServiceDependency) -> ResponseModel[BlogBatchResult]:
    return success_response(
        data=await service.change_lifecycle(payload, action="restore"),
        request_id=current_request_id(),
        message="文章已恢复为隐藏",
    )


@router.get(
    "/posts/{post_id}",
    response_model=ResponseModel[PostRead],
    summary="查看文章当前内容",
    dependencies=[Depends(require_permission(PermissionCode.POSTS_READ))],
)
async def get_post(post_id: uuid.UUID, service: BlogServiceDependency) -> ResponseModel[PostRead]:
    return success_response(data=await service.get_post(post_id), request_id=current_request_id())


@router.put(
    "/posts/{post_id}",
    response_model=ResponseModel[PostRead],
    summary="保存文章并立即生效，保持原公开状态",
    dependencies=[Depends(require_admin_csrf), Depends(require_permission(PermissionCode.POSTS_UPDATE))],
)
async def update_post(
    post_id: uuid.UUID, payload: PostUpdate, service: BlogServiceDependency
) -> ResponseModel[PostRead]:
    return success_response(
        data=await service.update_post(post_id, payload), request_id=current_request_id(), message="文章已保存"
    )


@router.patch(
    "/posts/{post_id}/status",
    response_model=ResponseModel[PostRead],
    summary="切换公开或隐藏，不重置首次发布时间",
    dependencies=[Depends(require_admin_csrf), Depends(require_permission(PermissionCode.POSTS_UPDATE))],
)
async def update_post_status(
    post_id: uuid.UUID, payload: PostStatusUpdate, service: BlogServiceDependency
) -> ResponseModel[PostRead]:
    return success_response(
        data=await service.update_status(post_id, payload), request_id=current_request_id(), message="文章状态已更新"
    )


@router.delete(
    "/posts/{post_id}",
    response_model=ResponseModel[BlogBatchResult],
    summary="将文章移入回收站",
    dependencies=[Depends(require_admin_csrf), Depends(require_permission(PermissionCode.POSTS_DELETE))],
)
async def delete_post(
    post_id: uuid.UUID, revision: Annotated[int, Query(gt=0)], service: BlogServiceDependency
) -> ResponseModel[BlogBatchResult]:
    return success_response(
        data=await service.change_one_lifecycle(post_id, revision, action="delete"),
        request_id=current_request_id(),
        message="文章已移入回收站",
    )


@router.post(
    "/posts/{post_id}/restore",
    response_model=ResponseModel[BlogBatchResult],
    summary="恢复文章并保持隐藏",
    dependencies=[Depends(require_admin_csrf), Depends(require_permission(PermissionCode.POSTS_RESTORE))],
)
async def restore_post(
    post_id: uuid.UUID, payload: RevisionInput, service: BlogServiceDependency
) -> ResponseModel[BlogBatchResult]:
    return success_response(
        data=await service.change_one_lifecycle(post_id, payload.revision, action="restore"),
        request_id=current_request_id(),
        message="文章已恢复为隐藏",
    )


@router.get(
    "/categories",
    response_model=ResponseModel[TaxonomyPage],
    summary="分页查看分类",
    dependencies=[Depends(require_permission(PermissionCode.CATEGORIES_READ))],
)
async def list_categories(
    service: BlogServiceDependency,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ResponseModel[TaxonomyPage]:
    return success_response(
        data=await service.list_taxonomy("categories", page=page, page_size=page_size), request_id=current_request_id()
    )


@router.post(
    "/categories",
    response_model=ResponseModel[TaxonomyRead],
    status_code=201,
    summary="创建分类",
    dependencies=[Depends(require_admin_csrf), Depends(require_permission(PermissionCode.CATEGORIES_CREATE))],
)
async def create_category(payload: TaxonomyCreate, service: BlogServiceDependency) -> ResponseModel[TaxonomyRead]:
    return success_response(
        data=await service.create_taxonomy("categories", payload), request_id=current_request_id(), message="分类已创建"
    )


@router.put(
    "/categories/{target_id}",
    response_model=ResponseModel[TaxonomyRead],
    summary="编辑分类",
    dependencies=[Depends(require_admin_csrf), Depends(require_permission(PermissionCode.CATEGORIES_UPDATE))],
)
async def update_category(
    target_id: uuid.UUID, payload: TaxonomyUpdate, service: BlogServiceDependency
) -> ResponseModel[TaxonomyRead]:
    return success_response(
        data=await service.update_taxonomy("categories", target_id, payload),
        request_id=current_request_id(),
        message="分类已保存",
    )


@router.post(
    "/categories/delete-impact",
    response_model=ResponseModel[TaxonomyImpact],
    summary="预览分类删除影响，包含回收站文章",
    dependencies=[Depends(require_admin_csrf), Depends(require_permission(PermissionCode.CATEGORIES_DELETE))],
)
async def category_delete_impact(
    payload: TaxonomyTargets, service: BlogServiceDependency
) -> ResponseModel[TaxonomyImpact]:
    return success_response(
        data=await service.deletion_impact("categories", payload.target_ids), request_id=current_request_id()
    )


@router.post(
    "/categories/delete-batch",
    response_model=ResponseModel[BlogBatchResult],
    summary="删除所选分类并清空文章分类",
    dependencies=[Depends(require_admin_csrf), Depends(require_permission(PermissionCode.CATEGORIES_DELETE))],
)
async def delete_categories(payload: TaxonomyDelete, service: BlogServiceDependency) -> ResponseModel[BlogBatchResult]:
    return success_response(
        data=await service.delete_taxonomy("categories", payload),
        request_id=current_request_id(),
        message="分类已删除，文章已保留",
    )


@router.get(
    "/tags",
    response_model=ResponseModel[TaxonomyPage],
    summary="分页查看标签",
    dependencies=[Depends(require_permission(PermissionCode.TAGS_READ))],
)
async def list_tags(
    service: BlogServiceDependency,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ResponseModel[TaxonomyPage]:
    return success_response(
        data=await service.list_taxonomy("tags", page=page, page_size=page_size), request_id=current_request_id()
    )


@router.post(
    "/tags",
    response_model=ResponseModel[TaxonomyRead],
    status_code=201,
    summary="创建标签",
    dependencies=[Depends(require_admin_csrf), Depends(require_permission(PermissionCode.TAGS_CREATE))],
)
async def create_tag(payload: TaxonomyCreate, service: BlogServiceDependency) -> ResponseModel[TaxonomyRead]:
    return success_response(
        data=await service.create_taxonomy("tags", payload), request_id=current_request_id(), message="标签已创建"
    )


@router.put(
    "/tags/{target_id}",
    response_model=ResponseModel[TaxonomyRead],
    summary="编辑标签",
    dependencies=[Depends(require_admin_csrf), Depends(require_permission(PermissionCode.TAGS_UPDATE))],
)
async def update_tag(
    target_id: uuid.UUID, payload: TaxonomyUpdate, service: BlogServiceDependency
) -> ResponseModel[TaxonomyRead]:
    return success_response(
        data=await service.update_taxonomy("tags", target_id, payload),
        request_id=current_request_id(),
        message="标签已保存",
    )


@router.post(
    "/tags/delete-impact",
    response_model=ResponseModel[TaxonomyImpact],
    summary="预览标签删除影响，文章去重计数",
    dependencies=[Depends(require_admin_csrf), Depends(require_permission(PermissionCode.TAGS_DELETE))],
)
async def tag_delete_impact(payload: TaxonomyTargets, service: BlogServiceDependency) -> ResponseModel[TaxonomyImpact]:
    return success_response(
        data=await service.deletion_impact("tags", payload.target_ids), request_id=current_request_id()
    )


@router.post(
    "/tags/delete-batch",
    response_model=ResponseModel[BlogBatchResult],
    summary="删除所选标签并保留文章及其他标签",
    dependencies=[Depends(require_admin_csrf), Depends(require_permission(PermissionCode.TAGS_DELETE))],
)
async def delete_tags(payload: TaxonomyDelete, service: BlogServiceDependency) -> ResponseModel[BlogBatchResult]:
    return success_response(
        data=await service.delete_taxonomy("tags", payload),
        request_id=current_request_id(),
        message="标签已删除，文章及其他标签已保留",
    )
