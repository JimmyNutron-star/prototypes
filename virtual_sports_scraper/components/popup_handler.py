import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config.settings import POPUP_CHECK_TIMEOUT
from config.selectors import POPUP_CLOSE_BUTTON
import logging

class PopupHandler:
    """
    Handles initial popups that might block interaction.
    MUST run before any other scraping logic.
    """
    def __init__(self, driver):
        self.driver = driver

    def handle_popup(self):
        """Checks for and closes popup if present."""
        try:
            logging.info("Checking for startup popups...")
            # Wait briefly for popup
            wait = WebDriverWait(self.driver, POPUP_CHECK_TIMEOUT)
            close_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, POPUP_CLOSE_BUTTON)))
            
            if close_btn:
                logging.info("Popup detected. Closing...")
                close_btn.click()
                time.sleep(1) # Wait for animation
                logging.info("Popup closed.")
                return True
        except Exception:
            logging.info("No popup detected or failed to close.")
            return False
