"""
Base scraper class with common functionality
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import time
from config import HEADLESS_MODE, BROWSER_WAIT_TIME, USER_AGENT
from utils.logger import ScraperLogger
from utils.file_handler import FileHandler

class BaseScraper:
    def __init__(self, scraper_name):
        """Initialize base scraper"""
        self.scraper_name = scraper_name
        self.logger = ScraperLogger(scraper_name)
        self.driver = None
        self.wait = None
        self.file_handler = FileHandler(scraper_name)
        self.initialize_browser()
    
    def initialize_browser(self):
        """Initialize Chrome browser"""
        try:
            chrome_options = Options()
            if HEADLESS_MODE:
                chrome_options.add_argument('--headless')
            
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument(f'--user-agent={USER_AGENT}')
            chrome_options.add_argument('--log-level=3')
            
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            self.wait = WebDriverWait(self.driver, BROWSER_WAIT_TIME)
            
            self.logger.info(f"Browser initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize browser: {e}")
            return False
    
    def navigate_to_url(self, url):
        """Navigate to URL with error handling"""
        try:
            self.logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            time.sleep(3)  # Initial page load
            
            # Verify page loaded
            if self.driver.current_url:
                self.logger.info(f"Page loaded successfully: {self.driver.current_url}")
                return True
            else:
                self.logger.error("Page failed to load")
                return False
                
        except Exception as e:
            self.logger.error(f"Navigation error: {e}")
            return False
    
    def close_popup(self):
        """Close any popups on the page"""
        try:
            time.sleep(2)
            popup_close = self.driver.find_element(By.CSS_SELECTOR, ".roadblock-close button")
            if popup_close:
                popup_close.click()
                self.logger.info("Popup closed")
                time.sleep(1)
                return True
        except:
            self.logger.info("No popup found")
            return False
    
    def safe_find_element(self, selector, by=By.CSS_SELECTOR, timeout=10):
        """Safely find element with timeout"""
        try:
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.presence_of_element_located((by, selector)))
            return element
        except TimeoutException:
            self.logger.warning(f"Element not found: {selector}")
            return None
        except Exception as e:
            self.logger.error(f"Error finding element {selector}: {e}")
            return None
    
    def safe_find_elements(self, selector, by=By.CSS_SELECTOR, timeout=10):
        """Safely find multiple elements"""
        try:
            wait = WebDriverWait(self.driver, timeout)
            wait.until(EC.presence_of_element_located((by, selector)))
            elements = self.driver.find_elements(by, selector)
            return elements
        except TimeoutException:
            self.logger.warning(f"Elements not found: {selector}")
            return []
        except Exception as e:
            self.logger.error(f"Error finding elements {selector}: {e}")
            return []
    
    def get_league_info(self):
        """Get current league and timer information"""
        try:
            league_info = {}
            
            # Get active league
            league_element = self.safe_find_element(".virtual-logos .logo.active .text-xs")
            if league_element:
                league_info['league'] = league_element.text.strip()
            
            # Get current timer
            timer_element = self.safe_find_element(".virtual-timer .ss.active")
            if timer_element:
                league_info['timer'] = timer_element.text.strip()
            
            return league_info
            
        except Exception as e:
            self.logger.error(f"Error getting league info: {e}")
            return {}
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.driver:
                self.driver.quit()
                self.logger.info("Browser closed")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def save_data(self, data, prefix=""):
        """Save data using file handler"""
        try:
            saved_files = self.file_handler.save_all_formats(data, prefix)
            for file_type, file_path in saved_files.items():
                if file_path:
                    self.logger.info(f"Data saved as {file_type}: {file_path}")
            return saved_files
        except Exception as e:
            self.logger.error(f"Error saving data: {e}")
            return {}