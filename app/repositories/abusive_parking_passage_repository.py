from datetime import datetime, date, time
from typing import List, Optional

from app.database.database import Database
from app.models.abusive_parking_passage import AbusiveParkingPassage


class AbusiveParkingPassageRepository:
    """
    Accès à la table abusive_parking_passages.
    """

    def __init__(self):
        self.db = Database()

    # ==========================================================
    # OUTILS
    # ==========================================================

    def _date_to_str(self, value):
        if value is None:
            return None
        if isinstance(value, date):
            return value.isoformat()
        return str(value)

    def _time_to_str(self, value):
        if value is None:
            return None
        if isinstance(value, time):
            return value.strftime("%H:%M")
        return str(value)

    def _str_to_date(self, value):
        if not value:
            return None
        return datetime.strptime(value, "%Y-%m-%d").date()

    def _str_to_time(self, value):
        if not value:
            return None
        return datetime.strptime(value, "%H:%M").time()

    def _row_to_object(self, row):
        if row is None:
            return None

        return AbusiveParkingPassage(
            id=row["id"],
            parking_id=row["parking_id"],
            passage_type=row["passage_type"],
            passage_date=self._str_to_date(row["passage_date"]),
            passage_time=self._str_to_time(row["passage_time"]),
            address=row["address"],
            latitude=row["latitude"],
            longitude=row["longitude"],
            photo_path=row["photo_path"],
            observations=row["observations"],
            agent=row["agent"],
            weather=row["weather"],
            created_at=row["created_at"],
        )

    # ==========================================================
    # CREATE
    # ==========================================================

    def add(self, passage: AbusiveParkingPassage):
        self.db.cursor.execute(
            """
            INSERT INTO abusive_parking_passages
            (
                parking_id,
                passage_type,
                passage_date,
                passage_time,
                address,
                latitude,
                longitude,
                photo_path,
                observations,
                agent,
                weather
            )
            VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                passage.parking_id,
                passage.passage_type,
                self._date_to_str(passage.passage_date),
                self._time_to_str(passage.passage_time),
                passage.address,
                passage.latitude,
                passage.longitude,
                passage.photo_path,
                passage.observations,
                passage.agent,
                passage.weather,
            ),
        )
        self.db.connection.commit()

    # ==========================================================
    # READ
    # ==========================================================

    def get_by_parking(self, parking_id: int) -> List[AbusiveParkingPassage]:
        self.db.cursor.execute(
            """
            SELECT *
            FROM abusive_parking_passages
            WHERE parking_id=?
            ORDER BY passage_date ASC, passage_time ASC
            """,
            (parking_id,),
        )
        return [self._row_to_object(r) for r in self.db.cursor.fetchall()]

    def get_last_passage(self, parking_id: int) -> Optional[AbusiveParkingPassage]:
        self.db.cursor.execute(
            """
            SELECT *
            FROM abusive_parking_passages
            WHERE parking_id=?
            ORDER BY passage_date DESC, passage_time DESC
            LIMIT 1
            """,
            (parking_id,),
        )
        return self._row_to_object(self.db.cursor.fetchone())

    def get_by_id(self, passage_id: int) -> Optional[AbusiveParkingPassage]:
        self.db.cursor.execute(
            "SELECT * FROM abusive_parking_passages WHERE id=?",
            (passage_id,),
        )
        return self._row_to_object(self.db.cursor.fetchone())

    # ==========================================================
    # UPDATE
    # ==========================================================

    def update(self, passage: AbusiveParkingPassage):
        self.db.cursor.execute(
            """
            UPDATE abusive_parking_passages
            SET
                passage_type=?,
                passage_date=?,
                passage_time=?,
                address=?,
                latitude=?,
                longitude=?,
                photo_path=?,
                observations=?,
                agent=?,
                weather=?
            WHERE id=?
            """,
            (
                passage.passage_type,
                self._date_to_str(passage.passage_date),
                self._time_to_str(passage.passage_time),
                passage.address,
                passage.latitude,
                passage.longitude,
                passage.photo_path,
                passage.observations,
                passage.agent,
                passage.weather,
                passage.id,
            ),
        )
        self.db.connection.commit()

    # ==========================================================
    # DELETE
    # ==========================================================

    def delete(self, passage_id: int):
        self.db.cursor.execute(
            "DELETE FROM abusive_parking_passages WHERE id=?",
            (passage_id,),
        )
        self.db.connection.commit()
