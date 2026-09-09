"""不依赖数据库的博客规则，预览和公开阅读共用此渲染入口。"""

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from markdown_it import MarkdownIt
from markdown_it.token import Token

from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException


class BlogMarkdown(MarkdownIt):
    def validateLink(self, url: str) -> bool:  # noqa: N802
        try:
            parsed = urlsplit(url)
        except ValueError:
            return False
        return (
            super().validateLink(url)
            and parsed.scheme.lower() in {"", "https", "http", "mailto"}
            and not url.startswith("//")
            and "\\" not in url
            and not any(ord(char) < 32 or ord(char) == 127 for char in url)
        )


@dataclass(frozen=True)
class RenderedMarkdown:
    html: str
    image_paths: frozenset[str]


def render_markdown(markdown: str, *, upload_base_url: str) -> RenderedMarkdown:
    parser = BlogMarkdown("commonmark", {"html": False, "maxNesting": 20}).enable("table").enable("strikethrough")
    tokens = parser.parse(markdown)
    paths: set[str] = set()
    pending: list[Token] = list(tokens)
    prefix = upload_base_url.rstrip("/") + "/article/"
    while pending:
        token = pending.pop()
        pending.extend(token.children or [])
        if token.type == "image":
            source = str(token.attrGet("src") or "")
            parsed = urlsplit(source)
            if (
                not source.startswith(prefix)
                or parsed.scheme
                or parsed.netloc
                or parsed.query
                or parsed.fragment
                or ".." in source
                or "%" in source
                or "\\" in source
            ):
                raise AppException(
                    status_code=422, code=ErrorCode.BLOG_MEDIA_INVALID, message="正文图片须使用本站上传的文章图片路径"
                )
            paths.add(source)
    if len(paths) > 100:
        raise AppException(
            status_code=422, code=ErrorCode.BLOG_MEDIA_INVALID, message="每篇文章最多引用 100 张正文图片"
        )
    return RenderedMarkdown(parser.renderer.render(tokens, parser.options, {}), frozenset(paths))


def publication_range(start: date | None, end: date | None) -> tuple[datetime | None, datetime | None]:
    shanghai = ZoneInfo("Asia/Shanghai")
    try:
        return (
            datetime.combine(start, time.min, shanghai).astimezone(UTC) if start else None,
            datetime.combine(end + timedelta(days=1), time.min, shanghai).astimezone(UTC) if end else None,
        )
    except OverflowError as exc:
        raise AppException(status_code=422, code=ErrorCode.VALIDATION_ERROR, message="日期超出支持范围") from exc


def confirmation_digest(snapshot: object) -> str:
    return hashlib.sha256(json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def require_revision(actual: int, expected: int) -> None:
    if actual != expected:
        raise AppException(
            status_code=412, code=ErrorCode.BLOG_REVISION_MISMATCH, message="内容已发生变化，请保留输入并重新加载后确认"
        )


def require_lifecycle(*, is_deleted: bool, expect_deleted: bool) -> None:
    if is_deleted != expect_deleted:
        raise AppException(status_code=409, code=ErrorCode.STATE_CONFLICT, message="文章状态已变化，请刷新列表")
