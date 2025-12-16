"""
Main Window for VRPTW Application
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout,
    QTabWidget, QStatusBar, QLabel
)
from PyQt6.QtGui import QAction

from .workspace_tab import WorkspaceTab
from .parse_tab import ParseTab
from .geocode_tab import GeocodeTab
from .cluster_tab import ClusterTab
from .solve_tab import SolveTab


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
        
        # Workspace path display
        self.workspace_label = QLabel("Workspace: <not selected>")
        self.workspace_label.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                color: #2c3e50;
                padding: 8px 12px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                font-family: monospace;
                font-size: 12px;
                font-weight: 500;
            }
        """)
        vbox.addWidget(self.workspace_label)
        
        # Tabs
        self.tabs = QTabWidget()
        vbox.addWidget(self.tabs, 1)
        self.setCentralWidget(central)
        
        # Add tabs
        self.workspace_tab = WorkspaceTab(self)
        self.parse_tab = ParseTab(self)
        self.geocode_tab = GeocodeTab(self)
        self.cluster_tab = ClusterTab(self)
        self.solve_tab = SolveTab(self)
        
        self.tabs.addTab(self.workspace_tab, "Workspace")
        self.tabs.addTab(self.parse_tab, "Parse")
        self.tabs.addTab(self.geocode_tab, "Geocode")
        self.tabs.addTab(self.cluster_tab, "Cluster")
        self.tabs.addTab(self.solve_tab, "Solve")
        
        # Connect workspace change signal to all tabs that need it
        self.workspace_tab.workspace_changed.connect(self.parse_tab.on_workspace_changed)
        self.workspace_tab.workspace_changed.connect(self.geocode_tab.on_workspace_changed)
        self.workspace_tab.workspace_changed.connect(self.cluster_tab.on_workspace_changed)
        self.workspace_tab.workspace_changed.connect(self.solve_tab.on_workspace_changed)
        
        # Connect workspace change signal to update path display
        self.workspace_tab.workspace_changed.connect(self.update_workspace_display)

        self._setup_statusbar()
    
    def update_workspace_display(self, workspace_path) -> None:
        """Update the workspace path display"""
        if workspace_path and workspace_path.exists():
            self.workspace_label.setText(f"Workspace: {workspace_path}")
        else:
            self.workspace_label.setText("Workspace: <not selected>")
    
    def _setup_statusbar(self) -> None:
        """Setup the status bar"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Ready")
