from dataclasses import dataclass
from typing import Optional, Union


@dataclass
class MapItem:
    """
    Objet géographique générique consommé par la cartographie
    opérationnelle. Les providers convertissent leurs données métier
    en MapItem avant publication.
    """

    id: Union[int, str, None] = None
    source: str = ""
    type: str = ""
    title: str = ""
    subtitle: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    color: str = ""
    icon: str = ""
    photo_path: str = ""
