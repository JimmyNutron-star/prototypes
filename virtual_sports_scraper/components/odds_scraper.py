from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config.selectors import MATCH_CONTAINER, TEAM_NAMES, ODDS_BUTTON
import logging

class OddsScraper:
    """
    Extracts odds data from the current page.
    """
    def __init__(self, driver):
        self.driver = driver

    def scrape_odds(self):
        """
        Scrapes all visible odds on the page.
        Returns a list of match dictionaries.
        """
        data = []
        try:
            # Wait for matches to load
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, MATCH_CONTAINER))
            )
            
            matches = self.driver.find_elements(By.CSS_SELECTOR, MATCH_CONTAINER)
            logging.info(f"Found {len(matches)} potential matches.")
            
            for match in matches:
                try:
                    # Extract teams
                    # The internal structure is .info -> .t -> .t-l (two divs for home/away)
                    team_names_els = match.find_elements(By.CSS_SELECTOR, TEAM_NAMES)
                    if len(team_names_els) >= 2:
                        home_team = team_names_els[0].text.strip()
                        away_team = team_names_els[1].text.strip()
                        teams_str = f"{home_team} vs {away_team}"
                    else:
                        continue # Skip if teams are not properly found
                    
                    # Extract odds
                    # .odds -> .o -> button
                    # The buttons contain <small class="o-1">label</small> <span class="o-2">value</span>
                    odds_els = match.find_elements(By.CSS_SELECTOR, ODDS_BUTTON)
                    odds_values = []
                    for btn in odds_els:
                        # get the whole text, e.g. "1\n3.00"
                        # or specifically target the value span if needed.
                        # For now, let's grab the full text spread
                        val = btn.text.replace("\n", " ").strip()
                        if val:
                            odds_values.append(val)
                    
                    if teams_str and odds_values:
                        match_data = {
                            "teams": teams_str,
                            "odds": odds_values,
                            "timestamp": time.time()
                        }
                        data.append(match_data)
                except Exception as inner_e:
                    # Skip incomplete matches
                    logging.debug(f"Skipping match due to error: {inner_e}")
                    continue
                    
            return data
        except Exception as e:
            logging.error(f"Error scraping odds: {e}")
            return []
