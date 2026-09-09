import uuid
from datetime import date, datetime
from enum import StrEnum
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.pagination import PageResult

Slug = Annotated[str, Field(min_length=1, max_length=120, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")]


class PostStatus(StrEnum):
    PUBLIC = "public"
    HIDDEN = "hidden"


class TaxonomyKind(StrEnum):
    CATEGORIES = "categories"
    TAGS = "tags"


class BlogInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TaxonomyCreate(BlogInput):
    name: str = Field(min_length=1, max_length=80)
    slug: Slug

    @field_validator("name")
    @classmethod
    def nonblank_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("名称不能为空")
        return value.strip()


class TaxonomyUpdate(TaxonomyCreate):
    revision: int = Field(gt=0)


class TaxonomyRead(TaxonomyUpdate):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


TaxonomyPage = PageResult[TaxonomyRead]


class PostContent(BlogInput):
    title: str = Field(min_length=1, max_length=200)
    summary: str = Field(default="", max_length=500)
    markdown: str = Field(min_length=1, max_length=200000)
    category_id: uuid.UUID | None = None
    tag_ids: list[uuid.UUID] = Field(default_factory=list, max_length=20)
    cover_asset_id: uuid.UUID | None = None

    @field_validator("title", "markdown")
    @classmethod
    def nonblank_content(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("标题和正文不能为空")
        return value

    @field_validator("tag_ids")
    @classmethod
    def unique_tags(cls, value: list[uuid.UUID]) -> list[uuid.UUID]:
        if len(value) != len(set(value)):
            raise ValueError("标签不能重复")
        return value


class PostCreate(PostContent):
    slug: Slug


class PostUpdate(PostContent):
    revision: int = Field(gt=0)


class PostSummary(BlogInput):
    id: uuid.UUID
    title: str
    slug: str
    summary: str
    status: PostStatus
    category: TaxonomyRead | None
    tags: list[TaxonomyRead]
    cover_asset_id: uuid.UUID | None
    cover_url: str | None
    published_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    revision: int


class PostRead(PostSummary):
    markdown: str


PostPage = PageResult[PostSummary]


class PostListQuery(BlogInput):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    status: PostStatus | None = None
    deleted: bool = False
    category_id: uuid.UUID | None = None
    tag_id: uuid.UUID | None = None
    published_from: date | None = None
    published_to: date | None = None

    @model_validator(mode="after")
    def valid_date_range(self) -> Self:
        if self.published_from and self.published_to and self.published_from > self.published_to:
            raise ValueError("开始日期不得晚于结束日期")
        if self.published_to == date.max:
            raise ValueError("结束日期超出支持范围")
        return self


class RevisionInput(BlogInput):
    revision: int = Field(gt=0)


class PostStatusUpdate(RevisionInput):
    status: PostStatus


class PostTarget(RevisionInput):
    id: uuid.UUID


class PostBatch(BlogInput):
    targets: list[PostTarget] = Field(min_length=1, max_length=100)

    @field_validator("targets")
    @classmethod
    def unique_targets(cls, value: list[PostTarget]) -> list[PostTarget]:
        if len(value) != len({target.id for target in value}):
            raise ValueError("文章不能重复")
        return value


class TaxonomyTargets(BlogInput):
    target_ids: list[uuid.UUID] = Field(min_length=1, max_length=100)

    @field_validator("target_ids")
    @classmethod
    def unique_targets(cls, value: list[uuid.UUID]) -> list[uuid.UUID]:
        if len(value) != len(set(value)):
            raise ValueError("删除目标不能重复")
        return value


class TaxonomyDelete(TaxonomyTargets):
    confirmation: str = Field(pattern=r"^[0-9a-f]{64}$", description="删除影响预览的摘要，目标或关联变化时拒绝执行")


class TaxonomyImpact(BlogInput):
    targets: list[TaxonomyRead]
    affected_posts: int
    confirmation: str


class BlogBatchResult(BlogInput):
    completed_count: int
    target_ids: list[uuid.UUID]


class MarkdownPreviewInput(BlogInput):
    markdown: str = Field(max_length=200000)


class MarkdownPreview(BlogInput):
    html: str
