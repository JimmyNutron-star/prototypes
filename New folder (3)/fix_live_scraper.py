"""
Add missing methods to live_match_scraper.py
"""

import os

# Read current file
with open("scrapers/live_match_scraper.py", "r", encoding="utf-8") as f:
    content = f.read()

# Check what's missing
missing_methods = []

if "def wait_for_live_and_start" not in content:
    missing_methods.append("wait_for_live_and_start")

if "def is_timer_live(self, timer_value):" not in content:
    missing_methods.append("is_timer_live")

if "def get_current_timer(self):" not in content:
    missing_methods.append("get_current_timer")

if missing_methods:
    print(f"❌ Missing methods: {', '.join(missing_methods)}")
    print("\n💡 You need to add these methods to live_match_scraper.py")
else:
    print("✅ All required methods are present!")