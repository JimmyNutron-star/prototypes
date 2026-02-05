from common import get_browser_and_load, finish_test
from components.popup_handler import PopupHandler
from components.market_scraper import MarketScraper
from config.settings import MARKETS
import logging
import argparse

def run_test():
    parser = argparse.ArgumentParser(description="Test selecting a specific market.")
    parser.add_argument("--market", type=str, default=MARKETS[0], help="Name of the market to test")
    args = parser.parse_args()
    
    market_to_test = args.market
    
    bm, driver = get_browser_and_load(f"Test Selected Market: {market_to_test}")
    
    try:
        PopupHandler(driver).handle_popup()
        scraper = MarketScraper(driver)
        
        if scraper.select_market(market_to_test):
            logging.info(f"Successfully selected market: {market_to_test}")
            finish_test(bm, success=True)
        else:
            logging.error(f"Failed to select market: {market_to_test}")
            finish_test(bm, success=False)
            
    except Exception as e:
        logging.error(f"Error: {e}")
        finish_test(bm, success=False)

if __name__ == "__main__":
    run_test()
