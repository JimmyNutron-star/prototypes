from common import setup_test_logger
from core.browser_manager import BrowserManager
import logging
import sys

def run_test():
    setup_test_logger("Browser Setup Test")
    
    try:
        bm = BrowserManager()
        driver = bm.start_browser()
        title = driver.title
        logging.info(f"Browser started successfully. Page title: {title}")
        
        # Verify it's working
        if driver is not None:
            bm.close_browser()
            logging.info("TEST PASSED")
            sys.exit(0)
    except Exception as e:
        logging.error(f"Browser test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_test()
