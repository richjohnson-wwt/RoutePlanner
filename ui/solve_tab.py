"""
Solve Tab for VRPTW Application
"""
from __future__ import annotations

import webbrowser
import tempfile
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QRadioButton,
    QButtonGroup, QComboBox, QPushButton, QLineEdit, QTextEdit, QSizePolicy,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator

try:
    import folium
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False

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
        
        # View On Map Button
        self.view_map_button = QPushButton("View On Map")
        self.view_map_button.setMinimumHeight(40)
        self.view_map_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 4px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.view_map_button.clicked.connect(self._on_view_map_clicked)
        self.view_map_button.setEnabled(False)  # Disabled until routes are available
        layout.addWidget(self.view_map_button)
        
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
            
            # Enable the View On Map button now that we have routes
            self.view_map_button.setEnabled(True)
            
        except Exception as e:
            import traceback
            log_callback(f"\nERROR: {str(e)}")
            log_callback(f"\nTraceback:\n{traceback.format_exc()}")
            log_callback("\nSolve failed. Please check the error message above.")
    
    def _on_view_map_clicked(self) -> None:
        """Handle View On Map button click - generate and display Folium map"""
        if not FOLIUM_AVAILABLE:
            self.solution_log.append("\nERROR: Folium library is not installed.")
            self.solution_log.append("Please install it with: pip install folium")
            return
        
        if not self.problem_state or not self.problem_state.routes:
            self.solution_log.append("\nNo routes available to display on map.")
            return
        
        try:
            self.solution_log.append("\nGenerating map...")
            
            # Create a map centered on the average location of all sites
            all_lats = []
            all_lngs = []
            
            # Collect all coordinates from sites in routes
            site_dict = {site.id: site for site in self.problem_state.sites}
            
            for route in self.problem_state.routes:
                for site_id in route.sequence:
                    site = site_dict.get(site_id)
                    if site and site.lat and site.lng:
                        all_lats.append(site.lat)
                        all_lngs.append(site.lng)
            
            if not all_lats or not all_lngs:
                self.solution_log.append("\nERROR: No valid coordinates found in routes.")
                return
            
            # Calculate center
            center_lat = sum(all_lats) / len(all_lats)
            center_lng = sum(all_lngs) / len(all_lngs)
            
            # Create map
            route_map = folium.Map(
                location=[center_lat, center_lng],
                zoom_start=7,
                tiles='OpenStreetMap'
            )
            
            # Define colors for different routes
            colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 
                     'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue', 
                     'darkpurple', 'pink', 'lightblue', 'lightgreen', 'gray', 
                     'black', 'lightgray']
            
            # Plot each route
            for route_idx, route in enumerate(self.problem_state.routes, 1):  # Start at 1 to match solution table
                color = colors[(route_idx - 1) % len(colors)]
                route_coords = []
                
                # Add markers and collect coordinates for route line
                for stop_idx, site_id in enumerate(route.sequence):
                    site = site_dict.get(site_id)
                    if not site or not site.lat or not site.lng:
                        continue
                    
                    route_coords.append([site.lat, site.lng])
                    
                    # Create popup with site information
                    popup_html = f"""
                    <div style="font-family: Arial; font-size: 12px;">
                        <b>Route {route_idx}</b><br>
                        <b>Stop {stop_idx + 1}</b> of {route.stops}<br>
                        <hr style="margin: 5px 0;">
                        <b>Site ID:</b> {site.id}<br>
                        <b>Address:</b> {site.address}<br>
                        <b>Cluster:</b> {route.cluster_id}<br>
                        <b>Coordinates:</b> {site.lat:.6f}, {site.lng:.6f}
                    </div>
                    """
                    
                    # Different icon for depot (first stop) vs regular stops
                    if stop_idx == 0:
                        icon = folium.Icon(color=color, icon='home', prefix='fa')
                    else:
                        icon = folium.Icon(color=color, icon='info-sign')
                    
                    folium.Marker(
                        location=[site.lat, site.lng],
                        popup=folium.Popup(popup_html, max_width=300),
                        tooltip=f"Route {route_idx} - Stop {stop_idx + 1}: {site.id}",
                        icon=icon
                    ).add_to(route_map)
                
                # Draw route line
                if len(route_coords) > 1:
                    folium.PolyLine(
                        route_coords,
                        color=color,
                        weight=3,
                        opacity=0.7,
                        popup=f"Route {route_idx} - {route.stops} stops, {route.service_hours:.2f} hours"
                    ).add_to(route_map)
            
            # Add a legend
            legend_html = f"""
            <div style="position: fixed; 
                        top: 10px; right: 10px; 
                        background-color: white; 
                        border: 2px solid grey; 
                        border-radius: 5px;
                        padding: 10px;
                        font-family: Arial;
                        font-size: 12px;
                        z-index: 9999;">
                <b>Route Summary</b><br>
                Total Routes: {len(self.problem_state.routes)}<br>
                Total Stops: {sum(r.stops for r in self.problem_state.routes)}<br>
                Total Hours: {sum(r.service_hours for r in self.problem_state.routes):.2f}<br>
                <hr style="margin: 5px 0;">
                <small>🏠 = Depot/Start</small>
            </div>
            """
            route_map.get_root().html.add_child(folium.Element(legend_html))
            
            # Save to workspace directory for persistence
            if self.problem_state.paths:
                # Use the workspace paths to get the route map path
                map_file = self.problem_state.paths.route_map_html()
            else:
                # Fallback to temp directory if paths not available
                temp_dir = Path(tempfile.gettempdir())
                map_file = temp_dir / f"route_map_{self.problem_state.state_code}.html"
            
            # Ensure directory exists
            map_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Save the map
            route_map.save(str(map_file))
            
            # Open in browser
            webbrowser.open(f"file://{map_file}")
            
            self.solution_log.append(f"Map saved to: {map_file}")
            self.solution_log.append("Map opened in browser.")
            
        except Exception as e:
            import traceback
            self.solution_log.append(f"\nERROR generating map: {str(e)}")
            self.solution_log.append(f"Traceback:\n{traceback.format_exc()}")
    
    def _update_solution_table(self, routes: list) -> None:
        """Update the solution table with stop-by-stop route data"""
        if not self.problem_state:
            return
        
        # Get table data from service (business logic layer)
        table_data = self.solve_service.generate_solution_table_data(self.problem_state, routes)
        
        # Set table row count
        self.solution_table.setRowCount(len(table_data))
        
        # Populate table with data (UI layer only)
        for row_idx, row_data in enumerate(table_data):
            for col_idx, value in enumerate(row_data):
                self.solution_table.setItem(row_idx, col_idx, QTableWidgetItem(value))
        
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
            
            # Enable view map button if we have routes
            has_routes = bool(self.problem_state.routes and len(self.problem_state.routes) > 0)
            self.view_map_button.setEnabled(has_routes)
            
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
        self.view_map_button.setEnabled(False)
    
    def set_problem_state(self, problem_state) -> None:
        """Set the problem state for this tab"""
        self.problem_state = problem_state
        self.setEnabled(problem_state is not None)
        
        if problem_state is None:
            self._reset_ui()
        else:
            self._refresh_ui_from_state()
