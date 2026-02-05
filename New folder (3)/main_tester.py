"""
Main orchestrator that manages all scrapers
"""

import time
import schedule
import threading
import os
from datetime import datetime
from scrapers.timer_monitor import TimerMonitor
from scrapers.matchday_scraper import MatchdayScraper
from scrapers.results_scraper import ResultsScraper
from scrapers.standings_scraper import StandingsScraper
from config import RESULTS_SCRAPE_TIME, STANDINGS_SCRAPE_TIME
from utils.helpers import create_summary_report
from utils.file_handler import FileHandler

class ScraperOrchestrator:
    def __init__(self):
        self.is_running = False
        self.timer_monitor = None
        self.monitor_thread = None
    
    def run_complete_test(self, max_wait_minutes=5):
        """
        Run complete test process once
        - Timer monitoring
        - Matchday data collection
        - Results data collection
        - Standings data collection
        """
        print("\n" + "="*70)
        print("🧪 COMPLETE SYSTEM TEST - ONE TIME RUN")
        print("="*70)
        
        test_start_time = datetime.now()
        print(f"Test started at: {test_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Max wait time: {max_wait_minutes} minutes")
        print("-"*70)
        
        # Create test directory
        test_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_dir = f"test_run_{test_timestamp}"
        os.makedirs(test_dir, exist_ok=True)
        print(f"📁 Test data will be saved in: {test_dir}")
        
        all_test_data = {
            'test_info': {
                'start_time': test_start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'max_wait_minutes': max_wait_minutes,
                'test_directory': test_dir
            },
            'timer_data': None,
            'matchday_data': None,
            'results_data': None,
            'standings_data': None
        }
        
        # Step 1: Timer Monitoring Test
        print("\n1️⃣ STEP 1: TIMER MONITORING")
        print("-"*40)
        
        timer_data = self._test_timer_monitoring(test_dir, max_wait_minutes)
        all_test_data['timer_data'] = timer_data
        
        # Step 2: Matchday Data Collection
        print("\n2️⃣ STEP 2: MATCHDAY DATA COLLECTION")
        print("-"*40)
        
        matchday_data = self._test_matchday_scraper(test_dir)
        all_test_data['matchday_data'] = matchday_data
        
        # Step 3: Results Data Collection
        print("\n3️⃣ STEP 3: RESULTS DATA COLLECTION")
        print("-"*40)
        
        results_data = self._test_results_scraper(test_dir)
        all_test_data['results_data'] = results_data
        
        # Step 4: Standings Data Collection
        print("\n4️⃣ STEP 4: STANDINGS DATA COLLECTION")
        print("-"*40)
        
        standings_data = self._test_standings_scraper(test_dir)
        all_test_data['standings_data'] = standings_data
        
        # Step 5: Save Complete Test Report
        print("\n5️⃣ STEP 5: GENERATING TEST REPORT")
        print("-"*40)
        
        self._save_test_report(all_test_data, test_dir)
        
        # Calculate duration
        test_end_time = datetime.now()
        duration = test_end_time - test_start_time
        duration_minutes = duration.total_seconds() / 60
        
        print("\n" + "="*70)
        print("✅ COMPLETE TEST FINISHED")
        print("="*70)
        print(f"Start Time: {test_start_time.strftime('%H:%M:%S')}")
        print(f"End Time: {test_end_time.strftime('%H:%M:%S')}")
        print(f"Total Duration: {duration_minutes:.1f} minutes")
        print(f"Test Directory: {test_dir}")
        print("="*70)
        
        return all_test_data
    
    def _test_timer_monitoring(self, test_dir, max_wait_minutes):
        """Test timer monitoring"""
        print("Starting timer monitor...")
        
        timer_monitor = TimerMonitor()
        timer_data = None
        
        try:
            # Setup timer monitor
            if not timer_monitor.navigate_to_url("https://odibets.com/odileague"):
                print("❌ Failed to initialize timer monitor")
                return None
            
            timer_monitor.close_popup()
            
            # Get initial timer
            initial_timer = timer_monitor.get_current_timer()
            print(f"⏰ Initial Timer: {initial_timer}")
            
            # Start monitoring for limited time
            max_checks = (max_wait_minutes * 60) // 10  # Convert minutes to checks
            print(f"Monitoring for up to {max_wait_minutes} minutes...")
            
            went_live, final_timer = timer_monitor.monitor_timer(
                check_interval=10,
                max_checks=max_checks
            )
            
            # Collect timer data
            timer_data = {
                'initial_timer': initial_timer,
                'final_timer': final_timer,
                'went_live': went_live,
                'timer_history': timer_monitor.timer_history
            }
            
            if went_live:
                print(f"🎯 Timer went LIVE at {final_timer}")
            else:
                print(f"⏰ Monitoring completed at {final_timer}")
            
            # Save timer data
            if timer_monitor.timer_history:
                import json
                timer_file = os.path.join(test_dir, "timer_monitor.json")
                with open(timer_file, 'w', encoding='utf-8') as f:
                    json.dump(timer_data, f, indent=2)
                print(f"💾 Timer data saved: {timer_file}")
            
            return timer_data
            
        except Exception as e:
            print(f"❌ Timer monitor error: {e}")
            return None
        finally:
            timer_monitor.cleanup()
    
    def _test_matchday_scraper(self, test_dir):
        """Test matchday scraper"""
        print("Running matchday scraper...")
        
        matchday_scraper = MatchdayScraper()
        matchday_data = None
        
        try:
            data = matchday_scraper.scrape_current_matchday()
            
            if data:
                print(f"✅ Scraped {data.get('total_games', 0)} games")
                
                # Save to test directory
                file_handler = FileHandler("matchday")
                test_file = os.path.join(test_dir, "matchday_data.json")
                
                import json
                with open(test_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                print(f"💾 Matchday data saved: {test_file}")
                
                # Create summary
                if data.get('games'):
                    summary_file = os.path.join(test_dir, "matchday_summary.txt")
                    with open(summary_file, 'w', encoding='utf-8') as f:
                        f.write(create_summary_report(data['games'], "matchday"))
                    print(f"📄 Matchday summary saved: {summary_file}")
                
                matchday_data = {
                    'total_games': data.get('total_games', 0),
                    'league': data.get('league_info', {}).get('league', 'Unknown'),
                    'timer': data.get('league_info', {}).get('timer', 'Unknown'),
                    'file_path': test_file
                }
            else:
                print("❌ No matchday data scraped")
            
            return matchday_data
            
        except Exception as e:
            print(f"❌ Matchday scraper error: {e}")
            return None
        finally:
            matchday_scraper.cleanup()
    
    def _test_results_scraper(self, test_dir):
        """Test results scraper"""
        print("Running results scraper...")
        
        results_scraper = ResultsScraper()
        results_data = None
        
        try:
            data = results_scraper.scrape_results()
            
            if data:
                print(f"✅ Scraped {data.get('total_weeks', 0)} weeks")
                
                # Save to test directory
                test_file = os.path.join(test_dir, "results_data.json")
                
                import json
                with open(test_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                print(f"💾 Results data saved: {test_file}")
                
                # Create summary
                if data.get('results_weeks'):
                    summary_file = os.path.join(test_dir, "results_summary.txt")
                    with open(summary_file, 'w', encoding='utf-8') as f:
                        f.write(create_summary_report(data['results_weeks'][0], "results"))
                    print(f"📄 Results summary saved: {summary_file}")
                
                results_data = {
                    'total_weeks': data.get('total_weeks', 0),
                    'league': data.get('league_info', {}).get('league', 'Unknown'),
                    'file_path': test_file
                }
            else:
                print("❌ No results data scraped")
            
            return results_data
            
        except Exception as e:
            print(f"❌ Results scraper error: {e}")
            return None
        finally:
            results_scraper.cleanup()
    
    def _test_standings_scraper(self, test_dir):
        """Test standings scraper"""
        print("Running standings scraper...")
        
        standings_scraper = StandingsScraper()
        standings_data = None
        
        try:
            data = standings_scraper.scrape_standings()
            
            if data:
                total_teams = data.get('standings', {}).get('total_teams', 0)
                print(f"✅ Scraped {total_teams} teams")
                
                # Save to test directory
                test_file = os.path.join(test_dir, "standings_data.json")
                
                import json
                with open(test_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                print(f"💾 Standings data saved: {test_file}")
                
                # Create summary
                if data.get('standings'):
                    summary_file = os.path.join(test_dir, "standings_summary.txt")
                    with open(summary_file, 'w', encoding='utf-8') as f:
                        f.write(create_summary_report(data['standings'], "standings"))
                    print(f"📄 Standings summary saved: {summary_file}")
                
                standings_data = {
                    'total_teams': total_teams,
                    'season': data.get('standings', {}).get('season', 'Unknown'),
                    'league': data.get('league_info', {}).get('league', 'Unknown'),
                    'file_path': test_file
                }
            else:
                print("❌ No standings data scraped")
            
            return standings_data
            
        except Exception as e:
            print(f"❌ Standings scraper error: {e}")
            return None
        finally:
            standings_scraper.cleanup()
    
    def _save_test_report(self, all_data, test_dir):
        """Save complete test report"""
        report_file = os.path.join(test_dir, "complete_test_report.txt")
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("ODIBETS SCRAPER SYSTEM - COMPLETE TEST REPORT\n")
            f.write("="*70 + "\n\n")
            
            test_info = all_data.get('test_info', {})
            f.write(f"Test Start Time: {test_info.get('start_time', 'Unknown')}\n")
            f.write(f"Max Wait Time: {test_info.get('max_wait_minutes', 'Unknown')} minutes\n")
            f.write(f"Test Directory: {test_info.get('test_directory', 'Unknown')}\n\n")
            
            f.write("📊 TEST RESULTS SUMMARY\n")
            f.write("-"*40 + "\n\n")
            
            # Timer Monitor Results
            timer_data = all_data.get('timer_data')
            f.write("1. TIMER MONITOR:\n")
            if timer_data:
                f.write(f"   Status: {'LIVE detected' if timer_data.get('went_live') else 'Completed normally'}\n")
                f.write(f"   Initial Timer: {timer_data.get('initial_timer', 'N/A')}\n")
                f.write(f"   Final Timer: {timer_data.get('final_timer', 'N/A')}\n")
                f.write(f"   Timer Checks: {len(timer_data.get('timer_history', []))}\n")
            else:
                f.write("   Status: ❌ FAILED\n")
            f.write("\n")
            
            # Matchday Results
            matchday_data = all_data.get('matchday_data')
            f.write("2. MATCHDAY SCRAPER:\n")
            if matchday_data:
                f.write(f"   Status: ✅ SUCCESS\n")
                f.write(f"   Games Scraped: {matchday_data.get('total_games', 0)}\n")
                f.write(f"   League: {matchday_data.get('league', 'Unknown')}\n")
                f.write(f"   Timer at Scrape: {matchday_data.get('timer', 'Unknown')}\n")
            else:
                f.write("   Status: ❌ FAILED\n")
            f.write("\n")
            
            # Results Scraper Results
            results_data = all_data.get('results_data')
            f.write("3. RESULTS SCRAPER:\n")
            if results_data:
                f.write(f"   Status: ✅ SUCCESS\n")
                f.write(f"   Weeks Scraped: {results_data.get('total_weeks', 0)}\n")
                f.write(f"   League: {results_data.get('league', 'Unknown')}\n")
            else:
                f.write("   Status: ❌ FAILED\n")
            f.write("\n")
            
            # Standings Scraper Results
            standings_data = all_data.get('standings_data')
            f.write("4. STANDINGS SCRAPER:\n")
            if standings_data:
                f.write(f"   Status: ✅ SUCCESS\n")
                f.write(f"   Teams Scraped: {standings_data.get('total_teams', 0)}\n")
                f.write(f"   Season: {standings_data.get('season', 'Unknown')}\n")
                f.write(f"   League: {standings_data.get('league', 'Unknown')}\n")
            else:
                f.write("   Status: ❌ FAILED\n")
            f.write("\n")
            
            # Overall Status
            successes = sum(1 for data in [matchday_data, results_data, standings_data] if data)
            total_tests = 3  # matchday, results, standings
            
            f.write("📈 OVERALL STATUS:\n")
            f.write("-"*40 + "\n")
            f.write(f"Successful Tests: {successes}/{total_tests}\n")
            f.write(f"Success Rate: {(successes/total_tests)*100:.1f}%\n")
            
            if successes == total_tests:
                f.write("\n🎉 ALL TESTS PASSED! System is working correctly.\n")
            elif successes > 0:
                f.write(f"\n⚠️  PARTIAL SUCCESS: {successes} out of {total_tests} tests passed.\n")
            else:
                f.write("\n❌ ALL TESTS FAILED. Check your setup and try again.\n")
            
            f.write("\n📁 Generated Files:\n")
            f.write("-"*40 + "\n")
            for file in os.listdir(test_dir):
                f.write(f"  • {file}\n")
            
            f.write("\n" + "="*70 + "\n")
            f.write("END OF TEST REPORT\n")
            f.write("="*70 + "\n")
        
        print(f"📄 Complete test report saved: {report_file}")
    
    def start_timer_monitoring(self):
        """Start timer monitor in a separate thread"""
        if self.timer_monitor and self.timer_monitor.is_monitoring:
            print("Timer monitor is already running")
            return
        
        self.timer_monitor = TimerMonitor()
        
        # Setup the monitor
        if not self.timer_monitor.navigate_to_url("https://odibets.com/odileague"):
            print("Failed to initialize timer monitor")
            return
        
        self.timer_monitor.close_popup()
        
        # Start monitoring in a separate thread
        self.monitor_thread = threading.Thread(target=self._run_timer_monitor)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        print("✅ Timer monitor started in background thread")
    
    def _run_timer_monitor(self):
        """Run timer monitor (to be called in thread)"""
        try:
            # Monitor until LIVE
            went_live, live_timer = self.timer_monitor.monitor_timer(max_checks=None)
            
            if went_live:
                print(f"\n🎯 Timer monitor detected LIVE at {live_timer}")
                
                # Trigger matchday scraper when LIVE
                self.trigger_matchday_scraper()
                
                # Continue monitoring (in case we want to track multiple matchdays)
                print("Continuing timer monitoring...")
                self.timer_monitor.monitor_timer()
            
        except Exception as e:
            print(f"Timer monitor error: {e}")
        finally:
            if self.timer_monitor:
                self.timer_monitor.cleanup()
    
    def trigger_matchday_scraper(self):
        """Trigger matchday scraper when timer goes LIVE"""
        print("\n⚡ Triggering matchday scraper...")
        
        matchday_scraper = MatchdayScraper()
        try:
            data = matchday_scraper.scrape_current_matchday()
            
            if data:
                # Save data
                saved_files = matchday_scraper.save_data(data, "matchday_live")
                
                # Create summary
                summary = create_summary_report(data['games'], "matchday")
                print(summary)
                
                print(f"✅ Matchday data saved successfully")
                
            else:
                print("❌ Failed to scrape matchday data")
                
        finally:
            matchday_scraper.cleanup()
    
    def run_results_scraper(self):
        """Run results scraper on schedule"""
        print(f"\n📈 Running results scraper at {datetime.now().strftime('%H:%M:%S')}")
        
        results_scraper = ResultsScraper()
        try:
            data = results_scraper.scrape_results()
            
            if data:
                saved_files = results_scraper.save_data(data, "results")
                
                # Create summary
                if data.get('results_weeks'):
                    summary = create_summary_report(data['results_weeks'][0], "results")
                    print(summary)
                
                print(f"✅ Results data saved successfully")
                
            else:
                print("❌ Failed to scrape results data")
                
        finally:
            results_scraper.cleanup()
    
    def run_standings_scraper(self):
        """Run standings scraper on schedule"""
        print(f"\n🏆 Running standings scraper at {datetime.now().strftime('%H:%M:%S')}")
        
        standings_scraper = StandingsScraper()
        try:
            data = standings_scraper.scrape_standings()
            
            if data:
                saved_files = standings_scraper.save_data(data, "standings")
                
                # Create summary
                summary = create_summary_report(data['standings'], "standings")
                print(summary)
                
                print(f"✅ Standings data saved successfully")
                
            else:
                print("❌ Failed to scrape standings data")
                
        finally:
            standings_scraper.cleanup()
    
    def run_manual_matchday_scrape(self):
        """Manual trigger for matchday scraper"""
        print("\n🎯 Running manual matchday scrape...")
        self.trigger_matchday_scraper()
    
    def setup_schedules(self):
        """Setup scheduled jobs"""
        # Schedule results scraper
        schedule.every().day.at(RESULTS_SCRAPE_TIME.strftime("%H:%M")).do(
            self.run_results_scraper
        )
        
        # Schedule standings scraper
        schedule.every().day.at(STANDINGS_SCRAPE_TIME.strftime("%H:%M")).do(
            self.run_standings_scraper
        )
        
        print(f"✅ Scheduled results scraper at {RESULTS_SCRAPE_TIME}")
        print(f"✅ Scheduled standings scraper at {STANDINGS_SCRAPE_TIME}")
    
    def start(self):
        """Start the orchestrator"""
        self.is_running = True
        
        print("\n" + "="*70)
        print("🎯 ODIBETS ODILEAGUE SCRAPER ORCHESTRATOR")
        print("="*70)
        
        # Setup schedules
        self.setup_schedules()
        
        # Start timer monitor
        self.start_timer_monitoring()
        
        print("\n✅ Orchestrator started successfully!")
        print("\nServices running:")
        print("  • Timer Monitor (continuous)")
        print(f"  • Results Scraper (scheduled at {RESULTS_SCRAPE_TIME})")
        print(f"  • Standings Scraper (scheduled at {STANDINGS_SCRAPE_TIME})")
        print("\nPress Ctrl+C to stop\n")
        
        # Main loop
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping orchestrator...")
            self.stop()
    
    def stop(self):
        """Stop the orchestrator"""
        self.is_running = False
        
        # Stop timer monitor
        if self.timer_monitor:
            self.timer_monitor.stop_monitoring()
        
        print("✅ Orchestrator stopped")

def main_menu():
    """Simple menu interface"""
    orchestrator = ScraperOrchestrator()
    
    print("\n" + "="*70)
    print("🎯 ODIBETS ODILEAGUE SCRAPER SYSTEM")
    print("="*70)
    print("\nOptions:")
    print("1. Start Full Orchestrator (Timer Monitor + Scheduled Scrapers)")
    print("2. Run Complete System Test (One-time run)")
    print("3. Run Timer Monitor Only")
    print("4. Run Matchday Scraper Now")
    print("5. Run Results Scraper Now")
    print("6. Run Standings Scraper Now")
    print("7. Exit")
    
    try:
        choice = input("\nEnter choice (1-7): ").strip()
        
        if choice == '1':
            orchestrator.start()
        elif choice == '2':
            # Run complete system test
            try:
                max_wait = int(input("\nEnter max wait time for timer (minutes, default 5): ") or "5")
                orchestrator.run_complete_test(max_wait_minutes=max_wait)
            except ValueError:
                print("⚠️ Using default wait time (5 minutes)")
                orchestrator.run_complete_test()
        elif choice == '3':
            # Run timer monitor only
            monitor = TimerMonitor()
            if monitor.navigate_to_url("https://odibets.com/odileague"):
                monitor.close_popup()
                monitor.monitor_timer()
                print(monitor.get_timer_summary())
            monitor.cleanup()
        elif choice == '4':
            orchestrator.run_manual_matchday_scrape()
        elif choice == '5':
            orchestrator.run_results_scraper()
        elif choice == '6':
            orchestrator.run_standings_scraper()
        elif choice == '7':
            print("👋 Goodbye!")
            return
        else:
            print("❌ Invalid choice")
        
    except KeyboardInterrupt:
        print("\n👋 Exiting...")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # First, install requirements
    print("📦 Setting up Odibets Scraper System...")
    
    main_menu()