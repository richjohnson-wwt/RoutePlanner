from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from .route import Route
from .site import Site
from .planning_stage import PlanningStage
from .workspace_paths import WorkspacePaths

# This object maintains the entire state of the application. Changes made are propogated to the top-level tab (ie geocode, cluster, solve)
# csv files are only created to persist the work between sessions.

@dataclass
class ProblemState:
    client: str
    workspace: str
    entity_type: str
    state_code: str

    sites: list[Site] = field(default_factory=list)
    clusters: dict[int, list[Site]] | None = None
    routes: list[Route] | None = None

    stage: PlanningStage | None = None
    paths: WorkspacePaths | None = None

    @classmethod
    def from_workspace(
        cls,
        client: str,
        workspace: str,
        entity_type: str,
        state_code: str,
        base_dir: Path,
    ) -> "ProblemState":
        """
        Hydrate ProblemState from the most advanced CSV available
        for the given client/workspace/state.
        """

        state_dir = (
            base_dir
            / client
            / workspace
            / state_code
        )

        paths = WorkspacePaths(state_dir)

        if not state_dir.exists():
            raise FileNotFoundError(f"State directory does not exist: {state_dir}")

        # Create empty shell first
        state = cls(
            client=client,
            workspace=workspace,
            entity_type=entity_type,
            state_code=state_code,
            paths=paths,
        )

        # Resume from most advanced artifact
        if paths.solution_csv().exists():
            state.routes = load_solution_csv(paths.solution_csv())
            state.sites = extract_sites_from_routes(state.routes)
            state.stage = PlanningStage.SOLVED
            return state

        if paths.clustered_csv().exists():
            state.sites, state.clusters = load_clustered_csv(paths.clustered_csv())
            state.stage = PlanningStage.CLUSTERED
            return state

        if paths.geocoded_csv().exists():
            state.sites = load_geocoded_csv(paths.geocoded_csv())
            state.stage = PlanningStage.GEOCODED
            return state

        if paths.addresses_csv().exists():
            state.sites = load_addresses_csv(paths.addresses_csv())
            state.stage = PlanningStage.ADDRESSES
            return state

        # Nothing usable exists
        raise FileNotFoundError(
            f"No usable CSVs found in {state_dir}"
        )

def load_addresses_csv(path: Path) -> list[Site]:
    """Load sites from addresses.csv (pre-geocoding).
    
    Expects standardized column names from ParseService:
    - site_id, address1, address2, city, state, zip
    """

    if not path.exists():
        raise FileNotFoundError(path)

    df = pd.read_csv(path)
    columns = [col.lower().strip() for col in df.columns]
    
    # Verify required columns exist
    if 'site_id' not in columns:
        raise ValueError(f"{path.name} is missing 'site_id' column")
    
    if 'state' not in columns:
        raise ValueError(f"{path.name} is missing 'state' column")
    
    # Get column references
    id_col = df.columns[columns.index('site_id')]
    state_col = df.columns[columns.index('state')]

    sites: list[Site] = []

    for _, row in df.iterrows():
        # Get ID and state
        site_id = str(row[id_col])
        state_code = str(row[state_col]).strip()
        
        # Build address string from address1, address2, city
        parts = []
        for col_name in ['address1', 'address2', 'city']:
            if col_name in columns:
                orig_col = df.columns[columns.index(col_name)]
                val = str(row[orig_col]).strip()
                if val and val.lower() != 'nan':
                    parts.append(val)
        
        address = ', '.join(parts) if parts else site_id
        
        sites.append(
            Site(
                id=site_id,
                address=address,
                state_code=state_code,
                lat=None,
                lng=None,
                display_name=address,
            )
        )

    return sites


def load_geocoded_csv(path: Path) -> list[Site]:
    """Load geocoded sites from geocoded.csv with lat/lng coordinates."""
    if not path.exists():
        raise FileNotFoundError(path)

    df = pd.read_csv(path)
    columns = [col.lower().strip() for col in df.columns]
    
    # Find ID column
    id_col = None
    for candidate in ['siteid', 'loc']:
        if candidate in columns:
            id_col = df.columns[columns.index(candidate)]
            break
    if id_col is None:
        id_col = df.columns[0]
    
    # Find state column
    state_col = None
    for candidate in ['state', 'st']:
        if candidate in columns:
            state_col = df.columns[columns.index(candidate)]
            break
    
    if state_col is None:
        raise ValueError(f"{path.name} is missing state column")
    
    # Find address column
    address_col = None
    if 'address' in columns:
        address_col = df.columns[columns.index('address')]
    
    # Find lat/lng columns
    lat_col = None
    lng_col = None
    if 'lat' in columns:
        lat_col = df.columns[columns.index('lat')]
    if 'lng' in columns:
        lng_col = df.columns[columns.index('lng')]
    elif 'lon' in columns:
        lng_col = df.columns[columns.index('lon')]
    
    sites: list[Site] = []
    
    for _, row in df.iterrows():
        site_id = str(row[id_col])
        state_code = str(row[state_col]).strip()
        
        # Get address
        address = str(row[address_col]).strip() if address_col else site_id
        
        # Get coordinates
        lat = None
        lng = None
        if lat_col and pd.notna(row[lat_col]):
            try:
                lat = float(row[lat_col])
            except (ValueError, TypeError):
                pass
        
        if lng_col and pd.notna(row[lng_col]):
            try:
                lng = float(row[lng_col])
            except (ValueError, TypeError):
                pass
        
        sites.append(
            Site(
                id=site_id,
                address=address,
                state_code=state_code,
                lat=lat,
                lng=lng,
                display_name=address,
            )
        )
    
    return sites


