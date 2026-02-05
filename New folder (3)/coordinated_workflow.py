"""
Standalone coordinated workflow: Timer → LIVE → Tracking
"""

import time
from datetime import datetime
from scrapers.live_match_scraper import LiveMatchScraper
from config import LIVE_SCRAPE_INTERVAL

def run_coordinated_workflow(wait_timeout_minutes=30, track_duration_minutes=90):
    """
    Complete coordinated workflow in one script
    """
    print("\n" + "="*70)
    print("🔄 COORDINATED WORKFLOW: TIMER → LIVE → TRACKING")
    print("="*70)
    
    print(f"\n📋 Parameters:")
    print(f"• Wait for LIVE timeout: {wait_timeout_minutes} minutes")
    print(f"• Track after LIVE: {track_duration_minutes} minutes")
    print(f"• Start time: {datetime.now().strftime('%H:%M:%S')}")
    print("-"*70)
    
    scraper = LiveMatchScraper()
    
    try:
        print(f"\n🚀 Step 1: Initializing...")
        
        # Navigate to page
        if not scraper.navigate_to_url("https://odibets.com/odileague"):
            print("❌ Failed to navigate")
            return False
        
        scraper.close_popup()
        
        # Check current timer
        timer = scraper.get_current_timer()
        print(f"⏰ Current timer: {timer}")
        
        if scraper.is_timer_live(timer):
            print("✅ Matchday is already LIVE!")
            should_start = input("Start tracking now? (y/n): ").strip().lower()
            if should_start != 'y':
                print("❌ Cancelled by user")
                return False
        
        print(f"\n⏳ Step 2: Waiting for LIVE...")
        print("(Press Ctrl+C to cancel)")
        
        # Monitor until LIVE
        wait_start = time.time()
        timeout_seconds = wait_timeout_minutes * 60
        last_timer = None
        
        while time.time() - wait_start < timeout_seconds:
            # Refresh page every 30 seconds
            elapsed = time.time() - wait_start
            if int(elapsed) % 30 == 0:
                scraper.driver.refresh()
                time.sleep(3)
                scraper.close_popup()
            
            # Check timer
            current_timer = scraper.get_current_timer()
            
            if current_timer and current_timer != last_timer:
                print(f"Timer: {current_timer}")
                last_timer = current_timer
            
            # Check if LIVE
            if scraper.is_timer_live(current_timer):
                wait_elapsed = time.time() - wait_start
                print(f"\n🎯 Timer went LIVE at {current_timer}!")
                print(f"   Waited {wait_elapsed/60:.1f} minutes")
                
                # Wait a moment for matches to load
                print("   Loading live matches...")
                time.sleep(5)
                
                # Start tracking
                print(f"\n📊 Step 3: Starting live tracking...")
                print(f"   Will track for {track_duration_minutes} minutes")
                print(f"   Updates every {LIVE_SCRAPE_INTERVAL} seconds")
                print("   (Press Ctrl+C to stop early)\n")
                
                success = scraper.start_live_tracking()
                
                if success:
                    # Track for specified duration
                    track_start = time.time()
                    track_seconds = track_duration_minutes * 60
                    
                    while time.time() - track_start < track_seconds and scraper.is_tracking:
                        time.sleep(5)  # Check every 5 seconds
                    
                    scraper.stop_tracking()
                    
                    # Final report
                    track_elapsed = time.time() - track_start
                    total_elapsed = time.time() - wait_start
                    
                    print(f"\n✅ Tracking completed!")
                    print(f"   Tracked for: {track_elapsed/60:.1f} minutes")
                    print(f"   Total time: {total_elapsed/60:.1f} minutes")
                    print(f"   Updates: {len(scraper.match_data_history)}")
                    
                    return True
                else:
                    print("❌ Failed to start tracking")
                    return False
            
            # Wait before next check
            time.sleep(10)
        
        # Timeout reached
        print(f"\n⏰ Timeout: Matchday didn't go LIVE within {wait_timeout_minutes} minutes")
        return False
        
    except KeyboardInterrupt:
        print("\n⚠️ Workflow interrupted by user")
        scraper.stop_tracking()
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        scraper.cleanup()

if __name__ == "__main__":
    print("🚀 Odibets Coordinated Workflow")
    print("-"*40)
    
    try:
        wait_time = int(input("Max wait for LIVE (minutes, default 30): ") or "30")
        track_time = int(input("Track after LIVE (minutes, default 90): ") or "90")
        
        success = run_coordinated_workflow(wait_time, track_time)
        
        if success:
            print("\n🎉 Workflow completed successfully!")
        else:
            print("\n❌ Workflow failed")
            
    except ValueError:
        print("⚠️ Using default values (30min wait, 90min track)")
        run_coordinated_workflow()
    except KeyboardInterrupt:
        print("\n👋 Exiting...")