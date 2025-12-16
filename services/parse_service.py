"""
Parse Service for VRPTW Application
Handles parsing Excel files based on YAML configuration and outputs state-based CSV files
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import yaml


class ParseService:
    """Service for parsing Excel files into state-based CSV files"""
    
    def __init__(self, config_path: Path):
        """
        Initialize the parse service with a configuration file
        
        Args:
            config_path: Path to the YAML configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> dict[str, Any]:
        """Load and parse the YAML configuration file"""
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def parse_excel(
        self,
        excel_path: Path,
        sheet_name: str,
        output_base_path: Path,
        log_callback: callable = None
    ) -> dict[str, int]:
        """
        Parse an Excel file and output state-based CSV files
        
        Args:
            excel_path: Path to the Excel file
            sheet_name: Name of the sheet to parse
            output_base_path: Base path for output (e.g., ~/Documents/RoutePlanner/JITB/phones)
            log_callback: Optional callback function for logging messages
        
        Returns:
            Dictionary mapping state codes to row counts
        """
        def log(msg: str) -> None:
            """Helper to log messages"""
            if log_callback:
                log_callback(msg)
        
        log(f"Loading Excel file: {excel_path}")
        log(f"Sheet: {sheet_name}")
        
        # Load the Excel file
        try:
            df = pd.read_excel(excel_path, sheet_name=sheet_name, engine="openpyxl")
            log(f"Loaded {len(df)} rows from Excel")
        except Exception as e:
            log(f"ERROR: Failed to load Excel file: {e}")
            raise
        
        # Get required headers from config
        required_headers = self.config.get('required_headers', [])
        log(f"Required headers: {', '.join(required_headers)}")
        
        # Normalize column names (lowercase, strip whitespace)
        df.columns = df.columns.str.strip().str.lower()
        
        # Check for required headers
        missing_headers = []
        for header in required_headers:
            header_lower = header.lower().strip()
            if header_lower not in df.columns:
                missing_headers.append(header)
        
        if missing_headers:
            error_msg = f"ERROR: Missing required headers: {', '.join(missing_headers)}"
            log(error_msg)
            raise ValueError(error_msg)
        
        log("All required headers found")
        
        # Filter to only required columns
        columns_to_keep = [h.lower().strip() for h in required_headers]
        df_filtered = df[columns_to_keep]
        
        # Group by state (st column)
        if 'st' not in df_filtered.columns:
            error_msg = "ERROR: 'st' column not found for state grouping"
            log(error_msg)
            raise ValueError(error_msg)
        
        # Get unique states
        states = df_filtered['st'].dropna().unique()
        log(f"Found {len(states)} unique states: {', '.join(sorted(states))}")
        
        # Create output directories and write CSV files per state
        state_counts = {}
        output_base_path.mkdir(parents=True, exist_ok=True)
        
        for state in states:
            state_str = str(state).strip()
            if not state_str:
                continue
            
            # Filter rows for this state
            state_df = df_filtered[df_filtered['st'] == state]
            row_count = len(state_df)
            state_counts[state_str] = row_count
            
            # Create state directory
            state_dir = output_base_path / state_str
            state_dir.mkdir(parents=True, exist_ok=True)
            
            # Write CSV file
            csv_path = state_dir / "addresses.csv"
            state_df.to_csv(csv_path, index=False)
            log(f"Wrote {row_count} rows to {csv_path}")
        
        log(f"Parse complete! Processed {len(state_counts)} states")
        return state_counts
