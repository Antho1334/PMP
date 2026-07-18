from datetime import date, time
from pathlib import Path
import shutil
import uuid

from PySide6.QtCore import Qt, QDate, QTime
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QSpinBox,
    QDateEdit,
    QTimeEdit,
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
    QTableWidget,
    QTableWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
    QHeaderView,
    QMessageBox,
    QFileDialog,
    QAbstractItemView,
    QGroupBox,
    QTabWidget,
    QComboBox,
)

from app.models.abusive_parking import AbusiveParking
from app.dialogs.abusive_parking_passage_dialog import (
    AbusiveParkingPassageDialog,
)
from app.services.abusive_parking_service import AbusiveParkingService
from app.services.abusive_parking_passage_service import (
    AbusiveParkingPassageService,
)
from app.services.map_service import MapService
from app.ui.widgets.operational_map import OperationalMap


class AbusiveParkingPage(QWidget):

    def __init__(self):
        super().__init__()

        self.service = AbusiveParkingService()
        self.passage_service = AbusiveParkingPassageService()
        self.map_service = MapService()

        self.parkings = []
        self.history_parkings = []

        self.selected_parking = None
        self.editing_parking = None

        self.selected_photo_path = None

        self.build_ui()

        self.refresh_active_table()
        self.refresh_history_table()

    # ==========================================================
    # CONSTRUCTION DE L'INTERFACE
    # ==========================================================

    def build_ui(self):

        main_layout = QVBoxLayout(self)

        # ------------------------------------------------------
        # TITRE
        # ------------------------------------------------------

        title = QLabel("🚗  Stationnement abusif")

        title.setStyleSheet(
            """
            font-size: 22px;
            font-weight: bold;
            """
        )

        subtitle = QLabel(
            "Gestion et suivi des véhicules placés sous surveillance"
        )

        subtitle.setStyleSheet(
            """
            color: #666666;
            font-size: 13px;
            """
        )

        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)

        # ------------------------------------------------------
        # ONGLETS
        # ------------------------------------------------------

        self.tabs = QTabWidget()

        self.active_tab = QWidget()
        self.map_tab = QWidget()
        self.history_tab = QWidget()

        self.tabs.addTab(
            self.active_tab,
            "Surveillances actives",
        )

        self.tabs.addTab(
            self.map_tab,
            "Carte",
        )

        self.tabs.addTab(
            self.history_tab,
            "Historique",
        )

        main_layout.addWidget(self.tabs)

        self.build_active_tab()
        self.build_map_tab()
        self.build_history_tab()
        self.tabs.currentChanged.connect(self._on_tab_changed)

    # ==========================================================
    # ONGLET SURVEILLANCES ACTIVES
    # ==========================================================

    def build_active_tab(self):

        main_layout = QHBoxLayout(
            self.active_tab
        )

        # ======================================================
        # FORMULAIRE
        # ======================================================

        form_group = QGroupBox(
            "Fiche de surveillance"
        )

        form_layout = QVBoxLayout(
            form_group
        )

        grid = QGridLayout()

        # ------------------------------------------------------
        # IMMATRICULATION
        # ------------------------------------------------------

        self.registration_input = QLineEdit()

        self.registration_input.setPlaceholderText(
            "Ex : AB-123-CD"
        )

        grid.addWidget(
            QLabel("Immatriculation :"),
            0,
            0,
        )

        grid.addWidget(
            self.registration_input,
            0,
            1,
        )

        # ------------------------------------------------------
        # MARQUE
        # ------------------------------------------------------

        self.brand_input = QLineEdit()

        grid.addWidget(
            QLabel("Marque :"),
            1,
            0,
        )

        grid.addWidget(
            self.brand_input,
            1,
            1,
        )

        # ------------------------------------------------------
        # MODÈLE
        # ------------------------------------------------------

        self.model_input = QLineEdit()

        grid.addWidget(
            QLabel("Modèle :"),
            2,
            0,
        )

        grid.addWidget(
            self.model_input,
            2,
            1,
        )

        # ------------------------------------------------------
        # GENRE
        # ------------------------------------------------------

        self.vehicle_type_input = QLineEdit()

        self.vehicle_type_input.setPlaceholderText(
            "Ex : VP, utilitaire, deux-roues..."
        )

        grid.addWidget(
            QLabel("Genre :"),
            3,
            0,
        )

        grid.addWidget(
            self.vehicle_type_input,
            3,
            1,
        )

        # ------------------------------------------------------
        # COULEUR
        # ------------------------------------------------------

        self.color_input = QLineEdit()

        grid.addWidget(
            QLabel("Couleur :"),
            4,
            0,
        )

        grid.addWidget(
            self.color_input,
            4,
            1,
        )

        # ------------------------------------------------------
        # PROPRIÉTAIRE
        # ------------------------------------------------------

        self.owner_input = QLineEdit()

        self.owner_input.setPlaceholderText(
            "Si connu"
        )

        grid.addWidget(
            QLabel("Propriétaire :"),
            5,
            0,
        )

        grid.addWidget(
            self.owner_input,
            5,
            1,
        )

        # ------------------------------------------------------
        # LIEU
        # ------------------------------------------------------

        self.location_input = QLineEdit()

        self.location_input.setPlaceholderText(
            "Lieu précis du stationnement"
        )

        grid.addWidget(
            QLabel("Lieu :"),
            6,
            0,
        )

        grid.addWidget(
            self.location_input,
            6,
            1,
        )

        self.latitude_input = QLineEdit()
        self.latitude_input.setPlaceholderText("Ex : 48.8566")
        self.longitude_input = QLineEdit()
        self.longitude_input.setPlaceholderText("Ex : 2.3522")
        coordinates = QWidget()
        coordinates_layout = QHBoxLayout(coordinates)
        coordinates_layout.setContentsMargins(0, 0, 0, 0)
        coordinates_layout.addWidget(QLabel("Lat."))
        coordinates_layout.addWidget(self.latitude_input)
        coordinates_layout.addWidget(QLabel("Lon."))
        coordinates_layout.addWidget(self.longitude_input)
        grid.addWidget(QLabel("Coordonnées :"), 7, 0)
        grid.addWidget(coordinates, 7, 1)

        # ------------------------------------------------------
        # DATE
        # ------------------------------------------------------

        self.monitoring_date = QDateEdit()

        self.monitoring_date.setCalendarPopup(
            True
        )

        self.monitoring_date.setDisplayFormat(
            "dd/MM/yyyy"
        )

        self.monitoring_date.setDate(
            QDate.currentDate()
        )

        grid.addWidget(
            QLabel("Date :"),
            8,
            0,
        )

        grid.addWidget(
            self.monitoring_date,
            8,
            1,
        )

        # ------------------------------------------------------
        # HEURE
        # ------------------------------------------------------

        self.monitoring_time = QTimeEdit()

        self.monitoring_time.setDisplayFormat(
            "HH:mm"
        )

        self.monitoring_time.setTime(
            QTime.currentTime()
        )

        grid.addWidget(
            QLabel("Heure :"),
            9,
            0,
        )

        grid.addWidget(
            self.monitoring_time,
            9,
            1,
        )

        # ------------------------------------------------------
        # DÉLAI
        # ------------------------------------------------------

        self.delay_input = QSpinBox()

        self.delay_input.setRange(
            1,
            365,
        )

        self.delay_input.setValue(
            7
        )

        self.delay_input.setSuffix(
            " jours"
        )

        grid.addWidget(
            QLabel("Délai :"),
            9,
            0,
        )

        grid.addWidget(
            self.delay_input,
            9,
            1,
        )

        form_layout.addLayout(grid)

        # ------------------------------------------------------
        # OBSERVATIONS
        # ------------------------------------------------------

        form_layout.addWidget(
            QLabel("Observations :")
        )

        self.observations_input = QTextEdit()

        self.observations_input.setMaximumHeight(
            100
        )

        form_layout.addWidget(
            self.observations_input
        )

        # ------------------------------------------------------
        # PHOTO
        # ------------------------------------------------------

        photo_layout = QHBoxLayout()

        self.btn_photo = QPushButton(
            "📷 Ajouter une photo"
        )

        self.photo_name_label = QLabel(
            "Aucune photo"
        )

        self.photo_name_label.setStyleSheet(
            "color: #666666;"
        )

        self.btn_photo.clicked.connect(
            self.select_photo
        )

        photo_layout.addWidget(
            self.btn_photo
        )

        photo_layout.addWidget(
            self.photo_name_label
        )

        form_layout.addLayout(
            photo_layout
        )

        # ------------------------------------------------------
        # BOUTONS
        # ------------------------------------------------------

        buttons_layout = QHBoxLayout()

        self.btn_new = QPushButton(
            "Nouvelle"
        )

        self.btn_add = QPushButton(
            "Enregistrer"
        )

        self.btn_update = QPushButton(
            "Modifier"
        )

        self.btn_new.clicked.connect(
            self.new_monitoring
        )

        self.btn_add.clicked.connect(
            self.add_monitoring
        )

        self.btn_update.clicked.connect(
            self.update_monitoring
        )

        buttons_layout.addWidget(
            self.btn_new
        )

        buttons_layout.addWidget(
            self.btn_add
        )

        buttons_layout.addWidget(
            self.btn_update
        )

        form_layout.addLayout(
            buttons_layout
        )

        main_layout.addWidget(
            form_group,
            1,
        )

        # ======================================================
        # PARTIE DROITE
        # ======================================================

        right_layout = QVBoxLayout()

        # ------------------------------------------------------
        # TABLEAU ACTIF
        # ------------------------------------------------------

        table_group = QGroupBox(
            "Véhicules actuellement sous surveillance"
        )

        table_layout = QVBoxLayout(
            table_group
        )

        self.active_table = QTableWidget()

        self.active_table.setColumnCount(
            6
        )

        self.active_table.setHorizontalHeaderLabels(
            [
                "Immatriculation",
                "Véhicule",
                "Lieu",
                "Mise en surveillance",
                "Jours écoulés",
                "Échéance",
            ]
        )

        self.active_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        self.active_table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.active_table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        self.active_table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        self.active_table.cellClicked.connect(
            self.show_parking_detail
        )

        self.active_table.cellDoubleClicked.connect(
            self.edit_parking
        )

        table_layout.addWidget(
            self.active_table
        )

        right_layout.addWidget(
            table_group,
            2,
        )

        # ------------------------------------------------------
        # DÉTAIL ACTIF
        # ------------------------------------------------------

        detail_group = QGroupBox(
            "Détail de la surveillance"
        )

        detail_layout = QVBoxLayout(
            detail_group
        )

        vehicle_layout = QHBoxLayout()

        self.photo_preview = QLabel(
            "Aucune photo"
        )

        self.photo_preview.setAlignment(
            Qt.AlignCenter
        )

        self.photo_preview.setMinimumSize(
            220,
            160,
        )

        self.photo_preview.setMaximumSize(
            300,
            220,
        )

        self.photo_preview.setStyleSheet(
            """
            border: 1px solid #cccccc;
            background-color: #f5f5f5;
            """
        )

        self.detail_label = QLabel(
            "Sélectionnez un véhicule dans le tableau."
        )

        self.detail_label.setWordWrap(
            True
        )

        self.detail_label.setAlignment(
            Qt.AlignTop
        )

        vehicle_layout.addWidget(
            self.photo_preview
        )

        vehicle_layout.addWidget(
            self.detail_label,
            1,
        )

        detail_layout.addLayout(
            vehicle_layout
        )

        self.procedure_tree = QTreeWidget()

        self.procedure_tree.setColumnCount(
            2
        )

        self.procedure_tree.setHeaderLabels(
            [
                "Date et heure",
                "Procédure",
            ]
        )

        self.procedure_tree.setRootIsDecorated(
            True
        )

        self.procedure_tree.setAlternatingRowColors(
            True
        )

        self.procedure_tree.header().setStretchLastSection(
            True
        )

        self.procedure_tree.itemClicked.connect(
            self.show_procedure_event_photo
        )

        detail_layout.addWidget(
            self.procedure_tree,
            1,
        )

        right_layout.addWidget(
            detail_group,
            1,
        )

        # ------------------------------------------------------
        # CLÔTURE
        # ------------------------------------------------------

        close_layout = QHBoxLayout()

        self.btn_new_passage = QPushButton(
            "➕ Nouveau passage"
        )

        self.btn_vehicle_moved = QPushButton(
            "Véhicule déplacé"
        )

        self.btn_impounded = QPushButton(
            "Mise en fourrière"
        )

        self.btn_vehicle_moved.clicked.connect(
            lambda: self.close_monitoring(
                "vehicle_moved"
            )
        )

        self.btn_impounded.clicked.connect(
            lambda: self.close_monitoring(
                "impounded"
            )
        )

        self.btn_new_passage.clicked.connect(
            self.add_passage
        )

        close_layout.addStretch()

        close_layout.addWidget(
            self.btn_new_passage
        )

        close_layout.addWidget(
            self.btn_vehicle_moved
        )

        close_layout.addWidget(
            self.btn_impounded
        )

        right_layout.addLayout(
            close_layout
        )

        main_layout.addLayout(
            right_layout,
            2,
        )

    # ==========================================================
    # ONGLET CARTE
    # ==========================================================

    def build_map_tab(self):
        layout = QVBoxLayout(self.map_tab)
        title = QLabel("Cartographie opérationnelle")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Afficher :"))
        self.map_status_filter = QComboBox()
        self.map_status_filter.addItem("Toutes les surveillances", None)
        self.map_status_filter.addItem("Surveillances actives", "active")
        self.map_status_filter.addItem("Véhicules déplacés", "vehicle_moved")
        self.map_status_filter.addItem("Mises en fourrière", "impounded")
        self.map_status_filter.currentIndexChanged.connect(self.refresh_map)
        self.btn_map_refresh = QPushButton("Actualiser")
        self.btn_map_refresh.clicked.connect(self.refresh_map)
        self.btn_map_fit = QPushButton("Cadrer les marqueurs")
        self.btn_map_fit.clicked.connect(lambda: self.operational_map.fit_to_items())
        toolbar.addWidget(self.map_status_filter)
        toolbar.addWidget(self.btn_map_refresh)
        toolbar.addWidget(self.btn_map_fit)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.operational_map = OperationalMap()
        self.operational_map.setMinimumHeight(400)
        self.operational_map.itemSelected.connect(self.show_map_item_detail)
        layout.addWidget(self.operational_map, 1)
        self.map_information = QLabel()
        self.map_information.setWordWrap(True)
        self.map_information.setStyleSheet("padding: 8px; background: #f8fafc; border: 1px solid #cbd5e1;")
        layout.addWidget(self.map_information)
        self.refresh_map()
        return

        layout = QVBoxLayout(
            self.map_tab
        )

        title = QLabel(
            "Carte des véhicules sous surveillance"
        )

        title.setAlignment(
            Qt.AlignCenter
        )

        title.setStyleSheet(
            """
            font-size: 20px;
            font-weight: bold;
            """
        )

        information = QLabel(
            "La cartographie interactive sera intégrée "
            "dans une prochaine étape."
        )

        information.setAlignment(
            Qt.AlignCenter
        )

        information.setStyleSheet(
            """
            color: #666666;
            font-size: 14px;
            """
        )

        layout.addStretch()

    def refresh_map(self):
        items = self.map_service.get_items()
        status = self.map_status_filter.currentData()
        if status:
            items = [item for item in items if item.type == status]
        self.operational_map.set_items(items)
        if items:
            self.map_information.setText(
                f"{len(items)} marqueur(s) affiché(s). Utilisez la molette pour zoomer, "
                "faites glisser la carte pour vous déplacer et cliquez sur un marqueur pour voir la fiche."
            )
        else:
            self.map_information.setText(
                "Aucun élément géolocalisé pour ce filtre. Renseignez latitude et longitude dans la fiche de surveillance."
            )

    def show_map_item_detail(self, item):
        self.map_information.setText(
            f"<b>{item.title}</b><br>{item.subtitle}<br>Coordonnées : "
            f"{item.latitude:.6f}, {item.longitude:.6f}"
        )
        for row, parking in enumerate(self.parkings):
            if parking.id == item.id:
                self.tabs.setCurrentWidget(self.active_tab)
                self.active_table.selectRow(row)
                self.show_parking_detail(row, 0)
                break

    def _on_tab_changed(self, index):
        if self.tabs.widget(index) is self.map_tab:
            self.refresh_map()
        return

        layout.addWidget(
            title
        )

        layout.addWidget(
            information
        )

        layout.addStretch()

    # ==========================================================
    # ONGLET HISTORIQUE V1.1
    # ==========================================================

    def build_history_tab(self):

        main_layout = QVBoxLayout(
            self.history_tab
        )

        # ------------------------------------------------------
        # BARRE DE RECHERCHE
        # ------------------------------------------------------

        search_layout = QHBoxLayout()

        search_label = QLabel(
            "Rechercher une immatriculation :"
        )

        self.history_search_input = QLineEdit()

        self.history_search_input.setPlaceholderText(
            "Ex : AB-123-CD"
        )

        self.history_search_input.returnPressed.connect(
            self.search_history
        )

        self.btn_history_search = QPushButton(
            "🔍 Rechercher"
        )

        self.btn_history_show_all = QPushButton(
            "Tout afficher"
        )

        self.btn_history_search.clicked.connect(
            self.search_history
        )

        self.btn_history_show_all.clicked.connect(
            self.show_all_history
        )

        search_layout.addWidget(
            search_label
        )

        search_layout.addWidget(
            self.history_search_input,
            1,
        )

        search_layout.addWidget(
            self.btn_history_search
        )

        search_layout.addWidget(
            self.btn_history_show_all
        )

        main_layout.addLayout(
            search_layout
        )

        # ------------------------------------------------------
        # TABLEAU HISTORIQUE
        # ------------------------------------------------------

        history_group = QGroupBox(
            "Surveillances clôturées"
        )

        history_layout = QVBoxLayout(
            history_group
        )

        self.history_table = QTableWidget()

        self.history_table.setColumnCount(
            6
        )

        self.history_table.setHorizontalHeaderLabels(
            [
                "Immatriculation",
                "Véhicule",
                "Lieu",
                "Début",
                "Fin",
                "Issue",
            ]
        )

        self.history_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        self.history_table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.history_table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        self.history_table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        self.history_table.cellClicked.connect(
            self.show_history_detail
        )

        history_layout.addWidget(
            self.history_table
        )

        main_layout.addWidget(
            history_group,
            2,
        )

        # ------------------------------------------------------
        # DÉTAIL DE L'ARCHIVE
        # ------------------------------------------------------

        detail_group = QGroupBox(
            "Détail de la surveillance archivée"
        )

        detail_layout = QHBoxLayout(
            detail_group
        )

        self.history_photo_preview = QLabel(
            "Aucune photo"
        )

        self.history_photo_preview.setAlignment(
            Qt.AlignCenter
        )

        self.history_photo_preview.setMinimumSize(
            220,
            160,
        )

        self.history_photo_preview.setMaximumSize(
            300,
            220,
        )

        self.history_photo_preview.setStyleSheet(
            """
            border: 1px solid #cccccc;
            background-color: #f5f5f5;
            """
        )

        self.history_detail_label = QLabel(
            "Sélectionnez une surveillance archivée."
        )

        self.history_detail_label.setWordWrap(
            True
        )

        self.history_detail_label.setAlignment(
            Qt.AlignTop
        )

        detail_layout.addWidget(
            self.history_photo_preview
        )

        detail_layout.addWidget(
            self.history_detail_label,
            1,
        )

        main_layout.addWidget(
            detail_group,
            1,
        )

    # ==========================================================
    # CRÉER UNE SURVEILLANCE
    # ==========================================================

    def add_monitoring(self):

        registration = (
            self.registration_input
            .text()
            .strip()
            .upper()
        )

        if not registration:

            QMessageBox.warning(
                self,
                "Champ obligatoire",
                "Veuillez renseigner l'immatriculation.",
            )

            return

        coordinates = self.get_form_coordinates()
        if coordinates is None:
            return

        qdate = self.monitoring_date.date()

        monitoring_date = date(
            qdate.year(),
            qdate.month(),
            qdate.day(),
        )

        parking = AbusiveParking(
            registration=registration,
            brand=self.brand_input.text().strip(),
            model=self.model_input.text().strip(),
            vehicle_type=(
                self.vehicle_type_input
                .text()
                .strip()
            ),
            color=self.color_input.text().strip(),
            owner=self.owner_input.text().strip(),
            location=self.location_input.text().strip(),
            latitude=coordinates[0],
            longitude=coordinates[1],
            monitoring_date=monitoring_date,
            monitoring_time=(
                self.monitoring_time
                .time()
                .toPython()
            ),
            monitoring_delay_days=(
                self.delay_input.value()
            ),
            photo_path=self.save_photo(),
            observations=(
                self.observations_input
                .toPlainText()
                .strip()
            ),
            status="active",
        )

        self.service.add_monitoring(
            parking
        )

        self.new_monitoring()

        self.refresh_active_table()
        self.refresh_history_table()
        self.refresh_map()

    # ==========================================================
    # MODIFIER
    # ==========================================================

    def update_monitoring(self):

        if self.editing_parking is None:

            QMessageBox.information(
                self,
                "Aucune surveillance",
                (
                    "Double-cliquez sur une surveillance "
                    "pour la modifier."
                ),
            )

            return

        registration = (
            self.registration_input
            .text()
            .strip()
            .upper()
        )

        if not registration:

            QMessageBox.warning(
                self,
                "Champ obligatoire",
                "Veuillez renseigner l'immatriculation.",
            )

            return

        coordinates = self.get_form_coordinates()
        if coordinates is None:
            return

        parking = self.editing_parking

        qdate = self.monitoring_date.date()

        parking.registration = registration
        parking.brand = self.brand_input.text().strip()
        parking.model = self.model_input.text().strip()

        parking.vehicle_type = (
            self.vehicle_type_input
            .text()
            .strip()
        )

        parking.color = self.color_input.text().strip()
        parking.owner = self.owner_input.text().strip()
        parking.location = self.location_input.text().strip()
        parking.latitude, parking.longitude = coordinates

        parking.monitoring_date = date(
            qdate.year(),
            qdate.month(),
            qdate.day(),
        )

        parking.monitoring_time = (
            self.monitoring_time
            .time()
            .toPython()
        )

        parking.monitoring_delay_days = (
            self.delay_input.value()
        )

        parking.observations = (
            self.observations_input
            .toPlainText()
            .strip()
        )

        if self.selected_photo_path:

            parking.photo_path = (
                self.save_photo()
            )

        self.service.update_monitoring(
            parking
        )

        self.new_monitoring()

        self.refresh_active_table()
        self.refresh_history_table()
        self.refresh_map()

    def get_form_coordinates(self):
        """Valide les coordonnées saisies, facultatives mais indissociables."""
        latitude_text = self.latitude_input.text().strip().replace(",", ".")
        longitude_text = self.longitude_input.text().strip().replace(",", ".")
        if not latitude_text and not longitude_text:
            return None, None
        try:
            latitude, longitude = float(latitude_text), float(longitude_text)
        except ValueError:
            QMessageBox.warning(self, "Coordonnées invalides", "Latitude et longitude doivent être des nombres.")
            return None
        if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
            QMessageBox.warning(self, "Coordonnées invalides", "Latitude : -90 à 90 ; longitude : -180 à 180.")
            return None
        return latitude, longitude

    # ==========================================================
    # PHOTO
    # ==========================================================

    def select_photo(self):

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner une photo",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp)",
        )

        if not file_path:
            return

        self.selected_photo_path = (
            file_path
        )

        self.photo_name_label.setText(
            Path(file_path).name
        )

    def save_photo(self):

        if not self.selected_photo_path:
            return None

        photo_directory = (
            Path(__file__).resolve().parents[3]
            / "data"
            / "abusive_parking"
            / "photos"
        )

        photo_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        source = Path(
            self.selected_photo_path
        )

        filename = (
            f"{uuid.uuid4().hex}"
            f"{source.suffix.lower()}"
        )

        destination = (
            photo_directory
            / filename
        )

        shutil.copy2(
            source,
            destination,
        )

        return str(
            destination
        )

    # ==========================================================
    # TABLEAU DES SURVEILLANCES ACTIVES
    # ==========================================================

    def refresh_active_table(self):

        self.parkings = (
            self.service.get_active()
        )

        self.active_table.setRowCount(
            len(self.parkings)
        )

        for row, parking in enumerate(
            self.parkings
        ):

            vehicle = (
                f"{parking.brand} "
                f"{parking.model}"
            ).strip()

            days_elapsed = (
                self.service.get_days_elapsed(
                    parking
                )
            )

            days_remaining = (
                self.service.get_days_remaining(
                    parking
                )
            )

            if days_remaining > 1:

                deadline = (
                    f"{days_remaining} jours restants"
                )

            elif days_remaining == 1:

                deadline = (
                    "1 jour restant"
                )

            elif days_remaining == 0:

                deadline = (
                    "Délai atteint"
                )

            else:

                deadline = (
                    f"Délai dépassé de "
                    f"{abs(days_remaining)} jour(s)"
                )

            date_text = ""

            if parking.monitoring_date:

                date_text = (
                    parking.monitoring_date
                    .strftime("%d/%m/%Y")
                )

            values = [
                parking.registration,
                vehicle,
                parking.location,
                date_text,
                str(days_elapsed),
                deadline,
            ]

            for column, value in enumerate(
                values
            ):

                self.active_table.setItem(
                    row,
                    column,
                    QTableWidgetItem(
                        value
                    ),
                )

    # ==========================================================
    # CONSULTATION ACTIVE
    # ==========================================================

    def show_parking_detail(
        self,
        row,
        column,
    ):

        if row < 0 or row >= len(
            self.parkings
        ):
            return

        parking = self.parkings[row]

        self.selected_parking = parking

        remaining = (
            self.service.get_days_remaining(
                parking
            )
        )

        detail = (
            f"<b>Immatriculation :</b> "
            f"{parking.registration}<br><br>"

            f"<b>Véhicule :</b> "
            f"{parking.brand} "
            f"{parking.model}<br>"

            f"<b>Lieu :</b> "
            f"{parking.location}<br>"

            f"<b>Délai restant :</b> "
            f"{remaining} jour(s)"
        )

        self.detail_label.setText(
            detail
        )

        self.show_photo(
            parking.photo_path,
            self.photo_preview,
        )

        self.refresh_procedure_history(
            parking
        )

    # ==========================================================
    # DOUBLE CLIC = ÉDITION
    # ==========================================================

    def edit_parking(
        self,
        row,
        column,
    ):

        if row < 0 or row >= len(
            self.parkings
        ):
            return

        parking = self.parkings[row]

        self.editing_parking = parking
        self.selected_parking = parking

        self.registration_input.setText(
            parking.registration
        )

        self.brand_input.setText(
            parking.brand
        )

        self.model_input.setText(
            parking.model
        )

        self.vehicle_type_input.setText(
            parking.vehicle_type
        )

        self.color_input.setText(
            parking.color
        )

        self.owner_input.setText(
            parking.owner
        )

        self.location_input.setText(
            parking.location
        )

        self.latitude_input.setText(
            "" if parking.latitude is None else str(parking.latitude)
        )
        self.longitude_input.setText(
            "" if parking.longitude is None else str(parking.longitude)
        )

        if parking.monitoring_date:

            self.monitoring_date.setDate(
                QDate(
                    parking.monitoring_date.year,
                    parking.monitoring_date.month,
                    parking.monitoring_date.day,
                )
            )

        if parking.monitoring_time:

            self.monitoring_time.setTime(
                QTime(
                    parking.monitoring_time.hour,
                    parking.monitoring_time.minute,
                )
            )

        self.delay_input.setValue(
            parking.monitoring_delay_days
        )

        self.observations_input.setPlainText(
            parking.observations
        )

        self.selected_photo_path = None

        if parking.photo_path:

            self.photo_name_label.setText(
                Path(
                    parking.photo_path
                ).name
            )

        else:

            self.photo_name_label.setText(
                "Aucune photo"
            )

        self.show_parking_detail(
            row,
            column,
        )

    # ==========================================================
    # AFFICHAGE PHOTO GÉNÉRIQUE
    # ==========================================================

    def show_photo(
        self,
        photo_path,
        target_label,
    ):

        if (
            not photo_path
            or not Path(photo_path).exists()
        ):

            target_label.clear()

            target_label.setText(
                "Aucune photo"
            )

            return

        pixmap = QPixmap(
            photo_path
        )

        if pixmap.isNull():

            target_label.clear()

            target_label.setText(
                "Photo indisponible"
            )

            return

        pixmap = pixmap.scaled(
            target_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

        target_label.setPixmap(
            pixmap
        )

    # ==========================================================
    # HISTORIQUE CHRONOLOGIQUE DE LA PROCÉDURE
    # ==========================================================

    def refresh_procedure_history(
        self,
        parking,
    ):
        """
        Affiche les événements de la procédure dans l'ordre
        chronologique. Chaque événement conserve son identifiant
        pour préparer les futures actions sur les passages.
        """

        self.procedure_tree.clear()

        if parking is None:
            return

        events = []

        events.append(
            (
                (
                    parking.monitoring_date or date.min,
                    parking.monitoring_time or time.min,
                    0,
                ),
                parking.monitoring_date,
                parking.monitoring_time,
                "Mise sous surveillance",
                [
                    ("Immatriculation", parking.registration),
                    ("Lieu", parking.location),
                    (
                        "Délai",
                        f"{parking.monitoring_delay_days} jour(s)",
                    ),
                    (
                        "Photo",
                        (
                            Path(parking.photo_path).name
                            if parking.photo_path
                            else ""
                        ),
                    ),
                    ("Observations", parking.observations),
                ],
                (
                    "monitoring",
                    parking.id,
                    parking.photo_path,
                ),
            )
        )

        if parking.id is not None:

            passages = self.passage_service.get_by_parking(
                parking.id
            )

            for passage in passages:

                events.append(
                    (
                        (
                            passage.passage_date or date.min,
                            passage.passage_time or time.min,
                            1,
                        ),
                        passage.passage_date,
                        passage.passage_time,
                        passage.passage_type or "Passage",
                        [
                            ("Adresse", passage.address),
                            ("Agent", passage.agent),
                            ("Météo", passage.weather),
                            ("Coordonnées", self.format_coordinates(
                                passage.latitude,
                                passage.longitude,
                            )),
                            (
                                "Photo",
                                (
                                    Path(passage.photo_path).name
                                    if passage.photo_path
                                    else ""
                                ),
                            ),
                            ("Observations", passage.observations),
                        ],
                        (
                            "passage",
                            passage.id,
                            passage.photo_path,
                        ),
                    )
                )

        if parking.status != "active":

            events.append(
                (
                    (
                        parking.closure_date or date.max,
                        parking.closure_time or time.max,
                        2,
                    ),
                    parking.closure_date,
                    parking.closure_time,
                    "Clôture de la surveillance",
                    [
                        (
                            "Issue",
                            self.get_status_label(
                                parking.status
                            ),
                        ),
                        ("Motif", parking.closure_reason),
                    ],
                    ("closure", parking.id, None),
                )
            )

        for _, event_date, event_time, title, details, data in sorted(
            events,
            key=lambda event: event[0],
        ):

            item = QTreeWidgetItem(
                [
                    self.format_event_datetime(
                        event_date,
                        event_time,
                    ),
                    title,
                ]
            )

            item.setData(
                0,
                Qt.UserRole,
                data,
            )

            for label, value in details:

                if value:

                    QTreeWidgetItem(
                        item,
                        ["", f"{label} : {value}"],
                    )

            self.procedure_tree.addTopLevelItem(
                item
            )

        self.procedure_tree.resizeColumnToContents(
            0
        )

    def show_procedure_event_photo(
        self,
        item,
        column,
    ):
        """
        Affiche la photo associée à l'événement sélectionné sans
        modifier l'image visible lorsqu'aucune photo n'est liée.
        """

        top_item = item

        while top_item.parent() is not None:
            top_item = top_item.parent()

        event_data = top_item.data(
            0,
            Qt.UserRole,
        )

        if not event_data or len(event_data) < 3:
            return

        photo_path = event_data[2]

        if photo_path:
            self.show_photo(
                photo_path,
                self.photo_preview,
            )

    @staticmethod
    def format_event_datetime(
        event_date,
        event_time,
    ):

        if event_date is None:
            return "Date non renseignée"

        value = event_date.strftime(
            "%d/%m/%Y"
        )

        if event_time is not None:
            value += f" à {event_time.strftime('%H:%M')}"

        return value

    @staticmethod
    def format_coordinates(
        latitude,
        longitude,
    ):

        if latitude is None or longitude is None:
            return ""

        return f"{latitude}, {longitude}"

    # ==========================================================
    # NOUVEAU PASSAGE DE CONTRÔLE
    # ==========================================================

    def add_passage(self):
        """
        Ouvre le formulaire d'un nouveau passage pour la
        surveillance actuellement sélectionnée.
        """

        if (
            self.selected_parking is None
            or self.selected_parking.id is None
        ):

            QMessageBox.information(
                self,
                "Aucune surveillance sélectionnée",
                (
                    "Sélectionnez un véhicule dans le tableau "
                    "avant d'ajouter un passage."
                ),
            )

            return

        dialog = AbusiveParkingPassageDialog(
            self.selected_parking.id,
            self,
        )

        if not dialog.exec():
            return

        passage = dialog.get_passage()

        if passage is None:
            return

        self.passage_service.add_passage(
            passage
        )

        self.refresh_active_table()

        self.refresh_procedure_history(
            self.selected_parking
        )

        QMessageBox.information(
            self,
            "Passage enregistré",
            "Le passage de contrôle a été enregistré.",
        )

    # ==========================================================
    # CLÔTURE
    # ==========================================================

    def close_monitoring(
        self,
        reason,
    ):

        if self.selected_parking is None:

            QMessageBox.information(
                self,
                "Aucune surveillance sélectionnée",
                (
                    "Sélectionnez un véhicule "
                    "avant de clôturer la surveillance."
                ),
            )

            return

        if reason == "vehicle_moved":

            reason_text = (
                "Véhicule déplacé"
            )

        else:

            reason_text = (
                "Mise en fourrière"
            )

        confirmation = QMessageBox.question(
            self,
            "Clôturer la surveillance",
            (
                f"Confirmer : {reason_text} ?\n\n"
                f"{self.selected_parking.registration}"
            ),
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.No,
        )

        if confirmation != QMessageBox.Yes:
            return

        self.service.close_monitoring(
            self.selected_parking.id,
            reason,
        )

        self.new_monitoring()

        self.refresh_active_table()
        self.refresh_history_table()
        self.refresh_map()

    # ==========================================================
    # HISTORIQUE
    # ==========================================================

    def refresh_history_table(
        self,
        parkings=None,
    ):

        if parkings is None:

            self.history_parkings = (
                self.service.get_history()
            )

        else:

            self.history_parkings = (
                parkings
            )

        self.history_table.setRowCount(
            len(self.history_parkings)
        )

        for row, parking in enumerate(
            self.history_parkings
        ):

            vehicle = (
                f"{parking.brand} "
                f"{parking.model}"
            ).strip()

            start_date = ""

            if parking.monitoring_date:

                start_date = (
                    parking.monitoring_date
                    .strftime("%d/%m/%Y")
                )

            end_date = ""

            if parking.closure_date:

                end_date = (
                    parking.closure_date
                    .strftime("%d/%m/%Y")
                )

            status = self.get_status_label(
                parking.status
            )

            values = [
                parking.registration,
                vehicle,
                parking.location,
                start_date,
                end_date,
                status,
            ]

            for column, value in enumerate(
                values
            ):

                self.history_table.setItem(
                    row,
                    column,
                    QTableWidgetItem(
                        value
                    ),
                )

    # ==========================================================
    # RECHERCHE HISTORIQUE
    # ==========================================================

    def search_history(self):

        keyword = (
            self.history_search_input
            .text()
            .strip()
            .upper()
        )

        if not keyword:

            self.show_all_history()
            return

        all_history = (
            self.service.get_history()
        )

        results = []

        for parking in all_history:

            registration = (
                parking.registration
                or ""
            ).upper()

            if keyword in registration:

                results.append(
                    parking
                )

        self.refresh_history_table(
            results
        )

        self.clear_history_detail()

    # ==========================================================
    # TOUT AFFICHER
    # ==========================================================

    def show_all_history(self):

        self.history_search_input.clear()

        self.refresh_history_table()

        self.clear_history_detail()

    # ==========================================================
    # DÉTAIL HISTORIQUE
    # ==========================================================

    def show_history_detail(
        self,
        row,
        column,
    ):

        if row < 0 or row >= len(
            self.history_parkings
        ):
            return

        parking = (
            self.history_parkings[row]
        )

        start_date = (
            parking.monitoring_date
            .strftime("%d/%m/%Y")
            if parking.monitoring_date
            else "Non renseignée"
        )

        start_time = (
            parking.monitoring_time
            .strftime("%H:%M")
            if parking.monitoring_time
            else "Non renseignée"
        )

        closure_date = (
            parking.closure_date
            .strftime("%d/%m/%Y")
            if parking.closure_date
            else "Non renseignée"
        )

        closure_time = (
            parking.closure_time
            .strftime("%H:%M")
            if parking.closure_time
            else "Non renseignée"
        )

        status = self.get_status_label(
            parking.status
        )

        detail = (
            f"<b>Immatriculation :</b> "
            f"{parking.registration}<br><br>"

            f"<b>Véhicule :</b> "
            f"{parking.brand} "
            f"{parking.model}<br>"

            f"<b>Genre :</b> "
            f"{parking.vehicle_type}<br>"

            f"<b>Couleur :</b> "
            f"{parking.color}<br>"

            f"<b>Propriétaire :</b> "
            f"{parking.owner or 'Non renseigné'}"
            f"<br><br>"

            f"<b>Lieu :</b> "
            f"{parking.location}<br><br>"

            f"<b>Début de surveillance :</b> "
            f"{start_date} à {start_time}<br>"

            f"<b>Fin de surveillance :</b> "
            f"{closure_date} à {closure_time}<br>"

            f"<b>Issue :</b> "
            f"{status}<br><br>"

            f"<b>Observations :</b><br>"
            f"{parking.observations or 'Aucune'}"
        )

        self.history_detail_label.setText(
            detail
        )

        self.show_photo(
            parking.photo_path,
            self.history_photo_preview,
        )

        self.refresh_procedure_history(
            parking
        )

    # ==========================================================
    # LIBELLÉ DU STATUT
    # ==========================================================

    def get_status_label(
        self,
        status,
    ):

        if status == "vehicle_moved":

            return "Véhicule déplacé"

        if status == "impounded":

            return "Mise en fourrière"

        return "Clôturé"

    # ==========================================================
    # EFFACER DÉTAIL HISTORIQUE
    # ==========================================================

    def clear_history_detail(self):

        self.history_table.clearSelection()

        self.history_detail_label.setText(
            "Sélectionnez une surveillance archivée."
        )

        self.history_photo_preview.clear()

        self.history_photo_preview.setText(
            "Aucune photo"
        )

        self.refresh_procedure_history(
            None
        )

    # ==========================================================
    # NOUVELLE SURVEILLANCE
    # ==========================================================

    def new_monitoring(self):

        self.selected_parking = None
        self.editing_parking = None
        self.selected_photo_path = None

        self.active_table.clearSelection()

        self.registration_input.clear()
        self.brand_input.clear()
        self.model_input.clear()
        self.vehicle_type_input.clear()
        self.color_input.clear()
        self.owner_input.clear()
        self.location_input.clear()
        self.latitude_input.clear()
        self.longitude_input.clear()

        self.monitoring_date.setDate(
            QDate.currentDate()
        )

        self.monitoring_time.setTime(
            QTime.currentTime()
        )

        self.delay_input.setValue(
            7
        )

        self.observations_input.clear()

        self.photo_name_label.setText(
            "Aucune photo"
        )

        self.photo_preview.clear()

        self.photo_preview.setText(
            "Aucune photo"
        )

        self.detail_label.setText(
            "Sélectionnez un véhicule dans le tableau."
        )

        self.refresh_procedure_history(
            None
        )

    # ==========================================================
    # ACTUALISATION À L'AFFICHAGE
    # ==========================================================

    def showEvent(
        self,
        event,
    ):

        self.refresh_active_table()
        self.refresh_history_table()
        self.refresh_map()

        super().showEvent(
            event
        )
