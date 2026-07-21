from datetime import date

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
    def add_monitoring(self, parking):
        raise NotImplementedError

    def update_monitoring(self, parking):
        raise NotImplementedError

    def delete_monitoring(self, parking_id):
        raise NotImplementedError

    def get_all(self):
        return self.get_active() + self.get_history()

    def get_active(self):
        return []

    def get_history(self):
        return []

    def get_by_id(self, parking_id):
        return next(
            (parking for parking in self.get_all() if parking.id == parking_id),
            None,
        )

    def get_by_registration(self, registration):
        return next(
            (
                parking
                for parking in self.get_all()
                if parking.registration == registration
            ),
            None,
        )

    def close_monitoring(self, parking_id, reason):
        raise NotImplementedError

    def get_days_elapsed(self, parking):
        if parking.monitoring_date is None:
            return 0
        return (date.today() - parking.monitoring_date).days

    def get_days_remaining(self, parking):
        return parking.monitoring_delay_days - self.get_days_elapsed(parking)

    def is_due(self, parking):
        return self.get_days_remaining(parking) <= 0

    def get_due_soon(self):
        vehicles = [
            parking
            for parking in self.get_active()
            if self.get_days_remaining(parking) <= 2
        ]
        return sorted(vehicles, key=self.get_days_remaining)

    def get_overdue(self):
        vehicles = [parking for parking in self.get_active() if self.is_due(parking)]
        return sorted(vehicles, key=self.get_days_remaining)

    def count_active(self):
        return len(self.get_active())

    def count_history(self):
        return len(self.get_history())

    def count_due_soon(self):
        return len(self.get_due_soon())

    def count_overdue(self):
        return len(self.get_overdue())


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
