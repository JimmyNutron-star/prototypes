"""
Main orchestrator that manages all scrapers
"""

import time
import schedule
import threading
from datetime import datetime
from scrapers.timer_monitor import TimerMonitor
from scrapers.matchday_scraper import MatchdayScraper
from scrapers.results_scraper import ResultsScraper
from scrapers.standings_scraper import StandingsScraper
from config import RESULTS_SCRAPE_TIME, STANDINGS_SCRAPE_TIME
from utils.helpers import create_summary_report

class ScraperOrchestrator:
    def __init__(self):
        self.is_running = False
        self.timer_monitor = None
        self.monitor_thread = None
    
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
    print("2. Run Timer Monitor Only")
    print("3. Run Matchday Scraper Now")
    print("4. Run Results Scraper Now")
    print("5. Run Standings Scraper Now")
    print("6. Exit")
    
    try:
        choice = input("\nEnter choice (1-6): ").strip()
        
        if choice == '1':
            orchestrator.start()
        elif choice == '2':
            # Run timer monitor only
            monitor = TimerMonitor()
            if monitor.navigate_to_url("https://odibets.com/odileague"):
                monitor.close_popup()
                monitor.monitor_timer()
                print(monitor.get_timer_summary())
            monitor.cleanup()
        elif choice == '3':
            orchestrator.run_manual_matchday_scrape()
        elif choice == '4':
            orchestrator.run_results_scraper()
        elif choice == '5':
            orchestrator.run_standings_scraper()
        elif choice == '6':
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