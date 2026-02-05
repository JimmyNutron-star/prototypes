"""
Helper functions and utilities
"""

import time
from datetime import datetime
import re

def format_timestamp(timestamp=None):
    """Format timestamp for display"""
    if not timestamp:
        timestamp = datetime.now()
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")

def parse_timer_value(timer_str):
    """Parse timer string into minutes and seconds"""
    if not timer_str:
        return None, None
    
    timer_str = timer_str.strip().lower()
    
    # Check if LIVE
    if 'live' in timer_str:
        return 0, 0
    
    # Parse MM:SS format
    match = re.match(r'(\d{1,2}):(\d{2})', timer_str)
    if match:
        minutes = int(match.group(1))
        seconds = int(match.group(2))
        return minutes, seconds
    
    return None, None

def calculate_time_until_live(timer_str):
    """Calculate seconds until LIVE"""
    minutes, seconds = parse_timer_value(timer_str)
    if minutes is None or seconds is None:
        return None
    
    return (minutes * 60) + seconds

def is_timer_live(timer_str, threshold=5):
    """Check if timer indicates LIVE status"""
    if not timer_str:
        return False
    
    timer_str = timer_str.strip().lower()
    
    # Check if explicitly LIVE
    if 'live' in timer_str:
        return True
    
    # Check if time is very low
    minutes, seconds = parse_timer_value(timer_str)
    if minutes is not None and seconds is not None:
        total_seconds = (minutes * 60) + seconds
        return total_seconds <= threshold
    
    return False

def create_summary_report(data, scraper_type):
    """Create a summary text report"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""
{'='*60}
ODIBETS ODILEAGUE - {scraper_type.upper()} REPORT
{'='*60}

Report Generated: {timestamp}

"""
    
    if scraper_type == "matchday":
        if isinstance(data, list) and data:
            report += f"Total Games: {len(data)}\n\n"
            for i, game in enumerate(data[:5], 1):  # Show first 5 games
                report += f"{i}. {game.get('home_team', 'N/A')} vs {game.get('away_team', 'N/A')}\n"
                report += f"   Odds: 1={game.get('home_odds', 'N/A')} | X={game.get('draw_odds', 'N/A')} | 2={game.get('away_odds', 'N/A')}\n"
                report += f"   GG/NG: Yes={game.get('gg_yes', 'N/A')} | No={game.get('gg_no', 'N/A')}\n\n"
            
            if len(data) > 5:
                report += f"... and {len(data) - 5} more matches\n"
    
    elif scraper_type == "results":
        if isinstance(data, dict) and 'games' in data:
            report += f"Week: {data.get('week_info', {}).get('week_title', 'Unknown')}\n"
            report += f"Time: {data.get('week_info', {}).get('time', 'Unknown')}\n"
            report += f"Total Games: {len(data.get('games', []))}\n\n"
            
            for i, game in enumerate(data['games'][:5], 1):
                report += f"{i}. {game.get('home_team', 'N/A')} {game.get('home_score', '?')}-{game.get('away_score', '?')} {game.get('away_team', 'N/A')}\n"
    
    elif scraper_type == "standings":
        if isinstance(data, dict) and 'teams' in data:
            report += f"Season: {data.get('season', 'Unknown')}\n"
            report += f"Total Teams: {len(data.get('teams', []))}\n\n"
            report += "Top 5 Teams:\n"
            
            for team in data['teams'][:5]:
                report += f"{team.get('position', '?')}. {team.get('team_name', 'N/A')} - {team.get('points', '0')} pts\n"
    
    report += f"\n{'='*60}\n"
    return report

def wait_with_progress(seconds, message="Waiting"):
    """Wait with progress indicator"""
    print(f"\n{message}...", end="")
    for i in range(seconds):
        time.sleep(1)
        print(".", end="", flush=True)
    print(" Done!")