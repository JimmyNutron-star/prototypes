from common import get_browser_and_load, finish_test
from components.popup_handler import PopupHandler
from components.market_scraper import MarketScraper
from components.odds_scraper import OddsScraper
from components.timer_watcher import TimerWatcher
from core.state_manager import StateManager
from config.settings import MARKETS
import logging
import argparse

def run_test():
    parser = argparse.ArgumentParser(description="Test odds scraping for a market.")
    parser.add_argument("--market", type=str, default=MARKETS[0])
    args = parser.parse_args()
    
    bm, driver = get_browser_and_load(f"Test Odds: {args.market}")
    
    try:
        PopupHandler(driver).handle_popup()
        market_scraper = MarketScraper(driver)
        odds_scraper = OddsScraper(driver)
        timer = TimerWatcher(driver)
        
        if not market_scraper.select_market(args.market):
            logging.error("Failed to select market")
            finish_test(bm, success=False)
            
        # Test scraping single pass
        remaining = timer.get_time_remaining()
        logging.info(f"Time remaining: {remaining}s")
        
        if remaining > 10:
            data = odds_scraper.scrape_odds()
            logging.info(f"Scraped {len(data)} matches from {args.market}")
            finish_test(bm, success=True)
        else:
            logging.info("Timer too low, skipping scrape test.")
            finish_test(bm, success=True)
            
    except Exception as e:
        logging.error(f"Error: {e}")
        finish_test(bm, success=False)

if __name__ == "__main__":
    run_test()
