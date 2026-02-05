"""
Live Match Scraper - Tracks matches in real-time once they go LIVE
"""

import time
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from scrapers.base_scraper import BaseScraper
from config import ODILEAGUE_URL, LIVE_SCRAPE_INTERVAL, MAX_LIVE_MATCH_DURATION
from utils.helpers import is_timer_live

class LiveMatchScraper(BaseScraper):
    def __init__(self):
        super().__init__("live_match")
        self.match_data_history = []
        self.current_match_state = {}
        self.live_matches = []
        self.is_tracking = False
        self.match_start_time = None
    
    def start_live_tracking(self, match_filter=None):
        """
        Start tracking live matches
        match_filter: Optional list of match indices or team names to track
        """
        try:
            self.logger.info("Starting live match tracking...")
            
            # Navigate to page
            if not self.navigate_to_url(ODILEAGUE_URL):
                return False
            
            self.close_popup()
            
            # Check if any matches are LIVE
            if not self._check_for_live_matches():
                self.logger.warning("No live matches found")
                return False
            
            # Start tracking
            self.is_tracking = True
            self.match_start_time = datetime.now()
            
            # Filter matches if specified
            if match_filter:
                self._filter_matches(match_filter)
            
            self.logger.info(f"Tracking {len(self.live_matches)} live matches")
            
            # Start the tracking loop
            self._track_live_matches()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting live tracking: {e}")
            return False
    
    def _check_for_live_matches(self):
        """Check if there are any live matches on the page"""
        try:
            # First, check if we're on the LIVE tab
            live_tab = self.safe_find_element(".tbs li.live", timeout=5)
            if live_tab:
                self.logger.info("Already on LIVE tab")
            else:
                # Try to switch to LIVE tab
                self._switch_to_live_tab()
            
            # Look for live match containers
            live_match_containers = self.safe_find_elements(".play.show .gm", timeout=10)
            
            if not live_match_containers:
                self.logger.warning("No live match containers found")
                return False
            
            self.live_matches = live_match_containers
            self.logger.info(f"Found {len(self.live_matches)} live match containers")
            
            # Extract initial match data
            for i, match_container in enumerate(self.live_matches):
                match_data = self._extract_match_data(match_container, i)
                if match_data:
                    self.current_match_state[i] = match_data
                    self.logger.info(f"Match {i+1}: {match_data.get('home_team')} vs {match_data.get('away_team')}")
            
            return len(self.current_match_state) > 0
            
        except Exception as e:
            self.logger.error(f"Error checking for live matches: {e}")
            return False
    
    def _switch_to_live_tab(self):
        """Switch to the LIVE matches tab"""
        try:
            live_tab = self.safe_find_element(".tbs li.live", timeout=10)
            if live_tab:
                # Check if already active
                if 'active' not in live_tab.get_attribute('class'):
                    live_tab.click()
                    self.logger.info("Switched to LIVE tab")
                    time.sleep(3)  # Wait for live matches to load
                else:
                    self.logger.info("Already on LIVE tab")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error switching to LIVE tab: {e}")
            return False
    
    def _extract_match_data(self, match_container, match_index):
        """Extract data from a live match container"""
        try:
            match_data = {
                'match_index': match_index,
                'timestamp': datetime.now().strftime("%H:%M:%S"),
                'scrape_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Extract team names
            try:
                home_team = match_container.find_element(By.CSS_SELECTOR, ".t-1-j")
                away_team = match_container.find_element(By.CSS_SELECTOR, ".t-2-j")
                match_data['home_team'] = home_team.text.strip()
                match_data['away_team'] = away_team.text.strip()
            except:
                match_data['home_team'] = 'Unknown'
                match_data['away_team'] = 'Unknown'
            
            # Extract current score
            try:
                score_elements = match_container.find_elements(By.CSS_SELECTOR, ".s .d")
                if len(score_elements) >= 2:
                    home_score = score_elements[0].text.strip()
                    away_score = score_elements[1].text.strip()
                    match_data['home_score'] = home_score
                    match_data['away_score'] = away_score
                    match_data['current_score'] = f"{home_score}-{away_score}"
                    
                    # Check if score is bold (indicating recent change)
                    if 'b' in score_elements[0].get_attribute('class'):
                        match_data['last_scorer'] = match_data['home_team']
                    elif 'b' in score_elements[1].get_attribute('class'):
                        match_data['last_scorer'] = match_data['away_team']
            except:
                match_data['home_score'] = '0'
                match_data['away_score'] = '0'
                match_data['current_score'] = '0-0'
            
            # Extract match minute
            try:
                minute_element = match_container.find_element(By.CSS_SELECTOR, ".dv span")
                match_data['current_minute'] = minute_element.text.strip()
            except:
                match_data['current_minute'] = '0'
            
            # Extract half-time score
            try:
                ht_score_element = match_container.find_element(By.CSS_SELECTOR, ".dv span")
                if ht_score_element and 'HT' in ht_score_element.text:
                    match_data['half_time_score'] = ht_score_element.text.replace('HT', '').strip()
            except:
                match_data['half_time_score'] = 'N/A'
            
            # Extract goal events
            match_data['home_events'] = self._extract_team_events(match_container, 'home')
            match_data['away_events'] = self._extract_team_events(match_container, 'away')
            
            # Extract team logos
            try:
                home_logo = match_container.find_element(By.CSS_SELECTOR, ".t-1-i")
                away_logo = match_container.find_element(By.CSS_SELECTOR, ".t-2-i")
                match_data['home_logo'] = home_logo.get_attribute('src')
                match_data['away_logo'] = away_logo.get_attribute('src')
            except:
                pass
            
            return match_data
            
        except Exception as e:
            self.logger.warning(f"Error extracting match data: {e}")
            return None
    
    def _extract_team_events(self, match_container, team_side):
        """Extract goal/event minutes for a team"""
        events = []
        try:
            if team_side == 'home':
                selector = ".hi:first-child span"
            else:
                selector = ".hi:last-child span"
            
            event_elements = match_container.find_elements(By.CSS_SELECTOR, selector)
            
            for event_element in event_elements:
                event_text = event_element.text.strip()
                if event_text:
                    # Determine event type based on text
                    event_type = 'goal'  # Default assumption
                    if "'" in event_text:
                        event_type = 'goal'
                    
                    events.append({
                        'minute': event_text,
                        'type': event_type,
                        'team': team_side
                    })
            
        except Exception as e:
            self.logger.debug(f"Error extracting {team_side} events: {e}")
        
        return events
    
    def _track_live_matches(self):
        """Main tracking loop for live matches"""
        tracking_start = datetime.now()
        update_count = 0
        
        self.logger.info(f"Starting live tracking at {tracking_start.strftime('%H:%M:%S')}")
        
        try:
            while self.is_tracking:
                # Check if maximum duration reached
                elapsed_minutes = (datetime.now() - tracking_start).total_seconds() / 60
                if elapsed_minutes > MAX_LIVE_MATCH_DURATION:
                    self.logger.info(f"Maximum tracking duration reached ({MAX_LIVE_MATCH_DURATION} minutes)")
                    break
                
                update_count += 1
                current_time = datetime.now().strftime("%H:%M:%S")
                
                self.logger.info(f"\n📊 Live Update #{update_count} at {current_time}")
                self.logger.info("-" * 40)
                
                # Refresh page periodically to get latest data
                if update_count % 10 == 0:  # Every 10 updates
                    self.driver.refresh()
                    time.sleep(3)
                    self.close_popup()
                    self._switch_to_live_tab()
                
                # Get current match data
                current_update = {
                    'update_number': update_count,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'matches': []
                }
                
                # Update data for each match
                for i, match_container in enumerate(self.live_matches):
                    try:
                        match_data = self._extract_match_data(match_container, i)
                        
                        if match_data:
                            # Check for changes from previous state
                            if i in self.current_match_state:
                                changes = self._detect_match_changes(
                                    self.current_match_state[i], 
                                    match_data
                                )
                                
                                if changes:
                                    match_data['changes'] = changes
                                    self.logger.info(f"Match {i+1} changes: {changes}")
                            
                            # Update current state
                            self.current_match_state[i] = match_data
                            current_update['matches'].append(match_data)
                            
                            # Log current state
                            self._log_match_status(i, match_data)
                    
                    except Exception as e:
                        self.logger.warning(f"Error updating match {i+1}: {e}")
                
                # Save this update to history
                self.match_data_history.append(current_update)
                
                # Save data periodically
                if update_count % 5 == 0:  # Every 5 updates
                    self._save_live_data(update_count)
                
                # Wait for next update
                time.sleep(LIVE_SCRAPE_INTERVAL)
                
        except KeyboardInterrupt:
            self.logger.info("Live tracking interrupted by user")
        except Exception as e:
            self.logger.error(f"Error in tracking loop: {e}")
        finally:
            self.stop_tracking()
    
    def _detect_match_changes(self, previous_data, current_data):
        """Detect changes between match updates"""
        changes = []
        
        # Check score changes
        prev_score = f"{previous_data.get('home_score', '0')}-{previous_data.get('away_score', '0')}"
        curr_score = f"{current_data.get('home_score', '0')}-{current_data.get('away_score', '0')}"
        
        if prev_score != curr_score:
            changes.append(f"Score changed: {prev_score} → {curr_score}")
        
        # Check minute changes
        prev_minute = previous_data.get('current_minute', '0')
        curr_minute = current_data.get('current_minute', '0')
        
        if prev_minute != curr_minute:
            changes.append(f"Minute: {prev_minute} → {curr_minute}")
        
        # Check for new events
        prev_home_events = len(previous_data.get('home_events', []))
        curr_home_events = len(current_data.get('home_events', []))
        
        if curr_home_events > prev_home_events:
            changes.append(f"New home team event (total: {curr_home_events})")
        
        prev_away_events = len(previous_data.get('away_events', []))
        curr_away_events = len(current_data.get('away_events', []))
        
        if curr_away_events > prev_away_events:
            changes.append(f"New away team event (total: {curr_away_events})")
        
        return changes
    
    def _log_match_status(self, match_index, match_data):
        """Log current match status"""
        status = (
            f"Match {match_index + 1}: "
            f"{match_data.get('home_team', 'Unknown')} "
            f"{match_data.get('home_score', '0')}-{match_data.get('away_score', '0')} "
            f"{match_data.get('away_team', 'Unknown')} "
            f"[{match_data.get('current_minute', '0')}']"
        )
        
        # Add event count if available
        home_events = len(match_data.get('home_events', []))
        away_events = len(match_data.get('away_events', []))
        
        if home_events > 0 or away_events > 0:
            status += f" ⚽:{home_events}/{away_events}"
        
        self.logger.info(status)
    
    def _save_live_data(self, update_count):
        """Save live match data to file"""
        try:
            if not self.match_data_history:
                return
            
            # Create timestamp for filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"live_matches_update_{update_count}_{timestamp}"
            
            # Prepare data to save
            save_data = {
                'tracking_session': {
                    'start_time': self.match_start_time.strftime("%Y-%m-%d %H:%M:%S"),
                    'total_updates': update_count,
                    'matches_tracked': len(self.current_match_state)
                },
                'current_matches': list(self.current_match_state.values()),
                'update_history': self.match_data_history[-10:]  # Last 10 updates
            }
            
            # Save using parent class method
            saved_files = self.save_data(save_data, f"live_{filename}")
            
            for file_type, file_path in saved_files.items():
                self.logger.info(f"Live data saved as {file_type}: {file_path}")
            
            # Also save a quick summary
            self._save_live_summary(update_count)
            
        except Exception as e:
            self.logger.error(f"Error saving live data: {e}")
    
    def _save_live_summary(self, update_count):
        """Save a text summary of live matches"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            summary_file = f"data/matchday/live_summary_{timestamp}.txt"
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write("="*60 + "\n")
                f.write("LIVE MATCH TRACKING SUMMARY\n")
                f.write("="*60 + "\n\n")
                
                f.write(f"Tracking Session: {self.match_start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Updates: {update_count}\n")
                f.write(f"Matches Tracked: {len(self.current_match_state)}\n")
                f.write(f"Current Time: {datetime.now().strftime('%H:%M:%S')}\n\n")
                
                f.write("📊 CURRENT MATCH STATUS:\n")
                f.write("-"*40 + "\n")
                
                for match_index, match_data in self.current_match_state.items():
                    f.write(f"\nMatch {match_index + 1}:\n")
                    f.write(f"  {match_data.get('home_team')} {match_data.get('home_score')}-{match_data.get('away_score')} {match_data.get('away_team')}\n")
                    f.write(f"  Minute: {match_data.get('current_minute', '0')}\n")
                    
                    home_events = len(match_data.get('home_events', []))
                    away_events = len(match_data.get('away_events', []))
                    f.write(f"  Events: ⚽ {home_events} | {away_events}\n")
                    
                    if match_data.get('half_time_score', 'N/A') != 'N/A':
                        f.write(f"  HT Score: {match_data.get('half_time_score')}\n")
                
                f.write("\n" + "="*60 + "\n")
            
            self.logger.info(f"Live summary saved: {summary_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving live summary: {e}")
    
    def _filter_matches(self, match_filter):
        """Filter which matches to track"""
        filtered_matches = []
        
        for i, match_container in enumerate(self.live_matches):
            try:
                match_data = self._extract_match_data(match_container, i)
                
                if not match_data:
                    continue
                
                # Check if match matches filter criteria
                should_track = False
                
                # If filter is a list of indices
                if isinstance(match_filter, list) and all(isinstance(x, int) for x in match_filter):
                    if i in match_filter:
                        should_track = True
                
                # If filter is a list of team names
                elif isinstance(match_filter, list) and all(isinstance(x, str) for x in match_filter):
                    home_team = match_data.get('home_team', '').lower()
                    away_team = match_data.get('away_team', '').lower()
                    
                    for team_filter in match_filter:
                        if team_filter.lower() in home_team or team_filter.lower() in away_team:
                            should_track = True
                            break
                
                # If no filter or match passes filter
                if should_track or match_filter is None:
                    filtered_matches.append(match_container)
                    self.logger.info(f"Including match: {match_data.get('home_team')} vs {match_data.get('away_team')}")
            
            except Exception as e:
                self.logger.warning(f"Error filtering match {i}: {e}")
        
        self.live_matches = filtered_matches
        self.logger.info(f"Filtered to {len(self.live_matches)} matches")
    
    def stop_tracking(self):
        """Stop live match tracking"""
        self.is_tracking = False
        
        # Save final data
        if self.match_data_history:
            self._save_live_data(len(self.match_data_history))
            self._save_final_report()
        
        self.logger.info("Live match tracking stopped")
    
    def _save_final_report(self):
        """Save final tracking report"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = f"data/matchday/live_final_report_{timestamp}.txt"
            
            total_updates = len(self.match_data_history)
            tracking_duration = datetime.now() - self.match_start_time
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("="*70 + "\n")
                f.write("LIVE MATCH TRACKING - FINAL REPORT\n")
                f.write("="*70 + "\n\n")
                
                f.write(f"Tracking Start: {self.match_start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Tracking End: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Duration: {tracking_duration.total_seconds()/60:.1f} minutes\n")
                f.write(f"Total Updates: {total_updates}\n")
                f.write(f"Average Update Interval: {LIVE_SCRAPE_INTERVAL} seconds\n")
                f.write(f"Matches Tracked: {len(self.current_match_state)}\n\n")
                
                f.write("🎯 FINAL MATCH RESULTS:\n")
                f.write("-"*40 + "\n")
                
                for match_index, match_data in self.current_match_state.items():
                    f.write(f"\nMatch {match_index + 1}:\n")
                    f.write(f"  {match_data.get('home_team')} {match_data.get('home_score')}-{match_data.get('away_score')} {match_data.get('away_team')}\n")
                    
                    # Show all events
                    home_events = match_data.get('home_events', [])
                    away_events = match_data.get('away_events', [])
                    
                    if home_events or away_events:
                        f.write("  Events:\n")
                        for event in home_events:
                            f.write(f"    {match_data.get('home_team')} ⚽ {event.get('minute', '?')}\n")
                        for event in away_events:
                            f.write(f"    {match_data.get('away_team')} ⚽ {event.get('minute', '?')}\n")
                    
                    f.write(f"  Final Minute: {match_data.get('current_minute', '0')}\n")
                
                f.write("\n📈 TRACKING STATISTICS:\n")
                f.write("-"*40 + "\n")
                
                # Calculate some statistics
                total_events = 0
                for match_data in self.current_match_state.values():
                    total_events += len(match_data.get('home_events', []))
                    total_events += len(match_data.get('away_events', []))
                
                f.write(f"Total Goals/Events Tracked: {total_events}\n")
                f.write(f"Average events per match: {total_events/len(self.current_match_state):.1f}\n")
                f.write(f"Updates per minute: {total_updates/(tracking_duration.total_seconds()/60):.1f}\n")
                
                f.write("\n" + "="*70 + "\n")
                f.write("END OF TRACKING REPORT\n")
                f.write("="*70 + "\n")
            
            self.logger.info(f"Final report saved: {report_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving final report: {e}")

    def wait_for_live_and_start(self, timeout_minutes=30, tracking_duration_minutes=90):
        """
        Wait for matchday to go LIVE, then start tracking
        This is the main method that coordinates with timer
        """
        self.logger.info(f"Waiting for LIVE to start tracking...")
        self.logger.info(f"Will wait up to {timeout_minutes} minutes for LIVE")
        self.logger.info(f"Will track for {tracking_duration_minutes} minutes after LIVE")
        
        try:
            # Step 1: Navigate to page
            if not self.navigate_to_url(ODILEAGUE_URL):
                self.logger.error("Failed to navigate to page")
                return False
            
            self.close_popup()
            
            # Step 2: Check current timer state
            league_info = self.get_league_info()
            current_timer = league_info.get('timer')
            self.logger.info(f"Current timer: {current_timer}")
            
            # If already LIVE, start tracking immediately
            if self.is_timer_live(current_timer):
                self.logger.info("Matchday is already LIVE! Starting tracking...")
                return self.start_live_tracking()
            
            # Step 3: Monitor timer until LIVE
            self.logger.info("Monitoring timer until LIVE...")
            
            start_time = time.time()
            timeout_seconds = timeout_minutes * 60
            last_logged_timer = None
            switched_to_live_tab = False
            
            while time.time() - start_time < timeout_seconds:
                # Refresh page periodically
                if int(time.time() - start_time) % 30 == 0:  # Every 30 seconds
                    self.driver.refresh()
                    time.sleep(3)
                    self.close_popup()
                
                # Check timer
                current_timer = self.get_current_timer()
                
                if current_timer and current_timer != last_logged_timer:
                    self.logger.info(f"Timer: {current_timer}")
                    last_logged_timer = current_timer
                
                # NEW: Switch to LIVE tab when timer reaches 10 seconds
                if not switched_to_live_tab and self._should_switch_to_live_tab(current_timer):
                    self.logger.info(f"Timer at {current_timer} - Switching to LIVE tab...")
                    if self._switch_to_live_tab():
                        switched_to_live_tab = True
                        self.logger.info("Successfully switched to LIVE tab")
                    else:
                        self.logger.warning("Failed to switch to LIVE tab")
                
                # Check if LIVE
                if self.is_timer_live(current_timer):
                    elapsed = time.time() - start_time
                    self.logger.info(f"🎯 Timer went LIVE at {current_timer} after {elapsed:.1f} seconds")
                    
                    # Make sure we're on LIVE tab
                    if not switched_to_live_tab:
                        self._switch_to_live_tab()
                        switched_to_live_tab = True
                    
                    # Wait a moment for live matches to load
                    time.sleep(5)
                    
                    # Start live tracking
                    success = self.start_live_tracking()
                    
                    if success:
                        # Track for specified duration
                        tracking_seconds = tracking_duration_minutes * 60
                        self.logger.info(f"Starting {tracking_duration_minutes} minutes of live tracking...")
                        
                        tracking_start = time.time()
                        while time.time() - tracking_start < tracking_seconds and self.is_tracking:
                            time.sleep(LIVE_SCRAPE_INTERVAL)
                        
                        self.stop_tracking()
                        return True
                    else:
                        self.logger.error("Failed to start live tracking after LIVE detected")
                        return False
                
                # Wait before next check
                time.sleep(10)  # Check every 10 seconds
            
            # Timeout reached
            self.logger.warning(f"Timeout: Matchday didn't go LIVE within {timeout_minutes} minutes")
            return False
            
        except KeyboardInterrupt:
            self.logger.info("Interrupted by user")
            self.stop_tracking()
            return False
        except Exception as e:
            self.logger.error(f"Error in wait_for_live_and_start: {e}")
            return False
    
    def _should_switch_to_live_tab(self, timer_value):
        """
        Check if we should switch to LIVE tab based on timer
        Returns True when timer is at 10 seconds or less
        """
        if not timer_value:
            return False
        
        # Already LIVE or switched
        if self.is_timer_live(timer_value):
            return False
        
        try:
            # Parse timer string like "00:10", "01:45", etc.
            if ':' in timer_value:
                minutes, seconds = timer_value.split(':')
                total_seconds = int(minutes) * 60 + int(seconds)
                
                # Switch when 10 seconds or less remain
                if total_seconds <= 10:
                    self.logger.info(f"Timer at {total_seconds} seconds - preparing to switch to LIVE tab")
                    return True
        except (ValueError, AttributeError) as e:
            self.logger.debug(f"Could not parse timer value '{timer_value}': {e}")
        
        return False

    def is_timer_live(self, timer_value):
        """Check if timer indicates LIVE status"""
        if not timer_value:
            return False
        
        timer_lower = timer_value.lower().strip()
        
        # Check for LIVE indicators
        live_indicators = ['live', 'l.i.v.e', 'in play', 'playing']
        for indicator in live_indicators:
            if indicator in timer_lower:
                return True
        
        # Check if time is 00:00 or similar
        try:
            if ':' in timer_value:
                parts = timer_value.split(':')
                if len(parts) == 2:
                    minutes, seconds = parts
                    if int(minutes) == 0 and int(seconds) <= 5:
                        return True
        except:
            pass
        
        return False
    
    def get_current_timer(self):
        """Get current timer value from the page"""
        try:
            # Try multiple selectors for timer
            timer_selectors = [
                ".virtual-timer .ss.active",
                ".virtual-timer",
                ".timer",
                "[class*='timer']",
                "[class*='countdown']"
            ]
            
            for selector in timer_selectors:
                timer_element = self.safe_find_element(selector, timeout=2)
                if timer_element and timer_element.text.strip():
                    return timer_element.text.strip()
            
            return None
        except Exception as e:
            self.logger.debug(f"Error getting timer: {e}")
            return None