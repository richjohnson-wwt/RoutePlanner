
import sqlite3
import os
from typing import Optional
from datetime import datetime


class GeocodeCache:
    """SQLite-based cache for geocoding results."""
    
    def __init__(self, db_path: str = None):
        """
        Initialize the geocode cache.
        
        Args:
            db_path: Path to SQLite database file. If None, uses default location.
        """
        if db_path is None:
            # Default to a cache directory in the project root
            cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cache')
            os.makedirs(cache_dir, exist_ok=True)
            db_path = os.path.join(cache_dir, 'geocode_cache.db')
        
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize the database schema if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS geocode_cache (
                address TEXT NOT NULL,
                state_code TEXT NOT NULL,
                lat REAL,
                lng REAL,
                display_name TEXT,
                timestamp TEXT NOT NULL,
                PRIMARY KEY (address, state_code)
            )
        ''')
        
        # Create index for faster lookups
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_address_state 
            ON geocode_cache(address, state_code)
        ''')
        
        conn.commit()
        conn.close()
    
    def get(self, address: str, state_code: str) -> Optional[dict]:
        """
        Retrieve cached geocoding result.
        
        Args:
            address: Address string
            state_code: State code (e.g., 'CA', 'NY')
            
        Returns:
            Dictionary with 'lat', 'lng', and 'display_name' or None if not cached
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT lat, lng, display_name 
            FROM geocode_cache 
            WHERE address = ? AND state_code = ?
        ''', (address, state_code))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            lat, lng, display_name = result
            # Only return if we have valid coordinates
            if lat is not None and lng is not None:
                return {
                    'lat': lat,
                    'lng': lng,
                    'display_name': display_name
                }
        
        return None
    
    def set(self, address: str, state_code: str, lat: Optional[float], 
            lng: Optional[float], display_name: Optional[str] = None):
        """
        Store geocoding result in cache.
        
        Args:
            address: Address string
            state_code: State code (e.g., 'CA', 'NY')
            lat: Latitude (can be None if geocoding failed)
            lng: Longitude (can be None if geocoding failed)
            display_name: Display name from geocoder
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT OR REPLACE INTO geocode_cache 
            (address, state_code, lat, lng, display_name, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (address, state_code, lat, lng, display_name, timestamp))
        
        conn.commit()
        conn.close()
    
    def clear(self):
        """Clear all cached entries."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM geocode_cache')
        conn.commit()
        conn.close()
    
    def get_stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM geocode_cache')
        total_entries = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM geocode_cache WHERE lat IS NOT NULL AND lng IS NOT NULL')
        successful_entries = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_entries': total_entries,
            'successful_entries': successful_entries,
            'failed_entries': total_entries - successful_entries
        }
