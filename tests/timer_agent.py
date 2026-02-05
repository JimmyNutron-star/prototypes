"""
Timer Agent - monitors all match timers and emits events
"""
import asyncio
from typing import Dict, List, Optional, Callable
from datetime import datetime
from playwright.async_api import Page

from models import AgentState, TimerEvent
from logger import AgentLogger
from config import config, selectors

class TimerAgent:
    """
    Monitors all match timers across all leagues
    Emits events when timer thresholds are crossed
    """
    
    def __init__(self, page: Page, event_callback: Callable):
        self.agent_name = "TimerAgent"
        self.logger = AgentLogger(self.agent_name)
        self.state = AgentState.INITIALIZING
        
        self.page = page
        self.event_callback = event_callback  # Callback to send events to orchestrator
        
        # Track timer states
        self.timer_states: Dict[str, Dict[int, str]] = {}  # {league: {index: timer_value}}
        self.previous_states: Dict[str, Dict[int, str]] = {}
        
        # Running flag
        self.running = False
        
        self.logger.info("TimerAgent initialized")
    
    async def start(self):
        """Start monitoring timers"""
        self.logger.state_change(self.state.value, AgentState.RUNNING.value)
        self.state = AgentState.RUNNING
        self.running = True
        
        self.logger.info("TimerAgent started - monitoring timers")
        
        # Start monitoring loop
        await self._monitor_loop()
    
    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                await self._check_timers()
                await asyncio.sleep(config.TIMER_CHECK_INTERVAL)
                
            except Exception as e:
                self.logger.error(f"Error in monitor loop: {e}")
                await asyncio.sleep(1)  # Brief pause on error
    
    async def _check_timers(self):
        """Check all visible timers and detect state changes"""
        try:
            # Get all timer elements
            timer_elements = await self.page.query_selector_all(selectors.TIMER_SLOT)
            
            if not timer_elements:
                return
            
            current_league = await self._get_current_league()
            if not current_league:
                return
            
            # Initialize league state if needed
            if current_league not in self.timer_states:
                self.timer_states[current_league] = {}
                self.previous_states[current_league] = {}
            
            # Check each timer
            for index, timer_elem in enumerate(timer_elements):
                try:
                    # Get timer text
                    timer_text = await timer_elem.inner_text()
                    timer_text = timer_text.strip()
                    
                    # Check if active
                    is_active = await timer_elem.evaluate("el => el.classList.contains('active')")
                    
                    # Store current state
                    previous_value = self.timer_states[current_league].get(index)
                    self.timer_states[current_league][index] = timer_text
                    
                    # Detect state changes and emit events
                    if previous_value != timer_text:
                        await self._handle_timer_change(
                            current_league, 
                            index, 
                            previous_value, 
                            timer_text,
                            is_active
                        )
                    
                except Exception as e:
                    self.logger.error(f"Error checking timer {index}: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Error in _check_timers: {e}")
    
    async def _handle_timer_change(
        self, 
        league: str, 
        index: int, 
        old_value: Optional[str], 
        new_value: str,
        is_active: bool
    ):
        """Handle timer state change and emit appropriate events"""
        
        # Parse timer value
        timer_seconds = self._parse_timer(new_value)
        
        # Determine event type
        event_type = None
        
        if timer_seconds is None:
            # Timer is "LIVE" or other non-numeric value
            if "LIVE" in new_value.upper() or new_value == "":
                event_type = "LIVE_START"
                self.logger.info(f"Match going LIVE", league=league, index=index)
        else:
            # Numeric timer
            if timer_seconds > config.MATCHDAY_START_THRESHOLD:
                # Timer > 1 minute - start matchday scraping
                if old_value is None or self._parse_timer(old_value) != timer_seconds:
                    event_type = "MATCHDAY_START"
                    self.logger.info(
                        f"Matchday scraping threshold reached", 
                        league=league, 
                        index=index, 
                        timer=new_value
                    )
            
            elif timer_seconds <= config.MATCHDAY_STOP_THRESHOLD and timer_seconds > 0:
                # Timer < 10 seconds - stop matchday, prepare for live
                old_seconds = self._parse_timer(old_value) if old_value else None
                if old_seconds is None or old_seconds > config.MATCHDAY_STOP_THRESHOLD:
                    event_type = "MATCHDAY_STOP"
                    self.logger.info(
                        f"Matchday stop threshold reached", 
                        league=league, 
                        index=index, 
                        timer=new_value
                    )
        
        # Emit event if detected
        if event_type:
            event = TimerEvent(
                league=league,
                timer_value=new_value,
                match_index=index,
                event_type=event_type
            )
            await self.event_callback(event)
            self.logger.agent_action(f"Event emitted: {event_type}", league=league, index=index)
    
    def _parse_timer(self, timer_str: Optional[str]) -> Optional[int]:
        """
        Parse timer string to seconds
        
        Args:
            timer_str: Timer string like "01:23" or "12:45"
            
        Returns:
            Total seconds or None if not parseable
        """
        if not timer_str:
            return None
        
        try:
            # Handle "MM:SS" format
            if ":" in timer_str:
                parts = timer_str.split(":")
                if len(parts) == 2:
                    minutes = int(parts[0])
                    seconds = int(parts[1])
                    return minutes * 60 + seconds
            
            # Try parsing as plain number
            return int(timer_str)
            
        except (ValueError, AttributeError):
            return None
    
    async def _get_current_league(self) -> Optional[str]:
        """Get currently active league"""
        try:
            active_league = await self.page.query_selector(selectors.LEAGUE_ACTIVE)
            if active_league:
                league_text = await active_league.inner_text()
                # Extract league name from text
                if "English" in league_text:
                    return "english"
                elif "Spanish" in league_text:
                    return "spanish"
                elif "Kenyan" in league_text:
                    return "kenyan"
                elif "Italian" in league_text:
                    return "italian"
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting current league: {e}")
            return None
    
    async def get_active_timer_index(self) -> Optional[int]:
        """Get the index of the currently active timer"""
        try:
            timer_elements = await self.page.query_selector_all(selectors.TIMER_SLOT)
            for index, timer_elem in enumerate(timer_elements):
                is_active = await timer_elem.evaluate("el => el.classList.contains('active')")
                if is_active:
                    return index
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting active timer: {e}")
            return None
    
    async def get_timer_value(self, index: int) -> Optional[str]:
        """Get timer value at specific index"""
        try:
            timer_elements = await self.page.query_selector_all(selectors.TIMER_SLOT)
            if 0 <= index < len(timer_elements):
                return await timer_elements[index].inner_text()
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting timer value: {e}")
            return None
    
    async def stop(self):
        """Stop timer monitoring"""
        self.logger.state_change(self.state.value, AgentState.STOPPING.value)
        self.state = AgentState.STOPPING
        self.running = False
        
        await asyncio.sleep(config.TIMER_CHECK_INTERVAL + 0.1)  # Wait for loop to finish
        
        self.state = AgentState.STOPPED
        self.logger.state_change(AgentState.STOPPING.value, self.state.value)
        self.logger.info("TimerAgent stopped")


async def main():
    """Independent runner for TimerAgent"""
    from playwright.async_api import async_playwright
    from data_agent import DataAgent
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Define a simple callback to see events
        async def mock_event_callback(event):
            print(f"\n[EVENT RECEIVED] {event.event_type} | League: {event.league} | Index: {event.match_index} | Value: {event.timer_value}")

        agent = TimerAgent(page, mock_event_callback)
        
        print(f"Navigating to {config.TARGET_URL}...")
        try:
            await page.goto(config.TARGET_URL, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(5) # Wait for page elements
            
            # Dismiss popup if it exists
            popup = await page.query_selector(selectors.POPUP_CLOSE)
            if popup:
                await popup.click()
            
            await agent.start()
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
