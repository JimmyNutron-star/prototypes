from common import get_browser_and_load, finish_test
from components.popup_handler import PopupHandler
from components.market_scraper import MarketScraper
from config.settings import MARKETS
import logging
import time
import random

def run_test():
    bm, driver = get_browser_and_load("Market Switching Test")
    
    try:
        PopupHandler(driver).handle_popup()
        scraper = MarketScraper(driver)
        
        test_sequence = []
        for _ in range(5):
            test_sequence.append(random.choice(MARKETS))
            
        logging.info(f"Testing switching sequence: {test_sequence}")
        
        for market in test_sequence:
            if not scraper.select_market(market):
                logging.error(f"Failed switch to {market}")
                finish_test(bm, success=False)
            time.sleep(0.5)
            
        finish_test(bm, success=True)
            
    except Exception as e:
        logging.error(f"Error: {e}")
        finish_test(bm, success=False)

if __name__ == "__main__":
    run_test()
