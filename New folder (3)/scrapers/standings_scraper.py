"""
Standings scraper - extracts league table data
"""

from datetime import datetime
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
            standings_data =