"""Composant réutilisable de recherche et sélection d'adresse."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class GeocodingSearchWidget(QWidget):
    """Présente les résultats d'un service de géocodage injecté."""

    resultSelected = Signal(object)

    def __init__(
        self,
        geocoding_service,
        parent=None,
        selection_button_text="Centrer sur ce résultat",
    ):
        super().__init__(parent)
        self._service = geocoding_service
        self._active_request_id = None
        self._results = []
        self._selection_button_text = selection_button_text
        self._build_ui()

        self._service.resultsReady.connect(self._show_results)
        self._service.searchFailed.connect(self._show_error)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Adresse :"))
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText(
            "Ex. 1 place de la Mairie, 34310 Montady"
        )
        self.search_button = QPushButton("Rechercher")
        self.query_input.returnPressed.connect(self.search)
        self.search_button.clicked.connect(self.search)
        search_layout.addWidget(self.query_input, 1)
        search_layout.addWidget(self.search_button)
        layout.addLayout(search_layout)

        self.results_list = QListWidget()
        self.results_list.setVisible(False)
        self.results_list.currentRowChanged.connect(
            self._update_selection_button
        )
        layout.addWidget(self.results_list)

        action_layout = QHBoxLayout()
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.select_button = QPushButton(self._selection_button_text)
        self.select_button.setEnabled(False)
        self.select_button.clicked.connect(self._select_current_result)
        action_layout.addWidget(self.status_label, 1)
        action_layout.addWidget(self.select_button)
        layout.addLayout(action_layout)

    def search(self):
        query = self.query_input.text()
        self._set_busy(True)
        try:
            request_id = self._service.search(query)
        except ValueError as error:
            self._set_busy(False)
            self.status_label.setText(str(error))
            return

        self._active_request_id = request_id
        self._results = []
        self.results_list.clear()
        self.results_list.setVisible(False)
        self.select_button.setEnabled(False)
        self.status_label.setText("Recherche en cours…")

    def _show_results(self, request_id, results):
        if request_id != self._active_request_id:
            return

        self._active_request_id = None
        self._set_busy(False)
        self._results = list(results)
        self.results_list.clear()

        for index, result in enumerate(self._results):
            details = " — ".join(
                value for value in (result.postcode, result.city) if value
            )
            text = result.label
            if details and details.lower() not in text.lower():
                text = f"{text} ({details})"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, index)
            self.results_list.addItem(item)

        self.results_list.setVisible(bool(self._results))
        self.select_button.setEnabled(False)
        if self._results:
            self.status_label.setText(
                f"{len(self._results)} résultat(s). Sélectionnez une adresse."
            )
        else:
            self.status_label.setText(
                "Aucune adresse ne correspond à cette recherche."
            )

    def _show_error(self, request_id, message):
        if request_id != self._active_request_id:
            return
        self._active_request_id = None
        self._set_busy(False)
        self.select_button.setEnabled(False)
        self.status_label.setText(message)

    def _update_selection_button(self, row):
        self.select_button.setEnabled(
            self._active_request_id is None
            and 0 <= row < len(self._results)
        )

    def _select_current_result(self):
        row = self.results_list.currentRow()
        if not 0 <= row < len(self._results):
            return
        self.resultSelected.emit(self._results[row])

    def _set_busy(self, busy):
        self.query_input.setEnabled(not busy)
        self.search_button.setEnabled(not busy)

    def set_query(self, query):
        """Préremplit la recherche sans la lancer."""
        self.query_input.setText(str(query or ""))

    def reset(self):
        """Réinitialise la recherche sans modifier le formulaire parent."""
        self._active_request_id = None
        self._results = []
        self.query_input.clear()
        self.results_list.clear()
        self.results_list.setVisible(False)
        self.select_button.setEnabled(False)
        self.status_label.clear()
        self._set_busy(False)
