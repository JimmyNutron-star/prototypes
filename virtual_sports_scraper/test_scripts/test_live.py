from common import get_browser_and_load, finish_test
from components.live_watcher import LiveWatcher
import logging

def run_test():
    bm, driver = get_browser_and_load("Live Match Test")
    
    try:
        live_watcher = LiveWatcher(driver)
        is_live = live_watcher.is_live()
        
        logging.info(f"Is Match Live? {is_live}")
        
        # This test passes if it runs without error, regardless of True/False
        finish_test(bm, success=True)
            
    except Exception as e:
        logging.error(f"Error: {e}")
        finish_test(bm, success=False)

if __name__ == "__main__":
    run_test()
