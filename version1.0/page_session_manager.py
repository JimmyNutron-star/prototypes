# page_session_manager.py
"""
Page Session Manager - Handles popup before any other logic
Critical requirement: Must run on every page load/reload
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time

class PageSessionManager:
    """Manages page sessions and handles roadblock popup"""
    
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
    
    def handle_popup(self) -> bool:
        """
        Handle the roadblock popup
        Returns: True if popup handled successfully, False otherwise
        """
        try:
            # Wait for popup to appear
            popup = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.roadblock"))
            )
            
            print("Popup detected. Attempting to close...")
            
            # Find and click close button
            close_button = popup.find_element(By.CSS_SELECTOR, "div.roadblock-close button")
            close_button.click()
            
            # Wait for popup to disappear
            self.wait.until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.roadblock"))
            )
            
            print("Popup closed successfully")
            
            # Verify page is interactive
            time.sleep(1)  # Brief pause for page stabilization
            
            return True
            
        except TimeoutException:
            print("No popup found or popup already closed")
            return True  # No popup is acceptable
            
        except NoSuchElementException:
            print("Could not find popup close button")
            return False
            
        except Exception as e:
            print(f"Error handling popup: {e}")
            return False
    
    def ensure_page_ready(self) -> bool:
        """
        Ensures page is ready for interaction
        Must be called before any other component runs
        """
        try:
            # First handle popup
            if not self.handle_popup():
                return False
            
            # Wait for main content to be visible
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.virtual-logos"))
            )
            
            print("Page is ready for scraping")
            return True
            
        except Exception as e:
            print(f"Page not ready: {e}")
            return False
    
    def reload_and_handle_popup(self) -> bool:
        """Reload page and handle popup again"""
        print("Reloading page...")
        self.driver.refresh()
        time.sleep(2)
        return self.ensure_page_ready()