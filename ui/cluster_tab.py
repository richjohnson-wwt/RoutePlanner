"""
Cluster Tab for VRPTW Application
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QRadioButton, 
    QButtonGroup, QComboBox, QPushButton, QTabWidget, QTableWidget, QTableWidgetItem, 
    QSizePolicy, QTextEdit
)
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt


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
        
        # Top row: Clustering controls
        top_layout = QHBoxLayout()
        
        # Clustering mode selector (left)
        mode_group = QGroupBox("Clustering Mode")
        mode_layout = QHBoxLayout(mode_group)
        mode_layout.setContentsMargins(8, 8, 8, 8)
        mode_layout.setSpacing(10)
        
        # Radio buttons
        self.auto_k_radio = QRadioButton("Auto K")
        self.manual_radio = QRadioButton("Manual")
        
        # Set Auto K as default
        self.auto_k_radio.setChecked(True)
        
        # Button group to manage mutual exclusivity
        self.mode_button_group = QButtonGroup(self)
        self.mode_button_group.addButton(self.auto_k_radio)
        self.mode_button_group.addButton(self.manual_radio)
        
        mode_layout.addWidget(self.auto_k_radio)
        mode_layout.addWidget(self.manual_radio)
        
        top_layout.addWidget(mode_group)
        
        # Number of clusters dropdown (middle)
        clusters_group = QGroupBox("Number of Clusters")
        clusters_layout = QHBoxLayout(clusters_group)
        clusters_layout.setContentsMargins(8, 8, 8, 8)
        
        self.num_clusters_combo = QComboBox()
        self.num_clusters_combo.addItems([str(i) for i in range(2, 21)])  # 2 to 20 clusters
        self.num_clusters_combo.setCurrentText("5")  # Default to 5
        
        clusters_layout.addWidget(self.num_clusters_combo)
        
        top_layout.addWidget(clusters_group)
        
        # Cluster button (right)
        self.cluster_button = QPushButton("Cluster")
        self.cluster_button.setMinimumWidth(100)
        self.cluster_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: 600;
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
        
        top_layout.addWidget(self.cluster_button)
        
        # Spacer to push everything to the left
        top_layout.addStretch()
        
        layout.addLayout(top_layout)
        
        # Connect radio buttons to enable/disable number of clusters dropdown
        self.auto_k_radio.toggled.connect(self._on_clustering_mode_changed)
        self.manual_radio.toggled.connect(self._on_clustering_mode_changed)
        
        # Connect Cluster button to clustering logic
        self.cluster_button.clicked.connect(self._on_cluster_clicked)
        
        # Set initial state (disable dropdown when Auto K is selected)
        self._on_clustering_mode_changed()
        
        # Sub-tab widget for Map, Sites, and ClusterLog views
        self.sub_tabs = QTabWidget()
        self.sub_tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Map tab - matplotlib canvas for visualizing clusters
        self.map_widget = QWidget()
        map_layout = QVBoxLayout(self.map_widget)
        map_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create matplotlib figure and canvas
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_xlabel('Longitude')
        self.ax.set_ylabel('Latitude')
        self.ax.set_title('Cluster Map')
        self.ax.grid(True, alpha=0.3)
        
        map_layout.addWidget(self.canvas)
        
        # Sites tab - table view of sites with cluster assignments
        self.sites_widget = QWidget()
        sites_layout = QVBoxLayout(self.sites_widget)
        sites_layout.setContentsMargins(0, 0, 0, 0)
        
        self.sites_table = QTableWidget()
        self.sites_table.setColumnCount(6)
        self.sites_table.setHorizontalHeaderLabels([
            'Site ID', 'Address', 'State', 'Latitude', 'Longitude', 'Cluster ID'
        ])
        self.sites_table.horizontalHeader().setStretchLastSection(False)
        self.sites_table.setAlternatingRowColors(True)
        
        sites_layout.addWidget(self.sites_table)
        
        # ClusterLog tab - text log for clustering progress
        self.log_widget = QWidget()
        log_layout = QVBoxLayout(self.log_widget)
        log_layout.setContentsMargins(0, 0, 0, 0)
        
        self.cluster_log = QTextEdit()
        self.cluster_log.setReadOnly(True)
        self.cluster_log.setMinimumHeight(200)
        self.cluster_log.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        log_layout.addWidget(self.cluster_log)
        
        # Add tabs to sub-tab widget
        self.sub_tabs.addTab(self.map_widget, "Map")
        self.sub_tabs.addTab(self.sites_widget, "Sites")
        self.sub_tabs.addTab(self.log_widget, "ClusterLog")
        
        layout.addWidget(self.sub_tabs, stretch=1)
    
    def _on_clustering_mode_changed(self) -> None:
        """Handle clustering mode radio button changes"""
        # Enable dropdown only when Manual mode is selected
        is_manual = self.manual_radio.isChecked()
        self.num_clusters_combo.setEnabled(is_manual)
    
    def _on_cluster_clicked(self) -> None:
        """Handle Cluster button click"""
        if not self.problem_state or not self.problem_state.sites:
            return
        
        # Clear previous log
        self.cluster_log.clear()
        
        # Switch to ClusterLog tab to show progress
        self.sub_tabs.setCurrentWidget(self.log_widget)
        
        # Determine clustering parameters from UI
        selection = "manual" if self.manual_radio.isChecked() else "auto"
        k = int(self.num_clusters_combo.currentText()) if selection == "manual" else None
        
        def log_message(msg: str):
            """Append message to cluster log"""
            self.cluster_log.append(msg)
        
        try:
            # Disable button during clustering
            self.cluster_button.setEnabled(False)
            self.cluster_button.setText("Clustering...")
            
            log_message(f"Starting clustering in {selection} mode...")
            if selection == "manual":
                log_message(f"Using K={k} clusters")
            
            # Perform clustering
            from services.cluster_service import ClusterService
            service = ClusterService(algorithm="kmeans", seed=42)
            
            service.cluster_problem(
                problem=self.problem_state,
                k=k,
                selection=selection,
                log_callback=log_message
            )
            
            # Update visualizations
            log_message("Updating visualizations...")
            self._update_map()
            self._update_sites_table()
            
            log_message("✓ Clustering complete!")
            self.cluster_button.setText("Cluster")
            
        except Exception as e:
            # Show error message
            log_message(f"✗ Error: {str(e)}")
            self.cluster_button.setText("Cluster")
        
        finally:
            # Re-enable button
            self.cluster_button.setEnabled(True)
    
    def _refresh_ui_from_state(self) -> None:
        """Refresh UI based on current problem state"""
        if self.problem_state and self.problem_state.sites:
            self._update_map()
            self._update_sites_table()
    
    def _reset_ui(self) -> None:
        """Reset UI to empty state"""
        # Clear map
        self.ax.clear()
        self.ax.set_xlabel('Longitude')
        self.ax.set_ylabel('Latitude')
        self.ax.set_title('Cluster Map')
        self.ax.grid(True, alpha=0.3)
        self.canvas.draw()
        
        # Clear sites table
        self.sites_table.setRowCount(0)
        
        # Clear cluster log
        self.cluster_log.clear()
    
    def _update_map(self) -> None:
        """Update the map visualization with current sites"""
        if not self.problem_state or not self.problem_state.sites:
            return
        
        # Clear previous plot
        self.ax.clear()
        
        # Separate sites by cluster (if clustered) or plot all together
        sites_with_coords = [s for s in self.problem_state.sites if s.lat is not None and s.lng is not None]
        
        if not sites_with_coords:
            self.ax.text(0.5, 0.5, 'No geocoded sites to display', 
                        ha='center', va='center', transform=self.ax.transAxes,
                        fontsize=12, color='gray')
        else:
            # Check if sites have cluster assignments
            has_clusters = any(s.cluster_id is not None for s in sites_with_coords)
            
            if has_clusters:
                # Plot sites colored by cluster
                clusters = {}
                for site in sites_with_coords:
                    cluster_id = site.cluster_id if site.cluster_id is not None else -1
                    if cluster_id not in clusters:
                        clusters[cluster_id] = []
                    clusters[cluster_id].append(site)
                
                # Use different colors for each cluster
                colors = plt.cm.tab10(range(len(clusters)))
                
                for idx, (cluster_id, sites) in enumerate(sorted(clusters.items())):
                    lats = [s.lat for s in sites]
                    lngs = [s.lng for s in sites]
                    label = f'Cluster {cluster_id}' if cluster_id >= 0 else 'Unclustered'
                    self.ax.scatter(lngs, lats, c=[colors[idx]], label=label, s=100, alpha=0.6, edgecolors='black')
                
                self.ax.legend(loc='best')
            else:
                # Plot all sites in single color (not yet clustered)
                lats = [s.lat for s in sites_with_coords]
                lngs = [s.lng for s in sites_with_coords]
                self.ax.scatter(lngs, lats, c='blue', s=100, alpha=0.6, edgecolors='black', label='Sites')
                self.ax.legend(loc='best')
        
        self.ax.set_xlabel('Longitude')
        self.ax.set_ylabel('Latitude')
        self.ax.set_title('Cluster Map')
        self.ax.grid(True, alpha=0.3)
        self.canvas.draw()
    
    def _update_sites_table(self) -> None:
        """Update the sites table with current site data"""
        if not self.problem_state or not self.problem_state.sites:
            self.sites_table.setRowCount(0)
            return
        
        sites = self.problem_state.sites
        self.sites_table.setRowCount(len(sites))
        
        for row, site in enumerate(sites):
            # Site ID
            self.sites_table.setItem(row, 0, QTableWidgetItem(site.id))
            
            # Address
            self.sites_table.setItem(row, 1, QTableWidgetItem(site.address))
            
            # State
            self.sites_table.setItem(row, 2, QTableWidgetItem(site.state_code))
            
            # Latitude
            lat_str = f"{site.lat:.6f}" if site.lat is not None else "N/A"
            self.sites_table.setItem(row, 3, QTableWidgetItem(lat_str))
            
            # Longitude
            lng_str = f"{site.lng:.6f}" if site.lng is not None else "N/A"
            self.sites_table.setItem(row, 4, QTableWidgetItem(lng_str))
            
            # Cluster ID
            cluster_str = str(site.cluster_id) if site.cluster_id is not None else "N/A"
            self.sites_table.setItem(row, 5, QTableWidgetItem(cluster_str))
        
        # Resize columns to content
        self.sites_table.resizeColumnsToContents()
    
    def set_problem_state(self, problem_state) -> None:
        """Set the problem state for this tab"""
        self.problem_state = problem_state
        self.setEnabled(problem_state is not None)
        
        if problem_state is None:
            self._reset_ui()
        else:
            self._refresh_ui_from_state()
