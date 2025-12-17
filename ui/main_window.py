"""
Main Window for VRPTW Application
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout,
    QTabWidget, QStatusBar, QLabel
)
from PyQt6.QtGui import QAction

from .control_bar import ControlBar
from .parse_tab import ParseTab
from .geocode_tab import GeocodeTab
from .cluster_tab import ClusterTab
from .solve_tab import SolveTab
from models.problem_state import ProblemState
from services.geocode_service import GeocodeService
from services.geocoder_nominatim import NominatimGeocoder
from services.geocoder_google import GoogleGeocoder


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("VRPTW Route Planner")
        self.resize(1200, 800)
        
        # Central layout with tabs
        central = QWidget(self)
        vbox = QVBoxLayout(central)
        vbox.setContentsMargins(6, 6, 6, 6)
        vbox.setSpacing(6)
        
        # Control bar with client, workspace, and state selection
        self.control_bar = ControlBar(self)
        vbox.addWidget(self.control_bar)
        
        # Tabs
        self.tabs = QTabWidget()
        vbox.addWidget(self.tabs, 1)
        self.setCentralWidget(central)
        
        # Add tabs (no Workspace tab)
        self.parse_tab = ParseTab(self)
        self.geocode_tab = GeocodeTab(self)
        self.cluster_tab = ClusterTab(self)
        self.solve_tab = SolveTab(self)
        
        self.tabs.addTab(self.parse_tab, "Parse")
        self.tabs.addTab(self.geocode_tab, "Geocode")
        self.tabs.addTab(self.cluster_tab, "Cluster")
        self.tabs.addTab(self.solve_tab, "Solve")
        
        # Connect tab change to update state dropdown enabled state
        self.tabs.currentChanged.connect(self.on_tab_changed)

        self._setup_statusbar()
        self.problem_state: ProblemState | None = None

        self.control_bar.workspace_changed.connect(self.parse_tab.on_workspace_changed)

        self.control_bar.workspace_changed.connect(self.on_workspace_or_state_changed)
        self.control_bar.state_changed.connect(self.on_workspace_or_state_changed)

        self.geocode_service = self._create_geocode_service()
        self.geocode_tab.set_service(self.geocode_service)
    
    def on_workspace_or_state_changed(self, value) -> None:
        """Handle workspace or state change to create new ProblemState"""
        # Update current selections from control bar
        self.current_client = self.control_bar.client_combo.currentText()
        self.current_workspace = self.control_bar.workspace_combo.currentText()
        self.current_state = self.control_bar.state_combo.currentText()
        
        # Only create ProblemState if we have valid client, workspace, and state
        if (self.current_client and self.current_client != "<no clients>" and
            self.current_workspace and self.current_workspace != "<no workspaces>" and
            self.current_state and self.current_state != "<no states>"):
            
            # Create new ProblemState
            from pathlib import Path
            base_dir = Path.home() / "Documents" / "RoutePlanner"
            
            try:
                self.problem_state = ProblemState.from_workspace(
                    client=self.current_client,
                    workspace=self.current_workspace,
                    entity_type="phones",
                    state_code=self.current_state,
                    base_dir=base_dir,
                )
            except FileNotFoundError as e:
                # No CSV files exist yet for this state - user needs to parse first
                self.problem_state = None
                self.statusbar.showMessage(f"No data found for {self.current_state}. Please parse data first.", 5000)
        else:
            self.problem_state = None
        
        # Propagate to tabs
        self.geocode_tab.set_problem_state(self.problem_state)
        self.cluster_tab.set_problem_state(self.problem_state)
        self.solve_tab.set_problem_state(self.problem_state)
    
    def on_tab_changed(self, index: int) -> None:
        """Handle tab change to update state dropdown enabled state"""
        tab_name = self.tabs.tabText(index)
        self.control_bar.update_state_dropdown_for_tab(tab_name)
    
    def _setup_statusbar(self) -> None:
        """Setup the status bar"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Ready")

    def _create_geocode_service(self) -> GeocodeService:
        # TODO: Add settings UI for geocoder selection
        # For now, default to Nominatim geocoder
        geocoder = NominatimGeocoder()
        return GeocodeService(geocoder)
