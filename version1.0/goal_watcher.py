# goal_watcher.py
"""
Goal Watcher - Records goal minutes during LIVE matches
Only active while match is LIVE, append-only recording
"""

import threading
import time
from typing import List, Set

class GoalWatcher:
    """Watches for goal events during LIVE matches"""
    
    def __init__(self, driver):
        self.driver = driver
        self.watched_matches = {}  # match_id -> set of recorded minutes
        self._stop_event = threading.Event()
        
    def extract_goal_minutes(self, match_element) -> List[int]:
        """Extract goal minutes from match element"""
        goal_minutes = []
        
        try:
            # Find all goal minute spans
            minute_spans = match_element.find_elements(
                By.CSS_SELECTOR, "div.hi span"
            )
            
            for span in minute_spans:
                text = span.text.strip()
                if "'" in text:
                    try:
                        minute = int(text.replace("'", ""))
                        goal_minutes.append(minute)
                    except ValueError:
                        continue
        
        except Exception as e:
            print(f"Error extracting goal minutes: {e}")
        
        return goal_minutes
    
    def watch_match_goals(self, match_id: str, match_element, state_manager):
        """Watch for goals in a specific LIVE match"""
        
        def watch_task():
            try:
                # Initialize recorded minutes for this match
                if match_id not in self.watched_matches:
                    self.watched_matches[match_id] = set()
                
                last_goals = set()
                
                while not self._stop_event.is_set():
                    # Check if match is still LIVE
                    match_record = state_manager.get_match(match_id)
                    if not match_record or match_record.state != MatchState.LIVE:
                        break
                    
                    # Extract current goal minutes
                    current_goal_minutes = self.extract_goal_minutes(match_element)
                    current_goals_set = set(current_goal_minutes)
                    
                    # Find new goals
                    new_goals = current_goals_set - self.watched_matches[match_id]
                    
                    # Record new goals
                    for minute in sorted(new_goals):
                        if state_manager.add_goal(match_id, minute):
                            self.watched_matches[match_id].add(minute)
                            print(f"Goal recorded for {match_id} at {minute}'")
                    
                    # Update last known goals
                    last_goals = current_goals_set
                    
                    time.sleep(1)  # Check every second
                    
            except Exception as e:
                print(f"Error watching goals for {match_id}: {e}")
        
        thread = threading.Thread(target=watch_task)
        thread.daemon = True
        thread.start()
        
        return thread
    
    def stop_watching(self, match_id: str):
        """Stop watching goals for a specific match"""
        if match_id in self.watched_matches:
            del self.watched_matches[match_id]
    
    def stop_all(self):
        """Stop all goal watching"""
        self._stop_event.set()
        self.watched_matches.clear()