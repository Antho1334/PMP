from datetime import date, datetime, time

from app.database.database import Database
from app.models.activity import Activity


class ActivityRepository:
    """
    Repository responsable de l'accès aux activités du Journal.

    Toutes les opérations SQL concernant les activités
    sont centralisées dans cette classe.
    """

    def __init__(self):
        self.database = Database()

    # ==========================================================
    # CREATE
    # ==========================================================

    def add(self, activity: Activity):
        """
        Enregistre une nouvelle activité dans la base de données.
        """

        self.database.cursor.execute(
            """
            INSERT INTO journal
            (
                activity_date,
                activity_time,
                category,
                title,
                report,
                important,
                folder_id,
                outlook_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                activity.activity_date.isoformat(),
                activity.activity_time.strftime("%H:%M"),
                activity.category,
                activity.title,
                activity.report,
                int(activity.important),
                activity.folder_id,
                activity.outlook_id,
            ),
        )

        self.database.connection.commit()

        # Récupération de l'identifiant créé par SQLite
        activity.id = self.database.cursor.lastrowid

        return activity

    # ==========================================================
    # READ
    # ==========================================================

    def get_all(self):
        """
        Retourne toutes les activités sous forme d'objets Activity.
        """

        self.database.cursor.execute(
            """
            SELECT
                id,
                activity_date,
                activity_time,
                category,
                title,
                report,
                important,
                folder_id,
                outlook_id
            FROM journal
            ORDER BY activity_date DESC, activity_time ASC
            """
        )

        rows = self.database.cursor.fetchall()

        activities = []

        for row in rows:

            activity = Activity(
                activity_date=self._parse_date(
                    row["activity_date"]
                ),
                activity_time=self._parse_time(
                    row["activity_time"]
                ),
                category=row["category"],
                title=row["title"],
                report=row["report"] or "",
                important=bool(row["important"]),
                folder_id=row["folder_id"],
                outlook_id=row["outlook_id"],
                id=row["id"],
            )

            activities.append(activity)

        return activities
        # ==========================================================
        # SEARCH
        # ==========================================================

    def search(self, keyword: str):
        """
        Recherche des activités par mot-clé.

        La recherche porte sur :
        - la catégorie ;
        - l'objet ;
        - le compte-rendu.

        La recherche n'est pas sensible à la casse.
        """

        keyword = keyword.strip()

        if not keyword:
            return self.get_all()

        search_value = f"%{keyword}%"

        self.database.cursor.execute(
            """
            SELECT
                id,
                activity_date,
                activity_time,
                category,
                title,
                report,
                important,
                folder_id,
                outlook_id
            FROM journal

            WHERE category LIKE ? COLLATE NOCASE
               OR title LIKE ? COLLATE NOCASE
               OR report LIKE ? COLLATE NOCASE

            ORDER BY activity_date DESC, activity_time ASC
            """,
            (
                search_value,
                search_value,
                search_value,
            ),
        )

        rows = self.database.cursor.fetchall()

        activities = []

        for row in rows:

            activity = Activity(
                activity_date=self._parse_date(
                    row["activity_date"]
                ),
                activity_time=self._parse_time(
                    row["activity_time"]
                ),
                category=row["category"],
                title=row["title"],
                report=row["report"] or "",
                important=bool(row["important"]),
                folder_id=row["folder_id"],
                outlook_id=row["outlook_id"],
                id=row["id"],
            )

            activities.append(activity)

        return activities
        # ==========================================================
        # SEARCH BY DATE
        # ==========================================================

    def search_by_date(self, activity_date: date):
        """
        Recherche toutes les activités enregistrées
        pour une date précise.
        """

        self.database.cursor.execute(
            """
            SELECT
                id,
                activity_date,
                activity_time,
                category,
                title,
                report,
                important,
                folder_id,
                outlook_id
            FROM journal

            WHERE activity_date = ?

            ORDER BY activity_time ASC
            """,
            (
                activity_date.isoformat(),
            ),
        )

        rows = self.database.cursor.fetchall()

        activities = []

        for row in rows:

            activity = Activity(
                activity_date=self._parse_date(
                    row["activity_date"]
                ),
                activity_time=self._parse_time(
                    row["activity_time"]
                ),
                category=row["category"],
                title=row["title"],
                report=row["report"] or "",
                important=bool(row["important"]),
                folder_id=row["folder_id"],
                outlook_id=row["outlook_id"],
                id=row["id"],
            )

            activities.append(activity)

        return activities

    # ==========================================================
    # UPDATE
    # ==========================================================

    def update(self, activity: Activity):
        """
        Met à jour une activité existante.

        L'activité doit obligatoirement posséder un ID SQLite.
        """

        if activity.id is None:
            raise ValueError(
                "Impossible de modifier une activité sans identifiant."
            )

        self.database.cursor.execute(
            """
            UPDATE journal

            SET
                activity_date = ?,
                activity_time = ?,
                category = ?,
                title = ?,
                report = ?,
                important = ?,
                folder_id = ?,
                outlook_id = ?,
                updated_at = CURRENT_TIMESTAMP

            WHERE id = ?
            """,
            (
                activity.activity_date.isoformat(),
                activity.activity_time.strftime("%H:%M"),
                activity.category,
                activity.title,
                activity.report,
                int(activity.important),
                activity.folder_id,
                activity.outlook_id,
                activity.id,
            ),
        )

        self.database.connection.commit()
            # ==========================================================
            # DELETE
            # ==========================================================

    def delete(self, activity_id: int):
        """
        Supprime une activité précise à partir de son ID SQLite.
        """

        if activity_id is None:
            raise ValueError(
                "Impossible de supprimer une activité sans identifiant."
            )

        self.database.cursor.execute(
            """
            DELETE FROM journal
            WHERE id = ?
            """,
            (activity_id,),
        )

        self.database.connection.commit()

    # ==========================================================
    # DELETE ALL
    # ==========================================================

    def delete_all(self):
        """
        Supprime toutes les activités du Journal.

        Conservé pour compatibilité.
        """

        self.database.cursor.execute(
            """
            DELETE FROM journal
            """
        )

        self.database.connection.commit()

    # ==========================================================
    # CONVERSION DATE
    # ==========================================================

    @staticmethod
    def _parse_date(value):
        """
        Convertit une date SQLite en objet date Python.
        """

        if not value:
            return date.today()

        try:
            return date.fromisoformat(value)

        except (ValueError, TypeError):
            return date.today()

    # ==========================================================
    # CONVERSION HEURE
    # ==========================================================

    @staticmethod
    def _parse_time(value):
        """
        Convertit une heure SQLite en objet time Python.
        """

        if not value:
            return time(0, 0)

        try:
            return datetime.strptime(
                value,
                "%H:%M"
            ).time()

        except (ValueError, TypeError):
            return time(0, 0)