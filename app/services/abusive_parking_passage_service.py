from app.models.abusive_parking_passage import AbusiveParkingPassage
from app.repositories.abusive_parking_passage_repository import (
    AbusiveParkingPassageRepository,
)


class AbusiveParkingPassageService:
    """
    Couche métier des passages de contrôle.
    """

    def __init__(self):
        self.repository = AbusiveParkingPassageRepository()

    # ==========================================================
    # CRUD
    # ==========================================================

    def add_passage(
        self,
        passage: AbusiveParkingPassage
    ):
        self.repository.add(passage)

    def update_passage(
        self,
        passage: AbusiveParkingPassage
    ):
        self.repository.update(passage)

    def delete_passage(
        self,
        passage_id: int
    ):
        self.repository.delete(passage_id)

    # ==========================================================
    # CONSULTATION
    # ==========================================================

    def get_by_id(
        self,
        passage_id: int
    ):
        return self.repository.get_by_id(passage_id)

    def get_by_parking(
        self,
        parking_id: int
    ):
        return self.repository.get_by_parking(parking_id)

    def get_last_passage(
        self,
        parking_id: int
    ):
        return self.repository.get_last_passage(parking_id)

    # ==========================================================
    # STATISTIQUES
    # ==========================================================

    def count_passages(
        self,
        parking_id: int
    ):
        return len(
            self.get_by_parking(parking_id)
        )
