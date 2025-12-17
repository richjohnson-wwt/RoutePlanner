
from .geocoder_strategy import Geocoder
from models.site import Site
import requests
import time
from typing import Optional


class NominatimGeocoder(Geocoder):
    name = "nominatim"
    
    def __init__(self, email: str = "user@example.com"):
        """
        Initialize Nominatim geocoder.
        
        Args:
            email: Contact email for Nominatim usage policy compliance
        """
        self.email = email
        self.base_url = "https://nominatim.openstreetmap.org/search"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': f'RoutePlanner/1.0 ({self.email})'
        })
        # Nominatim requires max 1 request per second
        self.request_delay = 1.0

    def geocode(self, sites: list[Site], log_callback=None) -> list[Site]:
        """
        Geocode a list of sites using Nominatim API.
        
        Args:
            sites: List of Site objects to geocode
            log_callback: Optional callback function for logging messages
            
        Returns:
            List of Site objects with lat/lng populated
        """
        def log(msg: str):
            """Helper to log messages"""
            if log_callback:
                log_callback(msg)
            else:
                print(msg)
        
        for i, site in enumerate(sites):
            # Skip if already geocoded
            if site.lat is not None and site.lng is not None:
                log(f"Skipping {site.id} (already geocoded)")
                continue
            
            # Build search query with address and state
            query = f"{site.address}, {site.state_code}, USA"
            log(f"Geocoding {site.id}: {query}")
            
            try:
                result = self._geocode_address(query)
                
                if result:
                    site.lat = result['lat']
                    site.lng = result['lng']
                    site.display_name = result.get('display_name', site.address)
                    log(f"  ✓ Success: ({site.lat}, {site.lng})")
                else:
                    # Geocoding failed, keep as None
                    site.lat = None
                    site.lng = None
                    log(f"  ✗ Not found")
                    
            except Exception as e:
                # Log error but continue with other sites
                log(f"  ✗ Error: {e}")
                site.lat = None
                site.lng = None
            
            # Respect rate limit (1 request per second)
            if i < len(sites) - 1:  # Don't sleep after last request
                time.sleep(self.request_delay)
        
        return sites

    def _geocode_address(self, query: str) -> Optional[dict]:
        """
        Geocode a single address using Nominatim API.
        
        Args:
            query: Address string to geocode
            
        Returns:
            Dictionary with 'lat', 'lng', and 'display_name' or None if not found
        """
        params = {
            'q': query,
            'format': 'json',
            'limit': 1,
            'addressdetails': 1
        }
        
        try:
            response = self.session.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            results = response.json()
            
            if results and len(results) > 0:
                result = results[0]
                return {
                    'lat': float(result['lat']),
                    'lng': float(result['lon']),
                    'display_name': result.get('display_name', '')
                }
            
            return None
            
        except requests.RequestException as e:
            print(f"Request error for query '{query}': {e}")
            return None
        except (KeyError, ValueError, IndexError) as e:
            print(f"Parse error for query '{query}': {e}")
            return None
