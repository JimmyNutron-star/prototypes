import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config.selectors import STANDINGS_TABLE
import logging

class StandingsScraper:
    """
    Scrapes league standings.
    Scheduled every 30 mins.
    """
    def __init__(self, driver):
        self.driver = driver

    def scrape_standings(self):
        """Scrapes the standings table."""
        try:
            # Wait for table
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, STANDINGS_TABLE))
            )
            # Assuming navigation to standings page happens before calling this
            table = self.driver.find_element(By.CSS_SELECTOR, STANDINGS_TABLE)
            rows = table.find_elements(By.TAG_NAME, "tr")
            logging.info(f"Scraping {len(rows)} standing rows.")
            
            standings = []
            for row in rows:
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) > 1:
                    standings.append({
                        "raw_data": [c.text for c in cols],
                        "timestamp": time.time()
                    })
            return standings
        except Exception as e:
            logging.error(f"Standings scraping error: {e}")
            return []
