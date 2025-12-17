
from dataclasses import dataclass


@dataclass
class Site:
    id: str
    address: str
    state_code: str
    lat: float | None = None
    lng: float | None = None
    display_name: str | None = None
    cluster_id: int | None = None