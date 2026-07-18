"""Adaptateurs métier pour la cartographie opérationnelle."""

from app.models.map_item import MapItem
from app.services.abusive_parking_service import AbusiveParkingService


class MapService:
    """Publie les données métier sous un format cartographique commun."""

    SOURCE_ABUSIVE_PARKING = "abusive_parking"

    def __init__(self):
        self.abusive_parking_service = AbusiveParkingService()

    def get_items(self, sources=None):
        """Retourne les éléments géolocalisés des sources demandées."""
        sources = set(sources or [self.SOURCE_ABUSIVE_PARKING])
        items = []
        if self.SOURCE_ABUSIVE_PARKING in sources:
            items.extend(self.get_abusive_parking_items())
        return items

    def get_abusive_parking_items(self):
        items = []
        for parking in self.abusive_parking_service.get_all():
            if parking.latitude is None or parking.longitude is None:
                continue
            vehicle = " ".join(value for value in (parking.brand, parking.model) if value)
            status = parking.status or "active"
            items.append(MapItem(
                id=parking.id,
                source=self.SOURCE_ABUSIVE_PARKING,
                type=status,
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
