"""
Geocode Tab for VRPTW Application
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTabWidget, QTextEdit,
    QSizePolicy, QListWidget, QTableWidget, QTableWidgetItem,
    QHeaderView
)
from PyQt6.QtCore import Qt, QSettings

from services.geocode_service import GeocodeService
from models.problem_state import ProblemState

class GeocodeTab(QWidget):
    """Geocode tab for geocoding addresses"""
    
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("GeocodeTab")
        
        self.problem_state: ProblemState | None = None
        self.service: GeocodeService | None = None
        self.settings = QSettings("RoutePlanner", "VRPTW")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        
        # Header
        header = QLabel("Geocode addresses to coordinates")
        header.setStyleSheet("font-weight: 600;")
        header.setWordWrap(True)
        layout.addWidget(header)
        
        # Email input row (for Nominatim)
        email_row = QHBoxLayout()
        email_label = QLabel("Email (Nominatim):")
        email_label.setMinimumWidth(120)
        email_row.addWidget(email_label)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("your.email@example.com")
        # Load saved email from settings
        saved_email = self.settings.value("nominatim_email", "")
        if saved_email:
            self.email_input.setText(saved_email)
        # Save email when it changes
        self.email_input.textChanged.connect(self._on_email_changed)
        email_row.addWidget(self.email_input, 1)
        
        layout.addLayout(email_row)
        
        # Geocode button row
        button_row = QHBoxLayout()
        button_row.addStretch(1)
        
        self.geocode_btn = QPushButton("Geocode")
        self.geocode_btn.clicked.connect(self.on_geocode_clicked)
        self.geocode_btn.setEnabled(False)
        button_row.addWidget(self.geocode_btn)
        
        layout.addLayout(button_row)
        
        # Sub-tabs: Geocode Log and Geocode View
        self.subtabs = QTabWidget()
        self.subtabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Geocode Log tab
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(200)
        self.log.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.log.setPlaceholderText("Geocoding logs will appear here...")
        self.subtabs.addTab(self.log, "Geocode Log")
        
        # Geocode View tab
        self.geocode_view = QWidget()
        self._init_geocode_view(self.geocode_view)
        self.subtabs.addTab(self.geocode_view, "Geocode View")
        
        layout.addWidget(self.subtabs, 1)

    def _init_geocode_view(self, container: QWidget) -> None:
        """Initialize the Geocode View tab content"""
        view_layout = QHBoxLayout(container)
        view_layout.setContentsMargins(6, 6, 6, 6)
        view_layout.setSpacing(6)
        
        # Left side: State list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        state_label = QLabel("States:")
        state_label.setStyleSheet("font-weight: 600;")
        left_layout.addWidget(state_label)
        
        self.state_list = QListWidget()
        self.state_list.currentTextChanged.connect(self.on_state_selected)
        left_layout.addWidget(self.state_list, 1)
        
        left_panel.setMaximumWidth(150)
        view_layout.addWidget(left_panel)
        
        # Right side: Table view
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        table_label = QLabel("Geocoded Sites:")
        table_label.setStyleSheet("font-weight: 600;")
        right_layout.addWidget(table_label)
        
        self.state_table = QTableWidget()
        self.state_table.setAlternatingRowColors(True)
        self.state_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.state_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        right_layout.addWidget(self.state_table, 1)
        
        view_layout.addWidget(right_panel, 1)

    def _on_email_changed(self, text: str) -> None:
        """Save email to settings when it changes"""
        self.settings.setValue("nominatim_email", text)

    def _refresh_ui_from_state(self) -> None:
        """Refresh UI based on current problem state"""
        if self.problem_state:
            self.geocode_btn.setEnabled(True)
            self.refresh_state_list()
        else:
            self.geocode_btn.setEnabled(False)
    
    def _reset_ui(self) -> None:
        """Reset UI to empty state"""
        self.geocode_btn.setEnabled(False)
        self.state_list.clear()
        self.clear_table()

    def set_problem_state(self, state: ProblemState | None) -> None:
        self.problem_state = state
        self.setEnabled(state is not None)

        if state is None:
            self._reset_ui()
        else:
            self._refresh_ui_from_state()

    def on_geocode_clicked(self) -> None:
        """Handle geocode button click"""
        if not self.problem_state:
            self.log.append("ERROR: No problem state loaded")
            return
        
        if not self.service:
            self.log.append("ERROR: Geocode service not initialized")
            return
        
        self.log.clear()
        self.log.append("Starting geocoding...")
        self.log.append(f"Geocoder: {self.service.geocoder_name}")
        self.log.append(f"Sites to geocode: {len(self.problem_state.sites)}")
        self.log.append("-" * 50)
        
        # Create a log callback that forces UI updates in real-time
        from PyQt6.QtCore import QCoreApplication
        def log_with_update(msg: str):
            self.log.append(msg)
            # Force Qt to process events so the log appears immediately
            QCoreApplication.processEvents()
        
        try:
            # Run the geocoding service with real-time log callback
            self.service.geocode_problem(self.problem_state, log_callback=log_with_update)
            
            self.log.append("-" * 50)
            self.log.append("Geocoding completed successfully!")
            self.log.append(f"Geocoded {len(self.problem_state.sites)} sites")
            
            # Refresh the view
            self._refresh_ui_from_state()
            
        except Exception as e:
            self.log.append("-" * 50)
            self.log.append(f"ERROR: Geocoding failed: {str(e)}")
            import traceback
            self.log.append(traceback.format_exc())

    def set_service(self, service: GeocodeService) -> None:
        self.service = service

    def refresh_state_list(self) -> None:
        """Refresh the state list in Geocode View based on current workspace"""
        self.state_list.clear()
        
        if not self.problem_state or not self.problem_state.paths:
            return
        
        try:
            # Get the parent directory (workspace level)
            workspace_dir = self.problem_state.paths.root.parent
            
            if workspace_dir.exists():
                states = []
                for p in workspace_dir.iterdir():
                    # Accept any directory (not just 2-letter codes)
                    # to support both full state names and state codes
                    if p.is_dir():
                        # Check if geocoded.csv exists
                        geocoded_csv = p / "geocoded.csv"
                        if geocoded_csv.exists():
                            states.append(p.name)
                
                for state in sorted(states):
                    self.state_list.addItem(state)
        except Exception:
            # Ignore filesystem errors
            pass

    def on_state_selected(self, state_code: str) -> None:
        """Handle state selection to display geocoded.csv content"""
        if not state_code or not self.problem_state or not self.problem_state.paths:
            self.clear_table()
            return
        
        # Get workspace directory
        workspace_dir = self.problem_state.paths.root.parent
        csv_path = workspace_dir / state_code / "geocoded.csv"
        
        if not csv_path.exists():
            self.clear_table()
            return
        
        # Load and display CSV
        try:
            import pandas as pd
            
            df = pd.read_csv(csv_path)
            self.populate_table_from_dataframe(df)
        except Exception:
            self.clear_table()

    def populate_table_from_dataframe(self, df) -> None:
        """Populate the table widget from a pandas DataFrame"""
        headers = list(df.columns)
        self.state_table.setColumnCount(len(headers))
        self.state_table.setHorizontalHeaderLabels([str(h) for h in headers])
        self.state_table.setRowCount(len(df))
        
        for r, (_, row) in enumerate(df.iterrows()):
            for c, h in enumerate(headers):
                self.state_table.setItem(r, c, QTableWidgetItem(str(row[h])))
        
        # Apply column sizing
        header_view = self.state_table.horizontalHeader()
        header_view.setStretchLastSection(True)
        try:
            header_view.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        except Exception:
            pass

    def clear_table(self) -> None:
        """Clear the table widget"""
        self.state_table.clear()
        self.state_table.setColumnCount(0)
        self.state_table.setRowCount(0)
        