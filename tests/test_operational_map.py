import json
import math

from app.models.map_item import MapItem
from app.ui.widgets.operational_map import (
    OperationalMap,
    _prepare_map_items,
    _serialize_map_items,
)


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


def test_item_table_uses_readable_source_and_id_key():
    item = MapItem(
        id=42,
        source="abusive_parking",
        latitude=43.3,
        longitude=3.1,
    )

    serialized, items_by_key = _prepare_map_items([item])

    assert serialized[0]["key"] == "abusive_parking:42"
    assert items_by_key["abusive_parking:42"] is item


def test_same_numeric_id_from_different_sources_stays_distinct():
    parking = MapItem(
        id=42, source="parking", latitude=43.3, longitude=3.1
    )
    intervention = MapItem(
        id=42, source="interventions", latitude=43.4, longitude=3.2
    )

    _, items_by_key = _prepare_map_items([parking, intervention])

    assert items_by_key["parking:42"] is parking
    assert items_by_key["interventions:42"] is intervention


def test_missing_and_duplicate_ids_receive_unique_fallback_keys():
    first = MapItem(source="parking", latitude=43.3, longitude=3.1)
    second = MapItem(source="parking", latitude=43.4, longitude=3.2)
    duplicate_a = MapItem(
        id=7, source="parking", latitude=43.5, longitude=3.3
    )
    duplicate_b = MapItem(
        id=7, source="parking", latitude=43.6, longitude=3.4
    )

    serialized, items_by_key = _prepare_map_items(
        [first, second, duplicate_a, duplicate_b]
    )
    keys = [item["key"] for item in serialized]

    assert len(keys) == len(set(keys))
    assert keys == [
        "parking:missing-0",
        "parking:missing-1",
        "parking:7",
        "parking:7~2",
    ]
    assert items_by_key["parking:7~2"] is duplicate_b


class _SignalRecorder:
    def __init__(self):
        self.values = []

    def emit(self, value):
        self.values.append(value)


def test_known_key_emits_original_item_once():
    item = MapItem(id=4, source="parking")
    widget = type("WidgetState", (), {})()
    widget._items_by_key = {"parking:4": item}
    widget._selected_key = None
    widget.itemSelected = _SignalRecorder()

    OperationalMap._handle_marker_selected(widget, "parking:4")

    assert widget._selected_key == "parking:4"
    assert widget.itemSelected.values == [item]


def test_unknown_key_is_ignored():
    widget = type("WidgetState", (), {})()
    widget._items_by_key = {}
    widget._selected_key = None
    widget.itemSelected = _SignalRecorder()

    OperationalMap._handle_marker_selected(widget, "unknown:1")

    assert widget._selected_key is None
    assert widget.itemSelected.values == []


def test_selection_is_kept_only_while_item_still_exists():
    selected = MapItem(
        id=4, source="parking", latitude=43.3, longitude=3.1
    )
    replacement = MapItem(
        id=5, source="parking", latitude=43.4, longitude=3.2
    )
    widget = type("WidgetState", (), {})()
    widget._items = []
    widget._serialized_items = []
    widget._items_by_key = {}
    widget._selected_key = "parking:4"
    widget._page_ready = False
    widget._fit_pending = False

    OperationalMap.set_items(widget, [selected])
    assert widget._selected_key == "parking:4"

    OperationalMap.set_items(widget, [replacement])
    assert widget._selected_key is None


def test_items_received_before_page_load_are_sent_when_ready():
    item = MapItem(
        id=4, source="parking", latitude=43.3, longitude=3.1
    )
    calls = []
    widget = type("WidgetState", (), {})()
    widget._items = []
    widget._serialized_items = []
    widget._items_by_key = {}
    widget._selected_key = None
    widget._page_ready = False
    widget._fit_pending = False
    widget._send_configuration = lambda: calls.append("configuration")
    widget._send_items = lambda: calls.append(
        ("items", widget._serialized_items)
    )

    OperationalMap.set_items(widget, [item])
    assert calls == []

    OperationalMap._on_load_finished(widget, True)

    assert calls[0] == "configuration"
    assert calls[1][0] == "items"
    assert calls[1][1][0]["key"] == "parking:4"
