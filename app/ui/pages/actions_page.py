from datetime import date

from PySide6.QtCore import Qt, QDate, QTime
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QCheckBox,
    QDateEdit,
    QTimeEdit,
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QAbstractItemView,
    QGroupBox,
)

from app.models.action import Action
from app.services.action_service import ActionService


class ActionsPage(QWidget):

    def __init__(self):
        super().__init__()

        self.service = ActionService()

        # Action sélectionnée pour consultation
        self.selected_action = None

        # Action actuellement ouverte en modification
        self.editing_action = None

        # Actions actuellement affichées
        self.actions = []

        self.build_ui()

        # Chargement automatique depuis SQLite
        self.refresh_table()

    # ==========================================================
    # CONSTRUCTION DE L'INTERFACE
    # ==========================================================

    def build_ui(self):

        # ------------------------------------------------------
        # TITRE
        # ------------------------------------------------------

        title = QLabel(
            "☑️  Actions"
        )

        title.setStyleSheet(
            """
            font-size: 22px;
            font-weight: bold;
            """
        )

        subtitle = QLabel(
            "Planifier et suivre les actions à réaliser"
        )

        subtitle.setStyleSheet(
            """
            color: #666666;
            font-size: 13px;
            """
        )

        header = QVBoxLayout()

        header.addWidget(
            title
        )

        header.addWidget(
            subtitle
        )

        # ------------------------------------------------------
        # BARRE D'OUTILS
        # ------------------------------------------------------

        self.btn_new = QPushButton(
            "➕ Nouvelle"
        )

        self.btn_save = QPushButton(
            "💾 Enregistrer"
        )

        self.btn_delete = QPushButton(
            "🗑️ Supprimer"
        )

        self.btn_show_all = QPushButton(
            "↩ Tout afficher"
        )

        toolbar = QHBoxLayout()

        toolbar.addWidget(
            self.btn_new
        )

        toolbar.addWidget(
            self.btn_save
        )

        toolbar.addWidget(
            self.btn_delete
        )

        toolbar.addWidget(
            self.btn_show_all
        )

        toolbar.addStretch()

        # Connexion des boutons
        self.btn_new.clicked.connect(
            self.new_action
        )

        self.btn_save.clicked.connect(
            self.save_action
        )

        self.btn_delete.clicked.connect(
            self.delete_action
        )

        self.btn_show_all.clicked.connect(
            self.show_all_actions
        )

        # ======================================================
        # FORMULAIRE
        # ======================================================

        # ------------------------------------------------------
        # DATE
        # ------------------------------------------------------

        self.action_date = QDateEdit()

        self.action_date.setDate(
            QDate.currentDate()
        )

        self.action_date.setCalendarPopup(
            True
        )

        self.action_date.setDisplayFormat(
            "dd/MM/yyyy"
        )

        # ------------------------------------------------------
        # HEURE
        # ------------------------------------------------------

        self.action_time = QTimeEdit()

        self.action_time.setTime(
            QTime.currentTime()
        )

        self.action_time.setDisplayFormat(
            "HH:mm"
        )

        # ------------------------------------------------------
        # OBJET
        # ------------------------------------------------------

        self.title_input = QLineEdit()

        self.title_input.setPlaceholderText(
            "Ex : Ouvrir le cimetière"
        )

        # ------------------------------------------------------
        # DESCRIPTION
        # ------------------------------------------------------

        self.description_input = QTextEdit()

        self.description_input.setPlaceholderText(
            "Description, consignes ou informations utiles..."
        )

        # ------------------------------------------------------
        # ACTION IMPORTANTE
        # ------------------------------------------------------

        self.important_checkbox = QCheckBox(
            "Action importante / prioritaire"
        )

        # ------------------------------------------------------
        # ACTION TERMINÉE
        # ------------------------------------------------------

        self.completed_checkbox = QCheckBox(
            "Action terminée"
        )

        # ------------------------------------------------------
        # RAPPEL OUTLOOK
        # ------------------------------------------------------

        self.outlook_checkbox = QCheckBox(
            "Créer un rappel Outlook"
        )

        # Pour Actions V1.0, cette option est enregistrée
        # dans SQLite.
        # La synchronisation Outlook sera développée ensuite.

        # ------------------------------------------------------
        # BOUTON AJOUTER
        # ------------------------------------------------------

        self.btn_add = QPushButton(
            "Ajouter l'action"
        )

        self.btn_add.clicked.connect(
            self.add_action
        )

        # ------------------------------------------------------
        # ORGANISATION DU FORMULAIRE
        # ------------------------------------------------------

        form = QGridLayout()

        form.addWidget(
            QLabel("Date :"),
            0,
            0,
        )

        form.addWidget(
            self.action_date,
            0,
            1,
        )

        form.addWidget(
            QLabel("Heure :"),
            1,
            0,
        )

        form.addWidget(
            self.action_time,
            1,
            1,
        )

        form.addWidget(
            QLabel("Objet :"),
            2,
            0,
        )

        form.addWidget(
            self.title_input,
            2,
            1,
        )

        form.addWidget(
            QLabel("Description :"),
            3,
            0,
        )

        form.addWidget(
            self.description_input,
            3,
            1,
        )

        form.addWidget(
            self.important_checkbox,
            4,
            1,
        )

        form.addWidget(
            self.completed_checkbox,
            5,
            1,
        )

        form.addWidget(
            self.outlook_checkbox,
            6,
            1,
        )

        form.addWidget(
            self.btn_add,
            7,
            1,
        )

        # ======================================================
        # TABLEAU DES ACTIONS
        # ======================================================

        self.table = QTableWidget()

        self.table.setColumnCount(
            6
        )

        self.table.setHorizontalHeaderLabels(
            [
                "Date",
                "Heure",
                "Objet",
                "Important",
                "Terminée",
                "Outlook",
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
        # SIMPLE CLIC = CONSULTATION
        # ------------------------------------------------------

        self.table.cellClicked.connect(
            self.show_action_detail
        )

        # ------------------------------------------------------
        # DOUBLE CLIC = MODIFICATION
        # ------------------------------------------------------

        self.table.cellDoubleClicked.connect(
            self.edit_selected_action
        )

        # ======================================================
        # ZONE DE CONSULTATION
        # ======================================================

        self.detail_group = QGroupBox(
            "Détail de l'action sélectionnée"
        )

        detail_layout = QVBoxLayout(
            self.detail_group
        )

        self.detail_header = QLabel(
            "Sélectionnez une action dans le tableau."
        )

        self.detail_header.setWordWrap(
            True
        )

        self.detail_header.setStyleSheet(
            """
            font-weight: bold;
            font-size: 13px;
            """
        )

        self.detail_description = QTextEdit()

        self.detail_description.setReadOnly(
            True
        )

        self.detail_description.setPlaceholderText(
            "La description de l'action apparaîtra ici."
        )

        self.detail_description.setMinimumHeight(
            140
        )

        detail_layout.addWidget(
            self.detail_header
        )

        detail_layout.addWidget(
            self.detail_description
        )

        # ======================================================
        # MISE EN PAGE GÉNÉRALE
        # ======================================================

        left = QVBoxLayout()

        left.addLayout(
            header
        )

        left.addLayout(
            toolbar
        )

        left.addLayout(
            form
        )

        left.addStretch()

        right = QVBoxLayout()

        right.addWidget(
            self.table,
            2,
        )

        right.addWidget(
            self.detail_group,
            1,
        )

        main = QHBoxLayout(
            self
        )

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
    # ==========================================================

    def add_action(self):

        # Vérification de l'objet
        if not self.title_input.text().strip():

            QMessageBox.warning(
                self,
                "Champ obligatoire",
                "Veuillez renseigner l'objet de l'action.",
            )

            return

        selected_qdate = (
            self.action_date.date()
        )

        selected_date = date(
            selected_qdate.year(),
            selected_qdate.month(),
            selected_qdate.day(),
        )

        action = Action(
            action_date=selected_date,
            action_time=(
                self.action_time
                .time()
                .toPython()
            ),
            title=(
                self.title_input
                .text()
                .strip()
            ),
            description=(
                self.description_input
                .toPlainText()
                .strip()
            ),
            important=(
                self.important_checkbox
                .isChecked()
            ),
            completed=(
                self.completed_checkbox
                .isChecked()
            ),
            outlook_reminder=(
                self.outlook_checkbox
                .isChecked()
            ),
        )

        self.service.add_action(
            action
        )

        self.refresh_table()

        self.new_action()

    # ==========================================================
    # SIMPLE CLIC
    # CONSULTATION
    # ==========================================================

    def show_action_detail(
        self,
        row,
        column,
    ):

        if row < 0 or row >= len(
            self.actions
        ):
            return

        self.selected_action = (
            self.actions[row]
        )

        action = self.selected_action

        important_text = (
            " — PRIORITAIRE"
            if action.important
            else ""
        )

        completed_text = (
            " — TERMINÉE"
            if action.completed
            else " — À FAIRE"
        )

        outlook_text = (
            " — RAPPEL OUTLOOK"
            if action.outlook_reminder
            else ""
        )

        self.detail_header.setText(
            (
                f"{action.action_date.strftime('%d/%m/%Y')}"
                f" à {action.action_time.strftime('%H:%M')}"
                f"{important_text}"
                f"{completed_text}"
                f"{outlook_text}\n"
                f"Objet : {action.title}"
            )
        )

        if action.description:

            self.detail_description.setPlainText(
                action.description
            )

        else:

            self.detail_description.setPlainText(
                "Aucune description renseignée."
            )

    # ==========================================================
    # DOUBLE CLIC
    # MODIFICATION
    # ==========================================================

    def edit_selected_action(
        self,
        row,
        column,
    ):

        if row < 0 or row >= len(
            self.actions
        ):
            return

        self.editing_action = (
            self.actions[row]
        )

        self.selected_action = (
            self.editing_action
        )

        action = (
            self.editing_action
        )

        # Date
        self.action_date.setDate(
            QDate(
                action.action_date.year,
                action.action_date.month,
                action.action_date.day,
            )
        )

        # Heure
        self.action_time.setTime(
            QTime(
                action.action_time.hour,
                action.action_time.minute,
            )
        )

        # Objet
        self.title_input.setText(
            action.title
        )

        # Description
        self.description_input.setPlainText(
            action.description
        )

        # Important
        self.important_checkbox.setChecked(
            action.important
        )

        # Terminée
        self.completed_checkbox.setChecked(
            action.completed
        )

        # Outlook
        self.outlook_checkbox.setChecked(
            action.outlook_reminder
        )

        # Mise à jour de la zone de consultation
        self.show_action_detail(
            row,
            column,
        )

    # ==========================================================
    # UPDATE
    # ==========================================================

    def save_action(self):

        if self.editing_action is None:

            QMessageBox.information(
                self,
                "Aucune action en modification",
                (
                    "Double-cliquez sur une action "
                    "dans le tableau pour la modifier."
                ),
            )

            return

        if not self.title_input.text().strip():

            QMessageBox.warning(
                self,
                "Champ obligatoire",
                "Veuillez renseigner l'objet de l'action.",
            )

            return

        selected_qdate = (
            self.action_date.date()
        )

        # Date
        self.editing_action.action_date = date(
            selected_qdate.year(),
            selected_qdate.month(),
            selected_qdate.day(),
        )

        # Heure
        self.editing_action.action_time = (
            self.action_time
            .time()
            .toPython()
        )

        # Objet
        self.editing_action.title = (
            self.title_input
            .text()
            .strip()
        )

        # Description
        self.editing_action.description = (
            self.description_input
            .toPlainText()
            .strip()
        )

        # Important
        self.editing_action.important = (
            self.important_checkbox
            .isChecked()
        )

        # Terminée
        self.editing_action.completed = (
            self.completed_checkbox
            .isChecked()
        )

        # Rappel Outlook
        self.editing_action.outlook_reminder = (
            self.outlook_checkbox
            .isChecked()
        )

        self.service.update_action(
            self.editing_action
        )

        self.selected_action = None

        self.editing_action = None

        self.clear_form()

        self.clear_detail()

        self.refresh_table()

        self.table.clearSelection()

    # ==========================================================
    # DELETE
    # ==========================================================

    def delete_action(self):

        if self.selected_action is None:

            QMessageBox.information(
                self,
                "Aucune action sélectionnée",
                (
                    "Sélectionnez une action dans "
                    "le tableau avant de la supprimer."
                ),
            )

            return

        confirmation = QMessageBox.question(
            self,
            "Confirmer la suppression",
            (
                "Voulez-vous vraiment supprimer "
                "cette action ?\n\n"
                f"{self.selected_action.title}"
            ),
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.No,
        )

        if confirmation != QMessageBox.Yes:

            return

        if self.selected_action.id is None:

            QMessageBox.warning(
                self,
                "Erreur",
                (
                    "Cette action ne possède pas "
                    "d'identifiant SQLite."
                ),
            )

            return

        self.service.delete_action(
            self.selected_action.id
        )

        self.selected_action = None

        self.editing_action = None

        self.clear_form()

        self.clear_detail()

        self.refresh_table()

        self.table.clearSelection()

    # ==========================================================
    # NOUVELLE ACTION
    # ==========================================================

    def new_action(self):

        self.selected_action = None

        self.editing_action = None

        self.table.clearSelection()

        self.clear_form()

        self.clear_detail()

    # ==========================================================
    # TOUT AFFICHER
    # ==========================================================

    def show_all_actions(self):

        self.selected_action = None

        self.editing_action = None

        self.clear_form()

        self.clear_detail()

        self.refresh_table()

        self.table.clearSelection()

    # ==========================================================
    # ACTUALISER LE TABLEAU
    # ==========================================================

    def refresh_table(self):

        self.actions = (
            self.service.get_all()
        )

        self.display_actions()

    # ==========================================================
    # AFFICHER LES ACTIONS
    # ==========================================================

    def display_actions(self):

        self.table.setRowCount(
            len(self.actions)
        )

        for row, action in enumerate(
            self.actions
        ):

            # Date
            self.table.setItem(
                row,
                0,
                QTableWidgetItem(
                    action.action_date.strftime(
                        "%d/%m/%Y"
                    )
                ),
            )

            # Heure
            self.table.setItem(
                row,
                1,
                QTableWidgetItem(
                    action.action_time.strftime(
                        "%H:%M"
                    )
                ),
            )

            # Objet
            self.table.setItem(
                row,
                2,
                QTableWidgetItem(
                    action.title
                ),
            )

            # Important
            self.table.setItem(
                row,
                3,
                QTableWidgetItem(
                    "⚠"
                    if action.important
                    else ""
                ),
            )

            # Terminée
            self.table.setItem(
                row,
                4,
                QTableWidgetItem(
                    "✔"
                    if action.completed
                    else ""
                ),
            )

            # Outlook
            self.table.setItem(
                row,
                5,
                QTableWidgetItem(
                    "🔔"
                    if action.outlook_reminder
                    else ""
                ),
            )

    # ==========================================================
    # NETTOYER LE FORMULAIRE
    # ==========================================================

    def clear_form(self):

        self.action_date.setDate(
            QDate.currentDate()
        )

        self.action_time.setTime(
            QTime.currentTime()
        )

        self.title_input.clear()

        self.description_input.clear()

        self.important_checkbox.setChecked(
            False
        )

        self.completed_checkbox.setChecked(
            False
        )

        self.outlook_checkbox.setChecked(
            False
        )

    # ==========================================================
    # NETTOYER LA ZONE DE DÉTAIL
    # ==========================================================

    def clear_detail(self):

        self.detail_header.setText(
            "Sélectionnez une action dans le tableau."
        )

        self.detail_description.clear()

    # ==========================================================
    # ACTUALISATION À L'AFFICHAGE
    # ==========================================================

    def showEvent(
        self,
        event,
    ):

        self.refresh_table()

        super().showEvent(
            event
        )