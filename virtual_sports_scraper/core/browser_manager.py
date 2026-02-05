from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import logging
from config.settings import HEADLESS_MODE, WINDOW_SIZE, IMPLICIT_WAIT, PAGE_LOAD_TIMEOUT

class BrowserManager:
    """
    Manages Selenium WebDriver instances.
    """
    def __init__(self):
        self.driver = None

    def start_browser(self):
        """Initializes and returns a Chrome WebDriver."""
        if self.driver:
            return self.driver

        options = Options()
        if HEADLESS_MODE:
            options.add_argument("--headless")
        
        # Standard options for stability
        options.add_argument(f"--window-size={WINDOW_SIZE}")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        try:
            logging.info("Starting Chrome Driver...")
            service = ChromeService(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.implicitly_wait(IMPLICIT_WAIT)
            self.driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
            logging.info("Browser started successfully.")
            return self.driver
        except Exception as e:
            logging.error(f"Failed to start browser: {e}")
            raise e

    def close_browser(self):
        """ safely closes the browser."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            finally:
                self.driver = None
