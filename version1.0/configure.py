# config.py
"""
Virtual Sports Scraper Configuration
"""

import os
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import timedelta

@dataclass
class ScraperConfig:
    # Target URL
    TARGET_URL: str = "https://odibets.com/odileague"
    
    # Timing Constants
    ROUND_DURATION: int = 120  # 2 minutes in seconds
    LIVE_WINDOW_DURATION: int = 35  # 35 seconds
    ODDS_SCRAPING_DEADLINE: int = 10  # Stop 10 seconds before round end
    RESULTS_SCRAPE_INTERVAL: int = 1800  # 30 minutes in seconds
    STANDINGS_SCRAPE_INTERVAL: int = 1800  # 30 minutes in seconds
    
    # CSS Selectors (from provided HTML)
    SELECTORS: Dict[str, str] = None
    
    # Data Storage
    JSON_STORAGE_PATH: str = "data/scraped_data.json"
    BACKUP_STORAGE_PATH: str = "data/backups/"
    
    # Browser Settings
    HEADLESS: bool = False
    BROWSER_TIMEOUT: int = 30
    
    def __post_init__(self):
        if self.SELECTORS is None:
            self.SELECTORS = {
                # Popup Elements
                "POPUP_ROOT": "div.roadblock",
                "POPUP_CLOSE_BUTTON": "div.roadblock-close button",
                
                # League Elements
                "LEAGUE_CONTAINER": "div.virtual-logos",
                "LEAGUE_ITEM": "div.logo",
                "LEAGUE_ACTIVE": "div.logo.active",
                
                # Timer Elements
                "TIMER_CONTAINER": "div.virtual-timer",
                "TIMER_ACTIVE": "div.ss.active",
                
                # Match Elements
                "MATCH_CONTAINER": "div.game.e",
                "TEAM_NAMES": "div.t-l",
                "TEAM_IMAGES": "span.w-4 img",
                
                # Odds Elements
                "ODDS_CONTAINER": "div.odds",
                "ODDS_1X2": "div.o.s-1.m3 button",
                "ODDS_GG_NG": "div.o.s-2.m2 button",
                "ODDS_VALUE": "span.o-2",
                
                # Market Selectors
                "MARKET_CONTAINER": "div.games-filter-d",
                "MARKET_BUTTONS": "div.games-filter-d button",
                "MARKET_DROPDOWN": "div.games-filter-d select",
                
                # Live Elements
                "LIVE_INDICATOR": "li.live",
                "LIVE_MATCH_TRACKER": "div.play.show",
                "LIVE_MATCH_ITEM": "div.gm",
                "LIVE_TEAM_SCORES": "div.s div.d",
                "GOAL_MINUTES": "div.hi span",
                
                # Results Elements
                "RESULTS_CONTAINER": "div.rs",
                "RESULT_ITEM": "div.rs-g",
                "RESULT_SCORES": "div.g-s span",
                
                # Standings Elements
                "STANDINGS_CONTAINER": "div.virtual-standings",
                "STANDINGS_TABLE": "table",
                "STANDINGS_ROW": "tbody tr"
            }

# Initialize config
config = ScraperConfig()