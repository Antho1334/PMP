"""Résolution centralisée des ressources officielles PMP."""

from collections.abc import Mapping
from enum import Enum
from os import PathLike
from pathlib import Path
from typing import TypeVar

from app.resources.application_resources import ApplicationResource
from app.resources.banners import Banner
from app.resources.catalog import (
    APPLICATION_RESOURCE_CATALOG,
    BANNER_CATALOG,
    FONT_CATALOG,
    ICON_CATALOG,
    LOGO_CATALOG,
    TEMPLATE_CATALOG,
    WATERMARK_CATALOG,
)
from app.resources.errors import ResourceNotFoundError
from app.resources.fonts import Font
from app.resources.icons import Icon
from app.resources.logos import Logo
from app.resources.templates import Template
from app.resources.watermarks import Watermark


_ResourceKey = TypeVar("_ResourceKey", bound=Enum)


class ResourceManager:
    """Résout les clés métier vers des fichiers locaux vérifiés."""

    def __init__(
        self,
        resource_root: str | PathLike[str] | None = None,
    ) -> None:
        if resource_root is None:
            root = Path(__file__).resolve().parent
        elif isinstance(resource_root, (str, PathLike)):
            root = Path(resource_root).resolve()
        else:
            raise TypeError("resource_root doit être un chemin ou None.")

        if not root.is_dir():
            raise ValueError("resource_root doit désigner un dossier existant.")
        self._resource_root = root

    def logo(self, resource: Logo) -> Path:
        """Retourne le chemin d'un logo officiel."""

        return self._resolve(resource, Logo, LOGO_CATALOG)

    def icon(self, resource: Icon) -> Path:
        """Retourne le chemin d'une icône officielle."""

        return self._resolve(resource, Icon, ICON_CATALOG)

    def banner(self, resource: Banner) -> Path:
        """Retourne le chemin d'une bannière officielle."""

        return self._resolve(resource, Banner, BANNER_CATALOG)

    def watermark(self, resource: Watermark) -> Path:
        """Retourne le chemin d'un filigrane officiel."""

        return self._resolve(resource, Watermark, WATERMARK_CATALOG)

    def template(self, resource: Template) -> Path:
        """Retourne le chemin d'un modèle documentaire officiel."""

        return self._resolve(resource, Template, TEMPLATE_CATALOG)

    def font(self, resource: Font) -> Path:
        """Retourne le chemin d'une police officielle."""

        return self._resolve(resource, Font, FONT_CATALOG)

    def application_resource(self, resource: ApplicationResource) -> Path:
        """Retourne le chemin d'une ressource technique officielle."""

        return self._resolve(
            resource,
            ApplicationResource,
            APPLICATION_RESOURCE_CATALOG,
        )

    def _resolve(
        self,
        resource: _ResourceKey,
        expected_type: type[_ResourceKey],
        catalog: Mapping[_ResourceKey, str],
    ) -> Path:
        if not isinstance(resource, expected_type):
            raise TypeError(
                f"resource doit être une valeur {expected_type.__name__}."
            )

        try:
            relative_path = catalog[resource]
        except KeyError as exc:
            raise ResourceNotFoundError(resource) from exc

        if not isinstance(relative_path, str) or not relative_path:
            raise ResourceNotFoundError(resource)

        candidate = (self._resource_root / relative_path).resolve()
        try:
            candidate.relative_to(self._resource_root)
        except ValueError as exc:
            raise ResourceNotFoundError(resource, candidate) from exc

        if not candidate.is_file():
            raise ResourceNotFoundError(resource, candidate)
        return candidate
