# timer_watcher.py
"""
Timer Watcher - Monitors round timer and controls scraping windows
Authoritative for timing decisions
"""

import re
from datetime import datetime, timedelta
import time
from typing import Callable, Optional
from selenium.webdriver.common.by import By

class TimerWatcher:
    """Monitors the round timer and controls scraping windows"""
    
    def __init__(self, driver):
        self.driver = driver
        self.current_time = None
        self.round_start_time = None
        self.last_round_start = None
        
    def get_timer_seconds(self) -> Optional[int]:
        """Extract timer value in seconds from DOM"""
        try:
            timer_element = self.driver.find_element(
                By.CSS_SELECTOR, "div.virtual-timer div.ss.active"
            )
            timer_text = timer_element.text.strip()
            
            # Parse MM:SS format
            if ':' in timer_text:
                minutes, seconds = timer_text.split(':')
                return int(minutes) * 60 + int(seconds)
            else:
                # Handle case without colon
                return int(timer_text)
                
        except Exception as e:
            print(f"Error reading timer: {e}")
            return None
    
    def is_round_start(self) -> bool:
        """Check if we're at the start of a new round (~120s)"""
        current_time = self.get_timer_seconds()
        
        if current_time is None:
            return False
            
        # Round start is when timer is approximately 120 seconds
        # Account for slight variations
        if 118 <= current_time <= 122:
            # Check if this is actually a new round start
            if self.last_round_start is None:
                self.last_round_start = datetime.now()
                return True
            else:
                # Don't trigger multiple times for same round
                time_since_last = (datetime.now() - self.last_round_start).total_seconds()
                if time_since_last > 60:  # At least 60 seconds since last start
                    self.last_round_start = datetime.now()
                    return True
        return False
    
    def is_scraping_allowed(self) -> bool:
        """
        Check if odds scraping is currently allowed
        Allowed only when timer > 10 seconds
        """
        current_time = self.get_timer_seconds()
        
        if current_time is None:
            return False
            
        # Scraping stops at 10 seconds remaining
        return current_time > 10
    
    def monitor_timer(self, 
                     on_round_start: Callable,
                     on_scraping_deadline: Callable,
                     check_interval: float = 1.0):
        """
        Monitor timer continuously
        Triggers callbacks based on timer events
        """
        last_round_start_state = False
        
        try:
            while True:
                current_seconds = self.get_timer_seconds()
                
                if current_seconds is not None:
                    # Check for round start
                    is_start = self.is_round_start()
                    if is_start and not last_round_start_state:
                        print(f"Round start detected at {current_seconds}s")
                        on_round_start()
                        last_round_start_state = True
                    elif not is_start:
                        last_round_start_state = False
                    
                    # Check for scraping deadline
                    if current_seconds <= 10:
                        print(f"Scraping deadline reached: {current_seconds}s remaining")
                        on_scraping_deadline()
                
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            print("Timer monitoring stopped")
        except Exception as e:
            print(f"Error in timer monitoring: {e}")