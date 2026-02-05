from common import get_browser_and_load, finish_test
import logging
import time

def run_test():
    bm, driver = get_browser_and_load("Navigation Test")
    
    try:
        # Simple check if current URL matches base URL or we have a body
        if driver.current_url:
            logging.info(f"Current URL: {driver.current_url}")
            body = driver.find_element("tag name", "body")
            if body:
                logging.info("Page body detected.")
                finish_test(bm, success=True)
            else:
                logging.error("Body not found")
                finish_test(bm, success=False)
        else:
            logging.error("No URL detected")
            finish_test(bm, success=False)
            
    except Exception as e:
        logging.error(f"Navigation error: {e}")
        finish_test(bm, success=False)

if __name__ == "__main__":
    run_test()
