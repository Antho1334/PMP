from datetime import datetime, date
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QFrame,
)

from app.services.journal_service import JournalService
from app.services.action_service import ActionService


class HomePage(QWidget):

    def __init__(self):
        super().__init__()

        # ======================================================
        # SERVICES
        # ======================================================

        self.journal_service = JournalService()
        self.action_service = ActionService()

        self.build_ui()

        # Premier chargement des données
        self.refresh_dashboard()

    # ==========================================================
    # CONSTRUCTION DE L'INTERFACE
    # ==========================================================

    def build_ui(self):

        # ------------------------------------------------------
        # CONTENEUR PRINCIPAL
        # ------------------------------------------------------

        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(
            30,
            15,
            30,
            25,
        )

        main_layout.setSpacing(
            15
        )

        # ======================================================
        # CARTOUCHE PMP
        # ======================================================

        cartouche_layout = QHBoxLayout()

        cartouche_layout.addStretch()

        self.cartouche_label = QLabel()

        self.cartouche_label.setAlignment(
            Qt.AlignCenter
        )

        cartouche_path = (
            Path(__file__).resolve().parents[2]
            / "resources"
            / "images"
            / "cartouche_pmp.png"
        )

        if cartouche_path.exists():

            pixmap = QPixmap(
                str(cartouche_path)
            )

            if not pixmap.isNull():

                pixmap = pixmap.scaled(
                    650,
                    150,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )

                self.cartouche_label.setPixmap(
                    pixmap
                )

        self.cartouche_label.setMaximumHeight(
            155
        )

        cartouche_layout.addWidget(
            self.cartouche_label
        )

        cartouche_layout.addStretch()

        main_layout.addLayout(
            cartouche_layout
        )

        # ======================================================
        # EN-TÊTE
        # ======================================================

        header_layout = QHBoxLayout()

        welcome_layout = QVBoxLayout()

        self.welcome_label = QLabel(
            "Bonjour Anthony"
        )

        self.welcome_label.setStyleSheet(
            """
            font-size: 28px;
            font-weight: bold;
            color: #202124;
            """
        )

        self.subtitle_label = QLabel(
            "PMP — Poste Municipal Personnel"
        )

        self.subtitle_label.setStyleSheet(
            """
            font-size: 15px;
            color: #666666;
            """
        )

        welcome_layout.addWidget(
            self.welcome_label
        )

        welcome_layout.addWidget(
            self.subtitle_label
        )

        # ------------------------------------------------------
        # DATE DU JOUR
        # ------------------------------------------------------

        self.date_label = QLabel(
            datetime.now().strftime(
                "%d/%m/%Y"
            )
        )

        self.date_label.setAlignment(
            Qt.AlignRight
            | Qt.AlignVCenter
        )

        self.date_label.setStyleSheet(
            """
            font-size: 15px;
            color: #555555;
            """
        )

        header_layout.addLayout(
            welcome_layout
        )

        header_layout.addStretch()

        header_layout.addWidget(
            self.date_label
        )

        main_layout.addLayout(
            header_layout
        )

        # ======================================================
        # VUE D'ENSEMBLE
        # ======================================================

        dashboard_title = QLabel(
            "Vue d'ensemble"
        )

        dashboard_title.setStyleSheet(
            """
            font-size: 18px;
            font-weight: bold;
            color: #303134;
            """
        )

        main_layout.addWidget(
            dashboard_title
        )

        # ======================================================
        # CARTES DE SYNTHÈSE
        # ======================================================

        cards_layout = QGridLayout()

        cards_layout.setSpacing(
            15
        )

        (
            self.card_today,
            self.value_today,
        ) = self.create_stat_card(
            "📋",
            "Activités aujourd'hui",
            "0",
        )

        (
            self.card_important,
            self.value_important,
        ) = self.create_stat_card(
            "⚠️",
            "Évènements importants",
            "0",
        )

        (
            self.card_actions,
            self.value_actions,
        ) = self.create_stat_card(
            "☑️",
            "Actions en cours",
            "0",
        )

        (
            self.card_folders,
            self.value_folders,
        ) = self.create_stat_card(
            "📁",
            "Dossiers actifs",
            "—",
        )

        cards_layout.addWidget(
            self.card_today,
            0,
            0,
        )

        cards_layout.addWidget(
            self.card_important,
            0,
            1,
        )

        cards_layout.addWidget(
            self.card_actions,
            0,
            2,
        )

        cards_layout.addWidget(
            self.card_folders,
            0,
            3,
        )

        main_layout.addLayout(
            cards_layout
        )

        # ======================================================
        # ZONE CENTRALE
        # ======================================================

        center_layout = QHBoxLayout()

        center_layout.setSpacing(
            20
        )

        # ======================================================
        # BLOC AUJOURD'HUI
        # ======================================================

        today_frame = QFrame()

        today_frame.setObjectName(
            "dashboardCard"
        )

        today_layout = QVBoxLayout(
            today_frame
        )

        today_layout.setContentsMargins(
            20,
            20,
            20,
            20,
        )

        today_title = QLabel(
            "Aujourd'hui"
        )

        today_title.setStyleSheet(
            """
            font-size: 18px;
            font-weight: bold;
            """
        )

        today_subtitle = QLabel(
            "Dernières activités du Journal"
        )

        today_subtitle.setStyleSheet(
            """
            color: #777777;
            font-size: 13px;
            """
        )

        today_layout.addWidget(
            today_title
        )

        today_layout.addWidget(
            today_subtitle
        )

        today_layout.addSpacing(
            12
        )

        self.today_content = QLabel()

        self.today_content.setWordWrap(
            True
        )

        self.today_content.setAlignment(
            Qt.AlignTop
        )

        self.today_content.setTextFormat(
            Qt.RichText
        )

        self.today_content.setStyleSheet(
            """
            color: #444444;
            font-size: 14px;
            """
        )

        today_layout.addWidget(
            self.today_content
        )

        today_layout.addStretch()

        center_layout.addWidget(
            today_frame,
            2,
        )

        # ======================================================
        # BLOC À SURVEILLER
        # ======================================================

        watch_frame = QFrame()

        watch_frame.setObjectName(
            "dashboardCard"
        )

        watch_layout = QVBoxLayout(
            watch_frame
        )

        watch_layout.setContentsMargins(
            20,
            20,
            20,
            20,
        )

        watch_title = QLabel(
            "À surveiller"
        )

        watch_title.setStyleSheet(
            """
            font-size: 18px;
            font-weight: bold;
            """
        )

        watch_subtitle = QLabel(
            "Prochaines actions prioritaires"
        )

        watch_subtitle.setStyleSheet(
            """
            color: #777777;
            font-size: 13px;
            """
        )

        watch_layout.addWidget(
            watch_title
        )

        watch_layout.addWidget(
            watch_subtitle
        )

        watch_layout.addSpacing(
            12
        )

        self.watch_content = QLabel()

        self.watch_content.setWordWrap(
            True
        )

        self.watch_content.setAlignment(
            Qt.AlignTop
        )

        self.watch_content.setTextFormat(
            Qt.RichText
        )

        self.watch_content.setStyleSheet(
            """
            color: #444444;
            font-size: 14px;
            """
        )

        watch_layout.addWidget(
            self.watch_content
        )

        watch_layout.addStretch()

        center_layout.addWidget(
            watch_frame,
            1,
        )

        main_layout.addLayout(
            center_layout,
            1,
        )

        # ======================================================
        # ACCÈS RAPIDES
        # ======================================================

        quick_title = QLabel(
            "Accès rapides"
        )

        quick_title.setStyleSheet(
            """
            font-size: 18px;
            font-weight: bold;
            """
        )

        main_layout.addWidget(
            quick_title
        )

        quick_layout = QHBoxLayout()

        quick_layout.setSpacing(
            12
        )

        self.btn_new_activity = QPushButton(
            "➕  Nouvelle activité"
        )

        self.btn_journal = QPushButton(
            "🗓️  Ouvrir le Journal"
        )

        self.btn_folders = QPushButton(
            "📁  Ouvrir les Dossiers"
        )

        self.btn_actions = QPushButton(
            "☑️  Voir les Actions"
        )

        for button in (
            self.btn_new_activity,
            self.btn_journal,
            self.btn_folders,
            self.btn_actions,
        ):

            button.setMinimumHeight(
                48
            )

            button.setCursor(
                Qt.PointingHandCursor
            )

            button.setStyleSheet(
                """
                QPushButton {
                    background-color: #ffffff;
                    border: 1px solid #dcdcdc;
                    border-radius: 8px;
                    padding: 10px 16px;
                    font-size: 14px;
                    text-align: left;
                }

                QPushButton:hover {
                    background-color: #f2f6ff;
                    border: 1px solid #9db8e8;
                }

                QPushButton:pressed {
                    background-color: #e5edfa;
                }
                """
            )

            quick_layout.addWidget(
                button
            )

        main_layout.addLayout(
            quick_layout
        )

        # ======================================================
        # STYLE GLOBAL
        # ======================================================

        self.setStyleSheet(
            """
            HomePage {
                background-color: #f5f6f8;
            }

            QFrame#dashboardCard {
                background-color: white;
                border: 1px solid #e2e2e2;
                border-radius: 10px;
            }
            """
        )

    # ==========================================================
    # CRÉATION D'UNE CARTE DE STATISTIQUE
    # ==========================================================

    def create_stat_card(
        self,
        icon,
        title,
        value,
    ):

        frame = QFrame()

        frame.setObjectName(
            "dashboardCard"
        )

        frame.setMinimumHeight(
            110
        )

        layout = QVBoxLayout(
            frame
        )

        layout.setContentsMargins(
            18,
            15,
            18,
            15,
        )

        top_layout = QHBoxLayout()

        icon_label = QLabel(
            icon
        )

        icon_label.setStyleSheet(
            """
            font-size: 22px;
            """
        )

        title_label = QLabel(
            title
        )

        title_label.setWordWrap(
            True
        )

        title_label.setStyleSheet(
            """
            font-size: 13px;
            color: #666666;
            """
        )

        top_layout.addWidget(
            icon_label
        )

        top_layout.addWidget(
            title_label
        )

        top_layout.addStretch()

        layout.addLayout(
            top_layout
        )

        value_label = QLabel(
            value
        )

        value_label.setStyleSheet(
            """
            font-size: 28px;
            font-weight: bold;
            color: #202124;
            """
        )

        layout.addWidget(
            value_label
        )

        return frame, value_label

    # ==========================================================
    # ACTUALISATION GÉNÉRALE DU TABLEAU DE BORD
    # ==========================================================

    def refresh_dashboard(self):

        # Mise à jour de la date
        self.date_label.setText(
            datetime.now().strftime(
                "%d/%m/%Y"
            )
        )

        # Actualisation du Journal
        self.refresh_journal_data()

        # Actualisation des Actions
        self.refresh_actions_data()

    # ==========================================================
    # ACTUALISATION DES DONNÉES DU JOURNAL
    # ==========================================================

    def refresh_journal_data(self):

        # ------------------------------------------------------
        # ACTIVITÉS DU JOUR
        # ------------------------------------------------------

        activities = (
            self.journal_service
            .search_activities_by_date(
                date.today()
            )
        )

        # ------------------------------------------------------
        # COMPTEUR ACTIVITÉS DU JOUR
        # ------------------------------------------------------

        self.value_today.setText(
            str(
                len(activities)
            )
        )

        # ------------------------------------------------------
        # COMPTEUR ÉVÈNEMENTS IMPORTANTS DU JOURNAL
        # ------------------------------------------------------

        important_count = sum(
            1
            for activity in activities
            if activity.important
        )

        self.value_important.setText(
            str(
                important_count
            )
        )

        # ------------------------------------------------------
        # AUCUNE ACTIVITÉ
        # ------------------------------------------------------

        if not activities:

            self.today_content.setText(
                "Aucune activité enregistrée aujourd'hui."
            )

            return

        # ------------------------------------------------------
        # TRI PAR HEURE
        # PLUS RÉCENTE EN PREMIER
        # ------------------------------------------------------

        sorted_activities = sorted(
            activities,
            key=lambda activity:
                activity.activity_time,
            reverse=True,
        )

        # ------------------------------------------------------
        # MAXIMUM 4 ACTIVITÉS
        # ------------------------------------------------------

        latest_activities = (
            sorted_activities[:4]
        )

        lines = []

        for activity in latest_activities:

            hour = (
                activity.activity_time
                .strftime("%H:%M")
            )

            important_marker = (
                " ⚠️"
                if activity.important
                else ""
            )

            line = (
                f"<b>{hour}</b>"
                f" &nbsp; "
                f"<b>{activity.category}</b>"
                f"{important_marker}"
                f"<br>"
                f"{activity.title}"
            )

            lines.append(
                line
            )

        self.today_content.setText(
            "<br><br>".join(
                lines
            )
        )

    # ==========================================================
    # ACTUALISATION DES ACTIONS
    # ==========================================================

    def refresh_actions_data(self):

        # ------------------------------------------------------
        # ACTIONS EN COURS
        # ------------------------------------------------------

        pending_actions = (
            self.action_service
            .get_pending()
        )

        # Mise à jour du compteur
        self.value_actions.setText(
            str(
                len(pending_actions)
            )
        )

        # ------------------------------------------------------
        # ACTIONS IMPORTANTES À VENIR
        # ------------------------------------------------------

        important_actions = (
            self.action_service
            .get_upcoming_important()
        )

        # ------------------------------------------------------
        # AUCUNE ACTION IMPORTANTE
        # ------------------------------------------------------

        if not important_actions:

            self.watch_content.setText(
                "Aucune action prioritaire à venir."
            )

            return

        # ------------------------------------------------------
        # MAXIMUM 4 ACTIONS IMPORTANTES
        # ------------------------------------------------------

        important_actions = (
            important_actions[:4]
        )

        lines = []

        today = date.today()

        for action in important_actions:

            # --------------------------------------------------
            # AFFICHAGE DE LA DATE
            # --------------------------------------------------

            if action.action_date == today:

                date_text = (
                    "Aujourd'hui"
                )

            else:

                date_text = (
                    action.action_date
                    .strftime("%d/%m/%Y")
                )

            # --------------------------------------------------
            # AFFICHAGE DE L'HEURE
            # --------------------------------------------------

            hour_text = (
                action.action_time
                .strftime("%H:%M")
            )

            # --------------------------------------------------
            # INDICATEUR OUTLOOK
            # --------------------------------------------------

            outlook_marker = (
                " 🔔"
                if action.outlook_reminder
                else ""
            )

            # --------------------------------------------------
            # CONSTRUCTION DE LA LIGNE
            # --------------------------------------------------

            line = (
                f"<b>⚠️ {date_text}</b>"
                f" à "
                f"<b>{hour_text}</b>"
                f"{outlook_marker}"
                f"<br>"
                f"{action.title}"
            )

            lines.append(
                line
            )

        self.watch_content.setText(
            "<br><br>".join(
                lines
            )
        )

    # ==========================================================
    # ACTUALISATION AUTOMATIQUE À L'AFFICHAGE
    # ==========================================================

    def showEvent(
        self,
        event,
    ):

        # Actualisation automatique à chaque fois
        # que l'utilisateur revient sur l'Accueil.
        self.refresh_dashboard()

        super().showEvent(
            event
        )