"""
Data storage agent - handles all data persistence with UPSERT logic
"""
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import shutil

from models import AgentState
from logger import AgentLogger

class DataAgent:
    """
    Centralized data management agent
    Handles JSON storage with UPSERT capabilities
    """
    
    def __init__(self, data_dir: str = "data", backup_dir: str = "data/backups"):
        self.agent_name = "DataAgent"
        self.logger = AgentLogger(self.agent_name)
        self.state = AgentState.INITIALIZING
        
        # Setup directories
        self.data_dir = Path(data_dir)
        self.backup_dir = Path(backup_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # File paths
        self.matches_file = self.data_dir / "matches.json"
        self.results_file = self.data_dir / "results.json"
        self.standings_file = self.data_dir / "standings.json"
        self.leagues_file = self.data_dir / "leagues.json"
        
        # In-memory cache
        self.matches_cache: Dict[str, Any] = {}
        self.results_cache: Dict[str, Any] = {}
        self.standings_cache: Dict[str, Any] = {}
        self.leagues_cache: Dict[str, Any] = {}
        
        # Lock for thread-safe operations
        self.lock = asyncio.Lock()
        
        self.logger.info("DataAgent initialized", data_dir=str(self.data_dir))
        
    async def initialize(self):
        """Initialize data agent - load existing data"""
        self.logger.state_change(self.state.value, AgentState.INITIALIZING.value)
        self.state = AgentState.INITIALIZING
        
        # Load existing data
        await self._load_data()
        
        self.state = AgentState.RUNNING
        self.logger.state_change(AgentState.INITIALIZING.value, self.state.value)
        self.logger.info("DataAgent ready")
        
    async def _load_data(self):
        """Load existing data from files into cache"""
        async with self.lock:
            # Load matches
            if self.matches_file.exists():
                with open(self.matches_file, 'r', encoding='utf-8') as f:
                    self.matches_cache = json.load(f)
                self.logger.info(f"Loaded {len(self.matches_cache)} matches from disk")
            
            # Load results
            if self.results_file.exists():
                with open(self.results_file, 'r', encoding='utf-8') as f:
                    self.results_cache = json.load(f)
                self.logger.info(f"Loaded {len(self.results_cache)} results from disk")
            
            # Load standings
            if self.standings_file.exists():
                with open(self.standings_file, 'r', encoding='utf-8') as f:
                    self.standings_cache = json.load(f)
                self.logger.info(f"Loaded standings data from disk")
            
            # Load leagues
            if self.leagues_file.exists():
                with open(self.leagues_file, 'r', encoding='utf-8') as f:
                    self.leagues_cache = json.load(f)
                self.logger.info(f"Loaded league data from disk")
    
    async def save_matchday_data(self, match_id: str, data: Dict[str, Any]) -> bool:
        """
        Save or update matchday data
        
        Args:
            match_id: Unique match identifier
            data: Matchday data dictionary
            
        Returns:
            Success status
        """
        async with self.lock:
            try:
                # UPSERT logic
                if match_id in self.matches_cache:
                    # Update existing
                    self.matches_cache[match_id]['matchday_data'] = data
                    self.matches_cache[match_id]['updated_at'] = datetime.now().isoformat()
                    self.logger.info(f"Updated matchday data", match_id=match_id)
                else:
                    # Insert new
                    self.matches_cache[match_id] = {
                        'match_id': match_id,
                        'matchday_data': data,
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
                    self.logger.info(f"Inserted new matchday data", match_id=match_id)
                
                # Persist to disk
                await self._save_to_file(self.matches_file, self.matches_cache)
                self.logger.data_collected("matchday", 1)
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to save matchday data: {e}", match_id=match_id)
                return False
    
    async def save_live_data(self, match_id: str, data: Dict[str, Any]) -> bool:
        """Save or update live match data"""
        async with self.lock:
            try:
                if match_id in self.matches_cache:
                    self.matches_cache[match_id]['live_data'] = data
                    self.matches_cache[match_id]['updated_at'] = datetime.now().isoformat()
                else:
                    self.matches_cache[match_id] = {
                        'match_id': match_id,
                        'live_data': data,
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
                
                await self._save_to_file(self.matches_file, self.matches_cache)
                self.logger.data_collected("live_data", 1)
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to save live data: {e}", match_id=match_id)
                return False
    
    async def save_result(self, match_id: str, data: Dict[str, Any]) -> bool:
        """Save final result"""
        async with self.lock:
            try:
                # Update match cache
                if match_id in self.matches_cache:
                    self.matches_cache[match_id]['final_result'] = data
                    self.matches_cache[match_id]['updated_at'] = datetime.now().isoformat()
                
                # Add to results cache
                self.results_cache[match_id] = data
                
                await self._save_to_file(self.matches_file, self.matches_cache)
                await self._save_to_file(self.results_file, self.results_cache)
                self.logger.data_collected("result", 1)
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to save result: {e}", match_id=match_id)
                return False
    
    async def save_standings(self, league: str, data: Dict[str, Any]) -> bool:
        """Save league standings"""
        async with self.lock:
            try:
                if league not in self.standings_cache:
                    self.standings_cache[league] = []
                
                # Add new standings snapshot
                self.standings_cache[league].append({
                    'data': data,
                    'timestamp': datetime.now().isoformat()
                })
                
                await self._save_to_file(self.standings_file, self.standings_cache)
                self.logger.data_collected("standings", 1)
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to save standings: {e}", league=league)
                return False
    
    async def mark_validated(self, match_id: str) -> bool:
        """Mark a match as validated"""
        async with self.lock:
            try:
                if match_id in self.matches_cache:
                    self.matches_cache[match_id]['validated'] = True
                    self.matches_cache[match_id]['validated_at'] = datetime.now().isoformat()
                    await self._save_to_file(self.matches_file, self.matches_cache)
                    self.logger.info(f"Match validated", match_id=match_id)
                    return True
                return False
                
            except Exception as e:
                self.logger.error(f"Failed to mark validated: {e}", match_id=match_id)
                return False
    
    async def get_match_data(self, match_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve match data"""
        async with self.lock:
            return self.matches_cache.get(match_id)
    
    async def _save_to_file(self, file_path: Path, data: Dict[str, Any]):
        """Save data to JSON file with atomic write"""
        try:
            # Write to temporary file first
            temp_file = file_path.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Atomic rename
            temp_file.replace(file_path)
            
        except Exception as e:
            self.logger.error(f"Failed to save file: {e}", file=str(file_path))
            raise
    
    async def create_backup(self):
        """Create backup of all data files"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_subdir = self.backup_dir / timestamp
            backup_subdir.mkdir(parents=True, exist_ok=True)
            
            # Backup all files
            for file in [self.matches_file, self.results_file, self.standings_file, self.leagues_file]:
                if file.exists():
                    shutil.copy2(file, backup_subdir / file.name)
            
            self.logger.info(f"Backup created", timestamp=timestamp)
            return True
            
        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, int]:
        """Get current statistics"""
        async with self.lock:
            return {
                'total_matches': len(self.matches_cache),
                'total_results': len(self.results_cache),
                'validated_matches': sum(1 for m in self.matches_cache.values() if m.get('validated', False))
            }
    
    async def shutdown(self):
        """Shutdown data agent"""
        self.logger.state_change(self.state.value, AgentState.STOPPING.value)
        self.state = AgentState.STOPPING
        
        # Final save
        await self._save_to_file(self.matches_file, self.matches_cache)
        await self._save_to_file(self.results_file, self.results_cache)
        await self._save_to_file(self.standings_file, self.standings_cache)
        
        # Create final backup
        await self.create_backup()
        
        self.state = AgentState.STOPPED
        self.logger.state_change(AgentState.STOPPING.value, self.state.value)
        self.logger.info("DataAgent shutdown complete")


async def main():
    """Independent runner for DataAgent"""
    import asyncio
    agent = DataAgent(data_dir="test_data")
    await agent.initialize()
    
    # Test saving some dummy data
    await agent.save_matchday_data("test_001", {"status": "ok", "message": "hello world"})
    
    stats = await agent.get_stats()
    print(f"DataAgent Stats: {stats}")
    
    await agent.shutdown()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
