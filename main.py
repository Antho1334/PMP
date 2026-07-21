from app.database.database import Database
from app.providers.abusive_parking_provider import AbusiveParkingProvider
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

    window = MainWindow(
        map_service,
        geocoding_service,
        abusive_parking_service,
    )
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
