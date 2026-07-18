from dataclasses import dataclass
from typing import Optional, Union


@dataclass
class MapItem:
    """
    Objet géographique générique consommé par la Cartographie
    Opérationnelle. Les modules métier doivent convertir leurs
    données en MapItem avant de les publier sur la carte.
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
    action_id: Union[int, str, None] = None
