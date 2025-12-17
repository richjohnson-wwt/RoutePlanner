from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from .route import Route
from .site import Site
from .planning_stage import PlanningStage
from .workspace_paths import WorkspacePaths

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
    
    Handles different column naming conventions from various clients:
    - ID: 'siteid', 'loc', or first column
    - State: 'state', 'st'
    - Address: 'address' or combination of 'street1', 'street2', 'city'
    """

    if not path.exists():
        raise FileNotFoundError(path)

    df = pd.read_csv(path)
    columns = [col.lower().strip() for col in df.columns]
    
    # Find ID column (siteid, loc, or first column as fallback)
    id_col = None
    for candidate in ['siteid', 'loc']:
        if candidate in columns:
            id_col = df.columns[columns.index(candidate)]
            break
    if id_col is None:
        id_col = df.columns[0]  # Use first column as ID
    
    # Find state column (state or st)
    state_col = None
    for candidate in ['state', 'st']:
        if candidate in columns:
            state_col = df.columns[columns.index(candidate)]
            break
    
    if state_col is None:
        raise ValueError(
            f"{path.name} is missing state column (expected 'state' or 'st')"
        )
    
    # Determine how to build address string
    has_address = 'address' in columns
    has_street_parts = 'street1' in columns or 'city' in columns
    
    if not has_address and not has_street_parts:
        raise ValueError(
            f"{path.name} is missing address information (expected 'address' or 'street1'/'city')"
        )

    sites: list[Site] = []

    for _, row in df.iterrows():
        # Get ID
        site_id = str(row[id_col])
        
        # Get state
        state_code = str(row[state_col]).strip()
        
        # Build address string
        if has_address:
            address_col = df.columns[columns.index('address')]
            address = str(row[address_col]).strip()
        else:
            # Build from parts
            parts = []
            for col_name in ['street1', 'street2', 'city']:
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
    """Load geocoded sites from geocoded.csv"""
    # TODO: Implement
    return []


def load_clustered_csv(path: Path) -> tuple[list[Site], dict[int, list[Site]]]:
    """Load clustered sites from clustered.csv"""
    # TODO: Implement
    return [], {}


def load_solution_csv(path: Path) -> list[Route]:
    """Load routes from solution.csv"""
    # TODO: Implement
    return []


def extract_sites_from_routes(routes: list[Route]) -> list[Site]:
    """Extract sites from solved routes"""
    # TODO: Implement
    return []