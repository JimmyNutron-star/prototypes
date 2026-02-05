import time
import re
from selenium.webdriver.common.by import By
from config.selectors import ROUND_TIMER
import logging

class TimerWatcher:
    """
    Monitors the round timer.
    Enforces the 10s deadline rule.
    """
    def __init__(self, driver):
        self.driver = driver

    def get_time_remaining(self):
        """
        Returns time remaining in seconds.
        Returns 0 if timer not found or parse error.
        """
        try:
            # New selector targets .ss.active
            # Format is MM:SS
            element = self.driver.find_element(By.CSS_SELECTOR, ROUND_TIMER)
            text = element.text.strip()
            
            # Remove any non-time chars just in case
            text = text.split(" ")[0].strip()

            if ":" in text:
                parts = text.split(":")
                minutes = int(parts[0])
                seconds = int(parts[1])
                return (minutes * 60) + seconds
            else:
                return int(text)
        except Exception as e:
            # logging.debug(f"Timer read error: {e}") 
            # Can be noisy if element is missing briefly
            return 0

    def is_safe_to_scrape(self):
        """Returns True if time > 10s."""
        remaining = self.get_time_remaining()
        if remaining > 10:
            return True
        return False
