"""
Integration tests for Parse Tab functionality.
Tests the complete workflow of parsing CSV files into ProblemState.
"""
import pytest
from pathlib import Path
from models.problem_state import load_addresses_csv
from services.parse_service import ParseService

# ParseTab does not use ProblemState. It just parses Excel file and populates columns' loc,street1,street2,city,st,zip in addresses.csv by state.
class TestParseTab:
    """Integration tests for parse tab operations."""

    def test_parse_excel(self, temp_workspace):
        """
        Test parsing Excel file and populating addresses.csv by state.
        """
        # GIVEN: Test Excel file with sites in LA and NC states
        # Use the actual test data file from tests/data directory
        test_dir = Path(__file__).parent
        excel_path = test_dir / "data" / "acme.xlsx"
        config_path = test_dir / "config" / "acme.yml"
        
        # Verify test files exist
        assert excel_path.exists(), f"Test data file not found: {excel_path}"
        assert config_path.exists(), f"Config file not found: {config_path}"
        
        # WHEN: parse_excel is called with output to temp workspace
        parse_service = ParseService(config_path)
        state_counts = parse_service.parse_excel(excel_path, "Sheet1", temp_workspace)
        
        # THEN: addresses.csv should be created under LA and NC directories
        la_addresses_csv = temp_workspace / "LA" / "addresses.csv"
        nc_addresses_csv = temp_workspace / "NC" / "addresses.csv"
        
        assert la_addresses_csv.exists(), "LA/addresses.csv should exist"
        assert nc_addresses_csv.exists(), "NC/addresses.csv should exist"
        
        # Verify the state counts (actual data has 7 LA sites and 9 NC sites based on test run)
        assert "LA" in state_counts, "LA should be in state counts"
        assert "NC" in state_counts, "NC should be in state counts"
        assert state_counts["LA"] > 0, f"LA should have sites, got {state_counts['LA']}"
        assert state_counts["NC"] > 0, f"NC should have sites, got {state_counts['NC']}"
        
        # Verify CSV contents can be loaded
        la_sites = load_addresses_csv(la_addresses_csv)
        nc_sites = load_addresses_csv(nc_addresses_csv)
        
        assert len(la_sites) == state_counts["LA"], f"LA sites loaded should match state count"
        assert len(nc_sites) == state_counts["NC"], f"NC sites loaded should match state count"
        
        # Verify sites have required fields
        assert la_sites[0].id is not None, "LA sites should have IDs"
        assert la_sites[0].state_code == "LA", "LA sites should have correct state code"
        assert nc_sites[0].id is not None, "NC sites should have IDs"
        assert nc_sites[0].state_code == "NC", "NC sites should have correct state code"
        
    
    def test_load_addresses_csv(self, temp_workspace):
        """
        Test loading addresses.csv file with standardized columns from ParseService.
        """
        # GIVEN: CSV with standardized column names (from ParseService)
        csv_data = """site_id,address1,city,state,zip
Site1,123 Main St,San Francisco,CA,94102
Site2,456 Oak Ave,New York,NY,10001
Site3,789 Pine Rd,Houston,TX,77002"""
        
        csv_path = temp_workspace / "addresses.csv"
        csv_path.write_text(csv_data)
        
        # WHEN: Load sites
        sites = load_addresses_csv(csv_path)
        
        # THEN: Verify sites were loaded correctly
        assert len(sites) == 3
        assert sites[0].id == "Site1"
        assert "123 Main St" in sites[0].address
        assert "San Francisco" in sites[0].address
        assert sites[0].state_code == "CA"
    

    
    def test_parse_csv_missing_required_columns(self, temp_workspace):
        """
        Test that loading fails gracefully when required columns are missing.
        """
        # GIVEN: CSV missing site_id column
        csv_data = """address1,city,state
123 Main St,San Francisco,CA"""
        
        csv_path = temp_workspace / "invalid.csv"
        csv_path.write_text(csv_data)
        
        # THEN: Should raise ValueError for missing site_id column
        with pytest.raises(ValueError, match="missing 'site_id' column"):
            load_addresses_csv(csv_path)
        
        # GIVEN: CSV missing state column
        csv_data2 = """site_id,address1,city
Site1,123 Main St,San Francisco"""
        
        csv_path2 = temp_workspace / "invalid2.csv"
        csv_path2.write_text(csv_data2)
        
        # THEN: Should raise ValueError for missing state column
        with pytest.raises(ValueError, match="missing 'state' column"):
            load_addresses_csv(csv_path2)
    
    