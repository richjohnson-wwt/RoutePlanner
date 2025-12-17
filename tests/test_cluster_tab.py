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
