from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config.selectors import LEAGUE_DROPDOWN, LEAGUE_OPTION_TEMPLATE
import logging
import time

class LeagueScraper:
    """
    Handles League selection and navigation.
    """
    def __init__(self, driver):
        self.driver = driver

    def select_league(self, league_name):
        """
        Selects a league by name finding the matching logo container.
        """
        try:
            logging.info(f"Selecting League: {league_name}")
            # The leagues are presented as logos in a flex container (.virtual-logos)
            # Each .logo div has a child text element describing the league
            
            # Wait for logos to be present
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".virtual-logos .logo"))
            )
            
            # Find the specific logo for the league
            # We look for the text inside the logo container
            logos = self.driver.find_elements(By.CSS_SELECTOR, ".virtual-logos .logo")
            
            target_logo = None
            for logo in logos:
                if league_name.lower() in logo.text.strip().lower():
                    target_logo = logo
                    break
            
            if target_logo:
                # scroll into view if needed
                self.driver.execute_script("arguments[0].scrollIntoView(true);", target_logo)
                time.sleep(0.5)
                target_logo.click()
                logging.info(f"Successfully selected {league_name}")
                return True
            else:
                logging.warning(f"League '{league_name}' not found in available logos.")
                return False

        except Exception as e:
            logging.error(f"Failed to select league {league_name}: {e}")
            return False
