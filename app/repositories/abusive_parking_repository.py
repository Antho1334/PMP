from dataclasses import dataclass
from datetime import datetime, date, time
from pathlib import Path
from typing import List, Optional

from app.database.database import Database
from app.models.abusive_parking import AbusiveParking


class AbusiveParkingNotFoundError(LookupError):
    """La surveillance ciblée n'existe plus dans SQLite."""


@dataclass(frozen=True)
class AbusiveParkingDeletionResult:
    deleted_files: tuple = ()
    preserved_files: tuple = ()
    failed_files: tuple = ()

    @property
    def has_file_warnings(self):
        return bool(self.failed_files)


class AbusiveParkingRepository:
    """
    Accès à la table abusive_parking.
    """

    def __init__(self, db=None):

        self.db = db or Database()

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
        """Supprime atomiquement la fiche et ses passages, puis ses photos sûres."""
        connection = self.db.connection
        cursor = self.db.cursor
        if cursor.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
            raise RuntimeError(
                "Les clés étrangères SQLite ne sont pas activées."
            )

        try:
            connection.execute("BEGIN")
            parking_row = cursor.execute(
                """
                SELECT photo_path
                FROM abusive_parking
                WHERE id=?
                """,
                (parking_id,),
            ).fetchone()
            if parking_row is None:
                raise AbusiveParkingNotFoundError(
                    "Cette surveillance n'existe plus ou a déjà été supprimée."
                )

            passage_rows = cursor.execute(
                """
                SELECT photo_path
                FROM abusive_parking_passages
                WHERE parking_id=?
                """,
                (parking_id,),
            ).fetchall()
            candidate_paths = [
                parking_row["photo_path"],
                *(row["photo_path"] for row in passage_rows),
            ]

            cursor.execute(
                "DELETE FROM abusive_parking WHERE id=?",
                (parking_id,),
            )
            if cursor.rowcount != 1:
                raise AbusiveParkingNotFoundError(
                    "Cette surveillance n'existe plus ou a déjà été supprimée."
                )
            connection.commit()
        except Exception:
            connection.rollback()
            raise

        try:
            return self._delete_unreferenced_photo_files(candidate_paths)
        except Exception as error:
            return AbusiveParkingDeletionResult(
                failed_files=(("Nettoyage des photos", str(error)),)
            )

    def _delete_unreferenced_photo_files(self, candidate_paths):
        """Efface uniquement les fichiers PMP valides devenus non référencés."""
        remaining_rows = self.db.cursor.execute(
            """
            SELECT photo_path
            FROM abusive_parking
            WHERE photo_path IS NOT NULL AND TRIM(photo_path)<>''
            UNION ALL
            SELECT photo_path
            FROM abusive_parking_passages
            WHERE photo_path IS NOT NULL AND TRIM(photo_path)<>''
            """
        ).fetchall()
        remaining_paths = {
            self._normalized_path(row["photo_path"])
            for row in remaining_rows
            if self._normalized_path(row["photo_path"]) is not None
        }

        deleted = []
        preserved = []
        failed = []
        handled = set()
        for raw_path in candidate_paths:
            path = self._normalized_path(raw_path)
            if path is None:
                if raw_path and str(raw_path).strip():
                    preserved.append(str(raw_path))
                continue
            if path in handled:
                continue
            handled.add(path)
            if (
                not self._is_managed_photo_path(path)
                or path in remaining_paths
                or not path.exists()
            ):
                preserved.append(str(path))
                continue
            try:
                path.unlink()
            except OSError as error:
                failed.append((str(path), str(error)))
            else:
                deleted.append(str(path))

        return AbusiveParkingDeletionResult(
            deleted_files=tuple(deleted),
            preserved_files=tuple(preserved),
            failed_files=tuple(failed),
        )

    @staticmethod
    def _normalized_path(raw_path):
        if not raw_path or not str(raw_path).strip():
            return None
        try:
            return Path(str(raw_path)).expanduser().resolve(strict=False)
        except (OSError, RuntimeError, ValueError):
            return None

    @staticmethod
    def _is_managed_photo_path(path):
        project_root = Path(__file__).resolve().parents[2]
        allowed_directories = (
            (
                project_root
                / "data"
                / "abusive_parking"
                / "photos"
            ).resolve(),
            (
                project_root
                / "data"
                / "abusive_parking"
                / "passages"
            ).resolve(),
        )
        for directory in allowed_directories:
            try:
                path.relative_to(directory)
            except ValueError:
                continue
            return True
        return False
