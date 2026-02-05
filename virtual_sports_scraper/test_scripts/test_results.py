from common import get_browser_and_load, finish_test
from components.popup_handler import PopupHandler
from components.results_scraper import ResultsScraper
from core.data_storage import DataStorage
import logging

def run_test():
    bm, driver = get_browser_and_load("Results Scraper Test")
    
    try:
        PopupHandler(driver).handle_popup()
        scraper = ResultsScraper(driver)
        storage = DataStorage()
        
        # Navigate strictly if needed (omitted for generic test, assuming on page)
        
        results = scraper.scrape_results()
        if results:
            logging.info(f"Scraped {len(results)} results.")
            storage.save_results(results)
            finish_test(bm, success=True)
        else:
            logging.warning("No results found.")
            finish_test(bm, success=True)
            
    except Exception as e:
        logging.error(f"Error: {e}")
        finish_test(bm, success=False)

if __name__ == "__main__":
    run_test()
