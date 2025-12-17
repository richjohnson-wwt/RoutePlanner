from pathlib import Path
from dataclasses import dataclass


@dataclass
class WorkspacePaths:
    root: Path

    def addresses_csv(self, state_code: str) -> Path:
        """Return path to addresses.csv for a given state"""
        return self.root / state_code / "addresses.csv"

    def geocoded_csv(self, state_code: str) -> Path:
        """Return path to geocoded.csv for a given state"""
        return self.root / state_code / "geocoded.csv"

    def clustered_csv(self, state_code: str) -> Path:
        """Return path to clustered.csv for a given state"""
        return self.root / state_code / "clustered.csv"

    def solution_csv(self, state_code: str) -> Path:
        """Return path to solution.csv for a given state"""
        return self.root / state_code / "solution.csv"

    def route_map_html(self, state_code: str) -> Path:
        """Return path to route_map.html for a given state"""
        return self.root / state_code / "route_map.html"