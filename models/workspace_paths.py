from pathlib import Path
from dataclasses import dataclass


@dataclass
class WorkspacePaths:
    root: Path

    def addresses_csv(self) -> Path:
        """Return path to addresses.csv for a given state"""
        return self.root / "addresses.csv"

    def geocoded_csv(self) -> Path:
        """Return path to geocoded.csv for a given state"""
        return self.root / "geocoded.csv"

    def clustered_csv(self) -> Path:
        """Return path to clustered.csv for a given state"""
        return self.root / "clustered.csv"

    def solution_csv(self) -> Path:
        """Return path to solution.csv for a given state"""
        return self.root / "solution.csv"

    def route_map_html(self) -> Path:
        """Return path to route_map.html for a given state"""
        return self.root / "route_map.html"