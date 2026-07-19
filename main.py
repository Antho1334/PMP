from app.database.database import Database
from app.providers.abusive_parking_provider import AbusiveParkingProvider
from app.services.map_registry import MapRegistry
from app.services.map_service import MapService
from app.services.geocoding_service import GeocodingService
import sys

from PySide6.QtWidgets import QApplication

from app.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    Database()

    map_registry = MapRegistry()
    map_registry.register(AbusiveParkingProvider())
    map_service = MapService(map_registry)
    geocoding_service = GeocodingService()

    window = MainWindow(map_service, geocoding_service)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
