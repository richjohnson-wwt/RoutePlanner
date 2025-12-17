"""
Integration tests for Cluster Tab functionality.
Tests the complete workflow of clustering sites.
"""
import pytest
from pathlib import Path
from models.problem_state import ProblemState


class TestClusterTab:
    """Integration tests for cluster tab operations."""
    
    def test_cluster_sites_with_manual_k(self, problem_state_workspace):
        """
        Test clustering sites with manually specified K=3.
        """
        # GIVEN: Geocoded sites ready for clustering
        base_dir, state_dir = problem_state_workspace
        
        # Create geocoded.csv with 6 sites (enough for 3 clusters)
        geocoded_csv = state_dir / "geocoded.csv"
        geocoded_csv.write_text("""SiteID,Address,State,Lat,Lng,DisplayName
Site1,123 Main St,CA,37.7749,-122.4194,San Francisco
Site2,456 Oak Ave,CA,37.7849,-122.4094,San Francisco
Site3,789 Pine Rd,CA,37.7949,-122.3994,San Francisco
Site4,111 Elm St,CA,34.0522,-118.2437,Los Angeles
Site5,222 Maple Ave,CA,34.0622,-118.2337,Los Angeles
Site6,333 Cedar Rd,CA,34.0722,-118.2237,Los Angeles""")
        
        problem = ProblemState.from_workspace(
            client="test_client",
            workspace="test_workspace",
            entity_type="site",
            state_code="CA",
            base_dir=base_dir
        )
        
        # Verify sites are loaded with coordinates
        assert len(problem.sites) == 6
        assert all(site.lat is not None for site in problem.sites)
        assert all(site.lng is not None for site in problem.sites)
        
        # WHEN: Cluster with manual K=3
        from services.cluster_service import ClusterService
        
        service = ClusterService(algorithm="kmeans", seed=42)
        service.cluster_problem(
            problem=problem,
            k=3,
            selection="manual",
            log_callback=None
        )
        
        # THEN: Each site should have a cluster_id assigned (0, 1, or 2)
        assert all(site.cluster_id is not None for site in problem.sites)
        cluster_ids = set(site.cluster_id for site in problem.sites)
        assert len(cluster_ids) == 3, "Should have exactly 3 clusters"
        assert cluster_ids == {0, 1, 2}, "Cluster IDs should be 0, 1, 2"
        
        # THEN: cluster_prefs.json should exist with correct values
        import json
        prefs_path = state_dir / "cluster_prefs.json"
        assert prefs_path.exists(), "cluster_prefs.json should be created"
        
        with open(prefs_path, 'r') as f:
            prefs = json.load(f)
        
        assert prefs['algorithm'] == 'kmeans'
        assert prefs['k'] == 3
        assert prefs['selection'] == 'manual'
        assert prefs['seed'] == 42
        
        # THEN: clustered.csv should exist with cluster assignments
        clustered_csv = problem.paths.clustered_csv()
        assert clustered_csv.exists(), "clustered.csv should be created"
        
        # Verify clustered.csv has cluster_id column
        import pandas as pd
        df = pd.read_csv(clustered_csv)
        assert 'cluster_id' in df.columns.str.lower()
        assert len(df) == 6, "All sites should be in clustered.csv"
    
    def test_load_clustered_csv_with_state_filtering(self, problem_state_workspace):
        """
        Test that clustered.csv is loaded correctly and state filtering works.
        This tests the integration of load_clustered_csv() with state filtering.
        """
        # GIVEN: A clustered.csv with sites from multiple states
        base_dir, state_dir = problem_state_workspace
        
        clustered_csv = state_dir / "clustered.csv"
        clustered_csv.write_text("""SiteID,Address,State,Lat,Lng,DisplayName,cluster_id
Site1,123 Main St,CA,37.7749,-122.4194,San Francisco,0
Site2,456 Oak Ave,CA,37.7849,-122.4094,San Francisco,0
Site3,789 Pine Rd,CA,37.7949,-122.3994,San Francisco,1
Site4,111 Elm St,TX,29.7604,-95.3698,Houston,0
Site5,222 Maple Ave,TX,29.7704,-95.3598,Houston,1
Site6,333 Cedar Rd,NY,40.7128,-74.0060,New York,2""")
        
        # WHEN: Load ProblemState for CA state
        problem = ProblemState.from_workspace(
            client="test_client",
            workspace="test_workspace",
            entity_type="site",
            state_code="CA",
            base_dir=base_dir
        )
        
        # THEN: All sites should be loaded (including non-CA sites)
        assert len(problem.sites) == 6, "All sites from clustered.csv should be loaded"
        assert problem.stage.name == "CLUSTERED", "Stage should be CLUSTERED"
        
        # THEN: Sites should have cluster_id assigned
        assert all(site.cluster_id is not None for site in problem.sites)
        
        # THEN: Clusters dict should be populated correctly
        assert problem.clusters is not None
        assert len(problem.clusters) == 3, "Should have 3 clusters (0, 1, 2)"
        assert 0 in problem.clusters
        assert 1 in problem.clusters
        assert 2 in problem.clusters
        
        # THEN: When filtering by CA state (as cluster tab does)
        ca_sites = [s for s in problem.sites if s.state_code == "CA"]
        assert len(ca_sites) == 3, "Should have 3 CA sites"
        
        # Verify CA sites have correct cluster assignments
        ca_cluster_ids = set(s.cluster_id for s in ca_sites)
        assert ca_cluster_ids == {0, 1}, "CA sites should be in clusters 0 and 1"
        
        # THEN: Verify specific site data
        site1 = next(s for s in problem.sites if s.id == "Site1")
        assert site1.state_code == "CA"
        assert site1.cluster_id == 0
        assert site1.lat == 37.7749
        assert site1.lng == -122.4194
        
        site4 = next(s for s in problem.sites if s.id == "Site4")
        assert site4.state_code == "TX"
        assert site4.cluster_id == 0
        
        # THEN: Verify cluster groupings
        cluster_0_sites = problem.clusters[0]
        assert len(cluster_0_sites) == 3, "Cluster 0 should have 3 sites"
        cluster_0_ids = {s.id for s in cluster_0_sites}
        assert cluster_0_ids == {"Site1", "Site2", "Site4"}
    
    def test_load_clustered_csv_handles_missing_cluster_ids(self, problem_state_workspace):
        """
        Test that load_clustered_csv() handles sites with missing or invalid cluster_ids.
        """
        # GIVEN: A clustered.csv with some missing/invalid cluster_ids
        base_dir, state_dir = problem_state_workspace
        
        clustered_csv = state_dir / "clustered.csv"
        clustered_csv.write_text("""SiteID,Address,State,Lat,Lng,DisplayName,cluster_id
Site1,123 Main St,CA,37.7749,-122.4194,San Francisco,0
Site2,456 Oak Ave,CA,37.7849,-122.4094,San Francisco,1
Site3,789 Pine Rd,CA,37.7949,-122.3994,San Francisco,-1
Site4,111 Elm St,CA,34.0522,-118.2437,Los Angeles,
Site5,222 Maple Ave,CA,34.0622,-118.2337,Los Angeles,invalid""")
        
        # WHEN: Load ProblemState
        problem = ProblemState.from_workspace(
            client="test_client",
            workspace="test_workspace",
            entity_type="site",
            state_code="CA",
            base_dir=base_dir
        )
        
        # THEN: Sites with valid cluster_ids should be loaded correctly
        assert len(problem.sites) == 5
        
        site1 = next(s for s in problem.sites if s.id == "Site1")
        assert site1.cluster_id == 0
        
        site2 = next(s for s in problem.sites if s.id == "Site2")
        assert site2.cluster_id == 1
        
        # Sites with invalid cluster_ids should have None
        site3 = next(s for s in problem.sites if s.id == "Site3")
        assert site3.cluster_id is None, "Negative cluster_id should be treated as None"
        
        site4 = next(s for s in problem.sites if s.id == "Site4")
        assert site4.cluster_id is None, "Empty cluster_id should be None"
        
        site5 = next(s for s in problem.sites if s.id == "Site5")
        assert site5.cluster_id is None, "Invalid cluster_id should be None"
        
        # THEN: Only sites with valid cluster_ids should be in clusters dict
        assert problem.clusters is not None
        assert len(problem.clusters) == 2, "Should have 2 clusters (0, 1)"
        assert 0 in problem.clusters
        assert 1 in problem.clusters
        assert len(problem.clusters[0]) == 1
        assert len(problem.clusters[1]) == 1
