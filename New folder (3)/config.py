"""
Configuration settings for Odibets scrapers
"""

import os
from datetime import time

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# Create data directories
for folder in ["matchday", "results", "standings", "logs"]:
    os.makedirs(os.path.join(DATA_DIR, folder), exist_ok=True)

# URLs
ODILEAGUE_URL = "https://odibets.com/odileague"

# Scraping intervals (in seconds)
TIMER_CHECK_INTERVAL = 10           # How often to check timer
MATCHDAY_SCRAPE_INTERVAL = 30       # How often to scrape matchday data
LIVE_CHECK_INTERVAL = 5             # How often to check when LIVE

# Scheduling
RESULTS_SCRAPE_TIME = time(2, 0)    # Run results scraper at 2 AM daily
STANDINGS_SCRAPE_TIME = time(3, 0)  # Run standings scraper at 3 AM daily

# Browser settings
HEADLESS_MODE = True                # Run browser in headless mode
BROWSER_WAIT_TIME = 15              # Default wait time for elements
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# Monitoring thresholds
LIVE_THRESHOLD_SECONDS = 5          # Consider LIVE when timer ≤ 5 seconds
TIMER_CHANGE_THRESHOLD = 3          # Only log timer changes > 3 seconds diff

# Live Match Scraper Settings
LIVE_SCRAPE_INTERVAL = 15  # Seconds between live updates
MAX_LIVE_MATCH_DURATION = 120  # Maximum minutes to track a live match
LIVE_MATCH_DATA_POINTS = ["score", "minute", "events", "stats"]

# Match Event Types (based on your HTML)
EVENT_TYPES = {
    'goal': 'G',
    'yellow_card': 'YC',
    'red_card': 'RC',
    'substitution': 'SUB',
    'penalty': 'PEN',
    'own_goal': 'OG'
}

# Data storage
SAVE_AS_JSON = True
SAVE_AS_CSV = True
SAVE_AS_EXCEL = False

# Notification settings (optional)
ENABLE_NOTIFICATIONS = False
EMAIL_RECEIVER = ""  # Add email for notifications