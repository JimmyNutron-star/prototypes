# standings_scraper.py
"""
Standings Scraper - Scrapes league standings
Runs on schedule (every 30 minutes), read-only
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List
from selenium.webdriver.common.by import By

class StandingsScraper:
    """Scrapes league standings on schedule"""
    
    def __init__(self, driver, scrape_interval: int = 1800):  # 30 minutes default
        self.driver = driver
        self.scrape_interval = scrape_interval
        self.last_scrape = None
        self._stop_event = threading.Event()
        
    def navigate_to_standings(self):
        """Navigate to standings tab"""
        try:
            standings_tab = self.driver.find_element(
                By.CSS_SELECTOR, "li"  # Adjust selector based on actual HTML
            )
            
            if "Standings" not in standings_tab.text:
                # Find and click standings tab
                all_tabs = self.driver.find_elements(
                    By.CSS_SELECTOR, "ul.tbs li"
                )
                
                for tab in all_tabs:
                    if "Standings" in tab.text:
                        tab.click()
                        time.sleep(2)
                        break
                        
            return True
        except Exception as e:
            print(f"Error navigating to standings: {e}")
            return False
    
    def scrape_standings(self) -> Dict:
        """Scrape league standings"""
        standings = {
            "league": "",
            "season": "",
            "teams": [],
            "scraped_at": datetime.now().isoformat()
        }
        
        if not self.navigate_to_standings():
            return standings
        
        try:
            # Extract league and season info
            title_elem = self.driver.find_element(
                By.CSS_SELECTOR, "div.virtual-standings div.title"
            )
            title_text = title_elem.text.strip()
            standings["league"] = title_text.split("Season")[0].strip()
            standings["season"] = title_text
            
            # Scrape standings table
            table_rows = self.driver.find_elements(
                By.CSS_SELECTOR, "div.virtual-standings table tbody tr"
            )
            
            for row in table_rows:
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    
                    if len(cells) >= 4:
                        position = cells[0].text.strip()
                        team_name = cells[1].text.strip()
                        points = cells[2].text.strip()
                        
                        # Extract form (last 5 games)
                        form_cells = cells[3].find_elements(
                            By.CSS_SELECTOR, "div"
                        )
                        form = [cell.text.strip() for cell in form_cells]
                        
                        team_standing = {
                            "position": int(position),
                            "team": team_name,
                            "points": int(points),
                            "form": form
                        }
                        
                        standings["teams"].append(team_standing)
                        
                except Exception as e:
                    print(f"Error parsing standings row: {e}")
                    continue
        
        except Exception as e:
            print(f"Error scraping standings: {e}")
        
        print(f"Scraped standings for {len(standings['teams'])} teams")
        return standings
    
    def save_standings(self, standings: Dict, filepath: str):
        """Save standings to JSON file"""
        try:
            # Load existing standings
            existing_data = []
            try:
                with open(filepath, 'r') as f:
                    existing_data = json.load(f)
            except FileNotFoundError:
                existing_data = []
            except json.JSONDecodeError:
                existing_data = []
            
            # Check if we already have this season's standings
            season_exists = False
            for existing in existing_data:
                if existing.get("season") == standings.get("season"):
                    # Update existing entry
                    existing.update(standings)
                    season_exists = True
                    break
            
            # If new season, add it
            if not season_exists:
                existing_data.append(standings)
            
            # Save all standings
            with open(filepath, 'w') as f:
                json.dump(existing_data, f, indent=2, default=str)
            
            print(f"Saved standings to {filepath}")
            
        except Exception as e:
            print(f"Error saving standings: {e}")
    
    def run_scheduled(self, standings_file: str):
        """Run standings scraping on schedule"""
        
        def scheduled_task():
            try:
                while not self._stop_event.is_set():
                    current_time = datetime.now()
                    
                    # Check if it's time to scrape
                    if (self.last_scrape is None or 
                        (current_time - self.last_scrape).total_seconds() >= self.scrape_interval):
                        
                        print("Starting scheduled standings scrape...")
                        standings = self.scrape_standings()
                        
                        if standings["teams"]:
                            self.save_standings(standings, standings_file)
                        
                        self.last_scrape = current_time
                        print(f"Next standings scrape at: {current_time + timedelta(seconds=self.scrape_interval)}")
                    
                    time.sleep(60)  # Check every minute
                    
            except Exception as e:
                print(f"Error in scheduled standings scraping: {e}")
        
        thread = threading.Thread(target=scheduled_task)
        thread.daemon = True
        thread.start()
        
        return thread
    
    def stop(self):
        """Stop scheduled scraping"""
        self._stop_event.set()