"""
Cluster Tab for VRPTW Application
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel
)
from PyQt6.QtCore import Qt


class ClusterTab(QWidget):
    """Cluster tab for clustering locations"""
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ClusterTab")
        
        # Store current workspace path and state
        self.current_workspace = None
        self.current_state = None
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        
        # Header
        header = QLabel("Cluster locations into groups")
        header.setStyleSheet("font-weight: 600;")
        header.setWordWrap(True)
        layout.addWidget(header)
        
        # Placeholder content
        placeholder = QLabel("Clustering functionality will be implemented here")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #7f8c8d;
                padding: 40px;
            }
        """)
        layout.addWidget(placeholder, stretch=1)
    
    def _refresh_ui_from_state(self) -> None:
        """Refresh UI based on current problem state"""
        pass
    
    def _reset_ui(self) -> None:
        """Reset UI to empty state"""
        pass
    
    def set_problem_state(self, problem_state) -> None:
        """Set the problem state for this tab"""
        self.problem_state = problem_state
        self.setEnabled(problem_state is not None)
        
        if problem_state is None:
            self._reset_ui()
        else:
            self._refresh_ui_from_state()
