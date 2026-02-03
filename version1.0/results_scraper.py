# results_scraper.py
"""
Results Scraper - Scrapes completed match results
Runs on schedule (every 30 minutes), read-only
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List
from selenium.webdriver.common.by import By

class ResultsScraper:
    """Scrapes match results on schedule"""
    
    def __init__(self, driver, scrape_interval: int = 1800):  # 30 minutes default
        self.driver = driver
        self.scrape_interval = scrape_interval
        self.last_scrape = None
        self._stop_event = threading.Event()
        
    def navigate_to_results(self):
        """Navigate to results tab"""
        try:
            results_tab = self.driver.find_element(
                By.CSS_SELECTOR, "li.active"  # Adjust selector based on actual HTML
            )
            
            if "Results" not in results_tab.text:
                # Find and click results tab
                all_tabs = self.driver.find_elements(
                    By.CSS_SELECTOR, "ul.tbs li"
                )
                
                for tab in all_tabs:
                    if "Results" in tab.text:
                        tab.click()
                        time.sleep(2)
                        break
                        
            return True
        except Exception as e:
            print(f"Error navigating to results: {e}")
            return False
    
    def scrape_results(self) -> List[Dict]:
        """Scrape all available results"""
        results = []
        
        if not self.navigate_to_results():
            return results
        
        try:
            # Find all result containers
            result_containers = self.driver.find_elements(
                By.CSS_SELECTOR, "div.rs"
            )
            
            for container in result_containers:
                try:
                    # Extract matchday info
                    matchday_info = container.find_element(
                        By.CSS_SELECTOR, "div.rs-t div.t"
                    ).text.strip()
                    
                    # Extract timestamp
                    timestamp_elem = container.find_element(
                        By.CSS_SELECTOR, "div.rs-t div.b"
                    )
                    timestamp = timestamp_elem.text.strip()
                    
                    # Extract individual matches
                    match_items = container.find_elements(
                        By.CSS_SELECTOR, "div.rs-g"
                    )
                    
                    for match_item in match_items:
                        try:
                            team_elements = match_item.find_elements(
                                By.CSS_SELECTOR, "div.g-t"
                            )
                            
                            if len(team_elements) >= 2:
                                team1 = team_elements[0].text.strip()
                                team2 = team_elements[1].text.strip()
                                
                                # Extract scores
                                score_elements = match_item.find_elements(
                                    By.CSS_SELECTOR, "div.g-s span"
                                )
                                
                                if len(score_elements) >= 2:
                                    score1 = int(score_elements[0].text.strip())
                                    score2 = int(score_elements[1].text.strip())
                                    
                                    result = {
                                        "matchday": matchday_info,
                                        "timestamp": timestamp,
                                        "team1": team1,
                                        "team2": team2,
                                        "score1": score1,
                                        "score2": score2,
                                        "scraped_at": datetime.now().isoformat()
                                    }
                                    
                                    results.append(result)
                                    
                        except Exception as e:
                            print(f"Error parsing individual result: {e}")
                            continue
                            
                except Exception as e:
                    print(f"Error parsing result container: {e}")
                    continue
        
        except Exception as e:
            print(f"Error scraping results: {e}")
        
        print(f"Scraped {len(results)} match results")
        return results
    
    def save_results(self, results: List[Dict], filepath: str):
        """Save results to JSON file"""
        try:
            # Load existing results
            existing_data = []
            try:
                with open(filepath, 'r') as f:
                    existing_data = json.load(f)
            except FileNotFoundError:
                existing_data = []
            except json.JSONDecodeError:
                existing_data = []
            
            # Append new results (avoid duplicates)
            existing_match_keys = {
                f"{r.get('team1', '')}_{r.get('team2', '')}_{r.get('timestamp', '')}"
                for r in existing_data
            }
            
            for result in results:
                match_key = f"{result['team1']}_{result['team2']}_{result['timestamp']}"
                if match_key not in existing_match_keys:
                    existing_data.append(result)
            
            # Save all results
            with open(filepath, 'w') as f:
                json.dump(existing_data, f, indent=2, default=str)
            
            print(f"Saved {len(results)} new results to {filepath}")
            
        except Exception as e:
            print(f"Error saving results: {e}")
    
    def run_scheduled(self, results_file: str):
        """Run results scraping on schedule"""
        
        def scheduled_task():
            try:
                while not self._stop_event.is_set():
                    current_time = datetime.now()
                    
                    # Check if it's time to scrape
                    if (self.last_scrape is None or 
                        (current_time - self.last_scrape).total_seconds() >= self.scrape_interval):
                        
                        print("Starting scheduled results scrape...")
                        results = self.scrape_results()
                        
                        if results:
                            self.save_results(results, results_file)
                        
                        self.last_scrape = current_time
                        print(f"Next results scrape at: {current_time + timedelta(seconds=self.scrape_interval)}")
                    
                    time.sleep(60)  # Check every minute
                    
            except Exception as e:
                print(f"Error in scheduled results scraping: {e}")
        
        thread = threading.Thread(target=scheduled_task)
        thread.daemon = True
        thread.start()
        
        return thread
    
    def stop(self):
        """Stop scheduled scraping"""
        self._stop_event.set()