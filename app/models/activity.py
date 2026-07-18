from dataclasses import dataclass
from datetime import date, time
from typing import Optional


@dataclass
class Activity:
    """
    Représente une activité du Journal PMP.
    """

    activity_date: date

    activity_time: time

    category: str

    title: str

    report: str

    important: bool = False

    folder_id: Optional[int] = None

    outlook_id: Optional[str] = None

    # Identifiant unique SQLite.
    # None lors de la création d'une nouvelle activité.
    # Renseigné automatiquement lors de la lecture depuis la base.
    id: Optional[int] = None