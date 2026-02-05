"""
Configuration settings for OdiLeague Agentic Scraper
"""
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class ScraperConfig:
    """Global configuration for the scraper system"""
    
    # Target URL
    TARGET_URL: str = "https://odibets.com/odileague"
    
    # Timing thresholds (in seconds)
    MATCHDAY_START_THRESHOLD: int = 60  # Start scraping when timer > 1 minute
    MATCHDAY_STOP_THRESHOLD: int = 10   # Stop matchday scraping when timer < 10 seconds
    
    # League configuration
    LEAGUES: List[str] = None
    
    # Scraping intervals (in seconds)
    TIMER_CHECK_INTERVAL: float = 0.5
    LIVE_MATCH_CHECK_INTERVAL: float = 2.0
    STANDINGS_MATCH_TRIGGER: int = 5  # Scrape standings every 5 matches
    
    # Browser settings
    HEADLESS: bool = False
    BROWSER_TIMEOUT: int = 60000  # 60 seconds
    
    # Data storage
    DATA_DIR: str = "data"
    BACKUP_DIR: str = "data/backups"
    
    # Retry settings
    MAX_RETRIES: int = 5
    RETRY_DELAY: float = 2.0
    
    # Logging
    LOG_LEVEL: str = "DEBUG"
    LOG_DIR: str = "logs"
    
    def __post_init__(self):
        if self.LEAGUES is None:
            self.LEAGUES = [
                {
                    "name": "English League",
                    "selector": "div.logo:nth-child(1)",
                    "id": "english"
                },
                {
                    "name": "Spanish League",
                    "selector": "div.logo:nth-child(2)",
                    "id": "spanish"
                },
                {
                    "name": "Kenyan League",
                    "selector": "div.logo:nth-child(3)",
                    "id": "kenyan"
                },
                {
                    "name": "Italian League",
                    "selector": "div.logo:nth-child(4)",
                    "id": "italian"
                }
            ]

# CSS Selectors
class Selectors:
    """CSS selectors for page elements"""
    
    # Popup
    POPUP_CLOSE = "div.roadblock-close button"
    
    # League selection
    LEAGUE_CONTAINER = "div.virtual-logos"
    LEAGUE_LOGO = "div.logo"
    LEAGUE_ACTIVE = "div.logo.active"
    
    # Timers
    TIMER_CONTAINER = "div.virtual-timer"
    TIMER_SLOT = "div.ss"
    TIMER_ACTIVE = "div.ss.active"
    
    # Matchday
    GAME_CONTAINER = "div.game"
    TEAM_NAMES = "div.t div.t-l"
    TEAM_LOGOS = "div.s img"
    ODDS_CONTAINER = "div.odds"
    ODDS_BUTTON = "button"
    
    # Market filters
    MARKET_FILTER_CONTAINER = "div.games-filter-d"
    MARKET_BUTTON = "div.games-filter-d button"
    MARKET_DROPDOWN = "div.games-filter-d select"
    
    # Tabs
    TAB_LIVE = "ul.tbs li.live"
    TAB_RESULTS = "ul.tbs li:nth-child(2)"
    TAB_STANDINGS = "ul.tbs li:nth-child(3)"
    
    # Live match
    LIVE_CONTAINER = "div.play.show"
    LIVE_MATCH = "div.gm"
    LIVE_SCORE = "div.gm-s div.d"
    LIVE_TEAM_HOME = "div.t-1 span.t-1-j"
    LIVE_TEAM_AWAY = "div.t-2 span.t-2-j"
    LIVE_GOAL_TIMES = "div.gm-h div.hi span"
    LIVE_HALFTIME_SCORE = "div.gm-h div.dv span"
    
    # Results
    RESULTS_CONTAINER = "div.rs"
    RESULTS_TITLE = "div.rs-t div.t"
    RESULTS_TIME = "div.rs-t div.b"
    RESULTS_MATCH = "div.rs-g"
    RESULTS_TEAM = "div.g-t"
    RESULTS_SCORE = "div.g-s span"
    
    # Standings
    STANDINGS_CONTAINER = "div.virtual-standings"
    STANDINGS_TITLE = "div.title"
    STANDINGS_TABLE = "div.tb table"
    STANDINGS_ROW = "tbody tr"

# Global config instance
config = ScraperConfig()
selectors = Selectors()
