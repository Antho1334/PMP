from dataclasses import dataclass
from datetime import date, time
from typing import Optional


@dataclass
class Action:
    """
    Représente une action à réaliser dans PMP.
    """

    # Date prévue pour l'action
    action_date: date

    # Heure prévue
    action_time: time

    # Objet de l'action
    title: str

    # Description ou consignes
    description: str = ""

    # Action importante / prioritaire
    important: bool = False

    # Action terminée
    completed: bool = False

    # Demande de rappel Outlook
    outlook_reminder: bool = False

    # Identifiant SQLite
    id: Optional[int] = None

    # Identifiant Outlook
    outlook_id: Optional[str] = None