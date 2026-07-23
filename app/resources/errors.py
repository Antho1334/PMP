"""Erreurs propres à la bibliothèque de ressources."""

from enum import Enum
from pathlib import Path


class ResourceNotFoundError(LookupError):
    """Signale qu'une ressource officielle ne peut pas être résolue."""

    def __init__(
        self,
        resource: Enum,
        resolved_path: Path | None = None,
    ) -> None:
        self.resource = resource
        self.resolved_path = resolved_path
        message = f"Ressource introuvable : {resource!r}."
        if resolved_path is not None:
            message = f"{message} Chemin résolu : {resolved_path}."
        super().__init__(message)
