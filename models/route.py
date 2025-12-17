
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Route:
    state_code: str
    cluster_id: int
    vehicle_id: int
    stops: int
    sequence: list[str]
    mode: str
    speed_mph: float
    service_hours: float
    solved_at: datetime
