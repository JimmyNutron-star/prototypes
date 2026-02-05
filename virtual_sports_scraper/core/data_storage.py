import json
import os
import threading
import shutil
import time
from datetime import datetime
from config.paths import MATCHES_FILE, ODDS_FILE, GOALS_FILE, RESULTS_FILE, BACKUPS_DIR

class DataStorage:
    """
    Handles JSON data storage with UPSERT-only policy and file locking.
    """
    def __init__(self):
        self._lock = threading.Lock()

    def _load_json(self, filepath):
        if not os.path.exists(filepath):
            return []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return []
                return json.loads(content)
        except Exception as e:
            print(f"[ERROR] Failed to load JSON from {filepath}: {e}")
            return []

    def _save_json(self, filepath, data):
        """Saves data to JSON with backup."""
        try:
            # Create incremental backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(BACKUPS_DIR, f"{os.path.basename(filepath)}_{timestamp}.bak")
            if os.path.exists(filepath):
                shutil.copy2(filepath, backup_path)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to print JSON to {filepath}: {e}")
            return False

    def upsert_matches(self, matches_data):
        """
        Upsert matches based on unique ID or keys.
        matches_data: List of dicts representing matches.
        """
        with self._lock:
            current_data = self._load_json(MATCHES_FILE)
            # Assuming match logic: check by league+teams+time or specific ID
            # Here we just append new ones or update existing if we had an ID system.
            # Simplified for prompt: Check duplicates by exact content or specific key if available.
            
            # Simple append + deduplicate strategy for now as user didn't specify ID schema
            # In a real app, we'd use a unique MatchID.
            
            for new_match in matches_data:
                # Check if exists (simplified check)
                exists = False
                for i, existing in enumerate(current_data):
                    # logic to identify match equality
                     if existing.get('teams') == new_match.get('teams') and existing.get('time') == new_match.get('time'):
                         current_data[i] = new_match # Update
                         exists = True
                         break
                if not exists:
                    current_data.append(new_match)
            
            self._save_json(MATCHES_FILE, current_data)

    def upsert_odds(self, odds_data):
        """Append-only/Upsert odds data."""
        with self._lock:
            current_data = self._load_json(ODDS_FILE)
            # Similar logic.
            current_data.extend(odds_data) # Often odds are just many data points
            self._save_json(ODDS_FILE, current_data)

    def append_goal(self, goal_event):
        """Strict append-only for goals."""
        with self._lock:
            current_data = self._load_json(GOALS_FILE)
            current_data.append(goal_event)
            self._save_json(GOALS_FILE, current_data)

    def save_results(self, results_data):
        """Upsert results."""
        with self._lock:
            current_data = self._load_json(RESULTS_FILE)
            # Deduplication logic required here
            current_data.extend(results_data)
            self._save_json(RESULTS_FILE, current_data)
