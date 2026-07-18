from app.models.map_item import MapItem
from app.providers.abusive_parking_provider import AbusiveParkingProvider
from app.providers.map_provider import MapProvider
from app.services.map_registry import MapRegistry
from app.services.map_service import MapService


class FakeProvider(MapProvider):
    def get_map_items(self):
        return [MapItem(id="item-1", source="interventions", title="Test", latitude=48.0, longitude=2.0)]


def test_registry_aggregates_registered_providers():
    registry = MapRegistry()
    registry.register(FakeProvider())

    items = registry.get_map_items()

    assert len(items) == 1
    assert items[0].source == "interventions"


def test_map_service_filters_only_registry_items():
    registry = MapRegistry()
    registry.register(FakeProvider())

    service = MapService(registry)

    assert len(service.get_items()) == 1
    assert service.get_items(["abusive_parking"]) == []
    assert len(service.get_items(["interventions"])) == 1


def test_abusive_parking_provider_converts_only_geolocated_items():
    parking = type("Parking", (), {
        "id": 7, "registration": "AA-123-AA", "brand": "Test", "model": "Car",
        "location": "Place centrale", "latitude": 48.0, "longitude": 2.0,
        "status": "active", "photo_path": None,
    })()
    missing_coordinates = type("Parking", (), {"latitude": None, "longitude": None})()
    service = type("Service", (), {"get_all": lambda self: [parking, missing_coordinates]})()

    items = AbusiveParkingProvider(service).get_map_items()

    assert len(items) == 1
    assert items[0].source == "abusive_parking"
    assert items[0].title == "AA-123-AA"
