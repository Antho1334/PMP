from pathlib import Path

import pytest

from app.resources.application_resources import ApplicationResource
from app.resources.banners import Banner
from app.resources.catalog import (
    APPLICATION_RESOURCE_CATALOG,
    BANNER_CATALOG,
    FONT_CATALOG,
    IMAGE_CATALOG,
    ICON_CATALOG,
    LOGO_CATALOG,
    TEMPLATE_CATALOG,
    WATERMARK_CATALOG,
)
from app.resources.errors import ResourceNotFoundError
from app.resources.fonts import Font
from app.resources.icons import Icon
from app.resources.images import Image
from app.resources.logos import Logo
from app.resources.resource_manager import ResourceManager
from app.resources.templates import Template
from app.resources.watermarks import Watermark


def _create_catalog_file(root: Path, relative_path: str) -> Path:
    target = root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"resource")
    return target.resolve()


@pytest.fixture
def complete_resource_root(tmp_path):
    for catalog in (
        LOGO_CATALOG,
        ICON_CATALOG,
        IMAGE_CATALOG,
        BANNER_CATALOG,
        WATERMARK_CATALOG,
        TEMPLATE_CATALOG,
        FONT_CATALOG,
        APPLICATION_RESOURCE_CATALOG,
    ):
        for relative_path in catalog.values():
            _create_catalog_file(tmp_path, relative_path)
    return tmp_path


def test_manager_can_use_its_default_resource_root():
    manager = ResourceManager()

    assert manager.logo(Logo.PMP).is_file()
    assert manager.banner(Banner.PMP).is_file()
    assert manager.image(Image.MUNICIPAL_POLICE_PATCH).is_file()
    assert manager.application_resource(
        ApplicationResource.OPERATIONAL_MAP_PAGE
    ).is_file()


def test_manager_uses_a_custom_resource_root(complete_resource_root):
    manager = ResourceManager(str(complete_resource_root))

    assert manager.logo(Logo.PMP).is_relative_to(complete_resource_root)


@pytest.mark.parametrize("invalid_root", [None, object(), 42])
def test_manager_rejects_an_invalid_explicit_resource_root(
    invalid_root,
    tmp_path,
):
    if invalid_root is None:
        invalid_root = tmp_path / "missing"

    with pytest.raises((TypeError, ValueError)):
        ResourceManager(invalid_root)


def test_manager_rejects_a_file_as_resource_root(tmp_path):
    root_file = tmp_path / "root.txt"
    root_file.write_text("not a directory", encoding="utf-8")

    with pytest.raises(ValueError, match="dossier"):
        ResourceManager(root_file)


@pytest.mark.parametrize(
    ("method_name", "resource", "catalog"),
    [
        ("logo", Logo.PMP, LOGO_CATALOG),
        ("icon", Icon.WARNING, ICON_CATALOG),
        ("image", Image.MUNICIPAL_POLICE_PATCH, IMAGE_CATALOG),
        ("banner", Banner.PMP, BANNER_CATALOG),
        ("watermark", Watermark.PMP, WATERMARK_CATALOG),
        ("template", Template.DAILY_REPORT_WORD, TEMPLATE_CATALOG),
        ("font", Font.DEFAULT, FONT_CATALOG),
        (
            "application_resource",
            ApplicationResource.OPERATIONAL_MAP_PAGE,
            APPLICATION_RESOURCE_CATALOG,
        ),
    ],
)
def test_each_resource_family_resolves_to_an_absolute_path(
    method_name,
    resource,
    catalog,
    complete_resource_root,
):
    manager = ResourceManager(complete_resource_root)

    resolved = getattr(manager, method_name)(resource)

    assert isinstance(resolved, Path)
    assert resolved.is_absolute()
    assert resolved == (complete_resource_root / catalog[resource]).resolve()


