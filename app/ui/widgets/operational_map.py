"""Widget Leaflet de la cartographie opérationnelle."""

import json
import math
from pathlib import Path
from urllib.parse import quote

from PySide6.QtCore import QObject, QUrl, Signal, Slot
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView


_MAP_PAGE = Path(__file__).resolve().parents[2] / "resources" / "map" / "operational_map.html"

_MAP_CONFIGURATION = {
    "defaultCenter": [43.3336, 3.1200],
    "defaultZoom": 14,
    "singleItemZoom": 17,
    "fitMaxZoom": 17,
    "tileLayer": {
        "url": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        "attribution": (
            '&copy; <a href="https://www.openstreetmap.org/copyright">'
            "OpenStreetMap</a> contributors"
        ),
        "minZoom": 0,
        "maxZoom": 19,
    },
}


def _prepare_map_items(items):
    """Construit les données Web et leur table de résolution Python."""
    serialized = []
    items_by_key = {}
    used_keys = set()

    for index, item in enumerate(items):
        try:
            latitude = float(item.latitude)
            longitude = float(item.longitude)
        except (AttributeError, TypeError, ValueError):
            continue

        if (
            not math.isfinite(latitude)
            or not math.isfinite(longitude)
            or not -90 <= latitude <= 90
            or not -180 <= longitude <= 180
        ):
            continue

        source = str(getattr(item, "source", "") or "")
        item_id = getattr(item, "id", None)
        readable_id = item_id if item_id is not None else f"missing-{index}"
        base_key = f"{quote(source, safe='')}:{quote(str(readable_id), safe='')}"
        key = base_key
        duplicate_number = 2
        while key in used_keys:
            key = f"{base_key}~{duplicate_number}"
            duplicate_number += 1
        used_keys.add(key)
        items_by_key[key] = item
        serialized.append(
            {
                "key": key,
                "title": str(getattr(item, "title", "") or ""),
                "subtitle": str(getattr(item, "subtitle", "") or ""),
                "latitude": latitude,
                "longitude": longitude,
                "color": str(getattr(item, "color", "") or ""),
                "icon": str(getattr(item, "icon", "") or ""),
            }
        )

    return serialized, items_by_key


def _serialize_map_items(items):
    """Retourne les éléments valides sous une forme JSON-compatible."""
    return _prepare_map_items(items)[0]


class _MapEventBridge(QObject):
    """Passerelle Web limitée aux événements émis par la carte."""

    def __init__(self, selection_handler, parent=None):
        super().__init__(parent)
        self._selection_handler = selection_handler

    @Slot(str)
    def selectMarker(self, key):
        self._selection_handler(key)


class OperationalMap(QWebEngineView):
    """Carte Leaflet conservant le contrat du précédent widget graphique."""

    itemSelected = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []
        self._serialized_items = []
        self._items_by_key = {}
        self._selected_key = None
        self._focused_location = None
        self._page_ready = False
        self._fit_pending = False

        self._event_bridge = _MapEventBridge(self._handle_marker_selected, self)
        self._web_channel = QWebChannel(self.page())
        self._web_channel.registerObject("mapEvents", self._event_bridge)
        self.page().setWebChannel(self._web_channel)

        self.settings().setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls,
            True,
        )
        self.loadFinished.connect(self._on_load_finished)
        self.load(QUrl.fromLocalFile(str(_MAP_PAGE)))

    def set_items(self, items):
        """Mémorise et affiche le dernier état cartographique reçu."""
        candidates = list(items)
        serialized, items_by_key = _prepare_map_items(candidates)

        self._items = candidates
        self._serialized_items = serialized
        self._items_by_key = items_by_key
        if self._selected_key not in self._items_by_key:
            self._selected_key = None
        self._fit_pending = True

        if self._page_ready:
            self._send_items()

    def fit_to_items(self):
        """Cadre les marqueurs, ou revient au centre par défaut."""
        if not self._page_ready:
            self._fit_pending = True
            return

        self.page().runJavaScript("window.PMPOperationalMap.fitToItems();")
        self._fit_pending = False

    def focus_location(self, latitude, longitude, label=""):
        """Centre la carte sur un repère temporaire indépendant du métier."""
        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except (TypeError, ValueError):
            return False
        if (
            not math.isfinite(latitude)
            or not math.isfinite(longitude)
            or not -90 <= latitude <= 90
            or not -180 <= longitude <= 180
        ):
            return False

        self._focused_location = {
            "latitude": latitude,
            "longitude": longitude,
            "label": str(label or ""),
        }
        if self._page_ready:
            self._send_focused_location()
        return True

    def _on_load_finished(self, success):
        self._page_ready = bool(success)
        if not self._page_ready:
            return

        self._send_configuration()
        self._send_items()
        if self._focused_location is not None:
            self._send_focused_location()

    def _send_configuration(self):
        payload = json.dumps(_MAP_CONFIGURATION, ensure_ascii=False)
        self.page().runJavaScript(
            f"window.PMPOperationalMap.configure({payload});"
        )

    def _send_items(self):
        payload = json.dumps(
            self._serialized_items,
            ensure_ascii=False,
            allow_nan=False,
        )
        self.page().runJavaScript(
            "window.PMPOperationalMap.setItems("
            f"{payload}, {json.dumps(self._selected_key)}"
            ");"
        )
        self._fit_pending = False

    def _send_focused_location(self):
        payload = json.dumps(
            self._focused_location,
            ensure_ascii=False,
            allow_nan=False,
        )
        self.page().runJavaScript(
            f"window.PMPOperationalMap.focusLocation({payload});"
        )

    def _handle_marker_selected(self, key):
        item = self._items_by_key.get(key)
        if item is None:
            return

        self._selected_key = key
        self.itemSelected.emit(item)
