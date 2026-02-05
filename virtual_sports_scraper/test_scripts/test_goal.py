from common import get_browser_and_load, finish_test
from components.goal_watcher import GoalWatcher
from core.data_storage import DataStorage
import logging
import time

def run_test():
    bm, driver = get_browser_and_load("Goal Watcher Test")
    
    try:
        storage = DataStorage()
        # Fake match ID for testing
        watcher = GoalWatcher(driver, storage, match_id="TEST_MATCH_001")
        
        logging.info("Scanning for goals for 5 seconds...")
        start = time.time()
        while time.time() - start < 5:
            watcher.check_for_goals()
            time.sleep(1)
            
        logging.info("Finished scanning.")
        finish_test(bm, success=True)
            
    except Exception as e:
        logging.error(f"Error: {e}")
        finish_test(bm, success=False)

if __name__ == "__main__":
    run_test()
