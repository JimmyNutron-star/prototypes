from common import get_browser_and_load, finish_test
from components.popup_handler import PopupHandler
from components.standings_scraper import StandingsScraper
import logging

def run_test():
    bm, driver = get_browser_and_load("Standings Scraper Test")
    
    try:
        PopupHandler(driver).handle_popup()
        scraper = StandingsScraper(driver)
        
        standings = scraper.scrape_standings()
        if standings:
            logging.info(f"Scraped {len(standings)} standing rows.")
            finish_test(bm, success=True)
        else:
            logging.warning("No standings found.")
            finish_test(bm, success=True)
            
    except Exception as e:
        logging.error(f"Error: {e}")
        finish_test(bm, success=False)

if __name__ == "__main__":
    run_test()
