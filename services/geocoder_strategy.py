from abc import ABC, abstractmethod
from models.site import Site

class Geocoder(ABC):
    name: str

    @abstractmethod
    def geocode(self, sites: list[Site]) -> list[Site]:
        """Return sites with lat/lng populated or raise."""
