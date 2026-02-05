"""
Debug runner for testing individual modules
"""

import sys
import traceback
from datetime import datetime

def test_timer_monitor():
    """Test timer monitor only"""
    print("\n🔍 TESTING TIMER MONITOR")
    print("="*50)
    
    from scrapers.timer_monitor import TimerMonitor
    
    monitor = TimerMonitor()
    try:
        # Test navigation
        print("1. Testing navigation...")
        if monitor.navigate_to_url("https://odibets.com/odileague"):
            print("   ✅ Navigation successful")
        else:
            print("   ❌ Navigation failed")
            return
        
        # Test popup closing
        print("2. Testing popup closing...")
        monitor.close_popup()
        print("   ✅ Popup handled")
        
        # Test timer reading
        print("3. Testing timer reading...")
        timer = monitor.get_current_timer()
        print(f"   Timer value: {timer}")
        
        # Quick monitoring test
        print("4. Quick monitoring test (10 seconds)...")
        monitor.monitor_timer(check_interval=2, max_checks=5)
        
        print("\n✅ Timer monitor test complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()
    finally:
        monitor.cleanup()

def test_matchday_scraper():
    """Test matchday scraper only"""
    print("\n🔍 TESTING MATCHDAY SCRAPER")
    print("="*50)
    
    from scrapers.matchday_scraper import MatchdayScraper
    
    scraper = MatchdayScraper()
    try:
        print("1. Starting matchday scrape...")
        data = scraper.scrape_current_matchday()
        
        if data:
            print(f"   ✅ Success! Scraped {data.get('total_games', 0)} games")
            
            # Show sample data
            if data.get('games'):
                game = data['games'][0]
                print(f"\n📊 Sample game:")
                print(f"   {game.get('home_team')} vs {game.get('away_team')}")
                print(f"   Odds: 1={game.get('home_odds')} | X={game.get('draw_odds')} | 2={game.get('away_odds')}")
            
            # Test saving
            print("\n2. Testing data saving...")
            saved_files = scraper.save_data(data, "test_matchday")
            print(f"   Saved files: {list(saved_files.keys())}")
            
        else:
            print("   ❌ No data scraped")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()
    finally:
        scraper.cleanup()

def test_results_scraper():
    """Test results scraper only"""
    print("\n🔍 TESTING RESULTS SCRAPER")
    print("="*50)
    
    from scrapers.results_scraper import ResultsScraper
    
    scraper = ResultsScraper()
    try:
        print("1. Starting results scrape...")
        data = scraper.scrape_results()
        
        if data:
            print(f"   ✅ Success! Scraped {data.get('total_weeks', 0)} weeks")
            
            # Test saving
            print("\n2. Testing data saving...")
            saved_files = scraper.save_data(data, "test_results")
            print(f"   Saved files: {list(saved_files.keys())}")
            
        else:
            print("   ❌ No data scraped")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()
    finally:
        scraper.cleanup()

def test_standings_scraper():
    """Test standings scraper only"""
    print("\n🔍 TESTING STANDINGS SCRAPER")
    print("="*50)
    
    from scrapers.standings_scraper import StandingsScraper
    
    scraper = StandingsScraper()
    try:
        print("1. Starting standings scrape...")
        data = scraper.scrape_standings()
        
        if data:
            print(f"   ✅ Success! Scraped {data.get('standings', {}).get('total_teams', 0)} teams")
            
            # Test saving
            print("\n2. Testing data saving...")
            saved_files = scraper.save_data(data, "test_standings")
            print(f"   Saved files: {list(saved_files.keys())}")
            
        else:
            print("   ❌ No data scraped")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()
    finally:
        scraper.cleanup()

def test_browser_connection():
    """Test basic browser connection"""
    print("\n🔍 TESTING BROWSER CONNECTION")
    print("="*50)
    
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Test in headless first
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        print("1. Initializing ChromeDriver...")
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        print("2. Testing navigation...")
        driver.get("https://odibets.com/odileague")
        time.sleep(3)
        
        print(f"   Page title: {driver.title}")
        print(f"   Current URL: {driver.current_url}")
        
        print("3. Testing page elements...")
        page_source = driver.page_source[:500]  # First 500 chars
        print(f"   Page source sample: {page_source}")
        
        print("\n✅ Browser connection test successful!")
        
    except Exception as e:
        print(f"❌ Browser test failed: {e}")
        traceback.print_exc()
    finally:
        if 'driver' in locals():
            driver.quit()

def run_all_tests():
    """Run all tests sequentially"""
    print("\n" + "="*70)
    print("🚀 COMPREHENSIVE TROUBLESHOOTING SESSION")
    print("="*70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    tests = [
        ("Browser Connection", test_browser_connection),
        ("Timer Monitor", test_timer_monitor),
        ("Matchday Scraper", test_matchday_scraper),
        ("Results Scraper", test_results_scraper),
        ("Standings Scraper", test_standings_scraper),
    ]
    
    results = {}
    
    for test_name, test_function in tests:
        try:
            print(f"\n{'='*50}")
            print(f"RUNNING: {test_name}")
            print(f"{'='*50}")
            
            test_function()
            results[test_name] = "PASSED"
            
        except Exception as e:
            print(f"\n❌ {test_name} FAILED: {e}")
            results[test_name] = "FAILED"
    
    # Print summary
    print("\n" + "="*70)
    print("📊 TEST RESULTS SUMMARY")
    print("="*70)
    
    for test_name, result in results.items():
        status = "✅" if result == "PASSED" else "❌"
        print(f"{status} {test_name}: {result}")
    
    print(f"\nFinished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    import time
    
    # Run specific test or all tests
    if len(sys.argv) > 1:
        test_name = sys.argv[1].lower()
        
        if test_name == "browser":
            test_browser_connection()
        elif test_name == "timer":
            test_timer_monitor()
        elif test_name == "matchday":
            test_matchday_scraper()
        elif test_name == "results":
            test_results_scraper()
        elif test_name == "standings":
            test_standings_scraper()
        elif test_name == "all":
            run_all_tests()
        else:
            print(f"Unknown test: {test_name}")
            print("Available tests: browser, timer, matchday, results, standings, all")
    else:
        # Run all tests by default
        run_all_tests()