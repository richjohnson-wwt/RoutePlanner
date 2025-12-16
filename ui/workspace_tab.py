"""
Workspace Tab for VRPTW Application
"""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QInputDialog
)
from PyQt6.QtCore import Qt

DEFAULT_BASE = Path.home() / "Documents" / "RoutePlanner"


class WorkspaceTab(QWidget):
    """Workspace tab for managing VRPTW problems"""
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("WorkspaceTab")
        
        self.base_path = DEFAULT_BASE
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        
        # Header
        header = QLabel("Select or create a Client and Workspace")
        header.setStyleSheet("font-weight: 600;")
        header.setWordWrap(True)
        layout.addWidget(header)
        
        # Client selection row
        client_row = QHBoxLayout()
        client_label = QLabel("Client:")
        client_label.setMinimumWidth(80)
        client_row.addWidget(client_label)
        
        self.client_combo = QComboBox()
        self.client_combo.setMinimumWidth(200)
        self.client_combo.currentIndexChanged.connect(self.on_client_changed)
        client_row.addWidget(self.client_combo, 1)
        
        new_client_btn = QPushButton("New Client...")
        new_client_btn.clicked.connect(self.on_new_client)
        client_row.addWidget(new_client_btn)
        
        layout.addLayout(client_row)
        
        # Workspace selection row
        workspace_row = QHBoxLayout()
        workspace_label = QLabel("Workspace:")
        workspace_label.setMinimumWidth(80)
        workspace_row.addWidget(workspace_label)
        
        self.workspace_combo = QComboBox()
        self.workspace_combo.setMinimumWidth(200)
        workspace_row.addWidget(self.workspace_combo, 1)
        
        new_workspace_btn = QPushButton("New Workspace...")
        new_workspace_btn.clicked.connect(self.on_new_workspace)
        workspace_row.addWidget(new_workspace_btn)
        
        layout.addLayout(workspace_row)
        
        # Content area
        content_layout = QHBoxLayout()
        
        layout.addLayout(content_layout)
        
        # Initialize client list
        self.refresh_clients()
        self._update_controls_enabled()
    
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
            # Restore selection if possible
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
    
    def on_client_changed(self) -> None:
        """Handle client selection change"""
        self.refresh_workspaces()
        self._update_controls_enabled()
    
    def on_new_client(self) -> None:
        """Handle new client button click"""
        name, ok = QInputDialog.getText(self, "New Client", "Client name (e.g., JITB):")
        name = name.strip()
        if not ok or not name:
            return
        
        safe = self._sanitize_name(name)
        client_dir = self.base_path / safe
        
        if client_dir.exists():
            # Already exists: just select it
            pass
        else:
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
        
        if ws_dir.exists():
            # Already exists: just select it
            pass
        else:
            ws_dir.mkdir(parents=True, exist_ok=True)
        
        self.refresh_workspaces()
        self.workspace_combo.setCurrentText(safe)
        self._update_controls_enabled()
    
    def _update_controls_enabled(self) -> None:
        """Update enabled state of controls based on selections"""
        has_client = self.client_combo.currentText() not in ("", "<no clients>")
        self.workspace_combo.setEnabled(has_client)
    
    def current_workspace_path(self) -> Path | None:
        """Get the current workspace path if valid selections are made"""
        client = self.client_combo.currentText()
        workspace = self.workspace_combo.currentText()
        
        if (not client or client == "<no clients>") or (not workspace or workspace == "<no workspaces>"):
            return None
        
        return self.base_path / client / workspace
    
    @staticmethod
    def _sanitize_name(name: str) -> str:
        """Sanitize a name for use as a directory name"""
        # Simple sanitization: remove path separators and strip
        return name.replace("/", "-").replace("\\", "-").strip()
