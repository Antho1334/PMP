from datetime import date, datetime, time

from app.database.database import Database
from app.models.action import Action


class ActionRepository:
    """
    Repository responsable de l'accès aux actions PMP.

    Toutes les opérations SQL concernant les actions
    sont centralisées dans cette classe.
    """

    def __init__(self):
        self.database = Database()

    # ==========================================================
    # CREATE
    # ==========================================================

    def add(self, action: Action):
        """
        Enregistre une nouvelle action dans la base de données.
        """

        self.database.cursor.execute(
            """
            INSERT INTO actions
            (
                action_date,
                action_time,
                title,
                description,
                important,
                completed,
                outlook_reminder,
                outlook_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                action.action_date.isoformat(),
                action.action_time.strftime("%H:%M"),
                action.title,
                action.description,
                int(action.important),
                int(action.completed),
                int(action.outlook_reminder),
                action.outlook_id,
            ),
        )

        self.database.connection.commit()

        # Récupération de l'identifiant SQLite
        action.id = self.database.cursor.lastrowid

        return action

    # ==========================================================
    # READ
    # ==========================================================

    def get_all(self):
        """
        Retourne toutes les actions enregistrées.
        """

        self.database.cursor.execute(
            """
            SELECT
                id,
                action_date,
                action_time,
                title,
                description,
                important,
                completed,
                outlook_reminder,
                outlook_id
            FROM actions

            ORDER BY action_date ASC, action_time ASC
            """
        )

        rows = self.database.cursor.fetchall()

        actions = []

        for row in rows:

            action = self._row_to_action(
                row
            )

            actions.append(
                action
            )

        return actions

    # ==========================================================
    # READ - ACTIONS EN COURS
    # ==========================================================

    def get_pending(self):
        """
        Retourne uniquement les actions non terminées.
        """

        self.database.cursor.execute(
            """
            SELECT
                id,
                action_date,
                action_time,
                title,
                description,
                important,
                completed,
                outlook_reminder,
                outlook_id
            FROM actions

            WHERE completed = 0

            ORDER BY action_date ASC, action_time ASC
            """
        )

        rows = self.database.cursor.fetchall()

        return [
            self._row_to_action(row)
            for row in rows
        ]

    # ==========================================================
    # READ - ACTIONS IMPORTANTES À VENIR
    # ==========================================================

    def get_upcoming_important(self):
        """
        Retourne les actions importantes non terminées
        dont la date est aujourd'hui ou à venir.

        Cette méthode servira notamment au bloc
        "À surveiller" de la page d'accueil.
        """

        today = date.today().isoformat()

        self.database.cursor.execute(
            """
            SELECT
                id,
                action_date,
                action_time,
                title,
                description,
                important,
                completed,
                outlook_reminder,
                outlook_id
            FROM actions

            WHERE important = 1
              AND completed = 0
              AND action_date >= ?

            ORDER BY action_date ASC, action_time ASC
            """,
            (
                today,
            ),
        )

        rows = self.database.cursor.fetchall()

        return [
            self._row_to_action(row)
            for row in rows
        ]

    # ==========================================================
    # UPDATE
    # ==========================================================

    def update(self, action: Action):
        """
        Modifie une action existante.
        """

        if action.id is None:

            raise ValueError(
                "Impossible de modifier une action sans identifiant."
            )

        self.database.cursor.execute(
            """
            UPDATE actions

            SET
                action_date = ?,
                action_time = ?,
                title = ?,
                description = ?,
                important = ?,
                completed = ?,
                outlook_reminder = ?,
                outlook_id = ?,
                updated_at = CURRENT_TIMESTAMP

            WHERE id = ?
            """,
            (
                action.action_date.isoformat(),
                action.action_time.strftime("%H:%M"),
                action.title,
                action.description,
                int(action.important),
                int(action.completed),
                int(action.outlook_reminder),
                action.outlook_id,
                action.id,
            ),
        )

        self.database.connection.commit()

    # ==========================================================
    # DELETE
    # ==========================================================

    def delete(self, action_id: int):
        """
        Supprime une action à partir de son identifiant SQLite.
        """

        if action_id is None:

            raise ValueError(
                "Impossible de supprimer une action sans identifiant."
            )

        self.database.cursor.execute(
            """
            DELETE FROM actions
            WHERE id = ?
            """,
            (
                action_id,
            ),
        )

        self.database.connection.commit()

    # ==========================================================
    # CONVERSION SQLITE -> ACTION
    # ==========================================================

    def _row_to_action(
        self,
        row,
    ):
        """
        Transforme une ligne SQLite en objet Action.
        """

        return Action(
            action_date=self._parse_date(
                row["action_date"]
            ),
            action_time=self._parse_time(
                row["action_time"]
            ),
            title=row["title"],
            description=(
                row["description"]
                or ""
            ),
            important=bool(
                row["important"]
            ),
            completed=bool(
                row["completed"]
            ),
            outlook_reminder=bool(
                row["outlook_reminder"]
            ),
            outlook_id=row["outlook_id"],
            id=row["id"],
        )

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

            return date.fromisoformat(
                value
            )

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

            return time(
                0,
                0
            )

        try:

            return datetime.strptime(
                value,
                "%H:%M"
            ).time()

        except (ValueError, TypeError):

            return time(
                0,
                0
            )