def save_geocoded_csv(path: Path, sites: list[Site]) -> None:
    """Save successfully geocoded sites to geocoded.csv with lat/lng coordinates.
    
    Only saves sites that have valid coordinates (lat and lng are not None).
    """
    # Create DataFrame from sites with valid coordinates only
    data = []
    for site in sites:
        # Only include sites that were successfully geocoded
        if site.lat is not None and site.lng is not None:
            data.append({
                'SiteID': site.id,
                'Address': site.address,
                'State': site.state_code,
                'Lat': site.lat,
                'Lng': site.lng,
                'DisplayName': site.display_name or site.address
            })
    
    df = pd.DataFrame(data)
    
    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to CSV
    df.to_csv(path, index=False)


def save_geocoded_errors_csv(path: Path, sites: list[Site]) -> None:
    """Save failed geocoding attempts to geocoded-errors.csv.
    
    Only saves sites that failed to geocode (lat and lng are None).
    """
    # Create DataFrame from sites that failed to geocode
    data = []
    for site in sites:
        # Only include sites that failed to geocode
        if site.lat is None or site.lng is None:
            data.append({
                'site_id': site.id,
                'address1': site.address.split(',')[0] if ',' in site.address else site.address,
                'city': site.address.split(',')[1].strip() if ',' in site.address and len(site.address.split(',')) > 1 else '',
                'state': site.state_code,
                'error': 'Failed to geocode address'
            })
    
    # Only write file if there are errors
    if data:
        df = pd.DataFrame(data)
        
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to CSV
        df.to_csv(path, index=False)


def save_clustered_csv(path: Path, sites: list[Site]) -> None:
    """Save clustered sites to clustered.csv with cluster assignments.
    
    Saves sites with their cluster_id assignments.
    """
    # Create DataFrame from sites
    data = []
    for site in sites:
        data.append({
            'SiteID': site.id,
            'Address': site.address,
            'State': site.state_code,
            'Lat': site.lat,
            'Lng': site.lng,
            'DisplayName': site.display_name or site.address,
            'cluster_id': site.cluster_id if site.cluster_id is not None else -1
        })
    
    df = pd.DataFrame(data)
    
    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to CSV
    df.to_csv(path, index=False)


def load_clustered_csv(path: Path) -> tuple[list[Site], dict[int, list[Site]]]:
    """Load clustered sites from clustered.csv"""
    if not path.exists():
        raise FileNotFoundError(path)
    
    df = pd.read_csv(path)
    columns = [col.lower().strip() for col in df.columns]
    
    # Find required columns
    id_col = None
    for candidate in ['siteid', 'site_id', 'loc']:
        if candidate in columns:
            id_col = df.columns[columns.index(candidate)]
            break
    if id_col is None:
        id_col = df.columns[0]
    
    # Find state column
    state_col = None
    for candidate in ['state', 'st']:
        if candidate in columns:
            state_col = df.columns[columns.index(candidate)]
            break
    
    # Find address column
    address_col = None
    for candidate in ['address', 'displayname']:
        if candidate in columns:
            address_col = df.columns[columns.index(candidate)]
            break
    
    # Find lat/lng columns
    lat_col = None
    lng_col = None
    if 'lat' in columns:
        lat_col = df.columns[columns.index('lat')]
    if 'lng' in columns:
        lng_col = df.columns[columns.index('lng')]
    elif 'lon' in columns:
        lng_col = df.columns[columns.index('lon')]
    
    # Find cluster_id column
    cluster_col = None
    for candidate in ['cluster_id', 'clusterid', 'cluster']:
        if candidate in columns:
            cluster_col = df.columns[columns.index(candidate)]
            break
    
    sites: list[Site] = []
    clusters: dict[int, list[Site]] = {}
    
    for _, row in df.iterrows():
        site_id = str(row[id_col])
        state_code = str(row[state_col]).strip() if state_col else ""
        address = str(row[address_col]).strip() if address_col else site_id
        
        # Get coordinates
        lat = None
        lng = None
        if lat_col and pd.notna(row[lat_col]):
            try:
                lat = float(row[lat_col])
            except (ValueError, TypeError):
                pass
        
        if lng_col and pd.notna(row[lng_col]):
            try:
                lng = float(row[lng_col])
            except (ValueError, TypeError):
                pass
        
        # Get cluster_id
        cluster_id = None
        if cluster_col and pd.notna(row[cluster_col]):
            try:
                cluster_id = int(row[cluster_col])
                if cluster_id < 0:
                    cluster_id = None
            except (ValueError, TypeError):
                pass
        
        site = Site(
            id=site_id,
            address=address,
            state_code=state_code,
            lat=lat,
            lng=lng,
            display_name=address,
            cluster_id=cluster_id,
        )
        
        sites.append(site)
        
        # Add to clusters dict
        if cluster_id is not None:
            if cluster_id not in clusters:
                clusters[cluster_id] = []
            clusters[cluster_id].append(site)
    
    return sites, clusters


def load_solution_csv(path: Path) -> list[Route]:
    """Load routes from solution.csv"""
    # TODO: Implement
    return []


def extract_sites_from_routes(routes: list[Route]) -> list[Site]:
    """Extract sites from solved routes"""
    # TODO: Implement
    return []