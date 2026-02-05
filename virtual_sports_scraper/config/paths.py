import os

# Base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
TEST_RESULTS_DIR = os.path.join(BASE_DIR, "test_results")

# Data subdirectories
LIVE_DATA_DIR = os.path.join(DATA_DIR, "live")
HISTORICAL_DATA_DIR = os.path.join(DATA_DIR, "historical")
BACKUPS_DIR = os.path.join(DATA_DIR, "backups")

# Test result subdirectories
LOGS_DIR = os.path.join(TEST_RESULTS_DIR, "test_logs")
SCREENSHOTS_DIR = os.path.join(TEST_RESULTS_DIR, "screenshots")
JSON_EXPORTS_DIR = os.path.join(TEST_RESULTS_DIR, "json_exports")

# File paths
MATCHES_FILE = os.path.join(LIVE_DATA_DIR, "matches.json")
ODDS_FILE = os.path.join(LIVE_DATA_DIR, "odds.json")
GOALS_FILE = os.path.join(LIVE_DATA_DIR, "goals.json")
RESULTS_FILE = os.path.join(HISTORICAL_DATA_DIR, "results.json")
STANDINGS_FILE = os.path.join(HISTORICAL_DATA_DIR, "standings.json")

def ensure_directories():
    """Create all necessary directories if they don't exist."""
    dirs = [
        LIVE_DATA_DIR, HISTORICAL_DATA_DIR, BACKUPS_DIR,
        LOGS_DIR, SCREENSHOTS_DIR, JSON_EXPORTS_DIR
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
