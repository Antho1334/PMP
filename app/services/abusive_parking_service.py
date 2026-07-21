from datetime import date

from PySide6.QtCore import QObject, Signal

from app.models.abusive_parking import AbusiveParking
from app.repositories.abusive_parking_repository import (
    AbusiveParkingRepository,
)


class AbusiveParkingService(QObject):
    """
    Couche métier du module Stationnement abusif.
    """

    monitoringChanged = Signal()

    def __init__(self, repository=None, parent=None):

        super().__init__(parent)

        self.repository = repository or AbusiveParkingRepository()

    # ==========================================================
    # CRUD
    # ==========================================================

    def add_monitoring(
        self,
        parking: AbusiveParking
    ):

        self.repository.add(parking)
        self.monitoringChanged.emit()

    def update_monitoring(
        self,
        parking: AbusiveParking
    ):

        self.repository.update(parking)
        self.monitoringChanged.emit()

    def delete_monitoring(
        self,
        parking_id: int
    ):

        result = self.repository.delete(parking_id)
        self.monitoringChanged.emit()
        return result

    # ==========================================================
    # CONSULTATION
    # ==========================================================

    def get_all(self):

        return self.repository.get_all()

    def get_active(self):

        return self.repository.get_active()

    def get_history(self):

        return self.repository.get_history()

    def get_by_id(
        self,
        parking_id: int
    ):

        return self.repository.get_by_id(parking_id)

    def get_by_registration(
        self,
        registration: str
    ):

        return self.repository.get_by_registration(
            registration
        )

    # ==========================================================
    # CLÔTURE
    # ==========================================================

    def close_monitoring(
        self,
        parking_id: int,
        reason: str
    ):

        self.repository.close_monitoring(
            parking_id,
            reason
        )
        self.monitoringChanged.emit()

    # ==========================================================
    # CALCULS MÉTIER
    # ==========================================================

    def get_days_elapsed(
        self,
        parking: AbusiveParking
    ) -> int:

        if parking.monitoring_date is None:
            return 0

        return (
            date.today()
            - parking.monitoring_date
        ).days

    def get_days_remaining(
        self,
        parking: AbusiveParking
    ) -> int:

        return (
            parking.monitoring_delay_days
            - self.get_days_elapsed(parking)
        )

    def is_due(
        self,
        parking: AbusiveParking
    ) -> bool:

        return self.get_days_remaining(
            parking
        ) <= 0

    # ==========================================================
    # LISTES POUR TABLEAU DE BORD
    # ==========================================================

    def get_due_soon(self):

        vehicles = []

        for parking in self.get_active():

            remaining = self.get_days_remaining(
                parking
            )

            if remaining <= 2:

                vehicles.append(parking)

        vehicles.sort(
            key=lambda x: self.get_days_remaining(x)
        )

        return vehicles

    def get_overdue(self):

        vehicles = []

        for parking in self.get_active():

            if self.is_due(parking):

                vehicles.append(parking)

        vehicles.sort(
            key=lambda x: self.get_days_remaining(x)
        )

        return vehicles

    # ==========================================================
    # STATISTIQUES
    # ==========================================================

    def count_active(self):

        return len(
            self.get_active()
        )

    def count_history(self):

        return len(
            self.get_history()
        )

    def count_due_soon(self):

        return len(
            self.get_due_soon()
        )

    def count_overdue(self):

        return len(
            self.get_overdue()
        )
