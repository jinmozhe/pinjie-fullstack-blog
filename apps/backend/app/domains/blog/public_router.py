from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response

from app.api.dependencies import PublicBlogServiceDependency
from app.core.context import current_request_id
from app.core.response import ResponseModel, success_response

from .public_schemas import PublicPostPage, PublicPostQuery, PublicPostRead, PublicTaxonomyCount, PublicTaxonomyPage
from .schemas import TaxonomyKind


def no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"


router = APIRouter(
    prefix="/blog",
    tags=["公开博客"],
    dependencies=[Depends(no_store)],
    responses={
        404: {"description": "内容不存在或不可公开访问"},
        422: {"description": "查询参数无效"},
        503: {"description": "文章服务暂时不可用"},
    },
)
PublicSlug = Annotated[str, Path(min_length=1, max_length=120, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")]


@router.get("/posts", response_model=ResponseModel[PublicPostPage], summary="分页读取或搜索公开文章标题和摘要")
async def public_posts(
    service: PublicBlogServiceDependency, query: Annotated[PublicPostQuery, Query()]
) -> ResponseModel[PublicPostPage]:
    return success_response(data=await service.list_posts(query), request_id=current_request_id())


@router.get("/posts/{slug}", response_model=ResponseModel[PublicPostRead], summary="读取公开文章与安全渲染正文")
async def public_post(slug: PublicSlug, service: PublicBlogServiceDependency) -> ResponseModel[PublicPostRead]:
    return success_response(data=await service.get_post(slug), request_id=current_request_id())


@router.get(
    "/taxonomy/{kind}", response_model=ResponseModel[PublicTaxonomyPage], summary="分页读取有公开文章的分类或标签"
)
async def public_taxonomies(
    kind: TaxonomyKind,
    service: PublicBlogServiceDependency,
    page: Annotated[int, Query(ge=1, le=1000000)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 100,
) -> ResponseModel[PublicTaxonomyPage]:
    return success_response(
        data=await service.list_taxonomy(kind.value, page=page, page_size=page_size), request_id=current_request_id()
    )


@router.get(
    "/taxonomy/{kind}/{slug}",
    response_model=ResponseModel[PublicTaxonomyCount],
    summary="读取公开分类或标签名称与文章数量",
)
async def public_taxonomy(
    kind: TaxonomyKind, slug: PublicSlug, service: PublicBlogServiceDependency
) -> ResponseModel[PublicTaxonomyCount]:
    return success_response(data=await service.get_taxonomy(kind.value, slug), request_id=current_request_id())
