# league_controller.py
"""
League Controller - Manages scraping for individual leagues
Each league operates independently and in parallel
"""

import threading
import time
from typing import List, Dict
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

class LeagueController:
    """Controls scraping for a single league"""
    
    def __init__(self, driver, league_name: str, league_element):
        self.driver = driver
        self.league_name = league_name
        self.league_element = league_element
        self.is_active = False
        self.market_scrapers = []
        self._stop_event = threading.Event()
        
    def activate_league(self):
        """Activate this league by clicking on it"""
        try:
            if "active" not in self.league_element.get_attribute("class"):
                self.league_element.click()
                time.sleep(1)  # Wait for league to load
                print(f"Activated league: {self.league_name}")
            self.is_active = True
            return True
        except Exception as e:
            print(f"Error activating league {self.league_name}: {e}")
            return False
    
    def scrape_matches(self) -> List[Dict]:
        """Scrape all matches for this league"""
        if not self.is_active:
            print(f"League {self.league_name} not active")
            return []
        
        try:
            matches = []
            match_elements = self.driver.find_elements(
                By.CSS_SELECTOR, "div.game.e"
            )
            
            for i, match_elem in enumerate(match_elements):
                try:
                    # Extract match information
                    team_elements = match_elem.find_elements(
                        By.CSS_SELECTOR, "div.t-l"
                    )
                    
                    if len(team_elements) >= 2:
                        team1 = team_elements[0].text.strip()
                        team2 = team_elements[1].text.strip()
                        
                        match_id = f"{self.league_name}_{team1}_{team2}_{int(time.time())}"
                        
                        matches.append({
                            "match_id": match_id,
                            "league": self.league_name,
                            "team1": team1,
                            "team2": team2,
                            "element": match_elem
                        })
                        
                except Exception as e:
                    print(f"Error parsing match {i} in {self.league_name}: {e}")
                    continue
            
            print(f"Found {len(matches)} matches in {self.league_name}")
            return matches
            
        except Exception as e:
            print(f"Error scraping matches for {self.league_name}: {e}")
            return []
    
    def start_scraping(self, state_manager, on_complete=None):
        """Start scraping process for this league"""
        if self._stop_event.is_set():
            return
        
        def scrape_task():
            try:
                # Activate league
                if not self.activate_league():
                    return
                
                # Scrape matches
                matches = self.scrape_matches()
                
                # Process each match
                for match_info in matches:
                    if self._stop_event.is_set():
                        break
                    
                    # Register match with state manager
                    state_manager.create_match(
                        match_info["match_id"],
                        match_info["league"],
                        match_info["team1"],
                        match_info["team2"]
                    )
                
                if on_complete:
                    on_complete(self.league_name, matches)
                    
            except Exception as e:
                print(f"Error in league scraping task for {self.league_name}: {e}")
        
        # Run in separate thread
        thread = threading.Thread(target=scrape_task)
        thread.daemon = True
        thread.start()
        
        return thread
    
    def stop(self):
        """Stop scraping for this league"""
        self._stop_event.set()
        self.is_active = False
        print(f"Stopped league controller: {self.league_name}")