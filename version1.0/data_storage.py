# data_storage.py
"""
Data Storage Layer - UPSERT-only data storage
Never deletes or overwrites historical data
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any
import hashlib

class JSONDataStorage:
    """JSON-based data storage with UPSERT semantics"""
    
    def __init__(self, base_path: str = "data"):
        self.base_path = base_path
        self.ensure_directory()
        
    def ensure_directory(self):
        """Ensure data directory exists"""
        os.makedirs(self.base_path, exist_ok=True)
        os.makedirs(os.path.join(self.base_path, "backups"), exist_ok=True)
    
    def generate_id(self, data: Dict) -> str:
        """Generate unique ID for data record"""
        # Create a hash based on match/league identifying information
        if "match_id" in data:
            return data["match_id"]
        elif "team1" in data and "team2" in data:
            key = f"{data.get('team1', '')}_{data.get('team2', '')}_{data.get('timestamp', '')}"
            return hashlib.md5(key.encode()).hexdigest()[:12]
        else:
            return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()[:12]
    
    def upsert_match(self, match_data: Dict, filepath: str = "matches.json"):
        """UPSERT match data (update if exists, insert if new)"""
        full_path = os.path.join(self.base_path, filepath)
        
        try:
            # Load existing data
            existing_data = []
            if os.path.exists(full_path):
                with open(full_path, 'r') as f:
                    existing_data = json.load(f)
            
            # Find existing match
            match_id = self.generate_id(match_data)
            found = False
            
            for i, existing in enumerate(existing_data):
                if self.generate_id(existing) == match_id:
                    # Update existing record
                    existing_data[i] = self.merge_data(existing, match_data)
                    found = True
                    break
            
            # If not found, insert new
            if not found:
                existing_data.append(match_data)
            
            # Save with backup
            self.create_backup(full_path)
            
            with open(full_path, 'w') as f:
                json.dump(existing_data, f, indent=2, default=str)
            
            print(f"Upserted match data: {match_id}")
            return True
            
        except Exception as e:
            print(f"Error upserting match data: {e}")
            return False
    
    def upsert_odds(self, match_id: str, odds_data: Dict, filepath: str = "odds.json"):
        """UPSERT odds data"""
        full_path = os.path.join(self.base_path, filepath)
        
        try:
            # Load existing data
            existing_data = {}
            if os.path.exists(full_path):
                with open(full_path, 'r') as f:
                    existing_data = json.load(f)
            
            # Get or create match odds
            if match_id not in existing_data:
                existing_data[match_id] = {}
            
            # Merge odds data (preserve old, add new)
            for market, odds in odds_data.items():
                if market not in existing_data[match_id]:
                    existing_data[match_id][market] = []
                
                # Add new odds entry with timestamp
                odds_entry = {
                    "odds": odds,
                    "timestamp": datetime.now().isoformat()
                }
                existing_data[match_id][market].append(odds_entry)
            
            # Save with backup
            self.create_backup(full_path)
            
            with open(full_path, 'w') as f:
                json.dump(existing_data, f, indent=2, default=str)
            
            print(f"Upserted odds for match: {match_id}")
            return True
            
        except Exception as e:
            print(f"Error upserting odds data: {e}")
            return False
    
    def upsert_goals(self, match_id: str, goals: List[int], filepath: str = "goals.json"):
        """UPSERT goal data (append-only)"""
        full_path = os.path.join(self.base_path, filepath)
        
        try:
            # Load existing data
            existing_data = {}
            if os.path.exists(full_path):
                with open(full_path, 'r') as f:
                    existing_data = json.load(f)
            
            # Get or create match goals
            if match_id not in existing_data:
                existing_data[match_id] = []
            
            # Append new goals (avoid duplicates)
            for goal in goals:
                if goal not in existing_data[match_id]:
                    existing_data[match_id].append(goal)
            
            # Sort goals chronologically
            existing_data[match_id].sort()
            
            # Save with backup
            self.create_backup(full_path)
            
            with open(full_path, 'w') as f:
                json.dump(existing_data, f, indent=2, default=str)
            
            print(f"Upserted goals for match: {match_id}")
            return True
            
        except Exception as e:
            print(f"Error upserting goal data: {e}")
            return False
    
    def merge_data(self, old_data: Dict, new_data: Dict) -> Dict:
        """Merge old and new data without overwriting"""
        merged = old_data.copy()
        
        for key, value in new_data.items():
            if key not in merged:
                merged[key] = value
            elif isinstance(value, dict) and isinstance(merged[key], dict):
                merged[key] = self.merge_data(merged[key], value)
            elif isinstance(value, list) and isinstance(merged[key], list):
                # Append new items, avoid duplicates
                for item in value:
                    if item not in merged[key]:
                        merged[key].append(item)
            elif key in ["last_updated", "scraped_at"]:
                # Always update timestamps
                merged[key] = value
            # For other fields, preserve old value (no overwrite)
        
        return merged
    
    def create_backup(self, filepath: str):
        """Create backup of existing file"""
        try:
            if os.path.exists(filepath):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"{os.path.basename(filepath)}.{timestamp}.bak"
                backup_path = os.path.join(self.base_path, "backups", backup_name)
                
                with open(filepath, 'r') as source, open(backup_path, 'w') as target:
                    target.write(source.read())
        except Exception as e:
            print(f"Error creating backup: {e}")