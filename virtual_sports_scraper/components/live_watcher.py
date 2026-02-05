from selenium.webdriver.common.by import By
from config.selectors import LIVE_BADGE
import logging

class LiveWatcher:
    """
    Detects if the match is currently LIVE.
    This is a HARD TRIGGER to stop scraping odds.
    """
    def __init__(self, driver):
        self.driver = driver

    def is_live(self):
        """Returns True if LIVE badge is present."""
        try:
            elements = self.driver.find_elements(By.CSS_SELECTOR, LIVE_BADGE)
            if elements:
                for el in elements:
                    if el.is_displayed():
                        return True
            return False
        except Exception:
            return False
