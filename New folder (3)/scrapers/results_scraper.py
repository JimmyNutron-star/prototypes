"""
Results scraper - extracts historical match results
"""

from datetime import datetime
import time
from selenium.webdriver.common.by import By  # ADD THIS IMPORT
from scrapers.base_scraper import BaseScraper
from config import ODILEAGUE_URL

class ResultsScraper(BaseScraper):
    def __init__(self):
        super().__init__("results")
    
    def scrape_results(self):
        """Scrape results data"""
        try:
            self.logger.info("Starting results scrape...")
            
            # Navigate to page
            if not self.navigate_to_url(ODILEAGUE_URL):
                return None
            
            # Close popup
            self.close_popup()
            
            # Switch to Results tab
            if not self.switch_to_results():
                self.logger.error("Failed to switch to Results tab")
                return None
            
            # Get league info
            league_info = self.get_league_info()
            self.logger.info(f"League: {league_info.get('league', 'Unknown')}")
            
            # Extract results data
            results_data = self.extract_results_data()
            
            if not results_data:
                self.logger.warning("No results data extracted")
                return None
            
            # Prepare final data
            final_data = {
                'scrape_timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'league_info': league_info,
                'results_weeks': results_data,
                'total_weeks': len(results_data)
            }
            
            self.logger.info(f"Successfully extracted {len(results_data)} results weeks")
            return final_data
            
        except Exception as e:
            self.logger.error(f"Error in results scrape: {e}")
            return None
    
    def switch_to_results(self):
        """Switch to Results tab"""
        try:
            results_tab = self.safe_find_element(".tbs li:nth-child(2)", timeout=10)
            if results_tab:
                results_tab.click()
                self.logger.info("Switched to Results tab")
                time.sleep(3)  # Wait for results to load
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error switching to results: {e}")
            return False
    
    def extract_results_data(self):
        """Extract all results data"""
        results_weeks = []
        
        try:
            # Find all results sections
            results_sections = self.safe_find_elements(".rs", timeout=10)
            
            if not results_sections:
                self.logger.warning("No results sections found")
                return results_weeks
            
            self.logger.info(f"Found {len(results_sections)} results sections")
            
            # Extract data from each section
            for section in results_sections[:5]:  # Limit to first 5 weeks
                try:
                    week_data = self._extract_week_results(section)
                    if week_data:
                        results_weeks.append(week_data)
                except Exception as e:
                    self.logger.warning(f"Error extracting week results: {e}")
                    continue
            
            return results_weeks
            
        except Exception as e:
            self.logger.error(f"Error extracting results: {e}")
            return []
    
    def _extract_week_results(self, section_element):
        """Extract results for a single week"""
        try:
            week_data = {}
            
            # Extract week info
            try:
                week_title = section_element.find_element(By.CSS_SELECTOR, ".rs-t .t")
                week_time = section_element.find_element(By.CSS_SELECTOR, ".rs-t .b")
                
                week_data['week_info'] = {
                    'title': week_title.text.strip(),
                    'time': week_time.text.strip()
                }
            except:
                week_data['week_info'] = {'title': 'Unknown', 'time': 'Unknown'}
            
            # Extract games
            games = []
            game_elements = section_element.find_elements(By.CLASS_NAME, "rs-g")
            
            for game_element in game_elements:
                try:
                    game_data = {}
                    
                    # Get team names
                    teams = game_element.find_elements(By.CLASS_NAME, "g-t")
                    if len(teams) >= 2:
                        game_data['home_team'] = teams[0].text.strip()
                        game_data['away_team'] = teams[2].text.strip() if len(teams) >= 3 else teams[1].text.strip()
                    
                    # Get scores
                    scores = game_element.find_elements(By.CSS_SELECTOR, ".g-s span")
                    if len(scores) >= 2:
                        game_data['home_score'] = scores[0].text.strip()
                        game_data['away_score'] = scores[1].text.strip()
                    
                    if game_data:
                        games.append(game_data)
                        
                except Exception as e:
                    continue
            
            week_data['games'] = games
            week_data['total_games'] = len(games)
            
            return week_data
            
        except Exception as e:
            self.logger.warning(f"Error extracting week: {e}")
            return None