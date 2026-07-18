"""Registre des sources participant à la cartographie opérationnelle."""

from app.providers.map_provider import MapProvider


class MapRegistry:
    """Centralise les providers cartographiques enregistrés au démarrage."""

    def __init__(self):
        self._providers = []

    def register(self, provider):
        if not isinstance(provider, MapProvider):
            raise TypeError("Un provider cartographique doit implémenter MapProvider.")
        self._providers.append(provider)

    def get_map_items(self):
        items = []
        for provider in self._providers:
            items.extend(provider.get_map_items())
        return items
