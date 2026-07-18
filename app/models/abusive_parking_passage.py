from dataclasses import dataclass
from datetime import date, time
from typing import Optional


@dataclass
class AbusiveParkingPassage:
    """
    Représente un passage de contrôle effectué
    dans le cadre d'une surveillance de stationnement abusif.
    """

    id: Optional[int] = None

    # Liaison avec la surveillance
    parking_id: Optional[int] = None

    # Nature du passage
    passage_type: str = "Contrôle"

    # Date / heure
    passage_date: Optional[date] = None
    passage_time: Optional[time] = None

    # Localisation
    address: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # Photo
    photo_path: str = ""

    # Observations
    observations: str = ""

    # Agent ayant effectué le passage
    agent: str = ""

    # Conditions météo (optionnel)
    weather: str = ""

    # Date de création
    created_at: Optional[str] = None