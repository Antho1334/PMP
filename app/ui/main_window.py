from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QWidget,
)

from app.ui.menu import Menu
from app.ui.page_manager import PageManager


class MainWindow(QMainWindow):

    def __init__(
        self,
        map_service,
        geocoding_service,
        abusive_parking_service,
        journal_service,
        daily_report_service,
        daily_report_renderer,
    ):
        super().__init__()

        self.setWindowTitle(
            "PMP - Poste Municipal Personnel"
        )

        self.resize(
            1400,
            850
        )

        # ======================================================
        # CRÉATION DES COMPOSANTS
        # ======================================================

        self.pages = PageManager(
            map_service,
            geocoding_service,
            abusive_parking_service,
            journal_service,
            daily_report_service,
            daily_report_renderer,
        )

        self.menu = Menu(
            self.pages
        )

        # ======================================================
        # NAVIGATION DU MENU LATÉRAL
        # ======================================================

        # Lorsque l'utilisateur clique sur un élément du menu,
        # la page correspondante est affichée.
        self.menu.currentRowChanged.connect(
            self.pages.setCurrentIndex
        )

        # ======================================================
        # CONNEXION DES ACCÈS RAPIDES DE LA PAGE D'ACCUEIL
        # ======================================================

        # Récupération de la page Accueil
        self.home_page = (
            self.pages.widget(0)
        )

        # Récupération de la page Journal
        self.journal_page = (
            self.pages.widget(1)
        )

        # ------------------------------------------------------
        # Nouvelle activité
        # ------------------------------------------------------

        self.home_page.btn_new_activity.clicked.connect(
            self.open_new_activity
        )

        # ------------------------------------------------------
        # Ouvrir le Journal
        # ------------------------------------------------------

        self.home_page.btn_journal.clicked.connect(
            lambda: self.navigate_to(1)
        )

        # ------------------------------------------------------
        # Ouvrir les Dossiers
        # ------------------------------------------------------

        self.home_page.btn_folders.clicked.connect(
            lambda: self.navigate_to(2)
        )

        # ------------------------------------------------------
        # Voir les Actions
        # ------------------------------------------------------

        self.home_page.btn_actions.clicked.connect(
            lambda: self.navigate_to(3)
        )

        # ======================================================
        # AFFICHER L'ACCUEIL AU DÉMARRAGE
        # ======================================================

        self.menu.setCurrentRow(
            0
        )

        # ======================================================
        # CONSTRUCTION DE LA FENÊTRE
        # ======================================================

        layout = QHBoxLayout()

        layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        layout.addWidget(
            self.menu
        )

        layout.addWidget(
            self.pages
        )

        central = QWidget()

        central.setLayout(
            layout
        )

        self.setCentralWidget(
            central
        )

    # ==========================================================
    # NAVIGATION VERS UNE PAGE
    # ==========================================================

    def navigate_to(
        self,
        index,
    ):
        """
        Navigue vers une page de PMP
        et synchronise le menu latéral.
        """

        self.menu.setCurrentRow(
            index
        )

    # ==========================================================
    # OUVRIR UNE NOUVELLE ACTIVITÉ
    # ==========================================================

    def open_new_activity(self):
        """
        Ouvre le Journal directement
        sur un formulaire de nouvelle activité.
        """

        # Réinitialisation du formulaire
        self.journal_page.new_activity()

        # Navigation vers le Journal
        self.navigate_to(
            1
        )
