"""Clés logiques des ressources techniques de l'application."""

from enum import Enum


class ApplicationResource(str, Enum):
    """Identifie une ressource applicative autonome."""

    OPERATIONAL_MAP_PAGE = "operational_map_page"
