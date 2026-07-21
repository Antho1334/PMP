from pathlib import Path

import pytest
from PySide6.QtTest import QSignalSpy

from app.models.abusive_parking import AbusiveParking
from app.providers.abusive_parking_provider import AbusiveParkingProvider
from app.repositories.abusive_parking_repository import (
    AbusiveParkingNotFoundError,
    AbusiveParkingRepository,
)
from app.services.abusive_parking_service import AbusiveParkingService
from tests.test_abusive_parking_geocoding_pipeline import TemporaryDatabase


def _repository(tmp_path):
    database = TemporaryDatabase(tmp_path / "deletion.db")
    return database, AbusiveParkingRepository(db=database)


def _add(repository, registration, photo_path=None):
    repository.add(
        AbusiveParking(
            registration=registration,
            photo_path=str(photo_path) if photo_path else None,
        )
    )
    return repository.get_by_registration(registration)


def test_delete_uses_id_and_cascades_passages(tmp_path):
    database, repository = _repository(tmp_path)
    try:
        target = _add(repository, "AA-123-AA")
        untouched = _add(repository, "BB-456-BB")
        database.cursor.execute(
            """
            INSERT INTO abusive_parking_passages
            (parking_id, passage_date, passage_time)
            VALUES (?, '2026-07-20', '10:00')
            """,
            (target.id,),
        )
        database.connection.commit()

        assert database.cursor.execute(
            "PRAGMA foreign_keys"
        ).fetchone()[0] == 1
        repository.delete(target.id)

        assert repository.get_by_id(target.id) is None
        assert repository.get_by_id(untouched.id) is not None
        assert database.cursor.execute(
            """
            SELECT COUNT(*)
            FROM abusive_parking_passages
            WHERE parking_id=?
            """,
            (target.id,),
        ).fetchone()[0] == 0
    finally:
        database.connection.close()


def test_missing_id_rolls_back_and_is_not_a_false_success(tmp_path):
    database, repository = _repository(tmp_path)
    try:
        _add(repository, "AA-123-AA")
        before = database.cursor.execute(
            "SELECT COUNT(*) FROM abusive_parking"
        ).fetchone()[0]

        with pytest.raises(AbusiveParkingNotFoundError):
            repository.delete(999_999)

        after = database.cursor.execute(
            "SELECT COUNT(*) FROM abusive_parking"
        ).fetchone()[0]
        assert after == before
    finally:
        database.connection.close()


def test_database_error_rolls_back_without_partial_deletion(tmp_path):
    database, repository = _repository(tmp_path)
    try:
        target = _add(repository, "AA-123-AA")
        database.cursor.execute(
            """
            CREATE TRIGGER prevent_parking_delete
            BEFORE DELETE ON abusive_parking
            BEGIN
                SELECT RAISE(ABORT, 'suppression refusée');
            END
            """
        )
        database.connection.commit()

        with pytest.raises(Exception):
            repository.delete(target.id)

        assert repository.get_by_id(target.id) is not None
    finally:
        database.connection.close()


def test_unreferenced_managed_photo_is_deleted(tmp_path, monkeypatch):
    database, repository = _repository(tmp_path)
    photo = tmp_path / "photo.jpeg"
    photo.write_bytes(b"photo")
    monkeypatch.setattr(
        repository,
        "_is_managed_photo_path",
        lambda path: path == photo.resolve(),
    )
    try:
        target = _add(repository, "AA-123-AA", photo)

        result = repository.delete(target.id)

        assert not photo.exists()
        assert result.deleted_files == (str(photo.resolve()),)
    finally:
        database.connection.close()


def test_shared_photo_is_preserved(tmp_path, monkeypatch):
    database, repository = _repository(tmp_path)
    photo = tmp_path / "shared.jpeg"
    photo.write_bytes(b"photo")
    monkeypatch.setattr(
        repository,
        "_is_managed_photo_path",
        lambda path: path == photo.resolve(),
    )
    try:
        target = _add(repository, "AA-123-AA", photo)
        _add(repository, "BB-456-BB", photo)

        result = repository.delete(target.id)

        assert photo.exists()
        assert result.preserved_files == (str(photo.resolve()),)
    finally:
        database.connection.close()


