import sqlite3
from pathlib import Path


class Database:
    """
    Gestion de la connexion à la base de données SQLite de PMP.
    """

    def __init__(self):

        # ======================================================
        # CHEMIN DE LA BASE DE DONNÉES
        # ======================================================

        database_directory = (
            Path(__file__).resolve().parents[2]
            / "database"
        )

        database_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.database_path = (
            database_directory
            / "pmp.db"
        )

        # ======================================================
        # CONNEXION SQLITE
        # ======================================================

        self.connection = sqlite3.connect(
            str(self.database_path)
        )

        self.connection.row_factory = sqlite3.Row

        self.cursor = self.connection.cursor()

        # Activation des clés étrangères
        self.cursor.execute(
            "PRAGMA foreign_keys = ON"
        )

        self.create_tables()

    # ==========================================================
    # CRÉATION DES TABLES
    # ==========================================================

    def create_tables(self):

        # ------------------------------------------------------
        # TABLE JOURNAL
        # ------------------------------------------------------

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS journal
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                activity_date TEXT NOT NULL,

                activity_time TEXT NOT NULL,

                category TEXT NOT NULL,

                title TEXT NOT NULL,

                report TEXT,

                important INTEGER NOT NULL DEFAULT 0,

                folder_id INTEGER,

                outlook_id TEXT,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # ------------------------------------------------------
        # TABLE ACTIONS
        # ------------------------------------------------------

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS actions
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                action_date TEXT NOT NULL,

                action_time TEXT NOT NULL,

                title TEXT NOT NULL,

                description TEXT,

                important INTEGER NOT NULL DEFAULT 0,

                completed INTEGER NOT NULL DEFAULT 0,

                outlook_reminder INTEGER NOT NULL DEFAULT 0,

                outlook_id TEXT,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # ------------------------------------------------------
        # TABLE STATIONNEMENT ABUSIF
        # ------------------------------------------------------

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS abusive_parking
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                registration TEXT NOT NULL,

                brand TEXT,

                model TEXT,

                vehicle_type TEXT,

                color TEXT,

                owner TEXT,

                location TEXT,

                latitude REAL,

                longitude REAL,

                monitoring_date TEXT,

                monitoring_time TEXT,

                monitoring_delay_days INTEGER DEFAULT 7,

                photo_path TEXT,

                observations TEXT,

                status TEXT DEFAULT 'active',

                closure_date TEXT,

                closure_time TEXT,

                closure_reason TEXT,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # ------------------------------------------------------
        # TABLE DES PASSAGES
        # ------------------------------------------------------

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS abusive_parking_passages
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                parking_id INTEGER NOT NULL,

                passage_date TEXT NOT NULL,

                passage_time TEXT NOT NULL,

                latitude REAL,

                longitude REAL,

                photo_path TEXT,

                observations TEXT,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (parking_id)
                    REFERENCES abusive_parking(id)
                    ON DELETE CASCADE
            )
            """
        )

        # ------------------------------------------------------
        # INDEX STATIONNEMENT
        # ------------------------------------------------------

        self.cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_abusive_parking_registration
            ON abusive_parking(registration)
            """
        )

        self.cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_abusive_parking_status
            ON abusive_parking(status)
            """
        )

        # ------------------------------------------------------
        # INDEX PASSAGES
        # ------------------------------------------------------

        self.cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_passages_parking
            ON abusive_parking_passages(parking_id)
            """
        )

        self.cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_passages_date
            ON abusive_parking_passages(passage_date)
            """
        )

        self.connection.commit()
        # ==========================================================
        # MIGRATION DE LA BASE
        # ==========================================================

def add_column_if_missing(
    self,
    table_name,
    column_name,
    definition
):

    self.cursor.execute(
        f"PRAGMA table_info({table_name})"
    )

    columns = [
        row["name"]
        for row in self.cursor.fetchall()
    ]

    if column_name not in columns:

        self.cursor.execute(
            f"""
            ALTER TABLE {table_name}
            ADD COLUMN {column_name} {definition}
            """
        )

    # ==========================================================
    # FERMETURE DE LA CONNEXION
    # ==========================================================

    def close(self):

        if self.connection:

            self.connection.close()