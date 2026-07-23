from datetime import date, datetime

from PySide6.QtCore import Qt, QTime, QDate
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QCheckBox,
    QComboBox,
    QTimeEdit,
    QDateEdit,
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QAbstractItemView,
    QInputDialog,
    QDialog,
    QDialogButtonBox,
    QCalendarWidget,
    QFileDialog,
    QGroupBox,
)

from app.models.activity import Activity
from app.services.journal_service import JournalService
from app.services.journal_pdf_service import JournalPdfService


class JournalPage(QWidget):

    def __init__(self, journal_service=None):
        super().__init__()

        self.service = journal_service or JournalService()
        self.pdf_service = JournalPdfService()

        # Activité sélectionnée dans le tableau
        self.selected_activity = None

        # Activité actuellement ouverte en modification
        self.editing_activity = None

        # Activités actuellement affichées
        self.activities = []

        self.build_ui()

        # Chargement automatique depuis SQLite
        self.refresh_table()

    # ==========================================================
    # CONSTRUCTION DE L'INTERFACE
    # ==========================================================

    def build_ui(self):

        # ------------------------------------------------------
        # En-tête
        # ------------------------------------------------------

        title = QLabel(
            "🗓️  Journal quotidien"
        )

        title.setStyleSheet(
            "font-size:22px;"
            "font-weight:bold;"
        )

        current_date = QLabel(
            datetime.now().strftime(
                "%A %d %B %Y"
            )
        )

        current_date.setAlignment(
            Qt.AlignRight | Qt.AlignVCenter
        )

        header = QHBoxLayout()

        header.addWidget(title)
        header.addStretch()
        header.addWidget(current_date)

        # ------------------------------------------------------
        # Barre d'outils
        # ------------------------------------------------------

        self.btn_new = QPushButton(
            "➕ Nouveau"
        )

        self.btn_save = QPushButton(
            "💾 Enregistrer"
        )

        self.btn_delete = QPushButton(
            "🗑️ Supprimer"
        )

        self.btn_search = QPushButton(
            "🔍 Rechercher"
        )

        self.btn_search_date = QPushButton(
            "📅 Rechercher par date"
        )

        self.btn_show_all = QPushButton(
            "↩ Tout afficher"
        )

        self.btn_pdf = QPushButton(
            "📄 Export PDF"
        )

        toolbar = QHBoxLayout()

        for button in (
            self.btn_new,
            self.btn_save,
            self.btn_delete,
            self.btn_search,
            self.btn_search_date,
            self.btn_show_all,
            self.btn_pdf,
        ):
            toolbar.addWidget(button)

        toolbar.addStretch()

        # Connexion des boutons
        self.btn_new.clicked.connect(
            self.new_activity
        )

        self.btn_save.clicked.connect(
            self.save_activity
        )

        self.btn_delete.clicked.connect(
            self.delete_activity
        )

        self.btn_search.clicked.connect(
            self.search_activities
        )

        self.btn_search_date.clicked.connect(
            self.search_by_date
        )

        self.btn_show_all.clicked.connect(
            self.show_all_activities
        )

        self.btn_pdf.clicked.connect(
            self.export_pdf
        )

        # ------------------------------------------------------
        # Formulaire de saisie / modification
        # ------------------------------------------------------

        # Date
        self.activity_date = QDateEdit()

        self.activity_date.setDate(
            QDate.currentDate()
        )

        self.activity_date.setCalendarPopup(
            True
        )

        self.activity_date.setDisplayFormat(
            "dd/MM/yyyy"
        )

        # Heure
        self.heure = QTimeEdit()

        self.heure.setTime(
            QTime.currentTime()
        )

        self.heure.setDisplayFormat(
            "HH:mm"
        )

        # Catégorie
        self.categorie = QComboBox()

        self.categorie.addItems(
            [
                "Sélectionner un item",
                "Prise de service",
                "Fin de service",
                "Patrouille",
                "Patrouille de nuit",
                "Intervention",
                "Appel téléphonique",
                "Plurico",
                "Surveillance évènement",
                "Police administrative",
                "Police judiciaire",
                "Urbanisme",
                "Circulation",
                "Stationnement",
                "Salubrité",
                "Tranquillité publique",
                "Médiation",
                "Opération de prévention",
                "Réunion",
                "Formation",
                "Divers",
            ]
        )

        # Objet
        self.objet = QLineEdit()

        # Compte-rendu
        self.compte_rendu = QTextEdit()

        # Important
        self.important = QCheckBox(
            "Évènement important"
        )

        # Ajouter
        self.btn_add = QPushButton(
            "Ajouter l'activité"
        )

        self.btn_add.clicked.connect(
            self.add_activity
        )

        # ------------------------------------------------------
        # Organisation du formulaire
        # ------------------------------------------------------

        form = QGridLayout()

        form.addWidget(
            QLabel("Date :"),
            0,
            0,
        )

        form.addWidget(
            self.activity_date,
            0,
            1,
        )

        form.addWidget(
            QLabel("Heure :"),
            1,
            0,
        )

        form.addWidget(
            self.heure,
            1,
            1,
        )

        form.addWidget(
            QLabel("Catégorie :"),
            2,
            0,
        )

        form.addWidget(
            self.categorie,
            2,
            1,
        )

        form.addWidget(
            QLabel("Objet :"),
            3,
            0,
        )

        form.addWidget(
            self.objet,
            3,
            1,
        )

        form.addWidget(
            QLabel("Compte-rendu :"),
            4,
            0,
        )

        form.addWidget(
            self.compte_rendu,
            4,
            1,
        )

        form.addWidget(
            self.important,
            5,
            1,
        )

        form.addWidget(
            self.btn_add,
            6,
            1,
        )

        # ------------------------------------------------------
        # Tableau des activités
        # ------------------------------------------------------

        self.table = QTableWidget()

        self.table.setColumnCount(5)

        self.table.setHorizontalHeaderLabels(
            [
                "Date",
                "Heure",
                "Catégorie",
                "Objet",
                "Important",
            ]
        )

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        self.table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        # ------------------------------------------------------
        # J1.7 - SIMPLE CLIC = CONSULTATION
        # ------------------------------------------------------

        self.table.cellClicked.connect(
            self.show_activity_detail
        )

        # ------------------------------------------------------
        # J1.7 - DOUBLE CLIC = MODIFICATION
        # ------------------------------------------------------

        self.table.cellDoubleClicked.connect(
            self.edit_selected_activity
        )

        # ------------------------------------------------------
        # Zone de lecture détaillée
        # ------------------------------------------------------

        self.detail_group = QGroupBox(
            "Détail de l'activité sélectionnée"
        )

        detail_layout = QVBoxLayout(
            self.detail_group
        )

        self.detail_header = QLabel(
            "Sélectionnez une activité dans le tableau."
        )

        self.detail_header.setWordWrap(
            True
        )

        self.detail_header.setStyleSheet(
            "font-weight:bold;"
            "font-size:13px;"
        )

        self.detail_report = QTextEdit()

        self.detail_report.setReadOnly(
            True
        )

        self.detail_report.setPlaceholderText(
            "Le compte-rendu complet apparaîtra ici."
        )

        self.detail_report.setMinimumHeight(
            140
        )

        detail_layout.addWidget(
            self.detail_header
        )

        detail_layout.addWidget(
            self.detail_report
        )

        # ------------------------------------------------------
        # Mise en page générale
        # ------------------------------------------------------

        left = QVBoxLayout()

        left.addLayout(header)
        left.addLayout(toolbar)
        left.addLayout(form)

        right = QVBoxLayout()

        right.addWidget(
            self.table,
            2,
        )

        right.addWidget(
            self.detail_group,
            1,
        )

        main = QHBoxLayout(self)

        main.addLayout(
            left,
            2,
        )

        main.addLayout(
            right,
            1,
        )

    # ==========================================================
    # CREATE
    # AJOUTER UNE ACTIVITÉ
    # ==========================================================

    def add_activity(self):

        # Vérification de l'objet
        if not self.objet.text().strip():

            QMessageBox.warning(
                self,
                "Champ obligatoire",
                "Veuillez renseigner l'objet de l'activité.",
            )

            return

        # Vérification de la catégorie
        if self.categorie.currentIndex() == 0:

            QMessageBox.warning(
                self,
                "Catégorie obligatoire",
                "Veuillez sélectionner une catégorie.",
            )

            return

        selected_qdate = (
            self.activity_date.date()
        )

        selected_date = date(
            selected_qdate.year(),
            selected_qdate.month(),
            selected_qdate.day(),
        )

        activity = Activity(
            activity_date=selected_date,
            activity_time=self.heure.time().toPython(),
            category=self.categorie.currentText(),
            title=self.objet.text().strip(),
            report=self.compte_rendu.toPlainText().strip(),
            important=self.important.isChecked(),
        )

        self.service.add_activity(
            activity
        )

        self.refresh_table()

        self.new_activity()

    # ==========================================================
    # SIMPLE CLIC
    # CONSULTATION UNIQUEMENT
    # ==========================================================

    def show_activity_detail(
        self,
        row,
        column,
    ):

        if row < 0 or row >= len(
            self.activities
        ):
            return

        # Activité sélectionnée pour consultation
        self.selected_activity = (
            self.activities[row]
        )

        activity = self.selected_activity

        # ------------------------------------------------------
        # IMPORTANT :
        # On ne charge PAS l'activité dans le formulaire.
        # Le simple clic sert uniquement à la consultation.
        # ------------------------------------------------------

        important_text = (
            " — ÉVÈNEMENT IMPORTANT"
            if activity.important
            else ""
        )

        self.detail_header.setText(
            (
                f"{activity.activity_date.strftime('%d/%m/%Y')}"
                f" à {activity.activity_time.strftime('%H:%M')}"
                f" — {activity.category}"
                f"{important_text}\n"
                f"Objet : {activity.title}"
            )
        )

        if activity.report:

            self.detail_report.setPlainText(
                activity.report
            )

        else:

            self.detail_report.setPlainText(
                "Aucun compte-rendu renseigné."
            )

    # ==========================================================
    # DOUBLE CLIC
    # OUVERTURE EN MODIFICATION
    # ==========================================================

    def edit_selected_activity(
        self,
        row,
        column,
    ):

        if row < 0 or row >= len(
            self.activities
        ):
            return

        # Activité ouverte en modification
        self.editing_activity = (
            self.activities[row]
        )

        # Elle devient également l'activité sélectionnée
        self.selected_activity = (
            self.editing_activity
        )

        activity = self.editing_activity

        # Date
        self.activity_date.setDate(
            QDate(
                activity.activity_date.year,
                activity.activity_date.month,
                activity.activity_date.day,
            )
        )

        # Heure
        self.heure.setTime(
            QTime(
                activity.activity_time.hour,
                activity.activity_time.minute,
            )
        )

        # Catégorie
        index = self.categorie.findText(
            activity.category
        )

        if index >= 0:

            self.categorie.setCurrentIndex(
                index
            )

        # Objet
        self.objet.setText(
            activity.title
        )

        # Compte-rendu
        self.compte_rendu.setPlainText(
            activity.report
        )

        # Important
        self.important.setChecked(
            activity.important
        )

        # Mise à jour également de la zone de détail
        self.show_activity_detail(
            row,
            column,
        )

    # ==========================================================
    # SEARCH BY KEYWORD
    # ==========================================================

    def search_activities(self):

        keyword, ok = QInputDialog.getText(
            self,
            "Rechercher dans le Journal",
            (
                "Saisissez un mot-clé :\n"
                "(catégorie, objet ou compte-rendu)"
            ),
        )

        if not ok:
            return

        keyword = keyword.strip()

        if not keyword:

            self.show_all_activities()

            return

        self.activities = (
            self.service.search_activities(
                keyword
            )
        )

        self.display_activities()

        self.selected_activity = None
        self.editing_activity = None

        self.table.clearSelection()

        self.clear_form()
        self.clear_detail()

        if not self.activities:

            QMessageBox.information(
                self,
                "Recherche",
                (
                    "Aucune activité trouvée pour :\n\n"
                    f"{keyword}"
                ),
            )

    # ==========================================================
    # SEARCH BY DATE
    # ==========================================================

    def search_by_date(self):

        dialog = QDialog(self)

        dialog.setWindowTitle(
            "Rechercher une journée"
        )

        layout = QVBoxLayout(dialog)

        label = QLabel(
            "Sélectionnez la date à rechercher :"
        )

        layout.addWidget(label)

        calendar = QCalendarWidget()

        calendar.setSelectedDate(
            QDate.currentDate()
        )

        calendar.setGridVisible(
            True
        )

        layout.addWidget(calendar)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok
            | QDialogButtonBox.Cancel
        )

        buttons.accepted.connect(
            dialog.accept
        )

        buttons.rejected.connect(
            dialog.reject
        )

        layout.addWidget(buttons)

        if dialog.exec() != QDialog.Accepted:
            return

        selected_qdate = (
            calendar.selectedDate()
        )

        selected_date = date(
            selected_qdate.year(),
            selected_qdate.month(),
            selected_qdate.day(),
        )

        self.activities = (
            self.service.search_activities_by_date(
                selected_date
            )
        )

        self.display_activities()

        self.selected_activity = None
        self.editing_activity = None

        self.table.clearSelection()

        self.clear_form()
        self.clear_detail()

        if not self.activities:

            QMessageBox.information(
                self,
                "Recherche par date",
                (
                    "Aucune activité enregistrée "
                    "pour cette date :\n\n"
                    f"{selected_date.strftime('%d/%m/%Y')}"
                ),
            )

    # ==========================================================
    # SHOW ALL
    # ==========================================================

    def show_all_activities(self):

        self.selected_activity = None
        self.editing_activity = None

        self.clear_form()
        self.clear_detail()

        self.refresh_table()

        self.table.clearSelection()

    # ==========================================================
    # UPDATE
    # ENREGISTRER UNE MODIFICATION
    # ==========================================================

    def save_activity(self):

        # ------------------------------------------------------
        # Seul un double clic ouvre une activité en modification
        # ------------------------------------------------------

        if self.editing_activity is None:

            QMessageBox.information(
                self,
                "Aucune activité en modification",
                (
                    "Double-cliquez sur une activité "
                    "dans le tableau pour la modifier."
                ),
            )

            return

        # Vérification de l'objet
        if not self.objet.text().strip():

            QMessageBox.warning(
                self,
                "Champ obligatoire",
                "Veuillez renseigner l'objet de l'activité.",
            )

            return

        # Vérification de la catégorie
        if self.categorie.currentIndex() == 0:

            QMessageBox.warning(
                self,
                "Catégorie obligatoire",
                "Veuillez sélectionner une catégorie.",
            )

            return

        selected_qdate = (
            self.activity_date.date()
        )

        # Date
        self.editing_activity.activity_date = date(
            selected_qdate.year(),
            selected_qdate.month(),
            selected_qdate.day(),
        )

        # Heure
        self.editing_activity.activity_time = (
            self.heure.time().toPython()
        )

        # Catégorie
        self.editing_activity.category = (
            self.categorie.currentText()
        )

        # Objet
        self.editing_activity.title = (
            self.objet.text().strip()
        )

        # Compte-rendu
        self.editing_activity.report = (
            self.compte_rendu
            .toPlainText()
            .strip()
        )

        # Important
        self.editing_activity.important = (
            self.important.isChecked()
        )

        # Mise à jour SQLite
        self.service.update_activity(
            self.editing_activity
        )

        # Fin du mode modification
        self.selected_activity = None
        self.editing_activity = None

        self.clear_form()
        self.clear_detail()

        self.refresh_table()

        self.table.clearSelection()

    # ==========================================================
    # DELETE
    # ==========================================================

    def delete_activity(self):

        # La suppression fonctionne avec un simple clic
        if self.selected_activity is None:

            QMessageBox.information(
                self,
                "Aucune activité sélectionnée",
                (
                    "Sélectionnez une activité dans "
                    "le tableau avant de la supprimer."
                ),
            )

            return

        confirmation = QMessageBox.question(
            self,
            "Confirmer la suppression",
            (
                "Voulez-vous vraiment supprimer "
                "cette activité ?\n\n"
                f"{self.selected_activity.title}"
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if confirmation != QMessageBox.Yes:
            return

        if self.selected_activity.id is None:

            QMessageBox.warning(
                self,
                "Erreur",
                (
                    "Cette activité ne possède pas "
                    "d'identifiant SQLite."
                ),
            )

            return

        self.service.delete_activity(
            self.selected_activity.id
        )

        self.selected_activity = None
        self.editing_activity = None

        self.clear_form()
        self.clear_detail()

        self.refresh_table()

        self.table.clearSelection()

    # ==========================================================
    # EXPORT PDF
    # ==========================================================

    def export_pdf(self):

        if not self.activities:

            QMessageBox.information(
                self,
                "Export PDF",
                "Aucune activité à exporter.",
            )

            return

        default_filename = (
            "Journal_PMP_"
            + datetime.now().strftime(
                "%Y-%m-%d"
            )
            + ".pdf"
        )

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exporter le Journal en PDF",
            default_filename,
            "Fichiers PDF (*.pdf)",
        )

        if not file_path:
            return

        if not file_path.lower().endswith(
            ".pdf"
        ):

            file_path += ".pdf"

        try:

            self.pdf_service.export(
                self.activities,
                file_path,
            )

            QMessageBox.information(
                self,
                "Export PDF",
                "Le Journal a été exporté avec succès.",
            )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Erreur d'export PDF",
                (
                    "Impossible de créer "
                    "le fichier PDF.\n\n"
                    f"{error}"
                ),
            )

    # ==========================================================
    # NOUVELLE ACTIVITÉ
    # ==========================================================

    def new_activity(self):

        self.selected_activity = None
        self.editing_activity = None

        self.table.clearSelection()

        self.clear_form()
        self.clear_detail()

    # ==========================================================
    # ACTUALISER LE TABLEAU
    # ==========================================================

    def refresh_table(self):

        self.activities = (
            self.service.get_all()
        )

        self.display_activities()

    # ==========================================================
    # AFFICHER LES ACTIVITÉS
    # ==========================================================

    def display_activities(self):

        self.table.setRowCount(
            len(self.activities)
        )

        for row, activity in enumerate(
            self.activities
        ):

            # Date
            self.table.setItem(
                row,
                0,
                QTableWidgetItem(
                    activity.activity_date.strftime(
                        "%d/%m/%Y"
                    )
                ),
            )

            # Heure
            self.table.setItem(
                row,
                1,
                QTableWidgetItem(
                    activity.activity_time.strftime(
                        "%H:%M"
                    )
                ),
            )

            # Catégorie
            self.table.setItem(
                row,
                2,
                QTableWidgetItem(
                    activity.category
                ),
            )

            # Objet
            self.table.setItem(
                row,
                3,
                QTableWidgetItem(
                    activity.title
                ),
            )

            # Important
            self.table.setItem(
                row,
                4,
                QTableWidgetItem(
                    "✔"
                    if activity.important
                    else ""
                ),
            )

    # ==========================================================
    # NETTOYER LE FORMULAIRE
    # ==========================================================

    def clear_form(self):

        self.activity_date.setDate(
            QDate.currentDate()
        )

        self.heure.setTime(
            QTime.currentTime()
        )

        # Retour sur "Sélectionner un item"
        self.categorie.setCurrentIndex(
            0
        )

        self.objet.clear()

        self.compte_rendu.clear()

        self.important.setChecked(
            False
        )

    # ==========================================================
    # NETTOYER LA ZONE DE DÉTAIL
    # ==========================================================

    def clear_detail(self):

        self.detail_header.setText(
            "Sélectionnez une activité dans le tableau."
        )

        self.detail_report.clear()
