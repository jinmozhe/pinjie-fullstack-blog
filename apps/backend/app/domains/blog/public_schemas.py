from datetime import datetime

from pydantic import Field, field_validator

from app.core.pagination import PageResult

from .schemas import BlogInput, Slug


class PublicTaxonomy(BlogInput):
    name: str
    slug: str


class PublicTaxonomyCount(PublicTaxonomy):
    post_count: int = Field(ge=1)


class PublicPostSummary(BlogInput):
    title: str
    slug: str
    summary: str
    category: PublicTaxonomy | None
    tags: list[PublicTaxonomy]
    cover_url: str | None
    published_at: datetime
    updated_at: datetime


class PublicPostRead(PublicPostSummary):
    html: str = Field(description="与后台预览共用安全规则生成的正文 HTML")


class PublicPostQuery(BlogInput):
    page: int = Field(default=1, ge=1, le=1000000)
    page_size: int = Field(default=12, ge=1, le=100)
    q: str = Field(default="", max_length=100, description="标题和摘要的字面包含查询，不检索正文")
    category: Slug | None = None
    tag: Slug | None = None

    @field_validator("q")
    @classmethod
    def trim_query(cls, value: str) -> str:
        return value.strip()


PublicPostPage = PageResult[PublicPostSummary]
PublicTaxonomyPage = PageResult[PublicTaxonomyCount]
