from enum import Enum, auto

class PlanningStage(Enum):
    ADDRESSES = auto()
    GEOCODED = auto()
    CLUSTERED = auto()
    SOLVED = auto()
