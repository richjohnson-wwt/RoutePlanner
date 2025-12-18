"""
Control Bar for VRPTW Application
Contains Client, Workspace, and State selection controls
"""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QComboBox, 
    QPushButton, QInputDialog, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QSettings

DEFAULT_BASE = Path.home() / "Documents" / "RoutePlanner"


class ControlBar(QWidget):
    """Control bar with client, workspace, and state selection"""
    
    # Signals
    workspace_changed = pyqtSignal(object)  # Emits workspace Path or None
    state_changed = pyqtSignal(str)  # Emits state code
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ControlBar")
        
        self.base_path = DEFAULT_BASE
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize QSettings for persistence
        self.settings = QSettings("RoutePlanner", "VRPTW")
        
        # Create main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
        
        # Client group
        client_group = QGroupBox("Client")
        client_layout = QHBoxLayout()
        client_layout.setContentsMargins(8, 8, 8, 8)
        
        self.client_combo = QComboBox()
        self.client_combo.setMinimumWidth(150)
        # Signal connection moved to after restoration
        client_layout.addWidget(self.client_combo)
        
        new_client_btn = QPushButton("New...")
        new_client_btn.setMaximumWidth(60)
        new_client_btn.clicked.connect(self.on_new_client)
        client_layout.addWidget(new_client_btn)
        
        client_group.setLayout(client_layout)
        layout.addWidget(client_group)
        
        # Workspace group
        workspace_group = QGroupBox("Workspace")
        workspace_layout = QHBoxLayout()
        workspace_layout.setContentsMargins(8, 8, 8, 8)
        
        self.workspace_combo = QComboBox()
        self.workspace_combo.setMinimumWidth(150)
        # Signal connection moved to after restoration
        workspace_layout.addWidget(self.workspace_combo)
        
        new_workspace_btn = QPushButton("New...")
        new_workspace_btn.setMaximumWidth(60)
        new_workspace_btn.clicked.connect(self.on_new_workspace)
        workspace_layout.addWidget(new_workspace_btn)
        
        workspace_group.setLayout(workspace_layout)
        layout.addWidget(workspace_group)
        
        # State group
        state_group = QGroupBox("State")
        state_layout = QHBoxLayout()
        state_layout.setContentsMargins(8, 8, 8, 8)
        
        self.state_combo = QComboBox()
        self.state_combo.setMinimumWidth(100)
        self.state_combo.setEnabled(False)
        self.state_combo.currentTextChanged.connect(self.on_state_changed)
        state_layout.addWidget(self.state_combo)
        
        state_group.setLayout(state_layout)
        layout.addWidget(state_group)
        
        layout.addStretch(1)
        
        # Initialize
        self.refresh_clients()
        self._update_controls_enabled()
        self._restore_selections()
        
        # Connect signals AFTER restoration to prevent overwriting saved settings
        self.client_combo.currentIndexChanged.connect(self.on_client_changed)
        self.workspace_combo.currentIndexChanged.connect(self.on_workspace_changed)
        self.state_combo.currentTextChanged.connect(self.on_state_changed)
        
        # Emit initial signals
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, self.emit_initial_signals)
    
    def list_clients(self) -> list[str]:
        """List all client directories"""
        if not self.base_path.exists():
            return []
        return sorted([p.name for p in self.base_path.iterdir() if p.is_dir()])
    
    def list_workspaces(self, client: str) -> list[str]:
        """List all workspace directories for a given client"""
        client_dir = self.base_path / client
        if not client_dir.exists():
            return []
        return sorted([p.name for p in client_dir.iterdir() if p.is_dir()])
    
    def list_states(self) -> list[str]:
        """List all states with addresses.csv in current workspace"""
        workspace_path = self.current_workspace_path()
        print(f"DEBUG list_states: workspace_path = {workspace_path}")
        if not workspace_path or not workspace_path.exists():
            print(f"DEBUG list_states: workspace_path doesn't exist or is None")
            return []
        
        states = []
        try:
            print(f"DEBUG list_states: Scanning {workspace_path} for state directories...")
            for p in sorted(workspace_path.iterdir()):
                print(f"DEBUG list_states:   Found: {p.name} (is_dir={p.is_dir()})")
                if p.is_dir():
                    csv_path = p / "addresses.csv"
                    print(f"DEBUG list_states:     Checking {csv_path} exists: {csv_path.exists()}")
                    if csv_path.exists():
                        states.append(p.name)
                        print(f"DEBUG list_states:     Added state: {p.name}")
        except Exception as e:
            print(f"DEBUG list_states: Exception: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"DEBUG list_states: Found {len(states)} states: {states}")
        return states
    
    def refresh_clients(self) -> None:
        """Refresh the client dropdown"""
        current = self.client_combo.currentText()
        self.client_combo.clear()
        clients = self.list_clients()
        if not clients:
            self.client_combo.addItem("<no clients>")
            self.client_combo.setEnabled(True)
        else:
            self.client_combo.addItems(clients)
            if current and current in clients:
                self.client_combo.setCurrentText(current)
    
    def refresh_workspaces(self) -> None:
        """Refresh the workspace dropdown for the selected client"""
        self.workspace_combo.clear()
        client = self.client_combo.currentText()
        if not client or client == "<no clients>":
            self.workspace_combo.addItem("<no workspaces>")
            self.workspace_combo.setEnabled(False)
            return
        
        workspaces = self.list_workspaces(client)
        if not workspaces:
            self.workspace_combo.addItem("<no workspaces>")
            self.workspace_combo.setEnabled(True)
        else:
            self.workspace_combo.addItems(workspaces)
            self.workspace_combo.setEnabled(True)
    
    def refresh_states(self) -> None:
        """Refresh the state dropdown based on current workspace"""
        print(f"DEBUG refresh_states: Called")
        self.state_combo.clear()
        states = self.list_states()
        print(f"DEBUG refresh_states: list_states returned {len(states)} states: {states}")
        
        if not states:
            print(f"DEBUG refresh_states: No states found, adding '<no states>' and disabling")
            self.state_combo.addItem("<no states>")
            self.state_combo.setEnabled(False)
        else:
            print(f"DEBUG refresh_states: Adding {len(states)} states to dropdown")
            self.state_combo.addItems(states)
            # Keep current enabled state - let update_state_dropdown_for_tab control it
            # Don't force disable here as it prevents enabling when switching tabs
            print(f"DEBUG refresh_states: Dropdown now has {self.state_combo.count()} items")
    
    def update_state_dropdown_for_tab(self, tab_name: str) -> None:
        """Update state dropdown enabled state based on current tab"""
        print(f"DEBUG update_state_dropdown_for_tab: tab_name='{tab_name}'")
        
        # State dropdown is disabled on Parse tab
        if tab_name == "Parse":
            self.state_combo.setEnabled(False)
            return
        
        # On other tabs, refresh states to ensure we have the latest list
        # This fixes timing issues where files might not be written yet after parsing
        self.refresh_states()
        
        # Enable if there are states available
        has_states = self.state_combo.count() > 0 and self.state_combo.itemText(0) != "<no states>"
        self.state_combo.setEnabled(has_states)
        print(f"DEBUG update_state_dropdown_for_tab: has_states={has_states}, enabled={has_states}")
    
    def _save_selections(self) -> None:
        """Save current selections to QSettings"""
        client = self.client_combo.currentText()
        workspace = self.workspace_combo.currentText()
        state = self.state_combo.currentText()
        
        if client and client != "<no clients>":
            self.settings.setValue("last_client", client)
        if workspace and workspace != "<no workspaces>":
            self.settings.setValue("last_workspace", workspace)
        if state and state != "<no states>":
            self.settings.setValue("last_state", state)
    
    def _restore_selections(self) -> None:
        """Restore selections from QSettings"""
        # Block signals during restoration to prevent premature saves
        self.client_combo.blockSignals(True)
        self.workspace_combo.blockSignals(True)
        self.state_combo.blockSignals(True)
        
        # Restore client
        last_client = self.settings.value("last_client", "")
        if last_client:
            index = self.client_combo.findText(last_client)
            if index >= 0:
                self.client_combo.setCurrentIndex(index)
                # Manually refresh workspaces for the restored client
                self.refresh_workspaces()
        
        # Restore workspace
        last_workspace = self.settings.value("last_workspace", "")
        if last_workspace:
            index = self.workspace_combo.findText(last_workspace)
            if index >= 0:
                self.workspace_combo.setCurrentIndex(index)
                # Manually refresh states for the restored workspace
                self.refresh_states()
        
        # Restore state
        last_state = self.settings.value("last_state", "")
        if last_state:
            index = self.state_combo.findText(last_state)
            if index >= 0:
                self.state_combo.setCurrentIndex(index)
        
        # Re-enable signals
        self.client_combo.blockSignals(False)
        self.workspace_combo.blockSignals(False)
        self.state_combo.blockSignals(False)
        
        # Update controls enabled state
        self._update_controls_enabled()
    
    def _update_controls_enabled(self) -> None:
        """Update enabled state of controls based on selections"""
        has_client = self.client_combo.currentText() not in ("", "<no clients>")
        self.workspace_combo.setEnabled(has_client)
    
    def on_client_changed(self) -> None:
        """Handle client selection change"""
        self.refresh_workspaces()
        self._update_controls_enabled()
        self._save_selections()
    
    def on_workspace_changed(self) -> None:
        """Handle workspace selection change and emit signal"""
        workspace_path = self.current_workspace_path()
        self.workspace_changed.emit(workspace_path)
        self.refresh_states()
        self._save_selections()
    
    def on_state_changed(self, state_code: str) -> None:
        """Handle state selection change and emit signal"""
        if state_code and state_code != "<no states>":
            self.state_changed.emit(state_code)
            self._save_selections()
    
    def emit_initial_signals(self) -> None:
        """Emit initial signals on startup"""
        workspace_path = self.current_workspace_path()
        self.workspace_changed.emit(workspace_path)
        
        state_code = self.state_combo.currentText()
        if state_code and state_code != "<no states>":
            self.state_changed.emit(state_code)
    
    def on_new_client(self) -> None:
        """Handle new client button click"""
        name, ok = QInputDialog.getText(self, "New Client", "Client name (e.g., JITB):")
        name = name.strip()
        if not ok or not name:
            return
        
        safe = self._sanitize_name(name)
        client_dir = self.base_path / safe
        
        if not client_dir.exists():
            client_dir.mkdir(parents=True, exist_ok=True)
        
        self.refresh_clients()
        self.client_combo.setCurrentText(safe)
        self.refresh_workspaces()
        self._update_controls_enabled()
    
    def on_new_workspace(self) -> None:
        """Handle new workspace button click"""
        client = self.client_combo.currentText()
        if not client or client == "<no clients>":
            return
        
        name, ok = QInputDialog.getText(self, "New Workspace", "Workspace name (e.g., Phones):")
        name = name.strip()
        if not ok or not name:
            return
        
        safe = self._sanitize_name(name)
        ws_dir = self.base_path / client / safe
        
        if not ws_dir.exists():
            ws_dir.mkdir(parents=True, exist_ok=True)
        
        self.refresh_workspaces()
        self.workspace_combo.setCurrentText(safe)
        self._update_controls_enabled()
    
    def current_workspace_path(self) -> Path | None:
        """Get the current workspace path if valid selections are made"""
        client = self.client_combo.currentText()
        workspace = self.workspace_combo.currentText()
        
        print(f"DEBUG current_workspace_path: client='{client}', workspace='{workspace}'")
        
        if (not client or client == "<no clients>") or (not workspace or workspace == "<no workspaces>"):
            print(f"DEBUG current_workspace_path: Returning None (invalid selections)")
            return None
        
        path = self.base_path / client / workspace
        print(f"DEBUG current_workspace_path: Returning {path}")
        return path
    
    @staticmethod
    def _sanitize_name(name: str) -> str:
        """Sanitize a name for use as a directory name"""
        return name.replace("/", "-").replace("\\", "-").strip()
