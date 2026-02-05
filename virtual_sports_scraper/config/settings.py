# Global Settings

# Browser Configuration
HEADLESS_MODE = False  # Set to True for production
WINDOW_SIZE = "1920,1080"
IMPLICIT_WAIT = 10
PAGE_LOAD_TIMEOUT = 30

# URLs
BASE_URL = "https://www.example.com/virtual-sports"  # TODO: Update with actual URL

# Timing (in seconds)
ROUND_DURATION = 120
ODDS_SCRAPING_WINDOW = 110  # 120 - 10
ODDS_DEADLINE_BUFFER = 10   # Stop scraping when timer <= 10s
LIVE_MATCH_WINDOW = 35
POPUP_CHECK_TIMEOUT = 5

# Scraping Schedules (in minutes)
RESULTS_INTERVAL = 30
STANDINGS_INTERVAL = 30

# Retry Policies
MAX_RETRIES = 3
RETRY_DELAY = 1.0

# League Identifiers
LEAGUES = [
    "English League",
    "Spanish League",
    "Kenyan League",
    "Italian League"
]

# Market Identifiers
MARKETS = [
    "1X2", "GG/NG", "Double Chance", "OV/UN 1.5", "OV/UN 2.5",
    "OV/UN 3.5", "1X2 and OV/UN 1.5", "1X2 and OV/UN 2.5", 
    "1X2 and OV/UN 3.5", "1X2 and OV/UN 4.5", "1X2 and OV/UN 5.5",
    "Correct Score", "Half-Time", "Double Chance (H/T)",
    "Half-Time Result", "1X2&NG", "Half Time / Full Time",
    "First Team to Score", "Goal:Goal Half Time", "Handicap -1",
    "Handicap -2", "Multi-Goals", "Team 1 Goal/No Goal",
    "Team 1 Over/Under 1.5", "Team 2 Goal/No Goal",
    "Team 2 Over/Under 1.5", "Time of First Goal",
    "Total Goals", "Total Goals Odd/Even"
]
