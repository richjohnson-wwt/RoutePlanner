"""
Geocode Tab for VRPTW Application
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel
)
from PyQt6.QtCore import Qt

from services.geocode_service import GeocodeService
from models.problem_state import ProblemState

class GeocodeTab(QWidget):
    """Geocode tab for geocoding addresses"""
    
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("GeocodeTab")
        
        self.problem_state: ProblemState | None = None

        self.service: GeocodeService | None = None
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        
        # Header
        header = QLabel("Geocode addresses to coordinates")
        header.setStyleSheet("font-weight: 600;")
        header.setWordWrap(True)
        layout.addWidget(header)
        
        # Placeholder content
        placeholder = QLabel("Geocoding functionality will be implemented here")
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

    def set_problem_state(self, state: ProblemState | None) -> None:
        self.problem_state = state
        self.setEnabled(state is not None)

        if state is None:
            self._reset_ui()
        else:
            self._refresh_ui_from_state()

    def on_run_geocode_clicked(self):
        assert self.problem_state is not None

        result = self.service.geocode(self.problem_state.sites)
        self.problem_state.geocoded = True
        self._refresh_ui_from_state()

    def set_service(self, service: GeocodeService) -> None:
        self.service = service
        