"""
Data models for the OdiLeague scraper
"""
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum

class MatchState(Enum):
    """Match lifecycle states"""
    IDLE = "idle"
    PENDING = "pending"
    MATCHDAY = "matchday"
    PRE_LIVE = "pre_live"
    LIVE = "live"
    FINISHED = "finished"
    VALIDATED = "validated"
    ARCHIVED = "archived"

class AgentState(Enum):
    """Agent lifecycle states"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"

@dataclass
class TeamInfo:
    """Team information"""
    name: str
    logo_url: Optional[str] = None
    
    def to_dict(self) -> dict:
        return asdict(self)

@dataclass
class OddsData:
    """Betting odds for a market"""
    market_type: str  # e.g., "1X2", "GG/NG"
    options: Dict[str, float]  # e.g., {"1": 3.00, "X": 3.64, "2": 2.20}
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        return asdict(self)

@dataclass
class MatchdayData:
    """Pre-match data"""
    match_id: str
    league: str
    home_team: TeamInfo
    away_team: TeamInfo
    timer: str
    markets: List[OddsData] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        data = asdict(self)
        data['home_team'] = self.home_team.to_dict()
        data['away_team'] = self.away_team.to_dict()
        data['markets'] = [m.to_dict() for m in self.markets]
        return data

@dataclass
class GoalEvent:
    """Goal event information"""
    team: str  # "home" or "away"
    minute: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        return asdict(self)

@dataclass
class LiveMatchData:
    """Live match data"""
    match_id: str
    league: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    halftime_score: Optional[str] = None
    goals: List[GoalEvent] = field(default_factory=list)
    match_phase: str = "live"  # "1H", "HT", "2H", "FT"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        data = asdict(self)
        data['goals'] = [g.to_dict() for g in self.goals]
        return data

@dataclass
class ResultData:
    """Final match result"""
    match_id: str
    league: str
    week: str
    match_time: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    validated: bool = False
    
    def to_dict(self) -> dict:
        return asdict(self)

@dataclass
class StandingsEntry:
    """Single team standing entry"""
    position: int
    team: str
    points: int
    form: List[str]  # ["W", "D", "L", "W", "W"]
    
    def to_dict(self) -> dict:
        return asdict(self)

@dataclass
class StandingsData:
    """League standings"""
    league: str
    season: str
    entries: List[StandingsEntry] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        data = asdict(self)
        data['entries'] = [e.to_dict() for e in self.entries]
        return data

@dataclass
class AgentMessage:
    """Message for inter-agent communication"""
    sender: str
    recipient: str  # Can be specific agent or "broadcast"
    message_type: str
    payload: Dict
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        return asdict(self)

@dataclass
class TimerEvent:
    """Timer state change event"""
    league: str
    timer_value: str  # e.g., "01:23", "LIVE"
    match_index: int
    event_type: str  # "MATCHDAY_START", "MATCHDAY_STOP", "LIVE_START", "MATCH_END"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        return asdict(self)
