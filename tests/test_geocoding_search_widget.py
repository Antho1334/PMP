from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from app.models.geocoding_result import GeocodingResult
from app.ui.widgets.geocoding_search_widget import GeocodingSearchWidget


class FakeGeocodingService(QObject):
    resultsReady = Signal(int, object)
    searchFailed = Signal(int, str)

    def __init__(self):
        super().__init__()
        self.queries = []

    def search(self, query):
        self.queries.append(query)
        return len(self.queries)


def _application():
    return QApplication.instance() or QApplication([])


def test_result_selection_is_explicit():
    app = _application()
    service = FakeGeocodingService()
    widget = GeocodingSearchWidget(service)
    selected = []
    widget.resultSelected.connect(selected.append)
    result = GeocodingResult(
        label='1 rue de l’Église "Centre" <ancien>',
        latitude=43.3336,
        longitude=3.12,
        postcode="34310",
        city="Montady",
    )

    widget.query_input.setText("mairie montady")
    widget.search()
    service.resultsReady.emit(1, [result])

    assert selected == []
    assert not widget.select_button.isEnabled()

    widget.results_list.setCurrentRow(0)
    assert widget.select_button.isEnabled()
    widget.select_button.click()

    assert selected == [result]
    app.processEvents()


def test_stale_results_are_ignored():
    app = _application()
    service = FakeGeocodingService()
    widget = GeocodingSearchWidget(service)

    widget.query_input.setText("première adresse")
    widget.search()
    widget._active_request_id = 2
    service.resultsReady.emit(
        1,
        [GeocodingResult("Ancien résultat", 43.3, 3.1)],
    )

    assert widget.results_list.count() == 0
    app.processEvents()


def test_network_error_keeps_query_and_reenables_search():
    app = _application()
    service = FakeGeocodingService()
    widget = GeocodingSearchWidget(service)
    widget.query_input.setText("adresse à conserver")
    widget.search()

    service.searchFailed.emit(1, "Réseau indisponible")

    assert widget.query_input.text() == "adresse à conserver"
    assert widget.search_button.isEnabled()
    assert widget.status_label.text() == "Réseau indisponible"
    app.processEvents()


def test_selection_button_text_can_be_adapted_to_the_parent_form():
    app = _application()
    widget = GeocodingSearchWidget(
        FakeGeocodingService(),
        selection_button_text="Utiliser cette adresse",
    )

    assert widget.select_button.text() == "Utiliser cette adresse"
    app.processEvents()