def test_external_photo_is_never_deleted(tmp_path):
    database, repository = _repository(tmp_path)
    photo = tmp_path / "external.jpeg"
    photo.write_bytes(b"photo")
    try:
        target = _add(repository, "AA-123-AA", photo)

        result = repository.delete(target.id)

        assert photo.exists()
        assert result.preserved_files == (str(photo.resolve()),)
    finally:
        database.connection.close()


def test_file_error_after_commit_is_only_a_warning(
    tmp_path,
    monkeypatch,
):
    database, repository = _repository(tmp_path)
    photo = tmp_path / "locked.jpeg"
    photo.write_bytes(b"photo")
    monkeypatch.setattr(
        repository,
        "_is_managed_photo_path",
        lambda path: path == photo.resolve(),
    )
    original_unlink = Path.unlink

    def fail_for_test_photo(path, *args, **kwargs):
        if path == photo.resolve():
            raise PermissionError("fichier verrouillé")
        return original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_for_test_photo)
    try:
        target = _add(repository, "AA-123-AA", photo)

        result = repository.delete(target.id)

        assert repository.get_by_id(target.id) is None
        assert result.has_file_warnings
        assert photo.exists()
    finally:
        database.connection.close()


def test_signal_is_emitted_once_only_after_success(tmp_path):
    database, repository = _repository(tmp_path)
    try:
        repository.add(
            AbusiveParking(
                registration="AA-123-AA",
                latitude=43.3336,
                longitude=3.12,
            )
        )
        target = repository.get_by_registration("AA-123-AA")
        service = AbusiveParkingService(repository=repository)
        spy = QSignalSpy(service.monitoringChanged)
        provider = AbusiveParkingProvider(service)
        refresh_calls = []
        service.monitoringChanged.connect(
            lambda: refresh_calls.append(provider.get_map_items())
        )
        assert len(provider.get_map_items()) == 1

        service.delete_monitoring(target.id)

        assert spy.count() == 1
        assert refresh_calls == [[]]
        with pytest.raises(AbusiveParkingNotFoundError):
            service.delete_monitoring(target.id)
        assert spy.count() == 1
        assert refresh_calls == [[]]
        assert provider.get_map_items() == []
    finally:
        database.connection.close()


def test_signal_is_not_emitted_after_sqlite_error(tmp_path):
    database, repository = _repository(tmp_path)
    try:
        target = _add(repository, "AA-123-AA")
        database.cursor.execute(
            """
            CREATE TRIGGER prevent_service_delete
            BEFORE DELETE ON abusive_parking
            BEGIN
                SELECT RAISE(ABORT, 'suppression refusée');
            END
            """
        )
        database.connection.commit()
        service = AbusiveParkingService(repository=repository)
        spy = QSignalSpy(service.monitoringChanged)

        with pytest.raises(Exception):
            service.delete_monitoring(target.id)

        assert spy.count() == 0
        assert repository.get_by_id(target.id) is not None
    finally:
        database.connection.close()


def test_unreferenced_passage_photo_is_deleted_after_cascade(
    tmp_path,
    monkeypatch,
):
    database, repository = _repository(tmp_path)
    photo = tmp_path / "passage.jpeg"
    photo.write_bytes(b"photo")
    monkeypatch.setattr(
        repository,
        "_is_managed_photo_path",
        lambda path: path == photo.resolve(),
    )
    try:
        target = _add(repository, "AA-123-AA")
        database.cursor.execute(
            """
            INSERT INTO abusive_parking_passages
            (parking_id, passage_date, passage_time, photo_path)
            VALUES (?, '2026-07-20', '10:00', ?)
            """,
            (target.id, str(photo)),
        )
        database.connection.commit()

        result = repository.delete(target.id)

        assert not photo.exists()
        assert result.deleted_files == (str(photo.resolve()),)
    finally:
        database.connection.close()
