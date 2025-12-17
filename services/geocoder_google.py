from .geocoder_strategy import Geocoder
from models.site import Site


class GoogleGeocoder(Geocoder):
    name = "google"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def geocode(self, sites: list[Site]) -> list[Site]:
        for site in sites:
            site.lat = ...
            site.lng = ...
        return sites
