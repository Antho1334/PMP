"""Catalogue déclaratif des ressources officielles PMP."""

from app.resources.application_resources import ApplicationResource
from app.resources.banners import Banner
from app.resources.fonts import Font
from app.resources.icons import Icon
from app.resources.images import Image
from app.resources.logos import Logo
from app.resources.templates import Template
from app.resources.watermarks import Watermark


LOGO_CATALOG: dict[Logo, str] = {
    Logo.FRENCH_REPUBLIC: "assets/logos/common/french_republic.png",
    Logo.MUNICIPAL_POLICE: "assets/logos/common/municipal_police.png",
    Logo.MUNICIPALITY: "assets/logos/municipalities/default/logo.png",
    Logo.PMP: "images/night_watchers.png",
}

ICON_CATALOG: dict[Icon, str] = {
    Icon.PATROL: "assets/icons/operations/patrol.svg",
    Icon.PARKING: "assets/icons/domains/parking.svg",
    Icon.TRAFFIC: "assets/icons/domains/traffic.svg",
    Icon.URBAN_PLANNING: "assets/icons/domains/urban_planning.svg",
    Icon.INTERVENTION: "assets/icons/operations/intervention.svg",
    Icon.IMPOUND: "assets/icons/operations/impound.svg",
    Icon.ADMINISTRATIVE_POLICE: "assets/icons/domains/administrative_police.svg",
    Icon.JUDICIAL_POLICE: "assets/icons/domains/judicial_police.svg",
    Icon.WARNING: "assets/icons/statuses/warning.svg",
    Icon.IMPORTANT: "assets/icons/statuses/important.svg",
    Icon.INFORMATION: "assets/icons/statuses/information.svg",
}

IMAGE_CATALOG: dict[Image, str] = {
    Image.MUNICIPAL_POLICE_PATCH: "images/pm_montady_patch.png",
}

BANNER_CATALOG: dict[Banner, str] = {
    Banner.PMP: "images/cartouche_pmp.png",
}

WATERMARK_CATALOG: dict[Watermark, str] = {
    Watermark.PMP: "assets/watermarks/pmp.png",
}

TEMPLATE_CATALOG: dict[Template, str] = {
    Template.DAILY_REPORT_WORD: "assets/templates/word/daily_report.docx",
}

FONT_CATALOG: dict[Font, str] = {
    Font.DEFAULT: "assets/fonts/default.ttf",
}

APPLICATION_RESOURCE_CATALOG: dict[ApplicationResource, str] = {
    ApplicationResource.OPERATIONAL_MAP_PAGE: "map/operational_map.html",
}
