"""
Integration tests for Geocode Tab functionality.
Tests the complete workflow of geocoding sites with caching.
"""
import pytest
from pathlib import Path
from models.problem_state import ProblemState, load_geocoded_csv
from models.site import Site
from services.geocode_service import GeocodeService
from services.geocode_cache import GeocodeCache


class MockGeocoder:
    """Mock geocoder for testing without making real API calls."""
    
    name = "mock_geocoder"
    
    def __init__(self, fail_on_bad_addresses=False):
        """
        Initialize mock geocoder.
        
        Args:
            fail_on_bad_addresses: If True, addresses containing "Bad" will fail to geocode
        """
        self.fail_on_bad_addresses = fail_on_bad_addresses
    
    def geocode(self, sites, log_callback=None):
        """Mock geocode that returns predictable results."""
        for site in sites:
            # Check if this address should fail
            if self.fail_on_bad_addresses and "Bad" in site.address:
                # Leave coordinates as None to simulate geocoding failure
                site.lat = None
                site.lng = None
                site.display_name = None
                if log_callback:
                    log_callback(f"Failed to geocode: {site.address}")
            else:
                # Generate mock coordinates based on site ID
                site.lat = 37.0 + hash(site.id) % 10
                site.lng = -122.0 - hash(site.id) % 10
                site.display_name = f"{site.address}, {site.state_code}, USA"
        return sites


