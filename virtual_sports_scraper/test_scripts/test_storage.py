from common import setup_test_logger
from core.data_storage import DataStorage
import logging
import time
import os
from config.paths import ODDS_FILE

def run_test():
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting Storage Test")
    
    try:
        storage = DataStorage()
        
        # Test Data
        test_odds = [
            {"match_id": "TEST_1", "odds": [1.5, 2.0, 3.0], "timestamp": time.time()},
            {"match_id": "TEST_2", "odds": [1.1, 5.0, 8.0], "timestamp": time.time()}
        ]
        
        logging.info("Upserting test odds...")
        storage.upsert_odds(test_odds)
        
        # Verify file exists and contains data
        if os.path.exists(ODDS_FILE):
             logging.info(f"File created: {ODDS_FILE}")
             logging.info("TEST PASSED")
        else:
             logging.error("File was not created.")
             exit(1)
             
    except Exception as e:
        logging.error(f"Error: {e}")
        exit(1)

if __name__ == "__main__":
    run_test()
