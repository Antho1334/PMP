from PySide6.QtWidgets import QStackedWidget

from app.ui.pages.home_page import HomePage
from app.ui.pages.journal_page import JournalPage
from app.ui.pages.dossiers_page import DossiersPage
from app.ui.pages.actions_page import ActionsPage
from app.ui.pages.abusive_parking_page import AbusiveParkingPage
from app.ui.pages.operational_map_page import OperationalMapPage
from app.ui.pages.documents_page import DocumentsPage
from app.ui.pages.juridique_page import JuridiquePage
from app.ui.pages.contacts_page import ContactsPage
from app.ui.pages.dashboard_page import DashboardPage
from app.ui.pages.settings_page import SettingsPage
from app.ui.pages.daily_report_page import DailyReportPage


class PageManager(QStackedWidget):

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

        self.addWidget(HomePage())                # index 0
        self.addWidget(JournalPage(journal_service))  # index 1
        self.addWidget(DossiersPage())            # index 2
        self.addWidget(ActionsPage())             # index 3
        self.addWidget(
            AbusiveParkingPage(
                abusive_parking_service,
                geocoding_service,
            )
        )                                         # index 4
        self.addWidget(DocumentsPage())           # index 5
        self.addWidget(JuridiquePage())           # index 6
        self.addWidget(ContactsPage())            # index 7
        self.addWidget(DashboardPage())           # index 8
        self.addWidget(SettingsPage())            # index 9
        self.addWidget(
            OperationalMapPage(
                map_service,
                geocoding_service,
                abusive_parking_service,
            )
        )  # index 10
        self.addWidget(
            DailyReportPage(
                daily_report_service,
                daily_report_renderer,
            )
        )  # index 11
