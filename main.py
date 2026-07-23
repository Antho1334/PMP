from app.database.database import Database
from app.providers.abusive_parking_provider import AbusiveParkingProvider
from app.providers.journal_daily_report_provider import JournalDailyReportProvider
from app.renderers.daily_report_renderer import DailyReportRenderer
from app.services.daily_report_registry import DailyReportRegistry
from app.services.daily_report_service import DailyReportService
from app.services.journal_service import JournalService
from app.services.map_registry import MapRegistry
from app.services.map_service import MapService
from app.services.geocoding_service import GeocodingService
from app.services.abusive_parking_service import AbusiveParkingService
import sys

from PySide6.QtWidgets import QApplication

from app.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    Database()

    map_registry = MapRegistry()
    abusive_parking_service = AbusiveParkingService()
    map_registry.register(AbusiveParkingProvider(abusive_parking_service))
    map_service = MapService(map_registry)
    geocoding_service = GeocodingService()
    journal_service = JournalService()
    daily_report_registry = DailyReportRegistry()
    daily_report_registry.register(JournalDailyReportProvider(journal_service))
    daily_report_service = DailyReportService(daily_report_registry)
    daily_report_renderer = DailyReportRenderer()

    window = MainWindow(
        map_service,
        geocoding_service,
        abusive_parking_service,
        journal_service,
        daily_report_service,
        daily_report_renderer,
    )
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
