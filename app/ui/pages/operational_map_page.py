"""Page transverse de consultation de la cartographie opérationnelle."""

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.ui.widgets.operational_map import OperationalMap
from app.ui.widgets.geocoding_search_widget import GeocodingSearchWidget


class OperationalMapPage(QWidget):
    """Affiche les données publiées par les providers enregistrés."""

    def __init__(
        self,
        map_service,
        geocoding_service,
        abusive_parking_service=None,
    ):
        super().__init__()
        self.map_service = map_service
        self.geocoding_service = geocoding_service
        self._items = []
        self._build_ui()
        self.refresh_map()
        if abusive_parking_service is not None:
            abusive_parking_service.monitoringChanged.connect(
                self.refresh_map
            )

    def _build_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("Cartographie opérationnelle")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)
        self.geocoding_search = GeocodingSearchWidget(
            self.geocoding_service
        )
        self.geocoding_search.resultSelected.connect(
            self._focus_geocoding_result
        )
        layout.addWidget(self.geocoding_search)
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Source :"))
        self.source_filter = QComboBox()
        self.source_filter.currentIndexChanged.connect(self.refresh_map)
        self.refresh_button = QPushButton("Actualiser")
        self.refresh_button.clicked.connect(self.refresh_map)
        self.fit_button = QPushButton("Cadrer les marqueurs")
        toolbar.addWidget(self.source_filter)
        toolbar.addWidget(self.refresh_button)
        toolbar.addWidget(self.fit_button)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        self.map_widget = OperationalMap()
        self.map_widget.setMinimumHeight(450)
        self.map_widget.itemSelected.connect(self._show_item_detail)
        self.fit_button.clicked.connect(self.map_widget.fit_to_items)
        layout.addWidget(self.map_widget, 1)
        self.information = QLabel()
        self.information.setWordWrap(True)
        self.information.setStyleSheet("padding: 8px; background: #f8fafc; border: 1px solid #cbd5e1;")
        layout.addWidget(self.information)

    def refresh_map(self):
        all_items = self.map_service.get_items()
        sources = sorted({item.source for item in all_items})
        current_source = self.source_filter.currentData()
        self.source_filter.blockSignals(True)
        self.source_filter.clear()
        self.source_filter.addItem("Toutes les sources", None)
        for source in sources:
            self.source_filter.addItem(source, source)
        index = self.source_filter.findData(current_source)
        self.source_filter.setCurrentIndex(index if index >= 0 else 0)
        self.source_filter.blockSignals(False)
        selected_source = self.source_filter.currentData()
        self._items = [item for item in all_items if not selected_source or item.source == selected_source]
        self.map_widget.set_items(self._items)
        if self._items:
            self.information.setText(f"{len(self._items)} marqueur(s) affiché(s). Cliquez sur un marqueur pour voir ses détails.")
        else:
            self.information.setText("Aucun élément géolocalisé n’est publié par les sources sélectionnées.")

    def _show_item_detail(self, item):
        self.information.setText(
            f"<b>{item.title}</b><br>{item.subtitle}<br>Source : {item.source}"
            f"<br>Coordonnées : {item.latitude:.6f}, {item.longitude:.6f}"
        )

    def _focus_geocoding_result(self, result):
        self.map_widget.focus_location(
            result.latitude,
            result.longitude,
            result.label,
        )
