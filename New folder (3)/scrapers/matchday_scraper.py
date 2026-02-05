"""
Matchday scraper - extracts odds data for current matchday
"""

from datetime import datetime
from selenium.webdriver.common.by import By  # ADD THIS IMPORT
from scrapers.base_scraper import BaseScraper
from config import ODILEAGUE_URL

class MatchdayScraper(BaseScraper):
    def __init__(self):
        super().__init__("matchday")
        self.league_info = {}
    
    def scrape_current_matchday(self):
        """Scrape current matchday data"""
        try:
            self.logger.info("Starting matchday scrape...")
            
            # Navigate to page
            if not self.navigate_to_url(ODILEAGUE_URL):
                return None
            
            # Close popup
            self.close_popup()
            
            # Get league info
            self.league_info = self.get_league_info()
            self.logger.info(f"League: {self.league_info.get('league', 'Unknown')}")
            self.logger.info(f"Timer: {self.league_info.get('timer', 'Unknown')}")
            
            # Extract matchday data
            games_data = self.extract_games_data()
            
            if not games_data:
                self.logger.warning("No games data extracted")
                return None
            
            # Prepare final data
            matchday_data = {
                'scrape_timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'league_info': self.league_info,
                'games': games_data,
                'total_games': len(games_data)
            }
            
            self.logger.info(f"Successfully extracted {len(games_data)} games")
            return matchday_data
            
        except Exception as e:
            self.logger.error(f"Error in matchday scrape: {e}")
            return None
    
    def extract_games_data(self):
        """Extract data for all games in current matchday"""
        games_data = []
        
        try:
            # Find all game elements
            game_elements = self.safe_find_elements(".game.e", timeout=10)
            
            if not game_elements:
                self.logger.warning("No game elements found")
                return games_data
            
            self.logger.info(f"Found {len(game_elements)} game elements")
            
            # Extract data for each game
            for i, game_element in enumerate(game_elements):
                try:
                    game_data = self._extract_single_game(game_element)
                    if game_data:
                        game_data['game_number'] = i + 1
                        games_data.append(game_data)
                        
                except Exception as e:
                    self.logger.warning(f"Error extracting game {i+1}: {e}")
                    continue
            
            return games_data
            
        except Exception as e:
            self.logger.error(f"Error extracting games: {e}")
            return []
    
    def _extract_single_game(self, game_element):
        """Extract data from a single game element"""
        try:
            game_data = {}
            
            # Extract team names
            team_elements = game_element.find_elements(By.CSS_SELECTOR, ".t-l")
            if len(team_elements) >= 2:
                game_data['home_team'] = team_elements[0].text.strip()
                game_data['away_team'] = team_elements[1].text.strip()
            else:
                return None
            
            # Extract 1X2 odds
            try:
                odds_container = game_element.find_element(By.CSS_SELECTOR, ".o.s-1.m3")
                odds_buttons = odds_container.find_elements(By.TAG_NAME, "button")
                
                if len(odds_buttons) >= 3:
                    game_data['home_odds'] = odds_buttons[0].find_element(By.CSS_SELECTOR, ".o-2").text.strip()
                    game_data['draw_odds'] = odds_buttons[1].find_element(By.CSS_SELECTOR, ".o-2").text.strip()
                    game_data['away_odds'] = odds_buttons[2].find_element(By.CSS_SELECTOR, ".o-2").text.strip()
            except:
                game_data['home_odds'] = 'N/A'
                game_data['draw_odds'] = 'N/A'
                game_data['away_odds'] = 'N/A'
            
            # Extract GG/NG odds
            try:
                ggng_container = game_element.find_element(By.CSS_SELECTOR, ".o.s-2.m2")
                ggng_buttons = ggng_container.find_elements(By.TAG_NAME, "button")
                
                if len(ggng_buttons) >= 2:
                    game_data['gg_yes'] = ggng_buttons[0].find_element(By.CSS_SELECTOR, ".o-2").text.strip()
                    game_data['gg_no'] = ggng_buttons[1].find_element(By.CSS_SELECTOR, ".o-2").text.strip()
            except:
                game_data['gg_yes'] = 'N/A'
                game_data['gg_no'] = 'N/A'
            
            # Extract team logos (optional)
            try:
                logos = game_element.find_elements(By.CSS_SELECTOR, "img")
                if len(logos) >= 2:
                    game_data['home_logo'] = logos[0].get_attribute('src')
                    game_data['away_logo'] = logos[1].get_attribute('src')
            except:
                pass
            
            return game_data
            
        except Exception as e:
            self.logger.warning(f"Error in single game extraction: {e}")
            return None