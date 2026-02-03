# state_manager.py
"""
Central State Manager
Manages match states and enforces one-way transitions
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Set
import json
from datetime import datetime
import threading

class MatchState(Enum):
    """Match states - one-way transitions only"""
    NOT_STARTED = "NOT_STARTED"
    ODDS_SCRAPED = "ODDS_SCRAPED"
    LIVE = "LIVE"
    FINISHED = "FINISHED"

@dataclass
class MatchRecord:
    """Individual match record"""
    match_id: str
    league: str
    team1: str
    team2: str
    state: MatchState = MatchState.NOT_STARTED
    odds: Dict[str, float] = field(default_factory=dict)
    goals: List[int] = field(default_factory=list)
    scraped_at: List[datetime] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "match_id": self.match_id,
            "league": self.league,
            "team1": self.team1,
            "team2": self.team2,
            "state": self.state.value,
            "odds": self.odds,
            "goals": self.goals,
            "scraped_at": [dt.isoformat() for dt in self.scraped_at],
            "last_updated": self.last_updated.isoformat()
        }

class CentralStateManager:
    """Manages state for all matches with thread safety"""
    
    def __init__(self):
        self.matches: Dict[str, MatchRecord] = {}
        self.league_states: Dict[str, Set[str]] = {}  # league -> match_ids
        self._lock = threading.RLock()
        
    def create_match(self, match_id: str, league: str, team1: str, team2: str) -> MatchRecord:
        """Create new match record"""
        with self._lock:
            if match_id in self.matches:
                return self.matches[match_id]
                
            match = MatchRecord(match_id, league, team1, team2)
            self.matches[match_id] = match
            
            if league not in self.league_states:
                self.league_states[league] = set()
            self.league_states[league].add(match_id)
            
            return match
    
    def update_match_state(self, match_id: str, new_state: MatchState) -> bool:
        """Update match state with one-way transition enforcement"""
        with self._lock:
            if match_id not in self.matches:
                return False
                
            match = self.matches[match_id]
            current_state = match.state
            
            # Define valid transitions
            valid_transitions = {
                MatchState.NOT_STARTED: [MatchState.ODDS_SCRAPED, MatchState.LIVE],
                MatchState.ODDS_SCRAPED: [MatchState.LIVE],
                MatchState.LIVE: [MatchState.FINISHED],
                MatchState.FINISHED: []  # No transitions from FINISHED
            }
            
            if new_state in valid_transitions[current_state]:
                match.state = new_state
                match.last_updated = datetime.now()
                return True
            else:
                # Invalid transition - log but don't change
                print(f"Invalid state transition: {current_state} -> {new_state}")
                return False
    
    def add_odds(self, match_id: str, market: str, odds: float) -> bool:
        """Add odds to match (only if not LIVE or FINISHED)"""
        with self._lock:
            if match_id not in self.matches:
                return False
                
            match = self.matches[match_id]
            
            # Only add odds if match hasn't started
            if match.state in [MatchState.NOT_STARTED, MatchState.ODDS_SCRAPED]:
                match.odds[market] = odds
                match.scraped_at.append(datetime.now())
                
                if match.state == MatchState.NOT_STARTED:
                    self.update_match_state(match_id, MatchState.ODDS_SCRAPED)
                    
                return True
            return False
    
    def add_goal(self, match_id: str, minute: int) -> bool:
        """Add goal minute (append-only)"""
        with self._lock:
            if match_id not in self.matches:
                return False
                
            match = self.matches[match_id]
            
            # Only add goals if match is LIVE
            if match.state == MatchState.LIVE:
                # Avoid duplicates
                if minute not in match.goals:
                    match.goals.append(minute)
                    match.last_updated = datetime.now()
                    return True
            return False
    
    def get_match(self, match_id: str) -> Optional[MatchRecord]:
        """Get match by ID"""
        with self._lock:
            return self.matches.get(match_id)
    
    def get_matches_by_league(self, league: str) -> List[MatchRecord]:
        """Get all matches for a league"""
        with self._lock:
            match_ids = self.league_states.get(league, set())
            return [self.matches[mid] for mid in match_ids if mid in self.matches]
    
    def save_to_json(self, filepath: str):
        """Save all matches to JSON file"""
        with self._lock:
            data = {
                "matches": [match.to_dict() for match in self.matches.values()],
                "last_updated": datetime.now().isoformat()
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
    
    def load_from_json(self, filepath: str):
        """Load matches from JSON file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                
            with self._lock:
                self.matches.clear()
                self.league_states.clear()
                
                for match_data in data.get("matches", []):
                    match = MatchRecord(
                        match_id=match_data["match_id"],
                        league=match_data["league"],
                        team1=match_data["team1"],
                        team2=match_data["team2"]
                    )
                    match.state = MatchState(match_data["state"])
                    match.odds = match_data.get("odds", {})
                    match.goals = match_data.get("goals", [])
                    match.scraped_at = [
                        datetime.fromisoformat(dt) 
                        for dt in match_data.get("scraped_at", [])
                    ]
                    match.last_updated = datetime.fromisoformat(
                        match_data.get("last_updated", datetime.now().isoformat())
                    )
                    
                    self.matches[match.match_id] = match
                    
                    if match.league not in self.league_states:
                        self.league_states[match.league] = set()
                    self.league_states[match.league].add(match.match_id)
                    
        except FileNotFoundError:
            print(f"State file {filepath} not found. Starting fresh.")
        except Exception as e:
            print(f"Error loading state: {e}")