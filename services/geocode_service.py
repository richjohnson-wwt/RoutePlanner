
from .geocoder_strategy import Geocoder
from models.problem_state import ProblemState

class GeocodeService:
    def __init__(self, geocoder: Geocoder):
        self._geocoder = geocoder

    @property
    def geocoder_name(self) -> str:
        return self._geocoder.name

    def geocode_problem(self, problem: ProblemState) -> None:
        """
        Load addresses, geocode them, persist results.
        Mutates ProblemState *via* its persistence methods.
        """

        sites = problem.load_addresses()

        if not sites:
            raise RuntimeError("No sites to geocode")

        geocoded_sites = self._geocoder.geocode(sites)

        problem.save_geocoded(geocoded_sites)

        problem.metadata["geocoder"] = self._geocoder.name

