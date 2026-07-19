"""Test réel du fournisseur, désactivé sans autorisation réseau explicite."""

import os

import pytest
from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication

from app.services.geocoding_service import GeocodingService


pytestmark = pytest.mark.skipif(
    os.environ.get("PMP_RUN_NETWORK_TESTS") != "1",
    reason=(
        "Test réseau désactivé. Définir PMP_RUN_NETWORK_TESTS=1 "
        "pour interroger la Géoplateforme."
    ),
)


def test_geoplatform_returns_an_address():
    app = QApplication.instance() or QApplication([])
    service = GeocodingService()
    results = []
    errors = []
    loop = QEventLoop()
    service.resultsReady.connect(
        lambda _request_id, values: (results.extend(values), loop.quit())
    )
    service.searchFailed.connect(
        lambda _request_id, message: (errors.append(message), loop.quit())
    )
    QTimer.singleShot(12_000, loop.quit)

    service.search("Mairie de Montady 34310")
    loop.exec()
    app.processEvents()

    assert not errors
    assert results
    assert all(-90 <= result.latitude <= 90 for result in results)
