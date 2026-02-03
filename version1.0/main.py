# main.py
"""
Main Virtual Sports Scraper
Orchestrates all components according to workflow
"""

import os
import time
import threading
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Import all components
from config import config
from state_manager import CentralStateManager, MatchState
from page_session_manager import PageSessionManager
from timer_watcher import TimerWatcher
from league_controller import LeagueController
from market_scraper import MarketScraper
from live_match_watcher import LiveMatchWatcher
from goal_watcher import GoalWatcher
from results_scraper import ResultsScraper
from standings_scraper import StandingsScraper
from data_storage import JSONDataStorage

class VirtualSportsScraper:
    """Main orchestrator for the virtual sports scraper"""
    
    def __init__(self):
        self.driver = None
        self.state_manager = CentralStateManager()
        self.data_storage = JSONDataStorage()
        
        # Component instances
        self.page_manager = None
        self.timer_watcher = None
        self.league_controllers = []
        self.market_scrapers = []
        self.live_watcher = None
        self.goal_watcher = None
        self.results_scraper = None
        self.standings_scraper = None
        
        # Control flags
        self.is_running = False
        self.scraping_active = False
        self._stop_event = threading.Event()
        
    def setup_browser(self):
        """Setup Chrome browser with appropriate options"""
        chrome_options = Options()
        
        if config.HEADLESS:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Set user agent
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.set_page_load_timeout(config.BROWSER_TIMEOUT)
        
    def initialize_components(self):
        """Initialize all system components"""
        print("Initializing system components...")
        
        # 1. Page Session Manager (must run first)
        self.page_manager = PageSessionManager(self.driver)
        
        # 2. Timer Watcher
        self.timer_watcher = TimerWatcher(self.driver)
        
        # 3. League Controllers (will be populated dynamically)
        self.league_controllers = []
        
        # 4. Market Scrapers (will be populated dynamically)
        self.market_scrapers = []
        
        # 5. Live Match Watcher
        self.live_watcher = LiveMatchWatcher(self.driver)
        
        # 6. Goal Watcher
        self.goal_watcher = GoalWatcher(self.driver)
        
        # 7. Results Scraper
        self.results_scraper = ResultsScraper(
            self.driver, 
            config.RESULTS_SCRAPE_INTERVAL
        )
        
        # 8. Standings Scraper
        self.standings_scraper = StandingsScraper(
            self.driver,
            config.STANDINGS_SCRAPE_INTERVAL
        )
        
        print("All components initialized")
    
    def handle_live_match(self, match_id: str, match_info: dict):
        """Handle LIVE match detection"""
        print(f"Handling LIVE match: {match_id}")
        
        # Stop odds scraping for this match
        match_record = self.state_manager.get_match(match_id)
        if match_record:
            match_record.state = MatchState.LIVE
        
        # Start goal watching for this match
        self.goal_watcher.watch_match_goals(
            match_id, 
            match_info.get("element"), 
            self.state_manager
        )
    
    def start_odds_scraping(self):
        """Start odds scraping for current round"""
        if self.scraping_active:
            print("Scraping already active")
            return
        
        print("Starting odds scraping for new round...")
        self.scraping_active = True
        
        # Initialize league controllers
        self.initialize_leagues()
        
        # Initialize market scrapers
        self.initialize_markets()
        
        # Start scraping for each league
        for league_controller in self.league_controllers:
            league_controller.start_scraping(
                self.state_manager,
                on_complete=self.on_league_scraping_complete
            )
    
    def stop_odds_scraping(self):
        """Stop all odds scraping"""
        print("Stopping all odds scraping...")
        self.scraping_active = False
        
        for league_controller in self.league_controllers:
            league_controller.stop()
        
        for market_scraper in self.market_scrapers:
            market_scraper.stop()
    
    def initialize_leagues(self):
        """Initialize controllers for all leagues"""
        try:
            league_elements = self.driver.find_elements(
                By.CSS_SELECTOR, config.SELECTORS["LEAGUE_ITEM"]
            )
            
            for elem in league_elements:
                league_name_elem = elem.find_element(
                    By.CSS_SELECTOR, "div.text-xs"
                )
                league_name = league_name_elem.text.strip()
                
                controller = LeagueController(
                    self.driver, 
                    league_name, 
                    elem
                )
                self.league_controllers.append(controller)
                
            print(f"Initialized {len(self.league_controllers)} league controllers")
            
        except Exception as e:
            print(f"Error initializing leagues: {e}")
    
    def initialize_markets(self):
        """Initialize scrapers for all markets"""
        try:
            # Main markets (1X2, GG/NG, Double Chance)
            main_markets = ["1X2", "GG/NG", "Double Chance"]
            
            for market_name in main_markets:
                try:
                    # Find market button
                    market_buttons = self.driver.find_elements(
                        By.CSS_SELECTOR, config.SELECTORS["MARKET_BUTTONS"]
                    )
                    
                    for button in market_buttons:
                        if market_name in button.text:
                            scraper = MarketScraper(
                                self.driver, 
                                market_name, 
                                button
                            )
                            self.market_scrapers.append(scraper)
                            break
                            
                except Exception as e:
                    print(f"Error initializing market {market_name}: {e}")
                    continue
            
            # Dropdown markets (26+)
            try:
                dropdown = self.driver.find_element(
                    By.CSS_SELECTOR, config.SELECTORS["MARKET_DROPDOWN"]
                )
                options = dropdown.find_elements(By.TAG_NAME, "option")
                
                for option in options[1:]:  # Skip first option
                    market_name = option.text.strip()
                    if market_name:
                        scraper = MarketScraper(self.driver, market_name)
                        self.market_scrapers.append(scraper)
                        
            except Exception as e:
                print(f"Error initializing dropdown markets: {e}")
            
            print(f"Initialized {len(self.market_scrapers)} market scrapers")
            
        except Exception as e:
            print(f"Error initializing markets: {e}")
    
    def on_league_scraping_complete(self, league_name: str, matches: list):
        """Callback when league scraping completes"""
        print(f"League scraping complete for {league_name}: {len(matches)} matches")
        
        # Save state to JSON
        self.state_manager.save_to_json(config.JSON_STORAGE_PATH)
    
    def run(self):
        """Main execution loop"""
        try:
            print("Starting Virtual Sports Scraper...")
            self.is_running = True
            
            # Setup browser
            self.setup_browser()
            
            # Navigate to target URL
            print(f"Navigating to: {config.TARGET_URL}")
            self.driver.get(config.TARGET_URL)
            
            # Initialize components
            self.initialize_components()
            
            # Step 1: Handle popup (MUST run first)
            if not self.page_manager.ensure_page_ready():
                print("Failed to prepare page. Exiting.")
                return
            
            # Step 2: Start timer watcher
            timer_thread = self.timer_watcher.monitor_timer(
                on_round_start=self.start_odds_scraping,
                on_scraping_deadline=self.stop_odds_scraping
            )
            
            # Step 3: Start live match watcher
            live_thread = self.live_watcher.watch_live_matches(
                self.state_manager,
                on_live_detected=self.handle_live_match
            )
            
            # Step 4: Start scheduled scrapers
            results_thread = self.results_scraper.run_scheduled(
                os.path.join(config.BACKUP_STORAGE_PATH, "results.json")
            )
            
            standings_thread = self.standings_scraper.run_scheduled(
                os.path.join(config.BACKUP_STORAGE_PATH, "standings.json")
            )
            
            # Main loop
            while not self._stop_event.is_set():
                # Periodically save state
                if int(time.time()) % 300 == 0:  # Every 5 minutes
                    self.state_manager.save_to_json(config.JSON_STORAGE_PATH)
                    print("Auto-saved state")
                
                time.sleep(1)
            
        except KeyboardInterrupt:
            print("\nShutting down gracefully...")
        except Exception as e:
            print(f"Error in main execution: {e}")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Graceful shutdown"""
        print("Initiating shutdown sequence...")
        
        self.is_running = False
        self._stop_event.set()
        
        # Stop all components
        self.stop_odds_scraping()
        
        if self.live_watcher:
            self.live_watcher.stop()
        
        if self.goal_watcher:
            self.goal_watcher.stop_all()
        
        if self.results_scraper:
            self.results_scraper.stop()
        
        if self.standings_scraper:
            self.standings_scraper.stop()
        
        # Final state save
        self.state_manager.save_to_json(config.JSON_STORAGE_PATH)
        
        # Close browser
        if self.driver:
            self.driver.quit()
        
        print("Shutdown complete")

if __name__ == "__main__":
    scraper = VirtualSportsScraper()
    scraper.run()