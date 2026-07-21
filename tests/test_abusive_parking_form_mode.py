from app.models.abusive_parking import AbusiveParking

from tests.test_abusive_parking_geocoding import (
    FakeGeocodingService,
    FakeParkingService,
    _application,
)
from app.ui.pages.abusive_parking_page import AbusiveParkingPage


class StatefulParkingService(FakeParkingService):
    def __init__(self, parkings=None):
        self.parkings = list(parkings or [])
        self.add_calls = 0
        self.update_calls = 0
        self._next_id = max(
            (parking.id or 0 for parking in self.parkings),
            default=0,
        ) + 1

    def get_active(self):
        return list(self.parkings)

    def add_monitoring(self, parking):
        self.add_calls += 1
        parking.id = self._next_id
        self._next_id += 1
        self.parkings.append(parking)

    def update_monitoring(self, parking):
        self.update_calls += 1
        for index, current in enumerate(self.parkings):
            if current.id == parking.id:
                self.parkings[index] = parking
                return
        raise AssertionError("La ligne à modifier n'existe pas.")


def _stateful_page(parkings=None):
    _application()
    service = StatefulParkingService(parkings)
    page = AbusiveParkingPage(
        service=service,
        geocoding_service=FakeGeocodingService(),
    )
    return page, service


def test_primary_button_dispatches_to_add_in_creation_mode():
    page, _ = _stateful_page()
    calls = []
    page.add_monitoring = lambda: calls.append("add")
    page.update_monitoring = lambda: calls.append("update")

    page.btn_save.click()

    assert calls == ["add"]
    assert page.btn_save.text() == "Enregistrer"


def test_primary_button_dispatches_to_update_in_edit_mode():
    page, _ = _stateful_page()
    calls = []
    page.add_monitoring = lambda: calls.append("add")
    page.update_monitoring = lambda: calls.append("update")
    page.editing_parking = AbusiveParking(
        id=7,
        registration="AA-123-AA",
    )
    page._set_form_mode(True)

    page.btn_save.click()

    assert calls == ["update"]
    assert page.btn_save.text() == "Enregistrer les modifications"


def test_creation_increases_the_row_count_by_one():
    page, service = _stateful_page()
    page.registration_input.setText("AA-123-AA")
    initial_count = len(service.parkings)

    page.btn_save.click()

    assert len(service.parkings) == initial_count + 1
    assert service.add_calls == 1
    assert service.update_calls == 0


def test_double_click_keeps_id_and_update_changes_existing_row_only():
    existing = AbusiveParking(
        id=42,
        registration="AA-123-AA",
        brand="Ancienne marque",
    )
    page, service = _stateful_page([existing])
    initial_count = len(service.parkings)

    page.active_table.cellDoubleClicked.emit(0, 0)
    assert page.editing_parking is existing
    assert page.editing_parking.id == 42

    page.brand_input.setText("Nouvelle marque")
    page.btn_save.click()

    assert len(service.parkings) == initial_count
    assert service.add_calls == 0
    assert service.update_calls == 1
    assert service.parkings[0].id == 42
    assert service.parkings[0].brand == "Nouvelle marque"
    assert page.editing_parking is None
    assert page.btn_save.text() == "Enregistrer"


def test_new_button_returns_to_creation_mode():
    page, _ = _stateful_page(
        [AbusiveParking(id=7, registration="AA-123-AA")]
    )
    page.active_table.cellDoubleClicked.emit(0, 0)

    page.btn_new.click()

    assert page.editing_parking is None
    assert page.btn_save.text() == "Enregistrer"


def test_mode_changes_do_not_create_multiple_clicked_connections():
    page, _ = _stateful_page()
    calls = []
    page.add_monitoring = lambda: calls.append("add")
    page.update_monitoring = lambda: calls.append("update")

    for identifier in (1, 2, 3):
        page.editing_parking = AbusiveParking(
            id=identifier,
            registration="AA-123-AA",
        )
        page._set_form_mode(True)
        page.editing_parking = None
        page._set_form_mode(False)

    page.btn_save.click()

    assert calls == ["add"]
