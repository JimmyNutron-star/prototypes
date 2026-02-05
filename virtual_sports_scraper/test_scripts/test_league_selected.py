from common import get_browser_and_load, finish_test
from components.popup_handler import PopupHandler
from components.league_scraper import LeagueScraper
from config.settings import LEAGUES
import logging
import argparse
import sys

def run_test():
    parser = argparse.ArgumentParser(description="Test selecting a specific league.")
    parser.add_argument("--league", type=str, default=LEAGUES[0], help="Name of the league to test")
    args = parser.parse_args()
    
    league_to_test = args.league
    
    bm, driver = get_browser_and_load(f"Test Selected League: {league_to_test}")
    
    try:
        # Handle popup first
        PopupHandler(driver).handle_popup()
        
        scraper = LeagueScraper(driver)
        success = scraper.select_league(league_to_test)
        
        if success:
            logging.info(f"Successfully scraped/selected league: {league_to_test}")
            finish_test(bm, success=True)
        else:
            logging.error(f"Failed to select league: {league_to_test}")
            finish_test(bm, success=False)
            
    except Exception as e:
        logging.error(f"Error: {e}")
        finish_test(bm, success=False)

if __name__ == "__main__":
    run_test()
