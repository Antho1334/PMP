from PySide6.QtTest import QSignalSpy

from app.models.abusive_parking import AbusiveParking
from app.services.abusive_parking_service import AbusiveParkingService


class FakeRepository:
    def __init__(self):
        self.added = []
        self.updated = []

    def add(self, parking):
        self.added.append(parking)

    def update(self, parking):
        self.updated.append(parking)


class FailingRepository(FakeRepository):
    def add(self, parking):
        raise RuntimeError("échec de persistance")


def test_business_notification_is_emitted_after_create_and_update():
    repository = FakeRepository()
    service = AbusiveParkingService(repository=repository)
    spy = QSignalSpy(service.monitoringChanged)
    parking = AbusiveParking(registration="AA-123-AA")

    service.add_monitoring(parking)
    service.update_monitoring(parking)

    assert spy.count() == 2
    assert repository.added == [parking]
    assert repository.updated == [parking]


def test_business_notification_is_not_emitted_when_persistence_fails():
    service = AbusiveParkingService(repository=FailingRepository())
    spy = QSignalSpy(service.monitoringChanged)

    try:
        service.add_monitoring(AbusiveParking(registration="AA-123-AA"))
    except RuntimeError:
        pass

    assert spy.count() == 0
