from common import get_browser_and_load, finish_test
from components.popup_handler import PopupHandler
from components.market_scraper import MarketScraper
from config.settings import MARKETS
import logging
import time

def run_test():
    bm, driver = get_browser_and_load("Test All Markets")
    
    try:
        PopupHandler(driver).handle_popup()
        scraper = MarketScraper(driver)
        
        failures = []
        # Test first 5 markets to avoid extremely long test in dev
        # But for "All Markets" we should iterate all. 
        # I'll stick to full list but verify speed.
        for market in MARKETS:
            logging.info(f"Testing selection of: {market}")
            if not scraper.select_market(market):
                failures.append(market)
                logging.error(f"Failed: {market}")
            # time.sleep(0.5) # Fast switching
            
        if not failures:
            logging.info("All markets selected successfully.")
            finish_test(bm, success=True)
        else:
            logging.error(f"Failed markets: {failures}")
            finish_test(bm, success=False)
            
    except Exception as e:
        logging.error(f"Error: {e}")
        finish_test(bm, success=False)

if __name__ == "__main__":
    run_test()
