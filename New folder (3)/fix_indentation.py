"""
Fix indentation in Python files
"""

import os
import re

def fix_file_indentation(filename):
    """Fix indentation by converting tabs to spaces"""
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace tabs with 4 spaces
    content = content.replace('\t', '    ')
    
    # Write back
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Fixed indentation for {filename}")

def check_indentation(filename):
    """Check for mixed indentation"""
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines, 1):
        if '\t' in line and '    ' in line:
            print(f"⚠️ Line {i}: Mixed tabs and spaces in {filename}")
            return False
    
    return True

# Fix main orchestrator
fix_file_indentation("main_orchestrator.py")

# Check other files
files_to_check = [
    "scrapers/live_match_scraper.py",
    "scrapers/matchday_scraper.py",
    "scrapers/results_scraper.py",
    "scrapers/standings_scraper.py",
    "scrapers/timer_monitor.py",
    "scrapers/base_scraper.py"
]

for file in files_to_check:
    if os.path.exists(file):
        if check_indentation(file):
            print(f"✅ {file}: Clean indentation")
        else:
            fix_file_indentation(file)

print("\n🎉 All files checked and fixed if needed!")