import time
from selenium.webdriver.common.by import By
from config.selectors import GOAL_EVENT
import logging

class GoalWatcher:
    """
    Monitors for goal events during LIVE match.
    Append-only logic handled by DataStorage, but this component detects them.
    """
    def __init__(self, driver, data_storage, match_id):
        self.driver = driver
        self.storage = data_storage
        self.match_id = match_id
        self.captured_goals = set() # Avoid duplicates in memory for this session

    def check_for_goals(self):
        """Scans for new goal alerts."""
        try:
            elements = self.driver.find_elements(By.CSS_SELECTOR, GOAL_EVENT)
            for el in elements:
                text = el.text.strip()
                if text and text not in self.captured_goals:
                    logging.info(f"New Goal Detected: {text}")
                    self.captured_goals.add(text)
                    
                    goal_data = {
                        "match_id": self.match_id,
                        "event": text,
                        "timestamp": time.time()
                    }
                    self.storage.append_goal(goal_data)
        except Exception as e:
            logging.error(f"Goal watcher error: {e}")
