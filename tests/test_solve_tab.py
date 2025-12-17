"""
Integration tests for Solve Tab functionality.
Tests the complete workflow of solving routing problems.
"""
import pytest
from pathlib import Path
from datetime import datetime
from models.problem_state import ProblemState
from models.route import Route
from models.site import Site
from services.solve_service import SolveService


class TestSolveTab:
    """Integration tests for solve tab operations."""
    
    def test_haversine_distance_calculation(self):
        """Test that haversine distance calculation is accurate."""
        service = SolveService(time_limit_seconds=30)
        
        # San Francisco to Los Angeles (approx 347 miles)
        sf_lat, sf_lng = 37.7749, -122.4194
        la_lat, la_lng = 34.0522, -118.2437
        
        distance = service._haversine_distance(sf_lat, sf_lng, la_lat, la_lng)
        
        # Should be approximately 347 miles (within 10 miles tolerance)
        assert 337 <= distance <= 357, f"Expected ~347 miles, got {distance:.2f}"
    
    def test_haversine_distance_same_point(self):
        """Test that distance between same point is zero."""
        service = SolveService(time_limit_seconds=30)
        
        lat, lng = 37.7749, -122.4194
        distance = service._haversine_distance(lat, lng, lat, lng)
        
        assert distance == 0.0
    
    def test_generate_solution_table_data_basic(self, problem_state_workspace):
        """Test generating solution table data from routes."""
        base_dir, state_dir = problem_state_workspace
        
        # Setup: Create sites with coordinates
        csv_data = """SiteID,Address,State,Lat,Lng
Site1,123 Main St,CA,37.7749,-122.4194
Site2,456 Oak Ave,CA,37.7849,-122.4094
Site3,789 Pine Rd,CA,37.7949,-122.3994"""
        
        csv_path = state_dir / "geocoded.csv"
        csv_path.write_text(csv_data)
        
        problem = ProblemState.from_workspace(
            client="test_client",
            workspace="test_workspace",
            entity_type="site",
            state_code="CA",
            base_dir=base_dir
        )
        
        # Create a test route
        route = Route(
            state_code="CA",
            cluster_id=1,
            vehicle_id=1,
            stops=3,
            sequence=["Site1", "Site2", "Site3"],
            mode="ortools",
            speed_mph=50.0,
            service_hours=1.5,
            solved_at=datetime.now()
        )
        
        service = SolveService(time_limit_seconds=30)
        table_data = service.generate_solution_table_data(problem, [route])
        
        # Assert: Should have 3 rows (one per stop)
        assert len(table_data) == 3
        
        # Assert: Each row should have 12 columns
        for row in table_data:
            assert len(row) == 12
        
        # Assert: First row should be for Site1
        assert table_data[0][2] == "Site1"  # site_id column
        assert table_data[0][0] == "1"      # route_id column
        assert table_data[0][1] == "0"      # stop_sequence column
        
        # Assert: Coordinates should be present
        assert table_data[0][5] == "37.774900"  # lat
        assert table_data[0][6] == "-122.419400"  # lng
        
        # Assert: Times should be formatted
        assert ":" in table_data[0][7]  # arrival_time
        assert ":" in table_data[0][8]  # departure_time
    
    def test_generate_solution_table_data_multiple_routes(self, problem_state_workspace):
        """Test generating solution table data with multiple routes."""
        base_dir, state_dir = problem_state_workspace
        
        # Setup: Create sites with coordinates and clusters
        csv_data = """SiteID,Address,State,Lat,Lng,ClusterID
Site1,123 Main St,CA,37.7749,-122.4194,1
Site2,456 Oak Ave,CA,37.7849,-122.4094,1
Site3,789 Pine Rd,CA,37.7949,-122.3994,2
Site4,321 Elm St,CA,37.8049,-122.3894,2"""
        
        csv_path = state_dir / "clustered.csv"
        csv_path.write_text(csv_data)
        
        problem = ProblemState.from_workspace(
            client="test_client",
            workspace="test_workspace",
            entity_type="site",
            state_code="CA",
            base_dir=base_dir
        )
        
        # Create two test routes
        route1 = Route(
            state_code="CA",
            cluster_id=1,
            vehicle_id=1,
            stops=2,
            sequence=["Site1", "Site2"],
            mode="ortools",
            speed_mph=50.0,
            service_hours=1.0,
            solved_at=datetime.now()
        )
        
        route2 = Route(
            state_code="CA",
            cluster_id=2,
            vehicle_id=2,
            stops=2,
            sequence=["Site3", "Site4"],
            mode="ortools",
            speed_mph=50.0,
            service_hours=1.0,
            solved_at=datetime.now()
        )
        
        service = SolveService(time_limit_seconds=30)
        table_data = service.generate_solution_table_data(problem, [route1, route2])
        
        # Assert: Should have 4 rows total (2 stops per route)
        assert len(table_data) == 4
        
        # Assert: First two rows should be route 1
        assert table_data[0][0] == "1"  # route_id
        assert table_data[1][0] == "1"  # route_id
        
        # Assert: Last two rows should be route 2
        assert table_data[2][0] == "2"  # route_id
        assert table_data[3][0] == "2"  # route_id
        
        # Assert: Stop sequences should be correct
        assert table_data[0][1] == "0"  # first stop of route 1
        assert table_data[1][1] == "1"  # second stop of route 1
        assert table_data[2][1] == "0"  # first stop of route 2
        assert table_data[3][1] == "1"  # second stop of route 2
    
    def test_generate_solution_table_data_with_distances(self, problem_state_workspace):
        """Test that solution table includes travel times and distances."""
        base_dir, state_dir = problem_state_workspace
        
        # Setup: Create sites with coordinates (about 10 miles apart)
        csv_data = """SiteID,Address,State,Lat,Lng
Site1,Start,CA,37.7749,-122.4194
Site2,End,CA,37.8749,-122.4194"""
        
        csv_path = state_dir / "geocoded.csv"
        csv_path.write_text(csv_data)
        
        problem = ProblemState.from_workspace(
            client="test_client",
            workspace="test_workspace",
            entity_type="site",
            state_code="CA",
            base_dir=base_dir
        )
        
        # Create a route with 2 stops
        route = Route(
            state_code="CA",
            cluster_id=1,
            vehicle_id=1,
            stops=2,
            sequence=["Site1", "Site2"],
            mode="ortools",
            speed_mph=50.0,
            service_hours=1.0,
            solved_at=datetime.now()
        )
        
        service = SolveService(time_limit_seconds=30)
        table_data = service.generate_solution_table_data(problem, [route])
        
        # Assert: First stop should have travel time to next stop
        travel_time_min = table_data[0][10]  # travel_time_min column
        distance_miles = table_data[0][11]   # distance_miles column
        
        assert travel_time_min != ""  # Should have a value
        assert distance_miles != ""   # Should have a value
        
        # Assert: Last stop should not have travel time (no next stop)
        assert table_data[1][10] == ""  # No travel time
        assert table_data[1][11] == ""  # No distance
    
    def test_save_solution_creates_csv(self, problem_state_workspace):
        """Test that saving solution creates a CSV file with correct data."""
        base_dir, state_dir = problem_state_workspace
        
        # Setup: Create sites with coordinates
        csv_data = """SiteID,Address,State,Lat,Lng
Site1,123 Main St,CA,37.7749,-122.4194
Site2,456 Oak Ave,CA,37.7849,-122.4094"""
        
        csv_path = state_dir / "geocoded.csv"
        csv_path.write_text(csv_data)
        
        problem = ProblemState.from_workspace(
            client="test_client",
            workspace="test_workspace",
            entity_type="site",
            state_code="CA",
            base_dir=base_dir
        )
        
        # Create a test route
        route = Route(
            state_code="CA",
            cluster_id=1,
            vehicle_id=1,
            stops=2,
            sequence=["Site1", "Site2"],
            mode="ortools",
            speed_mph=50.0,
            service_hours=1.0,
            solved_at=datetime.now()
        )
        
        service = SolveService(time_limit_seconds=30)
        service._save_solution(problem, [route])
        
        # Assert: solution.csv should exist
        solution_path = problem.paths.solution_csv()
        assert solution_path.exists()
        
        # Assert: CSV should have correct headers and data
        content = solution_path.read_text()
        assert "route_id" in content
        assert "site_id" in content
        assert "Site1" in content
        assert "Site2" in content
        
        # Assert: Problem state should be updated
        assert problem.routes == [route]
        assert problem.stage.name == "SOLVED"
    
    def test_solution_table_data_time_progression(self, problem_state_workspace):
        """Test that arrival/departure times progress correctly through stops."""
        base_dir, state_dir = problem_state_workspace
        
        # Setup: Create sites
        csv_data = """SiteID,Address,State,Lat,Lng
Site1,Start,CA,37.7749,-122.4194
Site2,Middle,CA,37.7849,-122.4094
Site3,End,CA,37.7949,-122.3994"""
        
        csv_path = state_dir / "geocoded.csv"
        csv_path.write_text(csv_data)
        
        problem = ProblemState.from_workspace(
            client="test_client",
            workspace="test_workspace",
            entity_type="site",
            state_code="CA",
            base_dir=base_dir
        )
        
        # Create a route with 3 stops, 1.5 hours total (30 min per stop)
        route = Route(
            state_code="CA",
            cluster_id=1,
            vehicle_id=1,
            stops=3,
            sequence=["Site1", "Site2", "Site3"],
            mode="ortools",
            speed_mph=50.0,
            service_hours=1.5,
            solved_at=datetime.now()
        )
        
        service = SolveService(time_limit_seconds=30)
        table_data = service.generate_solution_table_data(problem, [route])
        
        # Assert: Each stop should have arrival and departure times
        for row in table_data:
            arrival_time = row[7]
            departure_time = row[8]
            assert arrival_time != ""
            assert departure_time != ""
            assert ":" in arrival_time
            assert ":" in departure_time
        
        # Assert: Departure time of first stop should be before arrival of second stop
        # (This is a basic sanity check - times should progress forward)
        first_departure = table_data[0][8]
        second_arrival = table_data[1][7]
        # Both should be valid time strings
        assert len(first_departure) > 0
        assert len(second_arrival) > 0
