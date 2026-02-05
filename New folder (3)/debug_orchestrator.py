"""
Debug the main orchestrator
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🔍 DEBUGGING MAIN ORCHESTRATOR")
print("="*60)

# Check 1: Basic Python environment
print("\n1️⃣ CHECKING PYTHON ENVIRONMENT:")
print("-"*40)
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"Script location: {__file__}")

# Check 2: Required files exist
print("\n2️⃣ CHECKING REQUIRED FILES:")
print("-"*40)

required_files = [
    "main_orchestrator.py",
    "config.py",
    "scrapers/__init__.py",
    "scrapers/base_scraper.py",
    "scrapers/timer_monitor.py",
    "scrapers/matchday_scraper.py",
    "scrapers/results_scraper.py",
    "scrapers/standings_scraper.py",
    "scrapers/live_match_scraper.py",
    "utils/__init__.py",
    "utils/helpers.py",
    "utils/file_handler.py"
]

for file in required_files:
    if os.path.exists(file):
        print(f"✅ {file}")
    else:
        print(f"❌ {file} - MISSING!")

# Check 3: Import all modules
print("\n3️⃣ TESTING IMPORTS:")
print("-"*40)

try:
    import schedule
    print("✅ schedule")
except ImportError as e:
    print(f"❌ schedule - {e}")

try:
    import threading
    print("✅ threading")
except ImportError as e:
    print(f"❌ threading - {e}")

try:
    from datetime import datetime
    print("✅ datetime")
except ImportError as e:
    print(f"❌ datetime - {e}")

# Check 4: Import our modules
print("\n4️⃣ TESTING OUR MODULE IMPORTS:")
print("-"*40)

try:
    from scrapers.timer_monitor import TimerMonitor
    print("✅ TimerMonitor")
except ImportError as e:
    print(f"❌ TimerMonitor - {e}")

try:
    from scrapers.matchday_scraper import MatchdayScraper
    print("✅ MatchdayScraper")
except ImportError as e:
    print(f"❌ MatchdayScraper - {e}")

try:
    from scrapers.results_scraper import ResultsScraper
    print("✅ ResultsScraper")
except ImportError as e:
    print(f"❌ ResultsScraper - {e}")

try:
    from scrapers.standings_scraper import StandingsScraper
    print("✅ StandingsScraper")
except ImportError as e:
    print(f"❌ StandingsScraper - {e}")

try:
    from scrapers.live_match_scraper import LiveMatchScraper
    print("✅ LiveMatchScraper")
except ImportError as e:
    print(f"❌ LiveMatchScraper - {e}")

try:
    from config import RESULTS_SCRAPE_TIME, STANDINGS_SCRAPE_TIME, LIVE_SCRAPE_INTERVAL
    print("✅ config.py imports")
except ImportError as e:
    print(f"❌ config.py - {e}")

try:
    from utils.helpers import create_summary_report
    print("✅ utils.helpers")
except ImportError as e:
    print(f"❌ utils.helpers - {e}")

try:
    from utils.file_handler import FileHandler
    print("✅ utils.file_handler")
except ImportError as e:
    print(f"❌ utils.file_handler - {e}")

# Check 5: Test main orchestrator class
print("\n5️⃣ TESTING ORCHESTRATOR CLASS CREATION:")
print("-"*40)

try:
    # First check if we can import the orchestrator
    exec(open("main_orchestrator.py", "r", encoding="utf-8").read())
    print("✅ Successfully read main_orchestrator.py")
    
    # Try to create an instance
    from main_orchestrator import ScraperOrchestrator
    orchestrator = ScraperOrchestrator()
    print("✅ Successfully created ScraperOrchestrator instance")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Check 6: Test specific methods
print("\n6️⃣ TESTING ORCHESTRATOR METHODS:")
print("-"*40)

try:
    orchestrator = ScraperOrchestrator()
    
    methods_to_check = [
        'run_complete_test',
        'run_live_match_tracking', 
        'run_timer_to_live_tracking',
        'start',
        'stop'
    ]
    
    for method in methods_to_check:
        if hasattr(orchestrator, method):
            print(f"✅ {method}() exists")
        else:
            print(f"❌ {method}() MISSING!")
            
except Exception as e:
    print(f"❌ Error checking methods: {e}")

# Check 7: Syntax check on main_orchestrator.py
print("\n7️⃣ CHECKING MAIN_ORCHESTRATOR.PY SYNTAX:")
print("-"*40)

try:
    with open("main_orchestrator.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check for common syntax errors
    lines = content.split('\n')
    
    # Check for unbalanced parentheses/brackets
    for i, line in enumerate(lines, 1):
        if line.count('(') != line.count(')'):
            print(f"⚠️ Line {i}: Unbalanced parentheses")
            print(f"   {line[:50]}...")
        if line.count('[') != line.count(']'):
            print(f"⚠️ Line {i}: Unbalanced brackets")
            print(f"   {line[:50]}...")
        if line.count('{') != line.count('}'):
            print(f"⚠️ Line {i}: Unbalanced braces")
            print(f"   {line[:50]}...")
    
    # Check for missing imports
    required_in_orchestrator = [
        "from scrapers.live_match_scraper import LiveMatchScraper",
        "class ScraperOrchestrator:",
        "def run_timer_to_live_tracking",
        "def main_menu():"
    ]
    
    for item in required_in_orchestrator:
        if item in content:
            print(f"✅ Found: {item.split()[1] if 'import' in item else item.split()[0]}")
        else:
            print(f"❌ Missing: {item.split()[1] if 'import' in item else item.split()[0]}")
    
    print("✅ Syntax check passed!")
    
except Exception as e:
    print(f"❌ Error in syntax check: {e}")

print("\n" + "="*60)
print("🔧 QUICK FIXES IF ERRORS FOUND:")
print("="*60)

# Suggest fixes based on common issues
print("\nCommon issues and fixes:")
print("1. If 'ModuleNotFoundError' for 'scrapers' - make sure you're running from project root")
print("2. If missing methods in LiveMatchScraper - add wait_for_live_and_start()")
print("3. If syntax errors - check for missing parentheses/brackets")
print("4. If import errors - run: pip install schedule")
print("\nRun: python debug_orchestrator.py to see detailed errors")