from dataclasses import dataclass
from datetime import date, time
from typing import Optional


@dataclass
class AbusiveParking:
    """
    Représente une surveillance de stationnement abusif dans PMP.

    La fiche reste conservée dans la base après la fin
    de la surveillance afin d'assurer la traçabilité.
    """

    # ==========================================================
    # INFORMATIONS VÉHICULE
    # ==========================================================

    registration: str

    brand: str = ""

    model: str = ""

    vehicle_type: str = ""

    color: str = ""

    owner: str = ""

    # ==========================================================
    # LOCALISATION
    # ==========================================================

    location: str = ""

    latitude: Optional[float] = None

    longitude: Optional[float] = None

    # ==========================================================
    # MISE EN SURVEILLANCE
    # ==========================================================

    monitoring_date: Optional[date] = None

    monitoring_time: Optional[time] = None

    # Délai de surveillance en jours
    # Paramétrable pour éviter de figer la logique métier
    monitoring_delay_days: int = 7

    # ==========================================================
    # PHOTO
    # ==========================================================

    # Chemin vers la photo enregistrée dans PMP
    photo_path: Optional[str] = None

    # ==========================================================
    # INFORMATIONS COMPLÉMENTAIRES
    # ==========================================================

    observations: str = ""

    # ==========================================================
    # STATUT
    # ==========================================================

    # Valeurs prévues :
    # "active"
    # "vehicle_moved"
    # "impounded"
    # "closed"

    status: str = "active"

    # ==========================================================
    # CLÔTURE DE LA SURVEILLANCE
    # ==========================================================

    closure_date: Optional[date] = None

    closure_time: Optional[time] = None

    closure_reason: str = ""

    # ==========================================================
    # IDENTIFIANT SQLITE
    # ==========================================================

    id: Optional[int] = None