@pytest.mark.parametrize(
    ("method_name", "invalid_resource"),
    [
        ("logo", Icon.WARNING),
        ("icon", Logo.PMP),
        ("image", Logo.PMP),
        ("banner", "pmp"),
        ("watermark", None),
        ("template", Font.DEFAULT),
        ("font", Template.DAILY_REPORT_WORD),
        ("application_resource", object()),
    ],
)
def test_each_method_rejects_a_key_from_the_wrong_family(
    method_name,
    invalid_resource,
    complete_resource_root,
):
    manager = ResourceManager(complete_resource_root)

    with pytest.raises(TypeError, match="resource"):
        getattr(manager, method_name)(invalid_resource)


def test_missing_file_raises_contextual_resource_error(tmp_path):
    manager = ResourceManager(tmp_path)

    with pytest.raises(ResourceNotFoundError) as captured:
        manager.icon(Icon.WARNING)

    assert captured.value.resource is Icon.WARNING
    assert captured.value.resolved_path == (
        tmp_path / ICON_CATALOG[Icon.WARNING]
    ).resolve()


def test_catalog_key_missing_raises_resource_error(
    complete_resource_root,
    monkeypatch,
):
    incomplete_catalog = dict(LOGO_CATALOG)
    del incomplete_catalog[Logo.PMP]
    monkeypatch.setattr(
        "app.resources.resource_manager.LOGO_CATALOG",
        incomplete_catalog,
    )

    with pytest.raises(ResourceNotFoundError) as captured:
        ResourceManager(complete_resource_root).logo(Logo.PMP)

    assert captured.value.resource is Logo.PMP
    assert captured.value.resolved_path is None


@pytest.mark.parametrize(
    "invalid_path",
    ["../outside.png", "", 42],
)
def test_invalid_catalog_path_is_rejected(
    invalid_path,
    complete_resource_root,
    monkeypatch,
):
    invalid_catalog = dict(LOGO_CATALOG)
    invalid_catalog[Logo.PMP] = invalid_path
    monkeypatch.setattr(
        "app.resources.resource_manager.LOGO_CATALOG",
        invalid_catalog,
    )

    with pytest.raises(ResourceNotFoundError):
        ResourceManager(complete_resource_root).logo(Logo.PMP)


def test_catalogued_directory_is_not_accepted_as_a_resource(
    complete_resource_root,
    monkeypatch,
):
    directory = complete_resource_root / "directory"
    directory.mkdir()
    invalid_catalog = dict(LOGO_CATALOG)
    invalid_catalog[Logo.PMP] = "directory"
    monkeypatch.setattr(
        "app.resources.resource_manager.LOGO_CATALOG",
        invalid_catalog,
    )

    with pytest.raises(ResourceNotFoundError):
        ResourceManager(complete_resource_root).logo(Logo.PMP)


def test_repeated_resolution_is_stable(complete_resource_root):
    manager = ResourceManager(complete_resource_root)

    assert manager.icon(Icon.WARNING) == manager.icon(Icon.WARNING)
    assert vars(manager) == {"_resource_root": complete_resource_root.resolve()}


def test_catalogs_cover_every_official_enum_member():
    assert set(LOGO_CATALOG) == set(Logo)
    assert set(ICON_CATALOG) == set(Icon)
    assert set(IMAGE_CATALOG) == set(Image)
    assert set(BANNER_CATALOG) == set(Banner)
    assert set(WATERMARK_CATALOG) == set(Watermark)
    assert set(TEMPLATE_CATALOG) == set(Template)
    assert set(FONT_CATALOG) == set(Font)
    assert set(APPLICATION_RESOURCE_CATALOG) == set(ApplicationResource)


def test_catalog_module_is_declarative_and_has_no_disk_access_names():
    from app.resources import catalog

    forbidden_names = {"Path", "open", "exists", "is_file", "resolve"}
    assert forbidden_names.isdisjoint(vars(catalog))


def test_resource_library_has_no_forbidden_dependencies():
    from app.resources import resource_manager

    forbidden_names = {
        "PySide6",
        "docx",
        "reportlab",
        "DailyReportRenderer",
        "DailyReportProvider",
        "JournalService",
    }
    assert forbidden_names.isdisjoint(vars(resource_manager))
