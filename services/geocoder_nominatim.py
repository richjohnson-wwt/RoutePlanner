
from .geocoder_strategy import Geocoder
from models.site import Site

class NominatimGeocoder(Geocoder):
    name = "nominatim"

    def geocode(self, sites: list[Site]) -> list[Site]:
        for site in sites:
            site.lat = ...
            site.lng = ...
        return sites
