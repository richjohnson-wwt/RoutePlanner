"""
Main Window for VRPTW Application
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout,
    QTabWidget, QStatusBar
)
from PyQt6.QtGui import QAction

from .workspace_tab import WorkspaceTab
from .parse_tab import ParseTab


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
        
        # Tabs
        self.tabs = QTabWidget()
        vbox.addWidget(self.tabs, 1)
        self.setCentralWidget(central)
        
        # Add tabs
        self.workspace_tab = WorkspaceTab(self)
        self.parse_tab = ParseTab(self)
        
        self.tabs.addTab(self.workspace_tab, "Workspace")
        self.tabs.addTab(self.parse_tab, "Parse")

        self._setup_statusbar()
    
    
    
    def _setup_statusbar(self) -> None:
        """Setup the status bar"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Ready")
