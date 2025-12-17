import json
import numpy as np
from pathlib import Path
from sklearn.cluster import KMeans
from models.problem_state import ProblemState


class ClusterService:
    """Service for clustering geocoded sites using K-means algorithm."""
    
    def __init__(self, algorithm: str = "kmeans", seed: int = 42):
        """
        Initialize the clustering service.
        
        Args:
            algorithm: Clustering algorithm to use (currently only "kmeans" supported)
            seed: Random seed for reproducibility
        """
        self.algorithm = algorithm
        self.seed = seed
    
    def cluster_problem(
        self, 
        problem: ProblemState, 
        k: int = None,
        selection: str = "auto",
        log_callback=None
    ) -> None:
        """
        Cluster sites and persist results.
        Mutates ProblemState by setting cluster_id on each Site.
        Saves cluster_prefs.json and clustered.csv.
        
        Args:
            problem: ProblemState with geocoded sites
            k: Number of clusters (None = auto determine)
            selection: "auto" or "manual"
            log_callback: Optional callback function for logging messages
        """
        def log(msg: str):
            """Helper to log messages"""
            if log_callback:
                log_callback(msg)
        
        sites = problem.sites
        
        if not sites:
            raise RuntimeError("No sites to cluster")
        
        # Filter out sites without valid coordinates
        sites_with_coords = [s for s in sites if s.lat is not None and s.lng is not None]
        sites_without_coords = [s for s in sites if s.lat is None or s.lng is None]
        
        if sites_without_coords:
            log(f"⚠ Warning: {len(sites_without_coords)} site(s) missing coordinates will be skipped")
            log(f"  Sites without coordinates: {', '.join([s.id for s in sites_without_coords[:5]])}" + 
                ("..." if len(sites_without_coords) > 5 else ""))
        
        if not sites_with_coords:
            raise RuntimeError("No sites with valid coordinates to cluster. Run geocoding first.")
        
        log(f"Clustering {len(sites_with_coords)} sites using {self.algorithm}")
        
        # Determine K if auto mode
        if selection == "auto":
            k = self._determine_optimal_k(sites_with_coords, log_callback=log)
            log(f"Auto-determined K={k}")
        elif k is None:
            raise ValueError("K must be specified when selection='manual'")
        
        # Perform K-means clustering on sites with coordinates
        coordinates = np.array([[site.lat, site.lng] for site in sites_with_coords])
        
        kmeans = KMeans(n_clusters=k, random_state=self.seed, n_init=10)
        cluster_labels = kmeans.fit_predict(coordinates)
        
        # Assign cluster_id to sites with coordinates
        for site, cluster_id in zip(sites_with_coords, cluster_labels):
            site.cluster_id = int(cluster_id)
        
        # Sites without coordinates get cluster_id = None (or -1 for "unassigned")
        for site in sites_without_coords:
            site.cluster_id = -1  # -1 indicates unassigned/no coordinates
        
        log(f"Assigned {len(sites_with_coords)} sites to {k} clusters")
        if sites_without_coords:
            log(f"  {len(sites_without_coords)} sites without coordinates marked as unassigned (cluster_id=-1)")
        
        # Save cluster preferences
        if problem.paths:
            prefs_path = problem.paths.root / "cluster_prefs.json"
            self._save_cluster_prefs(prefs_path, k, selection)
            log(f"Saved cluster preferences to {prefs_path}")
            
            # Save clustered results
            from models.problem_state import save_clustered_csv
            save_clustered_csv(problem.paths.clustered_csv(), problem.sites)
            log(f"Saved clustered results to {problem.paths.clustered_csv()}")
        
        # Update problem state
        from models.planning_stage import PlanningStage
        problem.stage = PlanningStage.CLUSTERED
        problem.clusters = {i: [s for s in sites_with_coords if s.cluster_id == i] for i in range(k)}
    
    def _determine_optimal_k(self, sites, log_callback=None) -> int:
        """
        Automatically determine optimal number of clusters.
        Uses elbow method with inertia.
        
        Args:
            sites: List of sites with coordinates
            log_callback: Optional logging callback
            
        Returns:
            Optimal K value
        """
        # Simple heuristic: sqrt(n/2) bounded between 2 and 10
        n = len(sites)
        k = max(2, min(10, int(np.sqrt(n / 2))))
        return k
    
    def _save_cluster_prefs(self, path: Path, k: int, selection: str) -> None:
        """Save clustering preferences to JSON file."""
        prefs = {
            "algorithm": self.algorithm,
            "k": k,
            "selection": selection,
            "seed": self.seed
        }
        
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            json.dump(prefs, f, indent=2)
