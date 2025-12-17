
from .geocoder_strategy import Geocoder
from .geocode_cache import GeocodeCache
from models.problem_state import ProblemState, save_geocoded_csv, save_geocoded_errors_csv
from models.site import Site

class GeocodeService:
    def __init__(self, geocoder: Geocoder, cache_path: str = None):
        self._geocoder = geocoder
        self._cache = GeocodeCache(cache_path)

    @property
    def geocoder_name(self) -> str:
        return self._geocoder.name

    def geocode_problem(self, problem: ProblemState, log_callback=None) -> None:
        """
        Load addresses, geocode them, persist results.
        Mutates ProblemState *via* its persistence methods.
        Uses cache to avoid redundant geocoding requests.
        
        Args:
            problem: ProblemState to geocode
            log_callback: Optional callback function for logging messages
        """
        def log(msg: str):
            """Helper to log messages"""
            if log_callback:
                log_callback(msg)

        sites = problem.sites

        if not sites:
            raise RuntimeError("No sites to geocode")

        # Check cache for each site first
        sites_to_geocode = []
        cache_hits = 0
        
        for site in sites:
            # Skip if already geocoded
            if site.lat is not None and site.lng is not None:
                continue
            
            # Check cache
            cached_result = self._cache.get(site.address, site.state_code)
            
            if cached_result:
                # Cache hit - use cached coordinates
                site.lat = cached_result['lat']
                site.lng = cached_result['lng']
                site.display_name = cached_result.get('display_name', site.address)
                cache_hits += 1
                log(f"Cache hit for {site.id}: ({site.lat}, {site.lng})")
            else:
                # Cache miss - need to geocode
                sites_to_geocode.append(site)
        
        if cache_hits > 0:
            log(f"Found {cache_hits} cached result(s)")
        
        # Geocode remaining sites
        if sites_to_geocode:
            log(f"Geocoding {len(sites_to_geocode)} site(s) via {self.geocoder_name}")
            geocoded_sites = self._geocoder.geocode(sites_to_geocode, log_callback=log_callback)
            
            # Store results in cache
            for site in geocoded_sites:
                self._cache.set(
                    site.address,
                    site.state_code,
                    site.lat,
                    site.lng,
                    getattr(site, 'display_name', None)
                )

        problem.sites = sites
        
        # Persist geocoded results to CSV
        if problem.paths:
            # Save successfully geocoded sites
            save_geocoded_csv(problem.paths.geocoded_csv(), problem.sites)
            log(f"Saved geocoded results to {problem.paths.geocoded_csv()}")
            
            # Save failed geocoding attempts to error file
            error_csv_path = problem.paths.geocoded_csv().parent / "geocoded-errors.csv"
            save_geocoded_errors_csv(error_csv_path, problem.sites)
            
            # Count failures for logging
            failed_count = sum(1 for site in problem.sites if site.lat is None or site.lng is None)
            if failed_count > 0:
                log(f"Saved {failed_count} failed geocoding attempts to {error_csv_path}")

