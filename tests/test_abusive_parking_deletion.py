from types import SimpleNamespace

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMessageBox

from app.models.abusive_parking import AbusiveParking
from tests.test_abusive_parking_form_mode import _stateful_page


class FakePassageService:
    def __init__(self, passages=None):
        self.passages = list(passages or [])

    def get_by_parking(self, parking_id):
        return list(self.passages)


def _prepare_confirmation(monkeypatch, confirmed):
    def add_button(box, text, role):
        button = object()
        if role == QMessageBox.DestructiveRole:
            box._test_delete_button = button
        return button

    monkeypatch.setattr(QMessageBox, "addButton", add_button)
    monkeypatch.setattr(
        QMessageBox,
        "setDefaultButton",
        lambda box, button: None,
    )
    monkeypatch.setattr(
        QMessageBox,
        "setEscapeButton",
        lambda box, button: None,
    )
    monkeypatch.setattr(QMessageBox, "exec", lambda box: 0)
    monkeypatch.setattr(
        QMessageBox,
        "clickedButton",
        lambda box: (
            box._test_delete_button if confirmed else None
        ),
    )


def _open_for_editing():
    parking = AbusiveParking(
        id=42,
        registration="AA-123-AA",
        brand="Marque",
        model="Modèle",
        location="Place centrale",
    )
    page, service = _stateful_page([parking])
    page.passage_service = FakePassageService()
    page.active_table.cellDoubleClicked.emit(0, 0)
    return page, service, parking


def test_delete_button_follows_form_mode_and_requires_valid_id():
    page, _ = _stateful_page()
    assert not page.btn_delete.isEnabled()

    page.editing_parking = AbusiveParking(
        registration="Sans identifiant"
    )
    page._set_form_mode(True)
    assert not page.btn_delete.isEnabled()

    page.editing_parking.id = 7
    page._set_form_mode(True)
    assert page.btn_delete.isEnabled()


def test_single_click_and_history_do_not_enable_deletion():
    page, _ = _stateful_page(
        [AbusiveParking(id=7, registration="AA-123-AA")]
    )
    page.show()
    QApplication.processEvents()

    item = page.active_table.item(0, 0)
    QTest.mouseClick(
        page.active_table.viewport(),
        Qt.MouseButton.LeftButton,
        pos=page.active_table.visualItemRect(item).center(),
    )
    assert page.selected_parking.id == 7
    assert page.editing_parking is None
    assert not page.btn_delete.isEnabled()

    page.tabs.setCurrentWidget(page.history_tab)
    assert not page.btn_delete.isEnabled()


def test_cancel_keeps_form_and_does_not_call_service(
    monkeypatch,
):
    page, service, parking = _open_for_editing()
    delete_calls = []
    service.delete_monitoring = delete_calls.append
    _prepare_confirmation(monkeypatch, confirmed=False)

    page.btn_delete.click()

    assert delete_calls == []
    assert page.editing_parking is parking
    assert page.btn_delete.isEnabled()


def test_confirmation_deletes_captured_editing_id_and_resets_form(
    monkeypatch,
):
    page, service, _ = _open_for_editing()
    delete_calls = []

    def delete_monitoring(parking_id):
        delete_calls.append(parking_id)
        service.parkings.clear()
        return SimpleNamespace(has_file_warnings=False)

    service.delete_monitoring = delete_monitoring
    _prepare_confirmation(monkeypatch, confirmed=True)

    page.btn_delete.click()

    assert delete_calls == [42]
    assert page.editing_parking is None
    assert not page.btn_delete.isEnabled()


def test_first_click_after_deletion_displays_remaining_detail(monkeypatch):
    first = AbusiveParking(id=41, registration="AA-123-AA")
    second = AbusiveParking(id=42, registration="BB-456-BB")
    page, service = _stateful_page([first, second])
    page.passage_service = FakePassageService()
    page.show()
    page.active_table.cellDoubleClicked.emit(0, 0)

    def delete_monitoring(parking_id):
        service.parkings = [
            parking for parking in service.parkings
            if parking.id != parking_id
        ]
        return SimpleNamespace(has_file_warnings=False)

    service.delete_monitoring = delete_monitoring
    _prepare_confirmation(monkeypatch, confirmed=True)
    page.btn_delete.click()

    item = page.active_table.item(0, 0)
    QTest.mouseClick(
        page.active_table.viewport(),
        Qt.MouseButton.LeftButton,
        pos=page.active_table.visualItemRect(item).center(),
    )

    assert page.selected_parking.id == 42
    assert "BB-456-BB" in page.detail_label.text()


def test_failure_keeps_form_and_reenables_button(
    monkeypatch,
):
    page, service, parking = _open_for_editing()

    def fail(parking_id):
        raise RuntimeError("SQLite indisponible")

    service.delete_monitoring = fail
    _prepare_confirmation(monkeypatch, confirmed=True)
    monkeypatch.setattr(
        QMessageBox,
        "critical",
        lambda *args, **kwargs: None,
    )

    page.btn_delete.click()

    assert page.editing_parking is parking
    assert page.btn_delete.isEnabled()


def test_reentrant_delete_is_ignored(monkeypatch):
    page, service, _ = _open_for_editing()
    delete_calls = []

    def delete_monitoring(parking_id):
        delete_calls.append(parking_id)
        page.delete_monitoring()
        service.parkings.clear()
        return SimpleNamespace(has_file_warnings=False)

    service.delete_monitoring = delete_monitoring
    _prepare_confirmation(monkeypatch, confirmed=True)

    page.btn_delete.click()

    assert delete_calls == [42]
