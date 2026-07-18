from datetime import date
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
    QHeaderView,
    QMessageBox,
    QFileDialog,
    QAbstractItemView,
    QGroupBox,
    QTabWidget,
)

from app.models.abusive_parking import AbusiveParking
from app.dialogs.abusive_parking_passage_dialog import (
    AbusiveParkingPassageDialog,
)
from app.services.abusive_parking_service import AbusiveParkingService
from app.services.abusive_parking_passage_service import (
    AbusiveParkingPassageService,
)


class AbusiveParkingPage(QWidget):

    def __init__(self):
        super().__init__()

        self.service = AbusiveParkingService()
        self.passage_service = AbusiveParkingPassageService()

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
            7,
            0,
        )

        grid.addWidget(
            self.monitoring_date,
            7,
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
            8,
            0,
        )

        grid.addWidget(
            self.monitoring_time,
            8,
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

        detail_layout = QHBoxLayout(
            detail_group
        )

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

        detail_layout.addWidget(
            self.photo_preview
        )

        detail_layout.addWidget(
            self.detail_label,
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

            f"<b>Genre :</b> "
            f"{parking.vehicle_type}<br>"

            f"<b>Couleur :</b> "
            f"{parking.color}<br>"

            f"<b>Propriétaire :</b> "
            f"{parking.owner or 'Non renseigné'}"
            f"<br><br>"

            f"<b>Lieu :</b> "
            f"{parking.location}<br>"

            f"<b>Délai restant :</b> "
            f"{remaining} jour(s)<br><br>"

            f"<b>Observations :</b><br>"
            f"{parking.observations or 'Aucune'}"
        )

        self.detail_label.setText(
            detail
        )

        self.show_photo(
            parking.photo_path,
            self.photo_preview,
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

    # ==========================================================
    # ACTUALISATION À L'AFFICHAGE
    # ==========================================================

    def showEvent(
        self,
        event,
    ):

        self.refresh_active_table()
        self.refresh_history_table()

        super().showEvent(
            event
        )
