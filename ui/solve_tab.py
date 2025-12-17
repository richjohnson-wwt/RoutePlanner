"""
Solve Tab for VRPTW Application
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QRadioButton,
    QButtonGroup, QComboBox, QPushButton, QLineEdit, QTextEdit, QSizePolicy,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator

from services.solve_service import SolveService

class SolveTab(QWidget):
    """Solve tab for VRPTW optimization"""
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("SolveTab")
        
        # Store current workspace path and state
        self.current_workspace = None
        self.current_state = None
        self.problem_state = None
        
        # Initialize solve service
        self.solve_service = SolveService(time_limit_seconds=30)
        
        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)
        
        # Left side: Control panel
        left_panel = self._create_control_panel()
        main_layout.addWidget(left_panel)
        
        # Right side: Results area (placeholder for now)
        right_panel = self._create_results_panel()
        main_layout.addWidget(right_panel, stretch=1)
    
    def _create_control_panel(self) -> QWidget:
        """Create the left-side control panel with solver configuration"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Solve Mode Group
        mode_group = QGroupBox("Solve Mode")
        mode_layout = QVBoxLayout(mode_group)
        mode_layout.setContentsMargins(8, 8, 8, 8)
        mode_layout.setSpacing(8)
        
        self.per_cluster_radio = QRadioButton("Per Cluster")
        self.whole_state_radio = QRadioButton("Whole State (Ignore Clusters)")
        
        # Set Per Cluster as default
        self.per_cluster_radio.setChecked(True)
        
        # Button group for mutual exclusivity
        self.mode_button_group = QButtonGroup(self)
        self.mode_button_group.addButton(self.per_cluster_radio)
        self.mode_button_group.addButton(self.whole_state_radio)
        
        mode_layout.addWidget(self.per_cluster_radio)
        mode_layout.addWidget(self.whole_state_radio)
        
        layout.addWidget(mode_group)
        
        # Service Time Group
        service_group = QGroupBox("Service Time (hours)")
        service_layout = QVBoxLayout(service_group)
        service_layout.setContentsMargins(8, 8, 8, 8)
        
        self.service_time_combo = QComboBox()
        # Generate service times from 0.25 to 6.0 hours in 15-minute (0.25 hour) increments
        service_times = []
        time = 0.25
        while time <= 6.0:
            # Format as hours and minutes for clarity
            hours = int(time)
            minutes = int((time - hours) * 60)
            if minutes == 0:
                label = f"{hours}h 0m ({time:.2f})"
            else:
                label = f"{hours}h {minutes}m ({time:.2f})"
            service_times.append(label)
            time += 0.25
        
        self.service_time_combo.addItems(service_times)
        # Default to 0.5 hours (30 minutes) - index 1
        self.service_time_combo.setCurrentIndex(1)
        
        service_layout.addWidget(self.service_time_combo)
        layout.addWidget(service_group)
        
        # Average Speed Group
        speed_group = QGroupBox("Average Speed (MPH)")
        speed_layout = QVBoxLayout(speed_group)
        speed_layout.setContentsMargins(8, 8, 8, 8)
        
        self.speed_input = QLineEdit()
        self.speed_input.setText("50")
        self.speed_input.setPlaceholderText("Enter speed in MPH")
        
        # Validator to only allow positive numbers
        speed_validator = QDoubleValidator(1.0, 200.0, 1, self)
        speed_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.speed_input.setValidator(speed_validator)
        
        speed_layout.addWidget(self.speed_input)
        layout.addWidget(speed_group)
        
        # Solve Button
        self.solve_button = QPushButton("Solve VRPTW")
        self.solve_button.setMinimumHeight(40)
        self.solve_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 4px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.solve_button.clicked.connect(self._on_solve_clicked)
        layout.addWidget(self.solve_button)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        return panel
    
    def _create_results_panel(self) -> QWidget:
        """Create the right-side results panel with sub-tabs"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create tab widget for Solution Log and Solution View
        self.results_tabs = QTabWidget()
        self.results_tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Solution Log tab
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        log_layout.setContentsMargins(8, 8, 8, 8)
        
        self.solution_log = QTextEdit()
        self.solution_log.setReadOnly(True)
        self.solution_log.setPlaceholderText("Solution log will appear here...")
        self.solution_log.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        log_layout.addWidget(self.solution_log)
        
        self.results_tabs.addTab(log_widget, "Solution Log")
        
        # Solution View tab
        view_widget = QWidget()
        view_layout = QVBoxLayout(view_widget)
        view_layout.setContentsMargins(8, 8, 8, 8)
        
        # Solution table
        self.solution_table = QTableWidget()
        self.solution_table.setColumnCount(12)
        self.solution_table.setHorizontalHeaderLabels([
            "Route ID", "Stop Seq", "Site ID", "Cluster ID", "Vehicle ID",
            "Lat", "Lng", "Arrival Time", "Departure Time",
            "Service Time (min)", "Travel Time (min)", "Distance (mi)"
        ])
        self.solution_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.solution_table.horizontalHeader().setStretchLastSection(True)
        self.solution_table.setAlternatingRowColors(True)
        self.solution_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.solution_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        view_layout.addWidget(self.solution_table)
        
        self.results_tabs.addTab(view_widget, "Solution View")
        
        layout.addWidget(self.results_tabs)
        
        return panel
    
    def _on_solve_clicked(self) -> None:
        """Handle Solve button click"""
        if not self.problem_state:
            self.solution_log.setText("Error: No problem state available. Please select a workspace and state.")
            return
        
        # Get configuration values
        per_cluster = self.per_cluster_radio.isChecked()
        service_time_text = self.service_time_combo.currentText()
        # Extract the numeric value from the label (e.g., "0h 30m (0.50)" -> 0.50)
        service_time = float(service_time_text.split('(')[1].rstrip(')'))
        
        try:
            speed_mph = float(self.speed_input.text())
        except ValueError:
            self.solution_log.setText("Error: Invalid speed value. Please enter a valid number.")
            return
        
        # Switch to Solution Log tab
        self.results_tabs.setCurrentIndex(0)
        
        # Log the configuration
        mode = "Per Cluster" if per_cluster else "Whole State"
        log_text = f"""Starting VRPTW Solve...

