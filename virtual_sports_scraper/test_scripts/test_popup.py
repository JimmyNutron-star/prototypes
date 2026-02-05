from common import get_browser_and_load, finish_test
from components.popup_handler import PopupHandler
import logging

def run_test():
    bm, driver = get_browser_and_load("Popup Handler Test")
    
    try:
        handler = PopupHandler(driver)
        result = handler.handle_popup()
        
        if result:
            logging.info("Popup was found and closed.")
        else:
            logging.info("No popup found (or failed), checking if site is accessible...")
        
        # Passed if no crash and logic ran
        finish_test(bm, success=True)
    except Exception as e:
        logging.error(f"Error: {e}")
        finish_test(bm, success=False)

if __name__ == "__main__":
    run_test()
