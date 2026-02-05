from common import get_browser_and_load, finish_test
from components.popup_handler import PopupHandler
from components.league_scraper import LeagueScraper
from config.settings import LEAGUES
import logging
import time

def run_test():
    bm, driver = get_browser_and_load("Test All Leagues")
    
    try:
        PopupHandler(driver).handle_popup()
        scraper = LeagueScraper(driver)
        
        failures = []
        for league in LEAGUES:
            logging.info(f"Testing selection of: {league}")
            if not scraper.select_league(league):
                failures.append(league)
                logging.error(f"Failed: {league}")
            else:
                logging.info(f"Passed: {league}")
            time.sleep(2) # Pause for visibility
            
        if not failures:
            logging.info("All leagues selected successfully.")
            finish_test(bm, success=True)
        else:
            logging.error(f"Failed leagues: {failures}")
            finish_test(bm, success=False)
            
    except Exception as e:
        logging.error(f"Error: {e}")
        finish_test(bm, success=False)

if __name__ == "__main__":
    run_test()
