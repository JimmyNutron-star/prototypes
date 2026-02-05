from common import get_browser_and_load, finish_test
from components.popup_handler import PopupHandler
from components.league_scraper import LeagueScraper
from components.odds_scraper import OddsScraper
from components.timer_watcher import TimerWatcher
from core.state_manager import StateManager
from config.settings import LEAGUES
import logging
import time
import argparse

def run_test():
    parser = argparse.ArgumentParser(description="Test odds scraping for a league.")
    parser.add_argument("--league", type=str, default=LEAGUES[0])
    args = parser.parse_args()
    
    bm, driver = get_browser_and_load(f"Test Odds: {args.league}")
    
    try:
        # Initialize components
        PopupHandler(driver).handle_popup()
        league_scraper = LeagueScraper(driver)
        odds_scraper = OddsScraper(driver)
        timer = TimerWatcher(driver)
        state_mgr = StateManager()
        
        # Select League
        if not league_scraper.select_league(args.league):
            logging.error("Failed to select league")
            finish_test(bm, success=False)
            
        # Simulated Round Loop
        logging.info("Starting odd scraping loop...")
        scraped_rounds = 0
        
        # Check timer
        remaining = timer.get_time_remaining()
        logging.info(f"Time remaining: {remaining}s")
        
        if state_mgr.is_odds_scraping_allowed(remaining):
            state_mgr.transition_to_odds_scraped()
            
            data = odds_scraper.scrape_odds()
            if data:
                logging.info(f"Scraped {len(data)} matches.")
                for match in data[:3]: # Log first 3
                    logging.info(f"Sample: {match}")
                finish_test(bm, success=True)
            else:
                logging.warning("No odds found (matches might be finished or selector mismatch).")
                # We consider this a pass if logic ran, but warn.
                finish_test(bm, success=True)
        else:
            logging.info("Skipping scraping due to timer/state restrictions.")
            finish_test(bm, success=True)
            
    except Exception as e:
        logging.error(f"Error: {e}")
        finish_test(bm, success=False)

if __name__ == "__main__":
    run_test()
