import json
import math

from app.models.map_item import MapItem
from app.ui.widgets.operational_map import _serialize_map_items


def test_serialization_ignores_invalid_coordinates():
    items = [
        MapItem(id=1, latitude=43.3, longitude=3.1),
        MapItem(id=2, latitude=None, longitude=3.1),
        MapItem(id=3, latitude=91, longitude=3.1),
        MapItem(id=4, latitude=43.3, longitude=181),
        MapItem(id=5, latitude=math.nan, longitude=3.1),
    ]

    serialized = _serialize_map_items(items)

    assert len(serialized) == 1
    assert serialized[0]["key"] == ":1"


def test_serialization_produces_safe_json_data():
    item = MapItem(
        id="item-1",
        source="interventions",
        title='Véhicule "signalé"',
        subtitle="<script>alert('x')</script>",
        latitude="43.3",
        longitude="3.1",
    )

    serialized = _serialize_map_items([item])
    payload = json.dumps(serialized, ensure_ascii=False, allow_nan=False)
    restored = json.loads(payload)

    assert restored[0]["title"] == 'Véhicule "signalé"'
    assert restored[0]["subtitle"] == "<script>alert('x')</script>"
    assert restored[0]["latitude"] == 43.3
    assert restored[0]["longitude"] == 3.1
