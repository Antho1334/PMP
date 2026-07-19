"""Tests d'intégration nécessitant un environnement Qt WebEngine graphique."""

import os

import pytest
from PySide6.QtCore import QEventLoop
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication

from app.models.map_item import MapItem
from app.ui.widgets.operational_map import OperationalMap


pytestmark = pytest.mark.skipif(
    os.environ.get("PMP_RUN_WEBENGINE_TESTS") != "1",
    reason=(
        "Test d'intégration WebEngine désactivé. Définir "
        "PMP_RUN_WEBENGINE_TESTS=1 dans un environnement graphique."
    ),
)


def test_leaflet_marker_click_emits_original_item_once():
    app = QApplication.instance() or QApplication([])
    widget = OperationalMap()
    load_spy = QSignalSpy(widget.loadFinished)
    item = MapItem(
        id=42,
        source="parking",
        title='Véhicule "signalé" <test>',
        latitude=43.3336,
        longitude=3.12,
    )
    selection_spy = QSignalSpy(widget.itemSelected)
    widget.set_items([item])
    widget.show()

    if not widget._page_ready:
        assert load_spy.wait(10_000)
    app.processEvents(QEventLoop.AllEvents, 500)

    widget.page().runJavaScript(
        "document.querySelector('.leaflet-interactive').dispatchEvent("
        "new MouseEvent('click', {bubbles: true}));"
    )

    assert selection_spy.wait(5_000)
    assert selection_spy.count() == 1
    assert selection_spy.at(0)[0] is item
    widget.close()
