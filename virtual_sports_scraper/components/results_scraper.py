import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config.selectors import RESULTS_CONTAINER
import logging

class ResultsScraper:
    """
    Scrapes historical results.
    Scheduled every 30 mins (logic in main loop/test).
    """
    def __init__(self, driver):
        self.driver = driver

    def scrape_results(self):
        """Scrapes the results container."""
        try:
            # Assuming navigation to results page happens before calling this
            # The structure is .rs -> .rs-g
            # .rs-g contains .g-t (team names) and .g-s (scores)
            
            # Update: Check if .rs container exists
            # Wait briefly
            try:
                WebDriverWait(self.driver, 5).until(
                   EC.presence_of_element_located((By.CSS_SELECTOR, ".rs"))
                )
            except:
                logging.info("Results table not found immediately.")
                return []

            container = self.driver.find_element(By.CSS_SELECTOR, ".rs")
            # Find all result rows
            rows = container.find_elements(By.CSS_SELECTOR, ".rs-g")
            
            logging.info(f"Scraping {len(rows)} result rows.")
            
            results = []
            for row in rows:
                try:
                    # Teams: .g-t (2 elements)
                    teams = row.find_elements(By.CSS_SELECTOR, ".g-t")
                    # Scores: .g-s -> spans (2 elements)
                    scores_container = row.find_element(By.CSS_SELECTOR, ".g-s")
                    scores = scores_container.find_elements(By.TAG_NAME, "span")
                    
                    if len(teams) >= 2 and len(scores) >= 2:
                        home_team = teams[0].text.strip()
                        away_team = teams[1].text.strip()
                        home_score = scores[0].text.strip()
                        away_score = scores[1].text.strip()
                        
                        results.append({
                            "home_team": home_team,
                            "away_team": away_team,
                            "home_score": home_score,
                            "away_score": away_score,
                            "raw_str": f"{home_team} {home_score}-{away_score} {away_team}",
                            "timestamp": time.time()
                        })
                except Exception as inner_e:
                    continue
                    
            return results
        except Exception as e:
            logging.error(f"Results scraping error: {e}")
            return []
