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
        
        # Get column mappings from config
        column_mappings = self.config.get('columns', {})
        if not column_mappings:
            error_msg = "ERROR: Config file missing 'columns' mapping"
            log(error_msg)
            raise ValueError(error_msg)
        
        log(f"Column mappings: {column_mappings}")
        
        # Normalize column names (lowercase, strip whitespace)
        df.columns = df.columns.str.strip().str.lower()
        
        # Verify all mapped columns exist in the Excel file
        missing_columns = []
        for field, excel_col in column_mappings.items():
            if excel_col:  # Skip empty mappings (like address2 might be empty)
                excel_col_lower = excel_col.lower().strip()
                if excel_col_lower not in df.columns:
                    missing_columns.append(f"{field} -> {excel_col}")
        
        if missing_columns:
            error_msg = f"ERROR: Missing required columns: {', '.join(missing_columns)}"
            log(error_msg)
            raise ValueError(error_msg)
        
        log("All required columns found")
        
        # Create a standardized DataFrame with renamed columns
        df_standardized = pd.DataFrame()
        
        for field, excel_col in column_mappings.items():
            if excel_col:  # Only map non-empty columns
                excel_col_lower = excel_col.lower().strip()
                df_standardized[field] = df[excel_col_lower]
        
        # Get the state column for grouping
        if 'state' not in df_standardized.columns:
            error_msg = "ERROR: 'state' field not mapped in config"
            log(error_msg)
            raise ValueError(error_msg)
        
        state_column = 'state'
        log(f"Using '{state_column}' column for state grouping")
        
        # Get unique states
        states = df_standardized[state_column].dropna().unique()
        log(f"Found {len(states)} unique states: {', '.join(sorted(str(s) for s in states))}")
        
        # Create output directories and write CSV files per state
        state_counts = {}
        output_base_path.mkdir(parents=True, exist_ok=True)
        
        for state in states:
            state_str = str(state).strip()
            if not state_str:
                continue
            
            # Filter rows for this state
            state_df = df_standardized[df_standardized[state_column] == state]
            row_count = len(state_df)
            state_counts[state_str] = row_count
            
            # Create state directory
            state_dir = output_base_path / state_str
            state_dir.mkdir(parents=True, exist_ok=True)
            
            # Write CSV file with standardized column names
            csv_path = state_dir / "addresses.csv"
            state_df.to_csv(csv_path, index=False)
            log(f"Wrote {row_count} rows to {csv_path}")
        
        log(f"Parse complete! Processed {len(state_counts)} states")
        return state_counts
