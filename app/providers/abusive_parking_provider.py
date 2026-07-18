"""Publication cartographique des surveillances de stationnement."""

from app.models.map_item import MapItem
from app.providers.map_provider import MapProvider
from app.services.abusive_parking_service import AbusiveParkingService


class AbusiveParkingProvider(MapProvider):
    """Convertit les surveillances géolocalisées en ``MapItem``."""

    source = "abusive_parking"

    def __init__(self, service=None):
        self.service = service or AbusiveParkingService()

    def get_map_items(self):
        items = []
        for parking in self.service.get_all():
            if parking.latitude is None or parking.longitude is None:
                continue
            vehicle = " ".join(value for value in (parking.brand, parking.model) if value)
            status = parking.status or "active"
            items.append(MapItem(
                id=parking.id, source=self.source, type=status,
                title=parking.registration,
                subtitle=vehicle or parking.location or "Lieu non renseigné",
                latitude=float(parking.latitude), longitude=float(parking.longitude),
                color=self._status_color(status), icon="vehicle",
                photo_path=parking.photo_path or "",
            ))
        return items

    @staticmethod
    def _status_color(status):
        return {"active": "#d97706", "vehicle_moved": "#15803d", "impounded": "#b91c1c"}.get(status, "#475569")
