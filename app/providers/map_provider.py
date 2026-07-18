"""Contrat des sources de données cartographiques."""

from abc import ABC, abstractmethod
from collections.abc import Iterable

from app.models.map_item import MapItem


class MapProvider(ABC):
    """Expose une source métier sous forme d'éléments cartographiques."""

    @abstractmethod
    def get_map_items(self) -> Iterable[MapItem]:
        """Retourne les éléments géolocalisés publiés par la source."""
