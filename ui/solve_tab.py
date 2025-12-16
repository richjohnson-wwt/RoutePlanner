"""
Solve Tab for VRPTW Application
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel
)
from PyQt6.QtCore import Qt


class SolveTab(QWidget):
    """Solve tab for VRPTW optimization"""
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("SolveTab")
        
        # Store current workspace path
        self.current_workspace = None
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        
        # Header
        header = QLabel("Solve VRPTW optimization problem")
        header.setStyleSheet("font-weight: 600;")
        header.setWordWrap(True)
        layout.addWidget(header)
        
        # Placeholder content
        placeholder = QLabel("VRPTW solving functionality will be implemented here")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #7f8c8d;
                padding: 40px;
            }
        """)
        layout.addWidget(placeholder, stretch=1)
    
    def on_workspace_changed(self, workspace_path) -> None:
        """Handle workspace change signal from WorkspaceTab"""
        self.current_workspace = workspace_path
        # TODO: Refresh solve view when workspace changes
