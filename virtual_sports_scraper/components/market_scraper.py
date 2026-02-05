from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config.selectors import MARKET_DROPDOWN, MARKET_OPTION_TEMPLATE
import logging
import time

class MarketScraper:
    """
    Handles Market selection (26+ markets).
    """
    def __init__(self, driver):
        self.driver = driver

    def select_market(self, market_name):
        """
        Selects a market by name.
        """
        try:
            logging.info(f"Selecting Market: {market_name}")
            dropdown = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, MARKET_DROPDOWN))
            )
            dropdown.click()
            time.sleep(0.5)

            # Construct XPath definition
            xpath = MARKET_OPTION_TEMPLATE.format(market_name)
            option = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            option.click()
            time.sleep(1) # Wait for table update
            logging.info(f"Successfully selected {market_name}")
            return True
        except Exception as e:
            logging.error(f"Failed to select market {market_name}: {e}")
            return False
