"""
Parse Tab for VRPTW Application
"""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QFileDialog,
    QTabWidget, QTextEdit, QSizePolicy, QListWidget,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt


class ParseTab(QWidget):
    """Parse tab for importing and parsing data"""
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ParseTab")
        
        # Store current workspace path
        self.current_workspace = None
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        
        # Header
        header = QLabel("Parse input data (Excel .xlsx orders)")
        header.setStyleSheet("font-weight: 600;")
        header.setWordWrap(True)
        layout.addWidget(header)
        
        # File picker row
        file_row = QHBoxLayout()
        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText("Select Excel .xlsx file...")
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.on_browse)
        file_row.addWidget(self.file_input, 1)
        file_row.addWidget(browse_btn)
        layout.addLayout(file_row)
        
        # Sheet selection row
        sheet_row = QHBoxLayout()
        sheet_label = QLabel("Sheet:")
        sheet_label.setMinimumWidth(80)
        sheet_row.addWidget(sheet_label)
        
        self.sheet_combo = QComboBox()
        self.sheet_combo.setEditable(False)
        self.sheet_combo.setEnabled(False)
        sheet_row.addWidget(self.sheet_combo, 1)
        
        layout.addLayout(sheet_row)
        
        # Config selection row
        config_row = QHBoxLayout()
        config_label = QLabel("Config:")
        config_label.setMinimumWidth(80)
        config_row.addWidget(config_label)
        
        self.config_combo = QComboBox()
        self.config_combo.setEditable(False)
        config_row.addWidget(self.config_combo, 1)
        
        layout.addLayout(config_row)
        
        # Populate config files
        self._populate_config_list()
        
        # Parse button row
        parse_row = QHBoxLayout()
        parse_row.addStretch(1)
        
        self.parse_btn = QPushButton("Parse")
        self.parse_btn.clicked.connect(self.on_parse)
        self.parse_btn.setEnabled(False)
        parse_row.addWidget(self.parse_btn)
        
        layout.addLayout(parse_row)
        
        # Sub-tabs: Parse Log and Parse View
        self.subtabs = QTabWidget()
        self.subtabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.subtabs.currentChanged.connect(self.on_subtab_changed)
        
        # Parse Log tab
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(200)
        self.log.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.log.setPlaceholderText("Logs will appear here...")
        self.subtabs.addTab(self.log, "Parse Log")
        
        # Parse View tab
        self.parse_view = QWidget()
        self._init_parse_view(self.parse_view)
        self.subtabs.addTab(self.parse_view, "Parse View")
        
        layout.addWidget(self.subtabs, 1)
    
    def _init_parse_view(self, container: QWidget) -> None:
        """Initialize the Parse View tab content"""
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
        left_layout.addWidget(self.state_list)
        
        left_panel.setMinimumWidth(150)
        left_panel.setMaximumWidth(250)
        view_layout.addWidget(left_panel)
        
        # Right side: Table view
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        table_label = QLabel("Addresses:")
        table_label.setStyleSheet("font-weight: 600;")
        right_layout.addWidget(table_label)
        
        self.state_table = QTableWidget()
        self.state_table.setAlternatingRowColors(True)
        self.state_table.setSortingEnabled(True)
        right_layout.addWidget(self.state_table)
        
        view_layout.addWidget(right_panel, stretch=1)
    
    def on_browse(self) -> None:
        """Handle browse button click to select Excel file"""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Excel .xlsx file",
            str(Path.home()),
            "Excel Files (*.xlsx);;All Files (*)",
        )
        if path:
            self.file_input.setText(path)
            self._populate_sheet_list(path)
    
    def _populate_sheet_list(self, path: str) -> None:
        """Populate the sheet dropdown with sheets from the Excel file"""
        self.sheet_combo.clear()
        self.sheet_combo.setEnabled(False)
        self.parse_btn.setEnabled(False)
        
        try:
            import pandas as pd
            
            xls = pd.ExcelFile(path, engine="openpyxl")
            sheets = xls.sheet_names
            
            if sheets:
                self.sheet_combo.addItems(sheets)
                self.sheet_combo.setEnabled(True)
                # Select first sheet by default
                self.sheet_combo.setCurrentIndex(0)
                # Enable Parse button now that file is loaded
                self.parse_btn.setEnabled(True)
        except Exception as e:
            # If pandas is not available or file can't be read, disable the combo
            self.sheet_combo.addItem(f"Error: {str(e)}")
            self.sheet_combo.setEnabled(False)
            self.parse_btn.setEnabled(False)
    
    def _populate_config_list(self) -> None:
        """Populate the config dropdown with available YAML config files"""
        self.config_combo.clear()
        
        # Get config directory
        config_dir = Path(__file__).parent.parent / "config"
        
        if not config_dir.exists():
            self.config_combo.addItem("<no configs>")
            self.config_combo.setEnabled(False)
            return
        
        # Find all .yaml files in config directory
        config_files = sorted(config_dir.glob("*.yaml"))
        
        if not config_files:
            self.config_combo.addItem("<no configs>")
            self.config_combo.setEnabled(False)
            return
        
        # Add config file names (without extension) to dropdown
        for config_file in config_files:
            self.config_combo.addItem(config_file.stem)
        
        self.config_combo.setEnabled(True)
        # Select first config by default
        if self.config_combo.count() > 0:
            self.config_combo.setCurrentIndex(0)
    
    def on_parse(self) -> None:
        """Handle parse button click"""
        from pathlib import Path
        from services.parse_service import ParseService
        
        # Clear the log
        self.log.clear()
        
        # Get the selected file and sheet
        excel_path = Path(self.file_input.text())
        sheet_name = self.sheet_combo.currentText()
        
        if not excel_path.exists():
            self.log.append("ERROR: Excel file not found")
            return
        
        if not sheet_name or sheet_name.startswith("Error:"):
            self.log.append("ERROR: No valid sheet selected")
            return
        
        # Get selected config file
        config_name = self.config_combo.currentText()
        
        if not config_name or config_name == "<no configs>":
            self.log.append("ERROR: No config file selected")
            return
        
        config_path = Path(__file__).parent.parent / "config" / f"{config_name}.yaml"
        
        if not config_path.exists():
            self.log.append(f"ERROR: Config file not found: {config_path}")
            return
        
        # Get output base path from current workspace
        output_base_path = self.current_workspace
        
        if not output_base_path:
            self.log.append("ERROR: No workspace selected. Please select a workspace first.")
            return
        
        self.log.append(f"Starting parse...")
        self.log.append(f"Config: {config_path.name}")
        self.log.append(f"Output: {output_base_path}")
        self.log.append("-" * 50)
        
        try:
            # Create parse service
            parse_service = ParseService(config_path)
            
            # Parse the Excel file
            state_counts = parse_service.parse_excel(
                excel_path=excel_path,
                sheet_name=sheet_name,
                output_base_path=output_base_path,
                log_callback=self.log.append
            )
            
            self.log.append("-" * 50)
            self.log.append("Parse completed successfully!")
            self.log.append(f"Total states processed: {len(state_counts)}")
            for state, count in sorted(state_counts.items()):
                self.log.append(f"  {state}: {count} rows")
                
        except Exception as e:
            self.log.append("-" * 50)
            self.log.append(f"ERROR: Parse failed: {str(e)}")
            import traceback
            self.log.append(traceback.format_exc())
        
        # Refresh the state list in Parse View after parsing
        self.refresh_state_list()
        
        # Notify control bar to refresh state dropdown
        if self.parent() and hasattr(self.parent(), 'control_bar'):
            self.parent().control_bar.refresh_states()
            # Update enabled state based on current tab
            current_tab_name = self.parent().tabs.tabText(self.parent().tabs.currentIndex())
            self.parent().control_bar.update_state_dropdown_for_tab(current_tab_name)
    
    def on_subtab_changed(self, index: int) -> None:
        """Handle sub-tab change to refresh Parse View when it becomes visible"""
        # Index 1 is the Parse View tab
        if index == 1:
            self.refresh_state_list()
    
    def on_workspace_changed(self, workspace_path) -> None:
        """Handle workspace change signal from WorkspaceTab"""
        # Store the workspace path
        self.current_workspace = workspace_path
        # Refresh the state list when workspace changes
        self.refresh_state_list()
    
    def refresh_state_list(self) -> None:
        """Refresh the state list in Parse View based on current workspace"""
        self.state_list.clear()
        
        # Use stored workspace path
        workspace_path = self.current_workspace
        
        if not workspace_path or not workspace_path.exists():
            return
        
        # Find all state directories
        try:
            states = []
            for p in sorted(workspace_path.iterdir()):
                if p.is_dir():
                    csv_path = p / "addresses.csv"
                    if csv_path.exists():
                        states.append(p.name)
            
            for state in states:
                self.state_list.addItem(state)
        except Exception:
            # Ignore filesystem errors
            pass
    
    def on_state_selected(self, state_code: str) -> None:
        """Handle state selection to display addresses.csv content"""
        if not state_code:
            self.clear_table()
            return
        
        # Use stored workspace path
        workspace_path = self.current_workspace
        
        if not workspace_path:
            self.clear_table()
            return
        
        csv_path = workspace_path / state_code / "addresses.csv"
        
        if not csv_path.exists():
            self.clear_table()
            return
        
        # Load and display CSV
        try:
            import pandas as pd
            
            df = pd.read_csv(csv_path)
            self.populate_table_from_dataframe(df)
        except Exception:
            # Fallback to csv module if pandas has an issue
            try:
                import csv
                
                with csv_path.open("r", encoding="utf-8", newline="") as f:
                    reader = csv.reader(f)
                    rows = list(reader)
                
                if not rows:
                    self.clear_table()
                    return
                
                headers = rows[0]
                data_rows = rows[1:]
                
                self.state_table.setColumnCount(len(headers))
                self.state_table.setHorizontalHeaderLabels(headers)
                self.state_table.setRowCount(len(data_rows))
                
                for r, row_vals in enumerate(data_rows):
                    for c, val in enumerate(row_vals):
                        self.state_table.setItem(r, c, QTableWidgetItem(str(val)))
                
                self._apply_table_column_sizing(headers)
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
        
        self._apply_table_column_sizing([str(h) for h in headers])
    
    def clear_table(self) -> None:
        """Clear the table widget"""
        self.state_table.clear()
        self.state_table.setColumnCount(0)
        self.state_table.setRowCount(0)
    
    def _apply_table_column_sizing(self, headers: list[str]) -> None:
        """Apply appropriate column sizing to the table"""
        header_view = self.state_table.horizontalHeader()
        header_view.setStretchLastSection(True)
        
        try:
            header_view.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        except Exception:
            pass
        
        # Set narrow fixed widths for specific columns
        name_to_index = {str(h).strip().lower(): i for i, h in enumerate(headers)}
        
        # State column (st or state)
        for state_col in ['st', 'state']:
            if state_col in name_to_index:
                idx = name_to_index[state_col]
                try:
                    header_view.setSectionResizeMode(idx, QHeaderView.ResizeMode.Interactive)
                except Exception:
                    pass
                self.state_table.setColumnWidth(idx, 50)
        
        # Zip column
        if 'zip' in name_to_index:
            idx = name_to_index['zip']
            try:
                header_view.setSectionResizeMode(idx, QHeaderView.ResizeMode.Interactive)
            except Exception:
                pass
            self.state_table.setColumnWidth(idx, 70)
