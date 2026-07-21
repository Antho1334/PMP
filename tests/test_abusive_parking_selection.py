from datetime import date, time

from PySide6.QtCore import Qt, QItemSelectionModel
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QAbstractItemView

from app.models.abusive_parking import AbusiveParking
from tests.test_abusive_parking_form_mode import _stateful_page
from tests.test_abusive_parking_geocoding import _application


def _page_with_two_rows():
    return _stateful_page(
        [
            AbusiveParking(
                id=1,
                registration="AA-123-AA",
                location="Place A",
            ),
            AbusiveParking(
                id=2,
                registration="BB-456-BB",
                location="Place B",
            ),
        ]
    )[0]


def _click_row(page, row):
    _application().processEvents()
    item = page.active_table.item(row, 0)
    position = page.active_table.visualItemRect(item).center()
    QTest.mouseClick(
        page.active_table.viewport(),
        Qt.MouseButton.LeftButton,
        pos=position,
    )


def test_first_mouse_click_displays_selected_detail():
    page = _page_with_two_rows()
    page.show()

    _click_row(page, 0)

    assert page.selected_parking.id == 1
    assert "AA-123-AA" in page.detail_label.text()
    assert page.registration_input.text() == "AA-123-AA"


def test_active_table_uses_single_row_selection():
    page = _page_with_two_rows()

    assert (
        page.active_table.selectionBehavior()
        == QAbstractItemView.SelectionBehavior.SelectRows
    )
    assert (
        page.active_table.selectionMode()
        == QAbstractItemView.SelectionMode.SingleSelection
    )


def test_clear_selection_alone_keeps_the_current_index():
    page = _page_with_two_rows()
    page.active_table.selectRow(0)

    page.active_table.clearSelection()

    assert page.active_table.currentIndex().isValid()
    assert page.active_table.currentRow() == 0
    assert page.active_table.selectedIndexes() == []
    assert page.active_table.selectionModel().selectedRows() == []


def test_new_monitoring_invalidates_current_index_and_clears_detail():
    page = _page_with_two_rows()
    page.active_table.selectRow(0)

    page.new_monitoring()

    assert not page.active_table.currentIndex().isValid()
    assert page.active_table.currentRow() == -1
    assert page.active_table.selectedIndexes() == []
    assert page.active_table.selectionModel().selectedRows() == []
    assert page.selected_parking is None
    assert "lectionnez" in page.detail_label.text()


def test_first_selection_after_new_monitoring_displays_detail():
    page = _page_with_two_rows()
    page.show()
    page.active_table.selectRow(0)
    page.new_monitoring()

    _click_row(page, 1)

    assert page.selected_parking.id == 2
    assert "BB-456-BB" in page.detail_label.text()


def test_first_click_after_creation_displays_detail():
    page, _ = _stateful_page(
        [AbusiveParking(id=1, registration="AA-123-AA")]
    )
    page.show()
    page.registration_input.setText("BB-456-BB")
    page.btn_save.click()

    _click_row(page, 1)

    assert page.selected_parking.id == 2
    assert "BB-456-BB" in page.detail_label.text()


def test_first_click_after_modification_displays_detail():
    page = _page_with_two_rows()
    page.show()
    page.active_table.cellDoubleClicked.emit(0, 0)
    page.brand_input.setText("Marque modifiee")
    page.btn_save.click()

    _click_row(page, 1)

    assert page.selected_parking.id == 2
    assert "BB-456-BB" in page.detail_label.text()


def test_programmatic_selection_change_updates_detail():
    page = _page_with_two_rows()

    page.active_table.selectRow(0)
    assert page.selected_parking.id == 1

    page.active_table.selectRow(1)
    assert page.selected_parking.id == 2
    assert "BB-456-BB" in page.detail_label.text()


def test_valid_current_index_displays_detail_when_selected_rows_is_empty():
    page = _page_with_two_rows()
    selection_model = page.active_table.selectionModel()
    current_index = page.active_table.model().index(1, 0)

    selection_model.setCurrentIndex(
        current_index,
        QItemSelectionModel.SelectionFlag.NoUpdate,
    )

    assert selection_model.selectedRows() == []
    assert page.selected_parking.id == 2
    assert "BB-456-BB" in page.detail_label.text()


def test_keyboard_navigation_updates_detail():
    page = _page_with_two_rows()
    page.show()
    page.active_table.selectRow(0)
    page.active_table.setFocus()

    QTest.keyClick(page.active_table, Qt.Key.Key_Down)

    assert page.selected_parking.id == 2
    assert "BB-456-BB" in page.detail_label.text()


def test_double_click_keeps_detail_and_enters_edit_mode():
    page = _page_with_two_rows()
    page.active_table.selectRow(0)
    assert page.editing_parking is None
    assert page.btn_save.text() == "Enregistrer"

    page.active_table.cellDoubleClicked.emit(0, 0)

    assert page.selected_parking.id == 1
    assert page.editing_parking.id == 1
    assert "AA-123-AA" in page.detail_label.text()
    assert page.btn_save.text() == "Enregistrer les modifications"


def test_load_parking_into_form_populates_fields_without_changing_state():
    page = _page_with_two_rows()
    parking = AbusiveParking(
        id=9,
        registration="CC-789-CC",
        brand="Marque",
        model="Modele",
        vehicle_type="Berline",
        color="Bleu",
        owner="Proprietaire",
        location="Place C",
        latitude=48.85,
        longitude=2.35,
        monitoring_date=date(2026, 7, 20),
        monitoring_time=time(14, 30),
        monitoring_delay_days=12,
        observations="Observation",
        photo_path=None,
    )

    page.load_parking_into_form(parking)

    assert page.selected_parking is None
    assert page.editing_parking is None
    assert page.registration_input.text() == "CC-789-CC"
    assert page.brand_input.text() == "Marque"
    assert page.model_input.text() == "Modele"
    assert page.vehicle_type_input.text() == "Berline"
    assert page.color_input.text() == "Bleu"
    assert page.owner_input.text() == "Proprietaire"
    assert page.location_input.text() == "Place C"
    assert page.latitude_input.text() == "48.85"
    assert page.longitude_input.text() == "2.35"
    assert page.monitoring_date.date().toPython() == date(2026, 7, 20)
    assert page.monitoring_time.time().toPython() == time(14, 30)
    assert page.delay_input.value() == 12
    assert page.observations_input.toPlainText() == "Observation"
    assert page.photo_name_label.text() == "Aucune photo"
    assert page.btn_save.text() == "Enregistrer"
