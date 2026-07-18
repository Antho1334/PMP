from datetime import date

from app.models.abusive_parking import AbusiveParking
from app.repositories.abusive_parking_repository import (
    AbusiveParkingRepository,
)


class AbusiveParkingService:
    """
    Couche métier du module Stationnement abusif.
    """

    def __init__(self):

        self.repository = AbusiveParkingRepository()

    # ==========================================================
    # CRUD
    # ==========================================================

    def add_monitoring(
        self,
        parking: AbusiveParking
    ):

        self.repository.add(parking)

    def update_monitoring(
        self,
        parking: AbusiveParking
    ):

        self.repository.update(parking)

    def delete_monitoring(
        self,
        parking_id: int
    ):

        self.repository.delete(parking_id)

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