from io import BytesIO

import pytest
from PIL import Image
from pydantic import ValidationError

from app.domains.settings.schemas import SiteSettingValue
from app.services.settings_media import SettingsMediaStore


def _image_bytes(color: str) -> BytesIO:
    source = BytesIO()
    Image.new("RGB", (32, 24), color=color).save(source, format="PNG")
    source.seek(0)
    return source


def test_site_setting_normalizes_and_deduplicates_keywords() -> None:
    value = SiteSettingValue(
        name=" 品界 ",
        logo=None,
        title=" 品界官网 ",
        keywords=[" 科技 ", "科技", "网络"],
        description=" 站点描述 ",
    )

    assert value.name == "品界"
    assert value.title == "品界官网"
    assert value.keywords == ["科技", "网络"]
    assert value.description == "站点描述"


def test_site_setting_rejects_overlong_keyword() -> None:
    with pytest.raises(ValidationError):
        SiteSettingValue(
            name="Pinjie",
            logo=None,
            title="Pinjie",
            keywords=["x" * 65],
            description="",
        )


@pytest.mark.asyncio
async def test_settings_media_rejects_non_image(tmp_path) -> None:
    store = SettingsMediaStore(tmp_path / "settings-media")

    with pytest.raises(ValueError, match="invalid_image"):
        await store.stage_site_logo(BytesIO(b"<svg></svg>"))


@pytest.mark.asyncio
async def test_settings_media_rollback_restores_previous_logo(tmp_path) -> None:
    store = SettingsMediaStore(tmp_path / "settings-media")
    first = await store.stage_site_logo(_image_bytes("red"))
    initial = await store.prepare_replace(staged=first, old_logo=None, old_revision=1, new_revision=2)
    await store.finalize(initial)
    assert await store.validate_logo(first.value())

    second = await store.stage_site_logo(_image_bytes("blue"))
    replacement = await store.prepare_replace(
        staged=second,
        old_logo=first.value(),
        old_revision=2,
        new_revision=3,
    )
    await store.rollback(replacement)

    assert await store.validate_logo(first.value())
    assert not await store.validate_logo(second.value())
