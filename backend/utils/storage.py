"""
Persistent storage for users using JSON file
Simple file-based database for development
"""
import json
import os
from pathlib import Path
from typing import Dict, Any
import threading

class JSONStorage:
    def __init__(self, file_path: str):
        """Initialize JSON storage with file path"""
        self.file_path = Path(file_path)
        self.lock = threading.Lock()
        
        # Ensure directory exists
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load or create storage file
        if self.file_path.exists():
            with open(self.file_path, 'r') as f:
                try:
                    self._data = json.load(f)
                except json.JSONDecodeError:
                    self._data = {}
        else:
            self._data = {}
            self._save()
    
    def _save(self):
        """Save data to file"""
        from datetime import datetime
        
        def json_serial(obj):
            """JSON serializer for objects not serializable by default json code"""
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")
        
        with open(self.file_path, 'w') as f:
            json.dump(self._data, f, indent=2, default=json_serial)
    
    def get(self, key: str, default=None):
        """Get value by key"""
        with self.lock:
            return self._data.get(key, default)
    
    def __setitem__(self, key: str, value: Any):
        """Set value by key"""
        with self.lock:
            self._data[key] = value
            self._save()
    
    def __getitem__(self, key: str):
        """Get value by key"""
        with self.lock:
            return self._data[key]
    
    def __delitem__(self, key: str):
        """Delete key"""
        with self.lock:
            del self._data[key]
            self._save()
    
    def __contains__(self, key: str):
        """Check if key exists"""
        return key in self._data
    
    def keys(self):
        """Get all keys"""
        return self._data.keys()
    
    def values(self):
        """Get all values"""
        return self._data.values()
    
    def items(self):
        """Get all items"""
        return self._data.items()
    
    def clear(self):
        """Clear all data"""
        with self.lock:
            self._data = {}
            self._save()


# Create storage directory
STORAGE_DIR = Path("storage")
STORAGE_DIR.mkdir(exist_ok=True)

# Initialize persistent storage
users_storage = JSONStorage(STORAGE_DIR / "users.json")
api_keys_storage = JSONStorage(STORAGE_DIR / "api_keys.json")
