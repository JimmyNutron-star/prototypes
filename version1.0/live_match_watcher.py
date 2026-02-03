# live_match_watcher.py
"""
Live Match Watcher - Detects when matches go LIVE
Hard trigger that immediately stops odds scraping
"""

import re
import time
from typing import List, Dict, Optional
from selenium.webdriver.common.by import By

class LiveMatchWatcher:
    """Watches for matches becoming LIVE"""
    
    def __init__(self, driver):
        self.driver = driver
        self.live_matches = set()
        self._stop_event = threading.Event()
        
    def check_for_live(self) -> List[Dict]:
        """Check for LIVE matches and return match information"""
        live_matches = []
        
        try:
            # Check for LIVE indicator in tabs
            live_tabs = self.driver.find_elements(
                By.CSS_SELECTOR, "li.live"
            )
            
            if live_tabs:
                # Click on LIVE tab to see live matches
                for tab in live_tabs:
                    if "active" not in tab.get_attribute("class"):
                        tab.click()
                        time.sleep(1)
                        break
            
            # Check live match tracker
            live_tracker = self.driver.find_element(
                By.CSS_SELECTOR, "div.play.show"
            )
            
            if live_tracker:
                live_match_elements = live_tracker.find_elements(
                    By.CSS_SELECTOR, "div.gm"
                )
                
                for match_elem in live_match_elements:
                    try:
                        # Extract team names
                        team1_elem = match_elem.find_element(
                            By.CSS_SELECTOR, "span.t-1-j"
                        )
                        team2_elem = match_elem.find_element(
                            By.CSS_SELECTOR, "span.t-2-j"
                        )
                        
                        team1 = team1_elem.text.strip()
                        team2 = team2_elem.text.strip()
                        
                        # Extract current minute
                        minute_spans = match_elem.find_elements(
                            By.CSS_SELECTOR, "div.hi span"
                        )
                        
                        current_minute = None
                        for span in minute_spans:
                            text = span.text.strip()
                            if "'" in text:
                                minute = int(text.replace("'", ""))
                                if current_minute is None or minute > current_minute:
                                    current_minute = minute
                        
                        live_matches.append({
                            "team1": team1,
                            "team2": team2,
                            "current_minute": current_minute,
                            "element": match_elem
                        })
                        
                    except Exception as e:
                        print(f"Error parsing live match: {e}")
                        continue
        
        except Exception as e:
            # No live matches or error
            pass
        
        return live_matches
    
    def watch_live_matches(self, state_manager, on_live_detected=None):
        """Continuously watch for LIVE matches"""
        
        def watch_task():
            try:
                while not self._stop_event.is_set():
                    live_matches = self.check_for_live()
                    
                    for match_info in live_matches:
                        # Create match ID pattern
                        match_id_pattern = f"{match_info['team1']}_{match_info['team2']}"
                        
                        # Find matching match in state manager
                        for match_id, match_record in state_manager.matches.items():
                            if (match_info['team1'] in match_record.team1 and 
                                match_info['team2'] in match_record.team2):
                                
                                # Update to LIVE state
                                if state_manager.update_match_state(match_id, MatchState.LIVE):
                                    print(f"Match {match_id} is now LIVE")
                                    
                                    if on_live_detected:
                                        on_live_detected(match_id, match_info)
                    
                    time.sleep(2)  # Check every 2 seconds
                    
            except Exception as e:
                print(f"Error in live match watching: {e}")
        
        thread = threading.Thread(target=watch_task)
        thread.daemon = True
        thread.start()
        
        return thread
    
    def stop(self):
        """Stop watching for LIVE matches"""
        self._stop_event.set()