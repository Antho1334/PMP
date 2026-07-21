import sqlite3

from app.models.abusive_parking import AbusiveParking
from app.models.geocoding_result import GeocodingResult
from app.providers.abusive_parking_provider import AbusiveParkingProvider
from app.repositories.abusive_parking_repository import (
    AbusiveParkingRepository,
)
from app.services.abusive_parking_service import AbusiveParkingService
from app.services.map_registry import MapRegistry
from app.services.map_service import MapService
from app.ui.widgets.operational_map import _serialize_map_items


class TemporaryDatabase:
    def __init__(self, path):
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()
        self.cursor.execute("PRAGMA foreign_keys = ON")
        self.cursor.execute(
            """
            CREATE TABLE abusive_parking
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                registration TEXT NOT NULL,
                brand TEXT,
                model TEXT,
                vehicle_type TEXT,
                color TEXT,
                owner TEXT,
                location TEXT,
                latitude REAL,
                longitude REAL,
                monitoring_date TEXT,
                monitoring_time TEXT,
                monitoring_delay_days INTEGER DEFAULT 7,
                photo_path TEXT,
                observations TEXT,
                status TEXT DEFAULT 'active',
                closure_date TEXT,
                closure_time TEXT,
                closure_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.cursor.execute(
            """
            CREATE TABLE abusive_parking_passages
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parking_id INTEGER NOT NULL,
                passage_type TEXT DEFAULT 'Contrôle',
                passage_date TEXT NOT NULL,
                passage_time TEXT NOT NULL,
                address TEXT,
                latitude REAL,
                longitude REAL,
                photo_path TEXT,
                observations TEXT,
                agent TEXT,
                weather TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parking_id)
                    REFERENCES abusive_parking(id)
                    ON DELETE CASCADE
            )
            """
        )
        self.connection.commit()


def test_geocoded_monitoring_reaches_leaflet_and_refreshes_once(tmp_path):
    database = TemporaryDatabase(tmp_path / "pipeline.db")
    try:
        repository = AbusiveParkingRepository(db=database)
        service = AbusiveParkingService(repository=repository)
        registry = MapRegistry()
        registry.register(AbusiveParkingProvider(service))
        map_service = MapService(registry)

        result = GeocodingResult(
            label="1 place de la Mairie, 34310 Montady",
            latitude=43.3336,
            longitude=3.12,
        )
        parking = AbusiveParking(
            registration="AA-123-AA",
            location=result.label,
            latitude=result.latitude,
            longitude=result.longitude,
        )

        refresh_calls = []
        leaflet_payloads = []

        def refresh_map():
            refresh_calls.append(True)
            leaflet_payloads.append(
                _serialize_map_items(map_service.get_items())
            )

        service.monitoringChanged.connect(refresh_map)
        service.add_monitoring(parking)

        stored = database.cursor.execute(
            """
            SELECT registration, location, latitude, longitude
            FROM abusive_parking
            """
        ).fetchone()
        assert dict(stored) == {
            "registration": "AA-123-AA",
            "location": result.label,
            "latitude": result.latitude,
            "longitude": result.longitude,
        }

        items = map_service.get_items()
        assert len(items) == 1
        assert items[0].source == "abusive_parking"
        assert items[0].title == "AA-123-AA"
        assert items[0].latitude == result.latitude
        assert items[0].longitude == result.longitude

        assert refresh_calls == [True]
        assert leaflet_payloads == [
            [
                {
                    "key": "abusive_parking:1",
                    "title": "AA-123-AA",
                    "subtitle": result.label,
                    "latitude": result.latitude,
                    "longitude": result.longitude,
                    "color": "#d97706",
                    "icon": "vehicle",
                }
            ]
        ]
    finally:
        database.connection.close()


def test_repository_update_preserves_row_count_and_sqlite_id(tmp_path):
    database = TemporaryDatabase(tmp_path / "update.db")
    try:
        repository = AbusiveParkingRepository(db=database)
        service = AbusiveParkingService(repository=repository)
        parking = AbusiveParking(
            registration="AA-123-AA",
            brand="Ancienne marque",
        )

        initial_count = database.cursor.execute(
            "SELECT COUNT(*) FROM abusive_parking"
        ).fetchone()[0]
        service.add_monitoring(parking)
        after_create_count = database.cursor.execute(
            "SELECT COUNT(*) FROM abusive_parking"
        ).fetchone()[0]
        stored = repository.get_all()[0]
        stored_id = stored.id

        stored.brand = "Nouvelle marque"
        service.update_monitoring(stored)
        after_update_count = database.cursor.execute(
            "SELECT COUNT(*) FROM abusive_parking"
        ).fetchone()[0]
        updated = repository.get_by_id(stored_id)

        assert after_create_count == initial_count + 1
        assert after_update_count == after_create_count
        assert updated.id == stored_id
        assert updated.brand == "Nouvelle marque"
    finally:
        database.connection.close()
