from datetime import datetime, date, time
from typing import List, Optional

from app.database.database import Database
from app.models.abusive_parking import AbusiveParking


class AbusiveParkingRepository:
    """
    Accès à la table abusive_parking.
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

        return datetime.strptime(
            value,
            "%Y-%m-%d"
        ).date()

    def _str_to_time(self, value):

        if not value:
            return None

        return datetime.strptime(
            value,
            "%H:%M"
        ).time()

    def _row_to_object(self, row):

        if row is None:
            return None

        return AbusiveParking(

            id=row["id"],

            registration=row["registration"],

            brand=row["brand"],

            model=row["model"],

            vehicle_type=row["vehicle_type"],

            color=row["color"],

            owner=row["owner"],

            location=row["location"],

            latitude=row["latitude"],

            longitude=row["longitude"],

            monitoring_date=self._str_to_date(
                row["monitoring_date"]
            ),

            monitoring_time=self._str_to_time(
                row["monitoring_time"]
            ),

            monitoring_delay_days=row["monitoring_delay_days"],

            photo_path=row["photo_path"],

            observations=row["observations"],

            status=row["status"],

            closure_date=self._str_to_date(
                row["closure_date"]
            ),

            closure_time=self._str_to_time(
                row["closure_time"]
            ),

            closure_reason=row["closure_reason"]
        )

    # ==========================================================
    # CREATE
    # ==========================================================

    def add(self, parking: AbusiveParking):

        self.db.cursor.execute(
            """
            INSERT INTO abusive_parking
            (
                registration,
                brand,
                model,
                vehicle_type,
                color,
                owner,
                location,
                latitude,
                longitude,
                monitoring_date,
                monitoring_time,
                monitoring_delay_days,
                photo_path,
                observations,
                status,
                closure_date,
                closure_time,
                closure_reason
            )

            VALUES
            (
                ?,?,?,?,?,?,?,?,?,?,
                ?,?,?,?,?,?,?,?
            )
            """,

            (

                parking.registration,

                parking.brand,

                parking.model,

                parking.vehicle_type,

                parking.color,

                parking.owner,

                parking.location,

                parking.latitude,

                parking.longitude,

                self._date_to_str(
                    parking.monitoring_date
                ),

                self._time_to_str(
                    parking.monitoring_time
                ),

                parking.monitoring_delay_days,

                parking.photo_path,

                parking.observations,

                parking.status,

                self._date_to_str(
                    parking.closure_date
                ),

                self._time_to_str(
                    parking.closure_time
                ),

                parking.closure_reason

            )
        )

        self.db.connection.commit()

    # ==========================================================
    # READ
    # ==========================================================

    def get_all(self) -> List[AbusiveParking]:

        self.db.cursor.execute(
            """
            SELECT *
            FROM abusive_parking
            ORDER BY monitoring_date DESC,
                     monitoring_time DESC
            """
        )

        rows = self.db.cursor.fetchall()

        return [
            self._row_to_object(row)
            for row in rows
        ]

    def get_active(self):

        self.db.cursor.execute(
            """
            SELECT *
            FROM abusive_parking

            WHERE status='active'

            ORDER BY monitoring_date ASC
            """
        )

        rows = self.db.cursor.fetchall()

        return [
            self._row_to_object(row)
            for row in rows
        ]

    def get_history(self):

        self.db.cursor.execute(
            """
            SELECT *

            FROM abusive_parking

            WHERE status<>'active'

            ORDER BY closure_date DESC
            """
        )

        rows = self.db.cursor.fetchall()

        return [
            self._row_to_object(row)
            for row in rows
        ]

    def get_by_id(
        self,
        parking_id: int
    ) -> Optional[AbusiveParking]:

        self.db.cursor.execute(
            """
            SELECT *

            FROM abusive_parking

            WHERE id=?
            """,

            (parking_id,)
        )

        return self._row_to_object(
            self.db.cursor.fetchone()
        )

    def get_by_registration(
        self,
        registration: str
    ):

        self.db.cursor.execute(
            """
            SELECT *

            FROM abusive_parking

            WHERE registration=?

            ORDER BY monitoring_date DESC

            LIMIT 1
            """,

            (registration,)
        )

        return self._row_to_object(
            self.db.cursor.fetchone()
        )

    # ==========================================================
    # UPDATE
    # ==========================================================

    def update(
        self,
        parking: AbusiveParking
    ):

        self.db.cursor.execute(
            """
            UPDATE abusive_parking

            SET

                registration=?,

                brand=?,

                model=?,

                vehicle_type=?,

                color=?,

                owner=?,

                location=?,

                latitude=?,

                longitude=?,

                monitoring_date=?,

                monitoring_time=?,

                monitoring_delay_days=?,

                photo_path=?,

                observations=?,

                status=?,

                closure_date=?,

                closure_time=?,

                closure_reason=?,

                updated_at=CURRENT_TIMESTAMP

            WHERE id=?
            """,

            (

                parking.registration,

                parking.brand,

                parking.model,

                parking.vehicle_type,

                parking.color,

                parking.owner,

                parking.location,

                parking.latitude,

                parking.longitude,

                self._date_to_str(
                    parking.monitoring_date
                ),

                self._time_to_str(
                    parking.monitoring_time
                ),

                parking.monitoring_delay_days,

                parking.photo_path,

                parking.observations,

                parking.status,

                self._date_to_str(
                    parking.closure_date
                ),

                self._time_to_str(
                    parking.closure_time
                ),

                parking.closure_reason,

                parking.id

            )
        )

        self.db.connection.commit()

    # ==========================================================
    # CLÔTURE
    # ==========================================================

    def close_monitoring(
        self,
        parking_id: int,
        reason: str
    ):

        today = date.today()

        now = datetime.now().strftime(
            "%H:%M"
        )

        self.db.cursor.execute(
            """
            UPDATE abusive_parking

            SET

                status=?,

                closure_date=?,

                closure_time=?,

                closure_reason=?,

                updated_at=CURRENT_TIMESTAMP

            WHERE id=?
            """,

            (

                reason,

                today.isoformat(),

                now,

                reason,

                parking_id

            )
        )

        self.db.connection.commit()

    # ==========================================================
    # DELETE
    # ==========================================================

    def delete(
        self,
        parking_id: int
    ):

        self.db.cursor.execute(
            """
            DELETE FROM abusive_parking

            WHERE id=?
            """,

            (parking_id,)
        )

        self.db.connection.commit()