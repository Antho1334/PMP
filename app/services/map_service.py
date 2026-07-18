"""Service transverse de consultation de la cartographie."""


class MapService:
    """Interroge exclusivement le registre des providers cartographiques."""

    def __init__(self, registry):
        self.registry = registry

    def get_items(self, sources=None):
        items = self.registry.get_map_items()
        if sources is None:
            return items
        sources = set(sources)
        return [item for item in items if item.source in sources]
