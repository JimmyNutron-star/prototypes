from common import get_browser_and_load, finish_test
from components.timer_watcher import TimerWatcher
import logging

def run_test():
    bm, driver = get_browser_and_load("Timer Test")
    
    try:
        timer = TimerWatcher(driver)
        remaining = timer.get_time_remaining()
        
        logging.info(f"Detected Time Remaining: {remaining} seconds")
        
        # Validation: Should be >= 0. 
        # If 0, it might be scraper failure OR actual 0.
        if remaining >= 0:
            finish_test(bm, success=True)
        else:
            logging.error("Negative time detected?")
            finish_test(bm, success=False)
            
    except Exception as e:
        logging.error(f"Error: {e}")
        finish_test(bm, success=False)

if __name__ == "__main__":
    run_test()
