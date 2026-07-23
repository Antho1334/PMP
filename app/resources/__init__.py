"""API publique de la bibliothèque de ressources PMP."""

from app.resources.application_resources import ApplicationResource
from app.resources.banners import Banner
from app.resources.errors import ResourceNotFoundError
from app.resources.fonts import Font
from app.resources.icons import Icon
from app.resources.logos import Logo
from app.resources.resource_manager import ResourceManager
from app.resources.templates import Template
from app.resources.watermarks import Watermark

__all__ = [
    "ApplicationResource",
    "Banner",
    "Font",
    "Icon",
    "Logo",
    "ResourceManager",
    "ResourceNotFoundError",
    "Template",
    "Watermark",
]
