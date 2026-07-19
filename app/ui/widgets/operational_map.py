"""Widget Leaflet de la cartographie opérationnelle."""

import json
import math
from pathlib import Path

from PySide6.QtCore import QUrl, Signal
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


def _serialize_map_items(items):
    """Retourne les éléments valides sous une forme JSON-compatible."""
    serialized = []

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
        key = f"{source}:{item_id if item_id is not None else index}"
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

    return serialized


class OperationalMap(QWebEngineView):
    """Carte Leaflet conservant le contrat du précédent widget graphique."""

    itemSelected = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []
        self._serialized_items = []
        self._page_ready = False
        self._fit_pending = False

        self.settings().setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls,
            True,
        )
        self.loadFinished.connect(self._on_load_finished)
        self.load(QUrl.fromLocalFile(str(_MAP_PAGE)))

    def set_items(self, items):
        """Mémorise et affiche le dernier état cartographique reçu."""
        candidates = list(items)
        serialized = _serialize_map_items(candidates)

        self._items = candidates
        self._serialized_items = serialized
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

    def _on_load_finished(self, success):
        self._page_ready = bool(success)
        if not self._page_ready:
            return

        self._send_configuration()
        self._send_items()

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
            f"window.PMPOperationalMap.setItems({payload});"
        )
        self._fit_pending = False
