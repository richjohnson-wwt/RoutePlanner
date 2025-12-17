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
        if paths.solution_csv(state.state_code).exists():
            state.routes = load_solution_csv(paths.solution_csv(state.state_code))
            state.sites = extract_sites_from_routes(state.routes)
            state.stage = PlanningStage.SOLVED
            return state

        if paths.clustered_csv(state.state_code).exists():
            state.sites, state.clusters = load_clustered_csv(paths.clustered_csv(state.state_code))
            state.stage = PlanningStage.CLUSTERED
            return state

        if paths.geocoded_csv(state.state_code).exists():
            state.sites = load_geocoded_csv(paths.geocoded_csv(state.state_code))
            state.stage = PlanningStage.GEOCODED
            return state

        if paths.addresses_csv(state.state_code).exists():
            state.sites = load_addresses_csv(paths.addresses_csv(state.state_code))
            state.stage = PlanningStage.ADDRESSES
            return state

        # Nothing usable exists
        raise FileNotFoundError(
            f"No usable CSVs found in {state_dir}"
        )

REQUIRED_COLUMNS = {"siteid", "address", "state"}

def load_addresses_csv(path: Path) -> list[Site]:
    """Load sites from addresses.csv (pre-geocoding)."""

    if not path.exists():
        raise FileNotFoundError(path)

    df = pd.read_csv(path)

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(
            f"{path.name} is missing required columns: {sorted(missing)}"
        )

    sites: list[Site] = []

    for row in df.itertuples(index=False):
        sites.append(
            Site(
                id=str(row.siteid),
                address=str(row.address).strip(),
                state_code=str(row.state).strip(),
                lat=None,
                lng=None,
                display_name=str(row.address).strip(),
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