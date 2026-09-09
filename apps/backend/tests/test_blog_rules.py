from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError

from app.core.exceptions import AppException
from app.core.identifiers import new_uuid7
from app.core.payload_sanitizer import is_sensitive_route
from app.domains.blog.rules import publication_range, render_markdown, require_revision
from app.domains.blog.schemas import PostBatch, PostCreate, PostListQuery, PostTarget, PostUpdate


def test_markdown_escapes_html_and_rejects_executable_links() -> None:
    rendered = render_markdown(
        "<script>alert(1)</script>\n\n[x](javascript:alert(1))\n\n[x](data:text/html,hello)",
        upload_base_url="/static/uploads",
    )
    assert "<script>" not in rendered.html
    assert "&lt;script&gt;" in rendered.html
    assert 'href="javascript:' not in rendered.html
    assert 'href="data:' not in rendered.html


def test_markdown_collects_reference_images_but_not_code_examples() -> None:
    rendered = render_markdown(
        "![示例][photo]\n\n[photo]: /static/uploads/article/one.png\n\n```text\n![ignored](/static/uploads/article/two.png)\n```",
        upload_base_url="/static/uploads",
    )
    assert rendered.image_paths == frozenset({"/static/uploads/article/one.png"})
    assert '<img src="/static/uploads/article/one.png"' in rendered.html
    assert "<pre><code" in rendered.html


@pytest.mark.parametrize(
    "source",
    [
        "https://example.com/a.png",
        "/static/uploads/avatar/a.png",
        "/static/uploads/article/../a.png",
        "/static/uploads/article/a.png?x=1",
    ],
)
def test_markdown_rejects_uncontrolled_image_paths(source: str) -> None:
    with pytest.raises(AppException):
        render_markdown(f"![image]({source})", upload_base_url="/static/uploads")


def test_beijing_date_filter_includes_local_day_excludes_next_day() -> None:
    start, end = publication_range(date(2026, 9, 9), date(2026, 9, 9))
    assert start == datetime(2026, 9, 8, 16, tzinfo=UTC)
    assert end == datetime(2026, 9, 9, 16, tzinfo=UTC)


def test_extreme_date_is_validation_error() -> None:
    with pytest.raises(AppException) as error:
        publication_range(date.min, None)
    assert error.value.status_code == 422


def test_protocol_relative_image_is_inert_text() -> None:
    rendered = render_markdown("![image](//example.com/a.png)", upload_base_url="/static/uploads")
    assert "<img" not in rendered.html
    assert not rendered.image_paths


def test_blog_rejects_stale_revision_and_unsupported_write_fields() -> None:
    with pytest.raises(AppException) as conflict:
        require_revision(2, 1)
    assert conflict.value.status_code == 412
    with pytest.raises(ValidationError):
        PostUpdate(title="标题", markdown="正文", revision=1, slug="changed")
    with pytest.raises(ValidationError):
        PostCreate(title="标题", markdown="正文", slug="hello", status="hidden")
    with pytest.raises(ValidationError):
        PostListQuery(published_from=date(2026, 9, 10), published_to=date(2026, 9, 9))
    target = PostTarget(id=new_uuid7(), revision=1)
    with pytest.raises(ValidationError):
        PostBatch(targets=[target, target])


def test_blog_content_never_enters_error_body_capture() -> None:
    assert is_sensitive_route("/api/v1/admin/blog/posts/{post_id}")
    assert is_sensitive_route("/api/v1/admin/blog/preview")
