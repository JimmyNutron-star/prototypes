"""
Lightweight timer monitor that runs continuously
"""

import time
from datetime import datetime
from scrapers.base_scraper import BaseScraper
from config import TIMER_CHECK_INTERVAL, LIVE_THRESHOLD_SECONDS, TIMER_CHANGE_THRESHOLD
from utils.helpers import is_timer_live, calculate_time_until_live

class TimerMonitor(BaseScraper):
    def __init__(self):
        super().__init__("timer_monitor")
        self.last_timer_value = None
        self.timer_history = []
        self.is_monitoring = False
    
    def monitor_timer(self, check_interval=TIMER_CHECK_INTERVAL, max_checks=None):
        """
        Monitor timer continuously
        Returns when timer goes LIVE or max_checks reached
        """
        self.is_monitoring = True
        check_count = 0
        
        self.logger.info(f"Starting timer monitoring (interval: {check_interval}s)")
        
        try:
            while self.is_monitoring:
                # Get current timer
                current_timer = self.get_current_timer()
                
                if current_timer:
                    # Check if timer changed significantly
                    timer_changed = self._check_timer_change(current_timer)
                    
                    if timer_changed:
                        seconds_until_live = calculate_time_until_live(current_timer)
                        
                        log_msg = f"Timer: {current_timer}"
                        if seconds_until_live is not None:
                            log_msg += f" (Live in {seconds_until_live}s)"
                        
                        self.logger.info(log_msg)
                        
                        # Record in history
                        self.timer_history.append({
                            'timestamp': datetime.now().strftime("%H:%M:%S"),
                            'timer': current_timer,
                            'seconds_until_live': seconds_until_live
                        })
                    
                    # Check if LIVE
                    if is_timer_live(current_timer, LIVE_THRESHOLD_SECONDS):
                        self.logger.info(f"🎯 MATCHDAY WENT LIVE at {current_timer}!")
                        self.is_monitoring = False
                        return True, current_timer
                
                # Increment check count
                check_count += 1
                
                # Check if max checks reached
                if max_checks and check_count >= max_checks:
                    self.logger.info(f"Max checks reached ({max_checks})")
                    self.is_monitoring = False
                    return False, current_timer
                
                # Wait for next check
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            self.logger.info("Monitoring interrupted by user")
            self.is_monitoring = False
            return False, None
        except Exception as e:
            self.logger.error(f"Monitoring error: {e}")
            self.is_monitoring = False
            return False, None
        
        return False, None
    
    def get_current_timer(self):
        """Get current timer value"""
        try:
            timer_element = self.safe_find_element(".virtual-timer .ss.active", timeout=5)
            if timer_element:
                return timer_element.text.strip()
            return None
        except:
            return None
    
    def _check_timer_change(self, current_timer):
        """Check if timer changed significantly from last value"""
        if self.last_timer_value is None:
            self.last_timer_value = current_timer
            return True
        
        # Only log if timer changed by more than threshold
        if current_timer != self.last_timer_value:
            self.last_timer_value = current_timer
            return True
        
        return False
    
    def stop_monitoring(self):
        """Stop the monitoring"""
        self.is_monitoring = False
        self.logger.info("Monitoring stopped")
    
    def get_timer_summary(self):
        """Get summary of timer monitoring"""
        if not self.timer_history:
            return "No timer data collected"
        
        summary = f"\n⏰ Timer Monitoring Summary\n"
        summary += f"{'='*40}\n"
        summary += f"Total checks: {len(self.timer_history)}\n"
        
        if self.timer_history:
            first_timer = self.timer_history[0]['timer']
            last_timer = self.timer_history[-1]['timer']
            summary += f"Timer progression: {first_timer} → {last_timer}\n"
        
        # Count unique timer values
        unique_timers = set(entry['timer'] for entry in self.timer_history)
        summary += f"Unique timer values: {len(unique_timers)}\n"
        
        return summary