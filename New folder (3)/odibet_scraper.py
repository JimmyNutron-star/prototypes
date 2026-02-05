from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
import json
import os
from datetime import datetime

class OdibetsContinuousScraper:
    def __init__(self, headless=False):
        """Initialize scraper with connection recovery"""
        self.headless = headless
        self.driver = None
        self.wait = None
        self.is_connected = False
        self.matchday_data_history = []
        self.timer_history = []
        self.current_matchday_number = 1
        self.scrape_count = 0
        
        # Initialize driver
        self._init_driver()
    
    def _init_driver(self):
        """Initialize or reinitialize the driver"""
        try:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
            
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--log-level=3')
            
            # Add user agent
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            self.wait = WebDriverWait(self.driver, 15)
            self.is_connected = True
            print("✅ WebDriver initialized successfully")
            
        except Exception as e:
            print(f"❌ Failed to initialize WebDriver: {e}")
            self.is_connected = False
            raise
    
    def check_connection(self):
        """Check if driver connection is still alive"""
        if not self.driver:
            return False
        
        try:
            # Simple check by getting current URL
            current_url = self.driver.current_url
            return True
        except WebDriverException:
            print("⚠️ WebDriver connection lost")
            self.is_connected = False
            return False
    
    def reconnect(self):
        """Reconnect the driver"""
        print("🔄 Attempting to reconnect...")
        try:
            self._init_driver()
            return True
        except Exception as e:
            print(f"❌ Reconnection failed: {e}")
            return False
    
    def safe_find_element(self, by, selector, timeout=10):
        """Safely find element with reconnection"""
        try:
            if not self.check_connection():
                if not self.reconnect():
                    return None
            
            wait = WebDriverWait(self.driver, timeout)
            return wait.until(EC.presence_of_element_located((by, selector)))
        except Exception as e:
            print(f"⚠️ Element not found: {selector} - {e}")
            return None
    
    def safe_find_elements(self, by, selector, timeout=10):
        """Safely find elements with reconnection"""
        try:
            if not self.check_connection():
                if not self.reconnect():
                    return []
            
            wait = WebDriverWait(self.driver, timeout)
            wait.until(EC.presence_of_element_located((by, selector)))
            return self.driver.find_elements(by, selector)
        except Exception as e:
            print(f"⚠️ Elements not found: {selector} - {e}")
            return []
    
    def close_popup(self):
        """Close any popups"""
        try:
            time.sleep(2)
            popup_close = self.safe_find_element(By.CSS_SELECTOR, ".roadblock-close button", timeout=5)
            if popup_close:
                popup_close.click()
                print("✅ Popup closed")
                time.sleep(1)
                return True
        except Exception as e:
            print(f"ℹ️ No popup found or error: {e}")
        return False
    
    def navigate_to_url(self, url="https://odibets.com/odileague"):
        """Navigate to URL with retry"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"🌐 Navigating to: {url} (Attempt {attempt + 1}/{max_retries})")
                self.driver.get(url)
                time.sleep(5)  # Wait for page load
                
                # Check if page loaded
                if "odileague" in self.driver.current_url.lower() or "odibets" in self.driver.current_url.lower():
                    print("✅ Page loaded successfully")
                    return True
                
            except Exception as e:
                print(f"⚠️ Navigation failed: {e}")
                if attempt < max_retries - 1:
                    print("🔄 Retrying...")
                    time.sleep(3)
                    if not self.reconnect():
                        continue
        
        print("❌ Failed to navigate to URL after retries")
        return False
    
    def get_current_timer(self):
        """Get current timer value with error handling"""
        try:
            timer_element = self.safe_find_element(By.CSS_SELECTOR, ".virtual-timer .ss.active", timeout=5)
            if timer_element:
                timer_value = timer_element.text.strip()
                return timer_value
            return None
        except Exception as e:
            print(f"⚠️ Could not get timer: {e}")
            return None
    
    def is_timer_live(self, timer_value):
        """Check if timer indicates LIVE status"""
        if not timer_value:
            return False
        
        timer_lower = timer_value.lower()
        if 'live' in timer_lower:
            return True
        
        try:
            if ':' in timer_value:
                minutes, seconds = timer_value.split(':')
                if int(minutes) == 0 and int(seconds) <= 2:
                    return True
        except:
            pass
        
        return False
    
    def extract_matchday_data(self):
        """Extract matchday data with error handling"""
        try:
            if not self.check_connection():
                if not self.reconnect():
                    return []
            
            # Wait for games to load
            time.sleep(2)
            
            game_elements = self.safe_find_elements(By.CSS_SELECTOR, ".game.e", timeout=10)
            if not game_elements:
                print("⚠️ No games found on page")
                return []
            
            print(f"📊 Found {len(game_elements)} games")
            matchday_games = []
            
            for i, game_element in enumerate(game_elements[:10]):  # Limit to first 10 games
                try:
                    game_data = self._extract_single_game(game_element)
                    if game_data:
                        game_data['matchday'] = self.current_matchday_number
                        game_data['scrape_timestamp'] = datetime.now().strftime("%H:%M:%S")
                        game_data['game_index'] = i + 1
                        matchday_games.append(game_data)
                except Exception as e:
                    print(f"⚠️ Error extracting game {i+1}: {e}")
                    continue
            
            return matchday_games
            
        except Exception as e:
            print(f"❌ Error in matchday extraction: {e}")
            return []
    
    def _extract_single_game(self, game_element):
        """Extract single game data"""
        try:
            game_data = {}
            
            # Team names
            team_elements = game_element.find_elements(By.CSS_SELECTOR, ".t-l")
            if len(team_elements) >= 2:
                game_data['home_team'] = team_elements[0].text.strip()
                game_data['away_team'] = team_elements[1].text.strip()
            else:
                return None  # Skip if no team names
            
            # 1X2 Odds
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
            
            # GG/NG Odds
            try:
                ggng_container = game_element.find_element(By.CSS_SELECTOR, ".o.s-2.m2")
                ggng_buttons = ggng_container.find_elements(By.TAG_NAME, "button")
                
                if len(ggng_buttons) >= 2:
                    game_data['gg_yes'] = ggng_buttons[0].find_element(By.CSS_SELECTOR, ".o-2").text.strip()
                    game_data['gg_no'] = ggng_buttons[1].find_element(By.CSS_SELECTOR, ".o-2").text.strip()
            except:
                game_data['gg_yes'] = 'N/A'
                game_data['gg_no'] = 'N/A'
            
            return game_data
            
        except Exception as e:
            print(f"⚠️ Error in single game extraction: {e}")
            return None
    
    def continuous_monitoring(self, scrape_interval=30, max_duration_minutes=60, stop_on_live=True):
        """Main continuous monitoring function"""
        print("\n" + "="*70)
        print("🎯 ODIBETS CONTINUOUS MONITORING")
        print("="*70)
        
        # Setup monitoring
        start_time = time.time()
        max_duration_seconds = max_duration_minutes * 60
        consecutive_errors = 0
        max_consecutive_errors = 3
        
        print(f"\n📊 Monitoring Parameters:")
        print(f"  • Scrape Interval: {scrape_interval} seconds")
        print(f"  • Max Duration: {max_duration_minutes} minutes")
        print(f"  • Stop on LIVE: {stop_on_live}")
        print(f"  • Start Time: {datetime.now().strftime('%H:%M:%S')}")
        print("-"*70)
        
        try:
            while True:
                # Check elapsed time
                elapsed = time.time() - start_time
                if elapsed > max_duration_seconds:
                    print(f"\n⏰ Maximum duration reached ({max_duration_minutes} minutes)")
                    break
                
                # Check connection
                if not self.check_connection():
                    print("⚠️ Connection lost, attempting to reconnect...")
                    if not self.reconnect():
                        print("❌ Failed to reconnect. Stopping monitoring.")
                        break
                    # Refresh page after reconnect
                    self.driver.refresh()
                    time.sleep(5)
                    self.close_popup()
                
                # Get current timer
                current_timer = self.get_current_timer()
                if current_timer:
                    self.timer_history.append({
                        'timestamp': datetime.now().strftime("%H:%M:%S"),
                        'timer': current_timer,
                        'elapsed_minutes': round(elapsed / 60, 2)
                    })
                    
                    print(f"\n⏰ Timer: {current_timer} | Elapsed: {round(elapsed/60, 1)} min")
                    
                    # Check if LIVE
                    if stop_on_live and self.is_timer_live(current_timer):
                        print(f"\n🎯 MATCHDAY WENT LIVE at {current_timer}!")
                        print("🛑 Stopping monitoring...")
                        break
                
                # Perform scrape
                self.scrape_count += 1
                print(f"\n📊 Scrape #{self.scrape_count} at {datetime.now().strftime('%H:%M:%S')}")
                
                matchday_data = self.extract_matchday_data()
                
                if matchday_data:
                    snapshot = {
                        'scrape_number': self.scrape_count,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'timer_at_scrape': current_timer,
                        'games': matchday_data
                    }
                    self.matchday_data_history.append(snapshot)
                    
                    print(f"✅ Collected {len(matchday_data)} games")
                    print(f"📈 Sample: {matchday_data[0]['home_team']} vs {matchday_data[0]['away_team']}")
                    print(f"        1: {matchday_data[0].get('home_odds', 'N/A')} | X: {matchday_data[0].get('draw_odds', 'N/A')} | 2: {matchday_data[0].get('away_odds', 'N/A')}")
                    
                    consecutive_errors = 0  # Reset error count on success
                    
                    # Check for odds changes
                    if len(self.matchday_data_history) > 1:
                        self._check_for_changes()
                else:
                    print("⚠️ No data collected")
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        print(f"❌ {max_consecutive_errors} consecutive errors. Refreshing page...")
                        self.driver.refresh()
                        time.sleep(5)
                        self.close_popup()
                        consecutive_errors = 0
                
                # Calculate wait time
                time_remaining = max(1, scrape_interval - (time.time() - start_time - (self.scrape_count - 1) * scrape_interval))
                print(f"⏳ Next scrape in {int(time_remaining)} seconds...")
                
                time.sleep(time_remaining)
                
        except KeyboardInterrupt:
            print("\n⚠️ Monitoring interrupted by user")
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
        
        finally:
            # Final summary
            print("\n" + "="*70)
            print("📊 MONITORING COMPLETE")
            print("="*70)
            print(f"Total scrapes: {self.scrape_count}")
            print(f"Total game snapshots: {sum(len(s['games']) for s in self.matchday_data_history)}")
            print(f"Final timer: {self.get_current_timer()}")
            print(f"Duration: {round((time.time() - start_time)/60, 1)} minutes")
            
            return self.matchday_data_history
    
    def _check_for_changes(self):
        """Check for odds changes between scrapes"""
        if len(self.matchday_data_history) < 2:
            return
        
        current = self.matchday_data_history[-1]
        previous = self.matchday_data_history[-2]
        
        current_games = {f"{g['home_team']} vs {g['away_team']}": g for g in current['games'] 
                        if 'home_team' in g and 'away_team' in g}
        previous_games = {f"{g['home_team']} vs {g['away_team']}": g for g in previous['games'] 
                         if 'home_team' in g and 'away_team' in g}
        
        changes = []
        for match_key, current_game in current_games.items():
            if match_key in previous_games:
                prev_game = previous_games[match_key]
                
                # Check each odds type for changes
                odds_types = ['home_odds', 'draw_odds', 'away_odds', 'gg_yes', 'gg_no']
                for odds_type in odds_types:
                    if (odds_type in current_game and odds_type in prev_game and 
                        current_game[odds_type] != prev_game[odds_type] and 
                        current_game[odds_type] != 'N/A' and prev_game[odds_type] != 'N/A'):
                        changes.append(f"{match_key}: {odds_type} {prev_game[odds_type]} → {current_game[odds_type]}")
        
        if changes:
            print("📈 Odds changes detected:")
            for change in changes[:3]:  # Show only first 3 changes
                print(f"   • {change}")
            if len(changes) > 3:
                print(f"   ... and {len(changes) - 3} more changes")
    
    def save_monitoring_data(self):
        """Save all monitoring data"""
        if not self.matchday_data_history:
            print("❌ No data to save!")
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        directory = f"odibets_monitoring_{timestamp}"
        os.makedirs(directory, exist_ok=True)
        
        print(f"\n💾 Saving data to: {directory}")
        
        # 1. Save matchday history
        history_file = os.path.join(directory, "matchday_history.json")
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(self.matchday_data_history, f, indent=2, ensure_ascii=False)
        print(f"✅ History saved: {history_file}")
        
        # 2. Save timer history
        if self.timer_history:
            timer_file = os.path.join(directory, "timer_history.csv")
            df_timer = pd.DataFrame(self.timer_history)
            df_timer.to_csv(timer_file, index=False)
            print(f"✅ Timer history saved: {timer_file}")
        
        # 3. Save latest data as CSV
        if self.matchday_data_history:
            latest_file = os.path.join(directory, "latest_odds.csv")
            latest_games = self.matchday_data_history[-1]['games']
            df_latest = pd.DataFrame(latest_games)
            df_latest.to_csv(latest_file, index=False)
            print(f"✅ Latest odds saved: {latest_file}")
        
        # 4. Create summary report
        report_file = os.path.join(directory, "monitoring_report.txt")
        self._create_summary_report(report_file)
        
        print(f"\n📁 All data saved in: {directory}")
        return directory
    
    def _create_summary_report(self, report_file):
        """Create monitoring summary report"""
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("ODIBETS ODILEAGUE MONITORING REPORT\n")
            f.write("="*70 + "\n\n")
            
            f.write(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("📊 MONITORING SUMMARY\n")
            f.write("-"*40 + "\n")
            f.write(f"Total Scrapes: {self.scrape_count}\n")
            f.write(f"Total Game Snapshots: {sum(len(s['games']) for s in self.matchday_data_history)}\n")
            
            if self.matchday_data_history:
                first_time = self.matchday_data_history[0]['timestamp']
                last_time = self.matchday_data_history[-1]['timestamp']
                f.write(f"Monitoring Period: {first_time} to {last_time}\n")
            
            # Timer summary
            if self.timer_history:
                f.write(f"\n⏰ TIMER SUMMARY\n")
                f.write("-"*40 + "\n")
                unique_timers = sorted(set(t['timer'] for t in self.timer_history if t['timer']))
                f.write(f"Timer Progression: {' → '.join(unique_timers)}\n")
            
            # Games summary
            if self.matchday_data_history and self.matchday_data_history[-1]['games']:
                f.write(f"\n🎯 CURRENT MATCHES\n")
                f.write("-"*40 + "\n")
                games = self.matchday_data_history[-1]['games']
                for i, game in enumerate(games[:5], 1):
                    f.write(f"{i}. {game.get('home_team', 'N/A')} vs {game.get('away_team', 'N/A')}\n")
                    f.write(f"   Odds: 1={game.get('home_odds', 'N/A')} | X={game.get('draw_odds', 'N/A')} | 2={game.get('away_odds', 'N/A')}\n")
                if len(games) > 5:
                    f.write(f"... and {len(games) - 5} more matches\n")
            
            f.write("\n" + "="*70 + "\n")
        
        print(f"✅ Summary report saved: {report_file}")
    
    def cleanup(self):
        """Cleanup resources"""
        print("\n🧹 Cleaning up resources...")
        try:
            if self.driver:
                self.driver.quit()
                print("✅ Browser closed")
        except:
            pass
        finally:
            self.is_connected = False
            print("✅ Cleanup complete")

# Simplified main execution
def run_simple_monitoring():
    """Simple monitoring without complex menu"""
    print("\n" + "="*70)
    print("🎯 ODIBETS ODILEAGUE MONITORING")
    print("="*70)
    
    # Create scraper (non-headless for debugging)
    scraper = OdibetsContinuousScraper(headless=False)
    
    try:
        # Setup
        print("\n🚀 Setting up scraper...")
        if not scraper.navigate_to_url("https://odibets.com/odileague"):
            print("❌ Failed to load page")
            return
        
        scraper.close_popup()
        
        # Get initial timer
        initial_timer = scraper.get_current_timer()
        print(f"⏰ Initial Timer: {initial_timer}")
        
        # Check if already LIVE
        if scraper.is_timer_live(initial_timer):
            print("⚠️ Matchday is already LIVE!")
            proceed = input("Continue monitoring anyway? (y/n): ").lower()
            if proceed != 'y':
                return
        
        # Get monitoring parameters
        print("\n⚙️  Set Monitoring Parameters:")
        try:
            interval = int(input("Scrape interval (seconds, 30-60 recommended): ") or "30")
            duration = int(input("Max duration (minutes): ") or "60")
        except:
            print("⚠️ Using default values (30s interval, 60 minutes)")
            interval = 30
            duration = 60
        
        # Start monitoring
        print(f"\n▶️  Starting monitoring...")
        print(f"   • Interval: {interval} seconds")
        print(f"   • Duration: {duration} minutes")
        print(f"   • Will stop when LIVE\n")
        
        scraper.continuous_monitoring(
            scrape_interval=interval,
            max_duration_minutes=duration,
            stop_on_live=True
        )
        
        # Save data
        print("\n💾 Saving collected data...")
        directory = scraper.save_monitoring_data()
        
        if directory:
            print(f"\n✅ Monitoring complete!")
            print(f"📁 Data saved in: {directory}")
            print(f"📊 Check the files for detailed information")
        
    except KeyboardInterrupt:
        print("\n⚠️ Monitoring interrupted by user")
        # Save partial data
        if hasattr(scraper, 'matchday_data_history') and scraper.matchday_data_history:
            print("\n💾 Saving partial data...")
            scraper.save_monitoring_data()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        scraper.cleanup()

def quick_test():
    """Quick test function"""
    print("\n🚀 Quick test mode...")
    scraper = OdibetsContinuousScraper(headless=False)
    
    try:
        if scraper.navigate_to_url():
            scraper.close_popup()
            
            print("\n🔍 Testing page elements...")
            
            # Test timer
            timer = scraper.get_current_timer()
            print(f"⏰ Timer: {timer}")
            print(f"📊 Is LIVE: {scraper.is_timer_live(timer)}")
            
            # Test game extraction
            print("\n📊 Testing game extraction...")
            games = scraper.extract_matchday_data()
            print(f"✅ Found {len(games)} games")
            
            if games:
                print(f"\n📈 Sample game:")
                print(f"   {games[0]['home_team']} vs {games[0]['away_team']}")
                print(f"   1: {games[0].get('home_odds', 'N/A')} | X: {games[0].get('draw_odds', 'N/A')} | 2: {games[0].get('away_odds', 'N/A')}")
            
            return True
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        scraper.cleanup()

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🎯 ODIBETS ODILEAGUE CONTINUOUS MONITORING SCRAPER")
    print("="*70)
    print("\nOptions:")
    print("1. Start Continuous Monitoring")
    print("2. Quick Test (Check if page loads)")
    print("3. Exit")
    
    try:
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == '1':
            run_simple_monitoring()
        elif choice == '2':
            quick_test()
        elif choice == '3':
            print("👋 Goodbye!")
        else:
            print("❌ Invalid choice. Running default monitoring...")
            run_simple_monitoring()
    except KeyboardInterrupt:
        print("\n👋 Exiting...")
    except Exception as e:
        print(f"❌ Error: {e}")