from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from app.models.geocoding_result import GeocodingResult
from app.ui.pages.abusive_parking_page import AbusiveParkingPage


class FakeGeocodingService(QObject):
    resultsReady = Signal(int, object)
    searchFailed = Signal(int, str)

    def search(self, query):
        return 1


class FakeParkingService:
    def get_active(self):
        return []

    def get_history(self):
        return []


def _application():
    return QApplication.instance() or QApplication([])


def _page():
    _application()
    return AbusiveParkingPage(
        service=FakeParkingService(),
        geocoding_service=FakeGeocodingService(),
    )


def test_selected_address_populates_temporary_location_state():
    page = _page()
    result = GeocodingResult(
        label="1 place de la Mairie, 34310 Montady",
        latitude=43.3336,
        longitude=3.12,
    )

    page._apply_geocoding_result(result)

    assert page.location_input.text() == result.label
    assert page._selected_latitude == result.latitude
    assert page._selected_longitude == result.longitude
    assert page._location_status == "valid"


def test_programmatic_location_update_does_not_invalidate_coordinates():
    page = _page()
    page._apply_geocoding_result(
        GeocodingResult("Adresse initiale", 43.3336, 3.12)
    )

    page.location_input.setText("Texte programmatique")

    assert page._selected_latitude == 43.3336
    assert page._selected_longitude == 3.12
    assert page._location_status == "valid"


def test_real_user_edit_invalidates_both_coordinates():
    page = _page()
    page._apply_geocoding_result(
        GeocodingResult("Adresse initiale", 43.3336, 3.12)
    )

    page.location_input.textEdited.emit("Adresse corrigée")

    assert page._selected_latitude is None
    assert page._selected_longitude is None
    assert page.latitude_input.text() == ""
    assert page.longitude_input.text() == ""
    assert page._location_status == "invalidated"


def test_manual_coordinates_are_kept_in_the_advanced_section():
    page = _page()

    assert not page.advanced_coordinates_widget.isVisible()
    page.advanced_coordinates_button.setChecked(True)
    page.latitude_input.setText("43.3336")
    page.longitude_input.setText("3.12")
    page._on_manual_coordinates_edited()

    assert page._selected_latitude == 43.3336
    assert page._selected_longitude == 3.12
    assert page._location_status == "valid"
