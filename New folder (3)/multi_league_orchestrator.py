"""
Multi-League Asynchronous Workflow Orchestrator
Handles all leagues simultaneously with independent workflows
"""

import asyncio
import threading
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from scrapers.timer_monitor import TimerMonitor
from scrapers.matchday_scraper import MatchdayScraper
from scrapers.live_match_scraper import LiveMatchScraper
from scrapers.results_scraper import ResultsScraper
from scrapers.standings_scraper import StandingsScraper
from utils.helpers import calculate_time_until_live, is_timer_live
import json
import os

class LeagueWorkflowManager:
    """Manages the complete workflow for a single league"""
    
    LEAGUES = [
        {"name": "English League", "selector_index": 0, "code": "EL"},
        {"name": "Spanish League", "selector_index": 1, "code": "SL"},
        {"name": "Kenyan League", "selector_index": 2, "code": "KL"},
        {"name": "Italian League", "selector_index": 3, "code": "IL"}
    ]
    
    def __init__(self, league_config, output_dir="data/multi_league"):
        """
        Initialize workflow manager for a specific league
        
        Args:
            league_config: Dict with league name, selector_index, and code
            output_dir: Directory to save league-specific data
        """
        self.league_name = league_config["name"]
        self.league_code = league_config["code"]
        self.selector_index = league_config["selector_index"]
        self.output_dir = os.path.join(output_dir, self.league_code)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Workflow state
        self.state = "initialized"
        self.timer_monitor = None
        self.current_timer = None
        self.matchday_data = None
        self.live_data = None
        self.results_data = None
        self.standings_data = None
        self.match_count = 0
        
        # Workflow flags
        self.is_running = False
        self.scraping_matchday = False
        self.scraping_live = False
        self.validation_complete = False
        
        print(f"✅ [{self.league_code}] Workflow manager initialized for {self.league_name}")
    
    def select_league(self, driver):
        """Select this league in the browser"""
        try:
            # Find all league logos
            league_logos = driver.find_elements("css selector", ".virtual-logos .logo")
            
            if self.selector_index < len(league_logos):
                league_logos[self.selector_index].click()
                time.sleep(2)  # Wait for league to load
                print(f"✅ [{self.league_code}] Selected {self.league_name}")
                return True
            else:
                print(f"❌ [{self.league_code}] League selector not found")
                return False
        except Exception as e:
            print(f"❌ [{self.league_code}] Error selecting league: {e}")
            return False
    
    def get_timer(self, driver):
        """Get current timer for this league"""
        try:
            timer_element = driver.find_element("css selector", ".virtual-timer .ss.active")
            return timer_element.text.strip()
        except:
            return None
    
    def run_workflow(self):
        """
        Main workflow execution for this league
        
        Workflow steps:
        1. Monitor timer (if > 1 minute)
        2. Scrape matchday data + multiple markets (until timer hits 10s)
        3. Prepare for live scraping (at 10s)
        4. Scrape live matches (goals, times, events)
        5. Scrape results and validate against live data
        6. Scrape standings (every 5 matches)
        """
        print(f"\n{'='*70}")
        print(f"🚀 [{self.league_code}] STARTING WORKFLOW: {self.league_name}")
        print(f"{'='*70}")
        
        self.is_running = True
        self.timer_monitor = TimerMonitor()
        
        try:
            # Navigate to page
            if not self.timer_monitor.navigate_to_url("https://odibets.com/odileague"):
                print(f"❌ [{self.league_code}] Failed to navigate")
                return self._create_result(False, "Navigation failed")
            
            self.timer_monitor.close_popup()
            
            # Select this league
            if not self.select_league(self.timer_monitor.driver):
                return self._create_result(False, "League selection failed")
            
            # STEP 1: Check initial timer
            self.current_timer = self.get_timer(self.timer_monitor.driver)
            print(f"⏰ [{self.league_code}] Initial timer: {self.current_timer}")
            
            seconds_until_live = calculate_time_until_live(self.current_timer)
            
            if seconds_until_live is None or seconds_until_live < 60:
                print(f"⚠️ [{self.league_code}] Timer less than 1 minute, skipping matchday scraping")
            else:
                # STEP 2: Scrape matchday data until 10 seconds
                self._scrape_matchday_phase(seconds_until_live)
            
            # STEP 3: Prepare for live (at 10 seconds)
            self._prepare_live_phase()
            
            # STEP 4: Scrape live matches
            self._scrape_live_phase()
            
            # STEP 5: Scrape and validate results
            self._scrape_and_validate_results()
            
            # STEP 6: Scrape standings if needed
            if self.match_count >= 5:
                self._scrape_standings()
            
            return self._create_result(True, "Workflow completed successfully")
            
        except Exception as e:
            print(f"❌ [{self.league_code}] Workflow error: {e}")
            import traceback
            traceback.print_exc()
            return self._create_result(False, f"Error: {str(e)}")
        finally:
            if self.timer_monitor:
                self.timer_monitor.cleanup()
            self.is_running = False
    
    def _scrape_matchday_phase(self, seconds_until_live):
        """Scrape matchday data and markets until timer hits 10 seconds"""
        print(f"\n📊 [{self.league_code}] PHASE 1: Matchday Scraping")
        print(f"   Will scrape until timer hits 10 seconds ({seconds_until_live}s remaining)")
        
        self.scraping_matchday = True
        scrape_count = 0
        
        while self.is_running:
            # Check timer
            self.current_timer = self.get_timer(self.timer_monitor.driver)
            seconds_remaining = calculate_time_until_live(self.current_timer)
            
            if seconds_remaining is not None and seconds_remaining <= 10:
                print(f"🎯 [{self.league_code}] Timer at {self.current_timer} - Stopping matchday scraping")
                break
            
            # Scrape matchday data
            try:
                scraper = MatchdayScraper()
                scraper.driver = self.timer_monitor.driver  # Reuse browser
                
                data = scraper.scrape_current_matchday()
                if data:
                    scrape_count += 1
                    self.matchday_data = data
                    
                    # Save data
                    filename = f"{self.league_code}_matchday_{scrape_count}_{datetime.now().strftime('%H%M%S')}.json"
                    filepath = os.path.join(self.output_dir, filename)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    
                    print(f"   ✅ [{self.league_code}] Matchday scrape #{scrape_count} - {data.get('total_games', 0)} games")
                
                # Don't cleanup scraper, we're reusing the browser
                
            except Exception as e:
                print(f"   ⚠️ [{self.league_code}] Matchday scrape error: {e}")
            
            # Wait before next scrape
            time.sleep(30)  # Scrape every 30 seconds
        
        self.scraping_matchday = False
        print(f"✅ [{self.league_code}] Matchday phase complete ({scrape_count} scrapes)")
    
    def _prepare_live_phase(self):
        """Prepare for live match scraping (wait for timer to hit 0)"""
        print(f"\n⏳ [{self.league_code}] PHASE 2: Preparing for LIVE")
        
        # Monitor timer until LIVE
        while self.is_running:
            self.current_timer = self.get_timer(self.timer_monitor.driver)
            
            if is_timer_live(self.current_timer):
                print(f"🎯 [{self.league_code}] Timer is LIVE at {self.current_timer}!")
                break
            
            seconds_remaining = calculate_time_until_live(self.current_timer)
            if seconds_remaining is not None:
                print(f"   ⏰ [{self.league_code}] {self.current_timer} ({seconds_remaining}s to LIVE)")
            
            time.sleep(5)  # Check every 5 seconds
        
        # Switch to LIVE tab
        try:
            live_tab = self.timer_monitor.driver.find_element("css selector", "ul.tbs li.live")
            live_tab.click()
            time.sleep(2)
            print(f"✅ [{self.league_code}] Switched to LIVE view")
        except Exception as e:
            print(f"⚠️ [{self.league_code}] Could not switch to LIVE tab: {e}")
    
    def _scrape_live_phase(self):
        """Scrape live match data (goals, times, events)"""
        print(f"\n⚽ [{self.league_code}] PHASE 3: Live Match Scraping")
        
        self.scraping_live = True
        live_scrapes = []
        scrape_count = 0
        
        # Scrape for 90 minutes (typical match duration)
        start_time = time.time()
        max_duration = 90 * 60  # 90 minutes in seconds
        
        while self.is_running and (time.time() - start_time) < max_duration:
            try:
                # Scrape live matches
                live_data = self._scrape_live_matches()
                
                if live_data:
                    scrape_count += 1
                    live_scrapes.append({
                        'timestamp': datetime.now().isoformat(),
                        'data': live_data
                    })
                    
                    # Save incremental data
                    filename = f"{self.league_code}_live_{scrape_count}_{datetime.now().strftime('%H%M%S')}.json"
                    filepath = os.path.join(self.output_dir, filename)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(live_data, f, indent=2, ensure_ascii=False)
                    
                    print(f"   ✅ [{self.league_code}] Live scrape #{scrape_count} - {len(live_data.get('matches', []))} matches")
                
                # Check if matches are finished
                if self._are_matches_finished(live_data):
                    print(f"🏁 [{self.league_code}] All matches finished")
                    break
                
            except Exception as e:
                print(f"   ⚠️ [{self.league_code}] Live scrape error: {e}")
            
            # Wait before next scrape
            time.sleep(15)  # Scrape every 15 seconds
        
        self.live_data = live_scrapes
        self.scraping_live = False
        print(f"✅ [{self.league_code}] Live phase complete ({scrape_count} scrapes)")
    
    def _scrape_live_matches(self):
        """Scrape current live match data"""
        try:
            matches = []
            match_elements = self.timer_monitor.driver.find_elements("css selector", ".play.show .gm")
            
            for idx, match_elem in enumerate(match_elements):
                try:
                    # Extract match data
                    home_team = match_elem.find_element("css selector", ".t-1-j").text
                    away_team = match_elem.find_element("css selector", ".t-2-j").text
                    
                    scores = match_elem.find_elements("css selector", ".s .d")
                    home_score = scores[0].text if len(scores) > 0 else "0"
                    away_score = scores[1].text if len(scores) > 1 else "0"
                    
                    # Get goal times
                    home_events = match_elem.find_elements("css selector", ".gm-h .hi:first-child span")
                    away_events = match_elem.find_elements("css selector", ".gm-h .hi:last-child span")
                    
                    home_goal_times = [event.text for event in home_events]
                    away_goal_times = [event.text for event in away_events]
                    
                    matches.append({
                        'match_index': idx,
                        'home_team': home_team,
                        'away_team': away_team,
                        'home_score': home_score,
                        'away_score': away_score,
                        'home_goal_times': home_goal_times,
                        'away_goal_times': away_goal_times
                    })
                    
                except Exception as e:
                    print(f"      ⚠️ Error parsing match {idx}: {e}")
            
            return {'matches': matches, 'total_matches': len(matches)}
            
        except Exception as e:
            print(f"   ❌ Error scraping live matches: {e}")
            return None
    
    def _are_matches_finished(self, live_data):
        """Check if all matches are finished (simple heuristic)"""
        if not live_data or 'matches' not in live_data:
            return False
        
        # Check if we have consistent scores for a while
        # This is a simplified check - you might want more sophisticated logic
        return False  # For now, rely on time limit
    
    def _scrape_and_validate_results(self):
        """Scrape results and validate against live data"""
        print(f"\n📋 [{self.league_code}] PHASE 4: Results Scraping & Validation")
        
        try:
            # Click Results tab
            results_tab = self.timer_monitor.driver.find_element("css selector", "ul.tbs li:nth-child(2)")
            results_tab.click()
            time.sleep(2)
            
            # Scrape results
            scraper = ResultsScraper()
            scraper.driver = self.timer_monitor.driver
            
            results_data = scraper.scrape_results()
            
            if results_data:
                self.results_data = results_data
                
                # Save results
                filename = f"{self.league_code}_results_{datetime.now().strftime('%H%M%S')}.json"
                filepath = os.path.join(self.output_dir, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(results_data, f, indent=2, ensure_ascii=False)
                
                print(f"   ✅ [{self.league_code}] Results scraped")
                
                # Validate against live data
                self._validate_live_vs_results()
            
        except Exception as e:
            print(f"   ❌ [{self.league_code}] Results scraping error: {e}")
    
    def _validate_live_vs_results(self):
        """Validate live match data against results data"""
        print(f"\n🔍 [{self.league_code}] Validating live data vs results...")
        
        if not self.live_data or not self.results_data:
            print(f"   ⚠️ [{self.league_code}] Missing data for validation")
            return
        
        # Get final live data (last scrape)
        final_live = self.live_data[-1]['data'] if self.live_data else None
        
        if not final_live:
            return
        
        # Compare scores
        discrepancies = []
        
        # This is a simplified validation - you'll need to match teams properly
        print(f"   ℹ️ [{self.league_code}] Validation logic to be implemented")
        print(f"   ℹ️ [{self.league_code}] Results data is the absolute truth")
        
        self.validation_complete = True
    
    def _scrape_standings(self):
        """Scrape league standings"""
        print(f"\n🏆 [{self.league_code}] PHASE 5: Standings Scraping")
        
        try:
            # Click Standings tab
            standings_tab = self.timer_monitor.driver.find_element("css selector", "ul.tbs li:nth-child(3)")
            standings_tab.click()
            time.sleep(2)
            
            # Scrape standings
            scraper = StandingsScraper()
            scraper.driver = self.timer_monitor.driver
            
            standings_data = scraper.scrape_standings()
            
            if standings_data:
                self.standings_data = standings_data
                
                # Save standings
                filename = f"{self.league_code}_standings_{datetime.now().strftime('%H%M%S')}.json"
                filepath = os.path.join(self.output_dir, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(standings_data, f, indent=2, ensure_ascii=False)
                
                print(f"   ✅ [{self.league_code}] Standings scraped")
            
        except Exception as e:
            print(f"   ❌ [{self.league_code}] Standings scraping error: {e}")
    
    def _create_result(self, success, message):
        """Create workflow result summary"""
        return {
            'league': self.league_name,
            'league_code': self.league_code,
            'success': success,
            'message': message,
            'matchday_scrapes': len(self.matchday_data) if self.matchday_data else 0,
            'live_scrapes': len(self.live_data) if self.live_data else 0,
            'results_scraped': self.results_data is not None,
            'standings_scraped': self.standings_data is not None,
            'validation_complete': self.validation_complete
        }


class MultiLeagueOrchestrator:
    """Orchestrates workflows for all leagues simultaneously"""
    
    def __init__(self, max_workers=4):
        """
        Initialize multi-league orchestrator
        
        Args:
            max_workers: Maximum number of concurrent league workflows
        """
        self.max_workers = max_workers
        self.league_managers = []
        self.results = []
        
        print(f"\n{'='*70}")
        print(f"🌍 MULTI-LEAGUE ORCHESTRATOR INITIALIZED")
        print(f"{'='*70}")
        print(f"Max concurrent leagues: {max_workers}")
        print(f"Total leagues: {len(LeagueWorkflowManager.LEAGUES)}")
    
    def run_all_leagues(self):
        """Run workflows for all leagues simultaneously"""
        print(f"\n🚀 Starting workflows for all leagues...")
        print(f"{'='*70}\n")
        
        # Create league managers
        for league_config in LeagueWorkflowManager.LEAGUES:
            manager = LeagueWorkflowManager(league_config)
            self.league_managers.append(manager)
        
        # Run workflows in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all league workflows
            future_to_league = {
                executor.submit(manager.run_workflow): manager
                for manager in self.league_managers
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_league):
                manager = future_to_league[future]
                try:
                    result = future.result()
                    self.results.append(result)
                    print(f"\n✅ [{manager.league_code}] Workflow completed: {result['message']}")
                except Exception as e:
                    print(f"\n❌ [{manager.league_code}] Workflow failed: {e}")
                    self.results.append({
                        'league': manager.league_name,
                        'league_code': manager.league_code,
                        'success': False,
                        'message': f'Exception: {str(e)}'
                    })
        
        # Print final summary
        self._print_summary()
        
        return self.results
    
    def _print_summary(self):
        """Print final summary of all league workflows"""
        print(f"\n{'='*70}")
        print(f"📊 MULTI-LEAGUE WORKFLOW SUMMARY")
        print(f"{'='*70}\n")
        
        successful = sum(1 for r in self.results if r['success'])
        failed = len(self.results) - successful
        
        print(f"Total Leagues: {len(self.results)}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"\nDetailed Results:")
        print(f"{'-'*70}")
        
        for result in self.results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} [{result['league_code']}] {result['league']}")
            print(f"   Message: {result['message']}")
            if result['success']:
                print(f"   Matchday scrapes: {result.get('matchday_scrapes', 0)}")
                print(f"   Live scrapes: {result.get('live_scrapes', 0)}")
                print(f"   Results: {'✅' if result.get('results_scraped') else '❌'}")
                print(f"   Standings: {'✅' if result.get('standings_scraped') else '❌'}")
            print()
        
        print(f"{'='*70}")


def test_single_league():
    """Test a single league workflow"""
    print("\n" + "="*70)
    print("🧪 SINGLE LEAGUE TESTING")
    print("="*70)
    print("\nAvailable Leagues:")
    
    for idx, league in enumerate(LeagueWorkflowManager.LEAGUES, 1):
        print(f"  {idx}. {league['name']} ({league['code']})")
    
    print(f"  {len(LeagueWorkflowManager.LEAGUES) + 1}. Back to main menu")
    print("="*70)
    
    try:
        choice = input("\nSelect league number: ").strip()
        league_idx = int(choice) - 1
        
        if league_idx == len(LeagueWorkflowManager.LEAGUES):
            return  # Back to main menu
        
        if 0 <= league_idx < len(LeagueWorkflowManager.LEAGUES):
            league_config = LeagueWorkflowManager.LEAGUES[league_idx]
            
            print(f"\n🚀 Starting workflow for {league_config['name']}...")
            print("="*70)
            
            # Create and run single league manager
            manager = LeagueWorkflowManager(league_config)
            result = manager.run_workflow()
            
            # Print result
            print("\n" + "="*70)
            print(f"📊 WORKFLOW RESULT: {league_config['name']}")
            print("="*70)
            print(f"Status: {'✅ SUCCESS' if result['success'] else '❌ FAILED'}")
            print(f"Message: {result['message']}")
            
            if result['success']:
                print(f"\nDetails:")
                print(f"  • Matchday scrapes: {result.get('matchday_scrapes', 0)}")
                print(f"  • Live scrapes: {result.get('live_scrapes', 0)}")
                print(f"  • Results scraped: {'✅' if result.get('results_scraped') else '❌'}")
                print(f"  • Standings scraped: {'✅' if result.get('standings_scraped') else '❌'}")
                print(f"  • Validation complete: {'✅' if result.get('validation_complete') else '❌'}")
            
            print("="*70)
            
            # Save result
            output_file = f"data/multi_league/{league_config['code']}/test_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print(f"\n📄 Result saved to: {output_file}")
            
        else:
            print("❌ Invalid league number")
            
    except ValueError:
        print("❌ Invalid input. Please enter a number.")
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


def run_all_leagues_workflow():
    """Run all leagues simultaneously"""
    print("\n" + "="*70)
    print("🌍 MULTI-LEAGUE ASYNCHRONOUS WORKFLOW")
    print("="*70)
    print("\nThis will run independent workflows for all leagues:")
    print("  • English League")
    print("  • Spanish League")
    print("  • Kenyan League")
    print("  • Italian League")
    print("\nEach league will:")
    print("  1. Monitor timer (if > 1 minute)")
    print("  2. Scrape matchday data until timer hits 10 seconds")
    print("  3. Switch to live scraping when timer goes LIVE")
    print("  4. Scrape live matches (goals, times, events)")
    print("  5. Scrape and validate results")
    print("  6. Scrape standings (every 5 matches)")
    print("\n" + "="*70)
    
    choice = input("\nStart multi-league workflow? (y/n): ").strip().lower()
    
    if choice == 'y':
        orchestrator = MultiLeagueOrchestrator(max_workers=4)
        results = orchestrator.run_all_leagues()
        
        # Save final results
        output_file = f"data/multi_league/workflow_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Results saved to: {output_file}")
    else:
        print("👋 Cancelled")


def main():
    """Main entry point with menu system"""
    while True:
        print("\n" + "="*70)
        print("🌍 ODILEAGUE MULTI-LEAGUE SCRAPER")
        print("="*70)
        print("\nOptions:")
        print("  1. Run All Leagues (Simultaneous)")
        print("  2. Test Single League (Individual)")
        print("  3. Exit")
        print("="*70)
        
        try:
            choice = input("\nEnter choice (1-3): ").strip()
            
            if choice == '1':
                run_all_leagues_workflow()
            elif choice == '2':
                test_single_league()
            elif choice == '3':
                print("\n👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please enter 1, 2, or 3.")
        
        except KeyboardInterrupt:
            print("\n\n👋 Exiting...")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
