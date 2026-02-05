
"""
Standings scraper - extracts league table data
"""

from datetime import datetime
import time
from selenium.webdriver.common.by import By  # ADD THIS IMPORT
from scrapers.base_scraper import BaseScraper
from config import ODILEAGUE_URL

class StandingsScraper(BaseScraper):
    def __init__(self):
        super().__init__("standings")
    
    def scrape_standings(self):
        """Scrape standings data"""
        try:
            self.logger.info("Starting standings scrape...")
            
            # Navigate to page
            if not self.navigate_to_url(ODILEAGUE_URL):
                return None
            
            # Close popup
            self.close_popup()
            
            # Switch to Standings tab
            if not self.switch_to_standings():
                self.logger.error("Failed to switch to Standings tab")
                return None
            
            # Get league info
            league_info = self.get_league_info()
            self.logger.info(f"League: {league_info.get('league', 'Unknown')}")
            
            # Extract standings data
            standings_data = self.extract_standings_data()
            
            if not standings_data:
                self.logger.warning("No standings data extracted")
                return None
            
            # Prepare final data
            final_data = {
                'scrape_timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'league_info': league_info,
                'standings': standings_data
            }
            
            self.logger.info(f"Successfully extracted standings for {len(standings_data.get('teams', []))} teams")
            return final_data
            
        except Exception as e:
            self.logger.error(f"Error in standings scrape: {e}")
            return None
    
    def switch_to_standings(self):
        """Switch to Standings tab"""
        try:
            standings_tab = self.safe_find_element(".tbs li:nth-child(3)", timeout=10)
            if standings_tab:
                standings_tab.click()
                self.logger.info("Switched to Standings tab")
                time.sleep(3)  # Wait for standings to load
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error switching to standings: {e}")
            return False
    
    def extract_standings_data(self):
        """Extract standings table data"""
        try:
            standings_data = {}
            
            # Get season title
            try:
                season_title = self.safe_find_element(".virtual-standings .title", timeout=5)
                if season_title:
                    standings_data['season'] = season_title.text.strip()
            except:
                standings_data['season'] = 'Unknown Season'
            
            # Extract table data
            teams_data = []
            table = self.safe_find_element(".virtual-standings table", timeout=10)
            
            if not table:
                self.logger.warning("Standings table not found")
                return standings_data
            
            # Get table rows
            rows = table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header
            
            for row in rows:
                try:
                    cols = row.find_elements(By.TAG_NAME, "td")
                    if len(cols) >= 4:
                        team_info = {
                            'position': cols[0].text.strip(),
                            'team_name': cols[1].text.strip(),
                            'points': cols[2].text.strip(),
                            'form': []
                        }
                        
                        # Extract form indicators
                        form_elements = cols[3].find_elements(By.CSS_SELECTOR, "div")
                        for form_element in form_elements:
                            team_info['form'].append(form_element.text.strip())
                        
                        teams_data.append(team_info)
                        
                except Exception as e:
                    self.logger.warning(f"Error extracting team row: {e}")
                    continue
            
            standings_data['teams'] = teams_data
            standings_data['total_teams'] = len(teams_data)
            
            return standings_data
            
        except Exception as e:
            self.logger.error(f"Error extracting standings: {e}")
            return {}