class TestGeocodeTab:
    """Integration tests for geocode tab operations."""
    
    def test_geocode_sites_without_coordinates(self, problem_state_workspace):
        """
        Test geocoding sites that don't have coordinates.
        """
        # GIVEN: Workspace with addresses.csv containing sites without coordinates
        base_dir, state_dir = problem_state_workspace
        cache_path = state_dir / "test_cache.db"
        
        addresses_csv = state_dir / "addresses.csv"
        addresses_csv.write_text("""site_id,address1,city,state,zip
Site1,123 Main St,San Francisco,CA,94102
Site2,456 Oak Ave,New York,NY,10001""")
        
        problem = ProblemState.from_workspace(
            client="test_client",
            workspace="test_workspace",
            entity_type="site",
            state_code="CA",
            base_dir=base_dir
        )
        
        # Verify sites don't have coordinates initially
        assert problem.sites[0].lat is None
        assert problem.sites[0].lng is None
        
        # WHEN: Geocode the sites
        geocoder = MockGeocoder()
        service = GeocodeService(geocoder, cache_path=str(cache_path))
        service.geocode_problem(problem)
        
        # THEN: All sites should have coordinates
        assert problem.sites[0].lat is not None
        assert problem.sites[0].lng is not None
        assert problem.sites[1].lat is not None
        assert problem.sites[1].lng is not None

    def test_geocoded_unfound_addresses_are_written_to_error_file(self, problem_state_workspace):
        """
        Test that geocoding errors are written to error file.
        """
        # GIVEN: addresses.csv that has addresses that cannot be found
        base_dir, state_dir = problem_state_workspace
        cache_path = state_dir / "test_cache.db"

        addresses_csv = state_dir / "addresses.csv"
        addresses_csv.write_text("""site_id,address1,city,state,zip
Site1,123 Bad Street St,San Francisco,CA,94102
Site2,456 Good Street St,New York,NY,10001""")
        
        problem = ProblemState.from_workspace(
            client="test_client",
            workspace="test_workspace",
            entity_type="site",
            state_code="CA",
            base_dir=base_dir
        )
        
        # Verify initial state - no coordinates
        assert problem.sites[0].lat is None
        assert problem.sites[1].lat is None
        
        # WHEN: Geocode the sites with a geocoder that fails on "Bad" addresses
        geocoder = MockGeocoder(fail_on_bad_addresses=True)
        service = GeocodeService(geocoder, cache_path=str(cache_path))
        service.geocode_problem(problem)
        
        # THEN: Site1 (Bad Street) should still have no coordinates
        assert problem.sites[0].lat is None
        assert problem.sites[0].lng is None
        
        # THEN: Site2 (Good Street) should have coordinates
        assert problem.sites[1].lat is not None
        assert problem.sites[1].lng is not None
        
        # THEN: geocoded.csv should only contain successfully geocoded sites
        geocoded_csv = problem.paths.geocoded_csv()
        assert geocoded_csv.exists(), "geocoded.csv should be created"
        
        from models.problem_state import load_geocoded_csv
        geocoded_sites = load_geocoded_csv(geocoded_csv)
        assert len(geocoded_sites) == 1, "Only successfully geocoded sites should be in geocoded.csv"
        assert geocoded_sites[0].id == "Site2", "Site2 should be in geocoded.csv"
        
        # THEN: geocoded-errors.csv should contain failed sites
        error_csv = state_dir / "geocoded-errors.csv"
        assert error_csv.exists(), "geocoded-errors.csv should be created for failed geocoding"
        
        import pandas as pd
        error_df = pd.read_csv(error_csv)
        assert len(error_df) == 1, "Failed site should be in error file"
        assert error_df.iloc[0]['site_id'] == "Site1", "Site1 should be in error file"
        assert "Bad Street" in error_df.iloc[0]['address1'], "Error file should contain the failed address"
        
            
        
        
    
    def test_geocode_with_cache_hit(self, problem_state_workspace):
        """
        Test that geocoding uses cache when available.
        """
        # GIVEN: Cache with pre-populated geocoding result
        base_dir, state_dir = problem_state_workspace
        cache_path = state_dir / "test_cache.db"
        cache = GeocodeCache(str(cache_path))
        
        # Pre-populate cache with known coordinates (address now includes city)
        cache.set("123 Main St, San Francisco", "CA", 37.7749, -122.4194, "San Francisco, CA")
        
        # Create addresses.csv with site that matches cached entry
        addresses_csv = state_dir / "addresses.csv"
        addresses_csv.write_text("""site_id,address1,city,state,zip
Site1,123 Main St,San Francisco,CA,94102""")
        
        problem = ProblemState.from_workspace(
            client="test_client",
            workspace="test_workspace",
            entity_type="site",
            state_code="CA",
            base_dir=base_dir
        )
        
        # WHEN: Geocode with cache available
        geocoder = MockGeocoder()
        service = GeocodeService(geocoder, cache_path=str(cache_path))
        
        log_messages = []
        service.geocode_problem(problem, log_callback=lambda msg: log_messages.append(msg))
        
        # THEN: Should use cached result instead of calling geocoder
        assert problem.sites[0].lat == 37.7749
        assert problem.sites[0].lng == -122.4194
        assert any("Cache hit" in msg for msg in log_messages)
    
    def test_geocode_with_cache_miss(self, problem_state_workspace):
        """
        Test that geocoding calls API on cache miss and stores result in cache.
        """
        # GIVEN: Empty cache and site that needs geocoding
        base_dir, state_dir = problem_state_workspace
        cache_path = state_dir / "test_cache.db"
        cache = GeocodeCache(str(cache_path))
        
        # Create addresses.csv with site not in cache
        addresses_csv = state_dir / "addresses.csv"
        addresses_csv.write_text("""site_id,address1,city,state,zip
Site1,999 New St,San Francisco,CA,94102""")
        
        problem = ProblemState.from_workspace(
            client="test_client",
            workspace="test_workspace",
            entity_type="site",
            state_code="CA",
            base_dir=base_dir
        )
        
        # WHEN: Geocode the site
        geocoder = MockGeocoder()
        service = GeocodeService(geocoder, cache_path=str(cache_path))
        service.geocode_problem(problem)
        
        # THEN: Result should be stored in cache for future use (address includes city)
        cached_result = cache.get("999 New St, San Francisco", "CA")
        assert cached_result is not None
        assert cached_result['lat'] == problem.sites[0].lat
        assert cached_result['lng'] == problem.sites[0].lng
    
    def test_geocode_skips_already_geocoded_sites(self, temp_workspace):
        """
        Test that geocoding skips sites that already have coordinates.
        """
        # Use a temporary cache to avoid interference
        cache_path = temp_workspace / "test_cache.db"
        
        # Create problem state with mixed sites
        problem = ProblemState(
            client="test",
            workspace="test",
            entity_type="site",
            state_code="CA",
            sites=[
                Site(id="Site1", address="123 Main St", state_code="CA", lat=37.7749, lng=-122.4194),
                Site(id="Site2", address="456 Oak Ave", state_code="NY")
            ]
        )
        
        # Track which sites were geocoded
        geocoded_ids = []
        
        class TrackingGeocoder(MockGeocoder):
            def geocode(self, sites, log_callback=None):
                for site in sites:
                    geocoded_ids.append(site.id)
                return super().geocode(sites, log_callback)
        
        geocoder = TrackingGeocoder()
        service = GeocodeService(geocoder, cache_path=str(cache_path))
        service.geocode_problem(problem)
        
        # Assert: Only Site2 should have been geocoded
        assert "Site1" not in geocoded_ids
        assert "Site2" in geocoded_ids
    
    def test_geocode_cache_statistics(self, temp_workspace):
        """
        Test cache statistics tracking for successful and failed geocoding attempts.
        """
        # GIVEN: Cache with mix of successful and failed geocoding results
        cache_path = temp_workspace / "test_cache.db"
        cache = GeocodeCache(str(cache_path))
        
        cache.set("123 Main St", "CA", 37.7749, -122.4194, "San Francisco, CA")
        cache.set("456 Oak Ave", "NY", 40.7128, -74.0060, "New York, NY")
        cache.set("789 Pine Rd", "TX", None, None, None)  # Failed geocoding
        
        # WHEN: Get cache statistics
        stats = cache.get_stats()
        
        # THEN: Statistics should correctly reflect successful and failed entries
        assert stats['total_entries'] == 3
        assert stats['successful_entries'] == 2
        assert stats['failed_entries'] == 1

    def test_geocode_writes_csv(self, problem_state_workspace):
        """
        Test that geocoding writes results to geocoded.csv using ProblemState.paths.
        """
        # GIVEN: Set up workspace and problem state
        base_dir, state_dir = problem_state_workspace
        cache_path = state_dir / "test_cache.db"
        
        # Create addresses.csv
        addresses_csv = state_dir / "addresses.csv"
        addresses_csv.write_text("""site_id,address1,city,state,zip
Site1,123 Main St,San Francisco,CA,94102
Site2,456 Oak Ave,New York,NY,10001""")
        
        # Load problem state from workspace
        problem = ProblemState.from_workspace(
            client="test_client",
            workspace="test_workspace",
            entity_type="site",
            state_code="CA",
            base_dir=base_dir
        )
        
        # Verify geocoded.csv doesn't exist yet
        assert not problem.paths.geocoded_csv().exists()
        
        # WHEN: Geocode the sites
        geocoder = MockGeocoder()
        service = GeocodeService(geocoder, cache_path=str(cache_path))
        service.geocode_problem(problem)
        
        # THEN: geocoded.csv should be written with geocoded results
        assert problem.paths.geocoded_csv().exists()
        
        # Verify the contents of geocoded.csv
        sites = load_geocoded_csv(problem.paths.geocoded_csv())
        assert len(sites) == 2
        assert sites[0].id == "Site1"
        assert sites[0].lat is not None
        assert sites[0].lng is not None
        assert sites[1].id == "Site2"
        assert sites[1].lat is not None
        assert sites[1].lng is not None
