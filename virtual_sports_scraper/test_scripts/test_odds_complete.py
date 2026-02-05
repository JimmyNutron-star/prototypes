from common import get_browser_and_load, finish_test
from components.popup_handler import PopupHandler
from components.league_scraper import LeagueScraper
from components.market_scraper import MarketScraper
from components.odds_scraper import OddsScraper
from config.settings import LEAGUES, MARKETS
import logging
import random

def run_test():
    bm, driver = get_browser_and_load("Complete Odds Test")
    
    try:
        PopupHandler(driver).handle_popup()
        l_scraper = LeagueScraper(driver)
        m_scraper = MarketScraper(driver)
        o_scraper = OddsScraper(driver)
        
        # Test a random combination
        league = random.choice(LEAGUES)
        market = random.choice(MARKETS[:5]) # Pick from first 5 for speed
        
        logging.info(f"Testing Combination: {league} + {market}")
        
        if not l_scraper.select_league(league):
            finish_test(bm, success=False)
        
        if not m_scraper.select_market(market):
            finish_test(bm, success=False)
            
        data = o_scraper.scrape_odds()
        logging.info(f"Scraped {len(data)} matches.")
        
        finish_test(bm, success=True)
            
    except Exception as e:
        logging.error(f"Error: {e}")
        finish_test(bm, success=False)

if __name__ == "__main__":
    run_test()