Configuration:
- Mode: {mode}
- Service Time: {service_time} hours
- Average Speed: {speed_mph} MPH
- State: {self.problem_state.state_code}
- Client: {self.problem_state.client}
- Workspace: {self.problem_state.workspace}

"""
        self.solution_log.setText(log_text)
        
        # Callback to append log messages to results
        def log_callback(msg: str):
            current_text = self.solution_log.toPlainText()
            self.solution_log.setText(current_text + msg + "\n")
            # Force UI update
            self.solution_log.repaint()
        
        try:
            # Call solve service
            log_callback("Calling solve service...")
            routes = self.solve_service.solve_problem(
                problem=self.problem_state,
                per_cluster=per_cluster,
                service_time_hours=service_time,
                speed_mph=speed_mph,
                log_callback=log_callback
            )
            
            # Display results summary
            log_callback("\n" + "="*50)
            log_callback("SOLVE COMPLETE!")
            log_callback("="*50)
            log_callback(f"\nGenerated {len(routes)} route(s):")
            
            for i, route in enumerate(routes, 1):
                log_callback(f"\nRoute {i}:")
                log_callback(f"  - Cluster ID: {route.cluster_id}")
                log_callback(f"  - Stops: {route.stops}")
                log_callback(f"  - Service Hours: {route.service_hours:.2f}")
                log_callback(f"  - Sequence: {', '.join(route.sequence[:5])}{'...' if len(route.sequence) > 5 else ''}")
            
            log_callback(f"\nTotal stops across all routes: {sum(r.stops for r in routes)}")
            log_callback(f"Total service hours: {sum(r.service_hours for r in routes):.2f}")
            
            # Update solution table
            self._update_solution_table(routes)
            
        except Exception as e:
            import traceback
            log_callback(f"\nERROR: {str(e)}")
            log_callback(f"\nTraceback:\n{traceback.format_exc()}")
            log_callback("\nSolve failed. Please check the error message above.")
    
    def _update_solution_table(self, routes: list) -> None:
        """Update the solution table with stop-by-stop route data"""
        from datetime import datetime, timedelta
        import math
        
        # Calculate total number of stops across all routes
        total_stops = sum(len(route.sequence) for route in routes)
        self.solution_table.setRowCount(total_stops)
        
        current_row = 0
        
        for route_idx, route in enumerate(routes):
            route_id = route_idx + 1
            
            # Start time for this route (9:00 AM)
            current_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
            
            # Get service time in minutes (convert from hours)
            service_time_minutes = (route.service_hours / len(route.sequence)) * 60 if route.sequence else 0
            
            for stop_seq, site_id in enumerate(route.sequence):
                # Find the site in problem_state
                site = None
                if self.problem_state:
                    site = next((s for s in self.problem_state.sites if s.id == site_id), None)
                
                # Calculate travel time and distance to next stop
                travel_time_min = ""
                distance_miles = ""
                if stop_seq < len(route.sequence) - 1:
                    next_site_id = route.sequence[stop_seq + 1]
                    next_site = next((s for s in self.problem_state.sites if s.id == next_site_id), None) if self.problem_state else None
                    if site and next_site and site.lat and site.lng and next_site.lat and next_site.lng:
                        # Calculate distance using Haversine formula from solve_service
                        distance = self.solve_service._haversine_distance(site.lat, site.lng, next_site.lat, next_site.lng)
                        # Calculate travel time based on speed
                        travel_time = (distance / route.speed_mph) * 60  # Convert to minutes
                        travel_time_min = f"{travel_time:.2f}"
                        distance_miles = f"{distance:.2f}"
                
                # Route ID
                self.solution_table.setItem(current_row, 0, QTableWidgetItem(str(route_id)))
                
                # Stop Sequence
                self.solution_table.setItem(current_row, 1, QTableWidgetItem(str(stop_seq)))
                
                # Site ID
                self.solution_table.setItem(current_row, 2, QTableWidgetItem(site_id))
                
                # Cluster ID
                self.solution_table.setItem(current_row, 3, QTableWidgetItem(str(route.cluster_id)))
                
                # Vehicle ID
                self.solution_table.setItem(current_row, 4, QTableWidgetItem(str(route.vehicle_id)))
                
                # Lat/Lng
                if site:
                    self.solution_table.setItem(current_row, 5, QTableWidgetItem(f"{site.lat:.6f}" if site.lat else ""))
                    self.solution_table.setItem(current_row, 6, QTableWidgetItem(f"{site.lng:.6f}" if site.lng else ""))
                else:
                    self.solution_table.setItem(current_row, 5, QTableWidgetItem(""))
                    self.solution_table.setItem(current_row, 6, QTableWidgetItem(""))
                
                # Arrival Time
                arrival_time_str = current_time.strftime("%I:%M %p")
                self.solution_table.setItem(current_row, 7, QTableWidgetItem(arrival_time_str))
                
                # Departure Time (arrival + service time)
                departure_time = current_time + timedelta(minutes=service_time_minutes)
                departure_time_str = departure_time.strftime("%I:%M %p")
                self.solution_table.setItem(current_row, 8, QTableWidgetItem(departure_time_str))
                
                # Service Time (min)
                self.solution_table.setItem(current_row, 9, QTableWidgetItem(f"{service_time_minutes:.1f}"))
                
                # Travel Time (min)
                self.solution_table.setItem(current_row, 10, QTableWidgetItem(travel_time_min))
                
                # Distance (miles)
                self.solution_table.setItem(current_row, 11, QTableWidgetItem(distance_miles))
                
                # Update current time for next stop (add service time + travel time)
                if travel_time_min:
                    current_time = departure_time + timedelta(minutes=float(travel_time_min))
                else:
                    current_time = departure_time
                
                current_row += 1
        
        # Resize columns to content
        self.solution_table.resizeColumnsToContents()

    
    def _refresh_ui_from_state(self) -> None:
        """Refresh UI based on current problem state"""
        if self.problem_state:
            # Enable solve button if we have clustered data
            has_clusters = (
                self.problem_state.stage and 
                self.problem_state.stage.name in ["CLUSTERED", "SOLVED"]
            )
            self.solve_button.setEnabled(has_clusters)
            
            # If we have existing routes (from loaded solution.csv), display them
            if self.problem_state.routes:
                self._update_solution_table(self.problem_state.routes)
                self.solution_log.setText(
                    f"Loaded existing solution with {len(self.problem_state.routes)} route(s).\n"
                    f"Total stops: {sum(r.stops for r in self.problem_state.routes)}\n"
                    f"Total hours: {sum(r.service_hours for r in self.problem_state.routes):.2f}\n\n"
                    "Click 'Solve VRPTW' to generate a new solution."
                )
            elif not has_clusters:
                self.solution_log.setText(
                    "Please complete clustering before solving.\n"
                    "Go to the Cluster tab to cluster your sites first."
                )
    
    def _reset_ui(self) -> None:
        """Reset UI to empty state"""
        self.solution_log.clear()
        self.solution_table.setRowCount(0)
        self.solve_button.setEnabled(False)
    
    def set_problem_state(self, problem_state) -> None:
        """Set the problem state for this tab"""
        self.problem_state = problem_state
        self.setEnabled(problem_state is not None)
        
        if problem_state is None:
            self._reset_ui()
        else:
            self._refresh_ui_from_state()
