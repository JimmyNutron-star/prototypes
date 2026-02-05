import sys
import os
import time
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.browser_manager import BrowserManager
from config.settings import BASE_URL

def setup_test_logger(test_name):
    logging.basicConfig(level=logging.INFO, 
                        format=f'%(asctime)s - [{test_name}] - %(levelname)s - %(message)s')
    logging.info(f"STARTING TEST: {test_name}")

def get_browser_and_load(test_name="Generic Test"):
    setup_test_logger(test_name)
    bm = BrowserManager()
    driver = bm.start_browser()
    
    try:
        logging.info(f"Navigating to {BASE_URL}")
        driver.get(BASE_URL)
        return bm, driver
    except Exception as e:
        logging.error(f"Failed to load page: {e}")
        bm.close_browser()
        sys.exit(1)

def finish_test(bm, success=True):
    if success:
        logging.info("TEST PASSED")
    else:
        logging.error("TEST FAILED")
    
    bm.close_browser()
    sys.exit(0 if success else 1)
