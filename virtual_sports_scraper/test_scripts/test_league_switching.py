from common import get_browser_and_load, finish_test
from components.popup_handler import PopupHandler
from components.league_scraper import LeagueScraper
from config.settings import LEAGUES
import logging
import time
import random

def run_test():
    bm, driver = get_browser_and_load("League Switching Test")
    
    try:
        PopupHandler(driver).handle_popup()
        scraper = LeagueScraper(driver)
        
        # Select 3 random transitions
        test_sequence = []
        for _ in range(3):
            test_sequence.append(random.choice(LEAGUES))
            
        logging.info(f"Testing switching sequence: {test_sequence}")
        
        for league in test_sequence:
            if not scraper.select_league(league):
                logging.error(f"Failed switch to {league}")
                finish_test(bm, success=False)
            time.sleep(1)
            
        finish_test(bm, success=True)
            
    except Exception as e:
        logging.error(f"Error: {e}")
        finish_test(bm, success=False)

if __name__ == "__main__":
    run_test()
