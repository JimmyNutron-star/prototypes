"""
Matchday Agent - scrapes pre-match data with enhanced features
"""
import asyncio
import hashlib
from typing import Dict, List, Optional, Tuple, Callable
from datetime import datetime
from playwright.async_api import Page

from models import AgentState, MatchdayData, TeamInfo, OddsData
from logger import AgentLogger
from config import config, selectors
from data_agent import DataAgent


class MatchdayAgent:
    """
    Scrapes pre-match data for a specific match
    Active when timer > 1 minute, stops when timer < 10 seconds
    Enhanced with retry logic, validation, and monitoring
    """
    
    def __init__(
        self, 
        page: Page, 
        data_agent: DataAgent,
        league: str,
        match_index: int,
        match_id: str
    ):
        self.agent_name = f"MatchdayAgent-{league}-{match_index}"
        self.logger = AgentLogger(self.agent_name)
        self.state = AgentState.INITIALIZING
        
        self.page = page
        self.data_agent = data_agent
        self.league = league
        self.match_index = match_index
        self.match_id = match_id
        
        self.running = False
        self._scraping_in_progress = False
        self.scrape_interval = 5.0  # Scrape every 5 seconds
        
        # Caching and duplicate detection
        self._last_data_hash = None
        self._consecutive_duplicates = 0
        
        # Monitoring metrics
        self.metrics = {
            'scrapes_completed': 0,
            'scrapes_failed': 0,
            'scrapes_skipped': 0,
            'last_scrape_time': None,
            'data_points_collected': 0,
            'last_successful_scrape': None,
            'total_runtime': 0.0
        }
        
        # Market type mapping
        self.market_type_map = {
            'm3': '1X2',
            'm2': 'GG/NG',  # Both Teams to Score
            'm4': 'Over/Under',
            'm5': 'Handicap',
            'm6': 'Double Chance',
            'm7': 'Draw No Bet',
            'm8': 'Half Time/Full Time',
            'm9': 'Correct Score',
            'm10': 'Asian Handicap',
        }
        
        self.logger.info("MatchdayAgent initialized", 
                        match_id=match_id, 
                        match_index=match_index,
                        league=league)
    
    async def start(self):
        """Start scraping matchday data"""
        self.logger.state_change(self.state.value, AgentState.RUNNING.value)
        self.state = AgentState.RUNNING
        self.running = True
        start_time = datetime.now()
        
        self.logger.info("MatchdayAgent started", start_time=start_time)
        
        # Start scraping loop
        asyncio.create_task(self._scrape_loop())
    
    async def _scrape_loop(self):
        """Main scraping loop with timer checks and adaptive intervals"""
        loop_start = datetime.now()
        
        while self.running:
            iteration_start = datetime.now()
            
            try:
                # Check if we should be active based on timer
                should_scrape = await self._should_scrape()
                
                if not should_scrape:
                    self.metrics['scrapes_skipped'] += 1
                    self.logger.debug("Timer condition not met, skipping scrape")
                    await asyncio.sleep(1)
                    continue
                
                # Scrape match data with retry logic
                matchday_data = await self._scrape_with_retry(
                    self._scrape_matchday_data,
                    max_retries=2,
                    delay=1
                )
                
                if matchday_data:
                    # Check for duplicates and adjust interval
                    if self._is_duplicate_data(matchday_data):
                        self.logger.debug("Duplicate data detected, skipping save")
                        await asyncio.sleep(self.scrape_interval)
                        continue
                    
                    # Save to data agent
                    await self.data_agent.save_matchday_data(
                        self.match_id,
                        matchday_data.to_dict()
                    )
                    
                    self.metrics['scrapes_completed'] += 1
                    self.metrics['last_scrape_time'] = datetime.now()
                    self.metrics['last_successful_scrape'] = datetime.now()
                    self.metrics['data_points_collected'] += len(matchday_data.markets)
                    
                    self.logger.data_collected("matchday_data",
                                              markets=len(matchday_data.markets),
                                              interval=self.scrape_interval)
                
                # Calculate adaptive sleep based on scrape duration
                iteration_duration = (datetime.now() - iteration_start).total_seconds()
                sleep_time = max(0.1, self.scrape_interval - iteration_duration)
                await asyncio.sleep(sleep_time)
                
            except asyncio.CancelledError:
                self.logger.info("Scrape loop cancelled")
                break
            except Exception as e:
                self.metrics['scrapes_failed'] += 1
                self.logger.error(f"Error in scrape loop: {e}", exc_info=True)
                await asyncio.sleep(1)  # Brief pause on error
        
        # Update total runtime
        self.metrics['total_runtime'] = (datetime.now() - loop_start).total_seconds()
    
    async def _should_scrape(self) -> bool:
        """Check if agent should scrape based on timer conditions"""
        try:
            timer_value = await self._get_timer_value()
            if not timer_value or timer_value.lower() == 'unknown':
                return True  # Default to active if timer not found
            
            # Parse timer value (e.g., "45:23", "1:23:45", or "FT")
            if timer_value.upper() == 'FT':
                return False  # Match finished
            
            if ':' in timer_value:
                parts = timer_value.split(':')
                
                if len(parts) == 2:  # MM:SS
                    minutes, seconds = map(int, parts)
                    total_seconds = minutes * 60 + seconds
                elif len(parts) == 3:  # HH:MM:SS
                    hours, minutes, seconds = map(int, parts)
                    total_seconds = hours * 3600 + minutes * 60 + seconds
                else:
                    return True  # Unknown format, continue scraping
                
                # Active when > 10 seconds, stop when <= 10 seconds
                # Also handle pre-match (timer might be negative or large)
                if total_seconds <= 10:
                    self.logger.info("Timer <= 10 seconds, stopping scrape")
                    await self.stop()
                    return False
                
                # Adaptive interval based on time to match start
                if total_seconds > 300:  # More than 5 minutes
                    self.scrape_interval = 10.0
                elif total_seconds > 60:  # More than 1 minute
                    self.scrape_interval = 5.0
                else:  # Less than 1 minute
                    self.scrape_interval = 2.0
                
                return True
            
            return True  # Unknown format, continue scraping
            
        except (ValueError, IndexError) as e:
            self.logger.warning(f"Error parsing timer '{timer_value}': {e}")
            return True
        except Exception as e:
            self.logger.error(f"Error in _should_scrape: {e}")
            return True
    
    async def _scrape_with_retry(self, func: Callable, max_retries: int = 3, delay: float = 1.0):
        """Execute a scrape function with retry logic"""
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                self._scraping_in_progress = True
                result = await func()
                self._scraping_in_progress = False
                return result
                
            except Exception as e:
                last_exception = e
                self._scraping_in_progress = False
                
                if attempt == max_retries - 1:
                    break
                
                self.logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                await asyncio.sleep(delay * (attempt + 1))  # Exponential backoff
        
        if last_exception:
            self.logger.error(f"All {max_retries} attempts failed: {last_exception}")
        
        return None
    
    async def _scrape_matchday_data(self) -> Optional[MatchdayData]:
        """Scrape complete matchday data with validation"""
        try:
            # Get all game containers
            game_containers = await self.page.query_selector_all(selectors.GAME_CONTAINER)
            
            if self.match_index >= len(game_containers):
                self.logger.warning(
                    f"Match index {self.match_index} out of range",
                    available=len(game_containers)
                )
                return None
            
            game_elem = game_containers[self.match_index]
            
            # Extract team information
            teams = await self._extract_teams(game_elem)
            if not teams:
                self.logger.warning("Failed to extract team information")
                return None
            
            home_team, away_team = teams
            
            # Validate team names
            if not home_team.name.strip() or not away_team.name.strip():
                self.logger.warning("Empty team names detected")
                return None
            
            # Extract odds
            markets = await self._extract_odds(game_elem)
            
            # Get current timer value
            timer_value = await self._get_timer_value()
            
            # Create matchday data object
            matchday_data = MatchdayData(
                match_id=self.match_id,
                league=self.league,
                home_team=home_team,
                away_team=away_team,
                timer=timer_value or "unknown",
                markets=markets,
                scrape_timestamp=datetime.now()
            )
            
            self.logger.debug(
                f"Scraped matchday data",
                home=home_team.name,
                away=away_team.name,
                timer=timer_value,
                markets=len(markets)
            )
            
            return matchday_data
            
        except Exception as e:
            self.logger.error(f"Error scraping matchday data: {e}", exc_info=True)
            return None
    
    async def _extract_teams(self, game_elem) -> Optional[Tuple[TeamInfo, TeamInfo]]:
        """Extract team information from game element with validation"""
        try:
            # Get team names with retry
            team_name_elems = await self._scrape_with_retry(
                lambda: game_elem.query_selector_all(selectors.TEAM_NAMES),
                max_retries=2
            )
            
            if not team_name_elems or len(team_name_elems) < 2:
                self.logger.warning("Insufficient team name elements found")
                return None
            
            # Extract team names
            home_name = await team_name_elems[0].inner_text()
            away_name = await team_name_elems[1].inner_text()
            
            # Clean team names
            home_name = home_name.strip()
            away_name = away_name.strip()
            
            # Get team logos
            logo_elems = await game_elem.query_selector_all(selectors.TEAM_LOGOS)
            home_logo = None
            away_logo = None
            
            if len(logo_elems) >= 2:
                home_logo = await logo_elems[0].get_attribute('src')
                away_logo = await logo_elems[1].get_attribute('src')
            
            home_team = TeamInfo(
                name=home_name,
                logo_url=home_logo,
                extracted_at=datetime.now()
            )
            away_team = TeamInfo(
                name=away_name,
                logo_url=away_logo,
                extracted_at=datetime.now()
            )
            
            return (home_team, away_team)
            
        except Exception as e:
            self.logger.error(f"Error extracting teams: {e}")
            return None
    
    async def _extract_odds(self, game_elem) -> List[OddsData]:
        """Extract odds from game element with comprehensive market detection"""
        markets = []
        
        try:
            # Get odds container
            odds_container = await game_elem.query_selector(selectors.ODDS_CONTAINER)
            if not odds_container:
                self.logger.debug("No odds container found")
                return markets
            
            # Get all odds sections
            odds_sections = await odds_container.query_selector_all('div.o')
            
            for section in odds_sections:
                try:
                    # Determine market type
                    market_type = await self._determine_market_type(section)
                    
                    # Extract odds buttons
                    buttons = await section.query_selector_all('button')
                    options = {}
                    
                    for button in buttons:
                        try:
                            # Skip disabled buttons
                            disabled = await button.get_attribute('disabled')
                            if disabled:
                                continue
                            
                            # Get option label and value
                            label_elem = await button.query_selector('small.o-1')
                            value_elem = await button.query_selector('span.o-2')
                            
                            if label_elem and value_elem:
                                label = await label_elem.inner_text()
                                value_str = await value_elem.inner_text()
                                
                                # Clean and parse value
                                value_str = value_str.strip()
                                
                                try:
                                    value = float(value_str)
                                    options[label.strip()] = {
                                        'odds': value,
                                        'timestamp': datetime.now()
                                    }
                                except ValueError:
                                    # Try to handle fractional odds (e.g., "5/2")
                                    if '/' in value_str:
                                        try:
                                            num, den = map(float, value_str.split('/'))
                                            value = num / den + 1
                                            options[label.strip()] = {
                                                'odds': value,
                                                'timestamp': datetime.now()
                                            }
                                        except (ValueError, ZeroDivisionError):
                                            continue
                    
                        except Exception as e:
                            self.logger.debug(f"Error extracting button: {e}")
                            continue
                    
                    if options:
                        market_data = OddsData(
                            market_type=market_type,
                            options=options,
                            extracted_at=datetime.now()
                        )
                        markets.append(market_data)
                
                except Exception as e:
                    self.logger.debug(f"Error extracting odds section: {e}")
                    continue
            
            self.logger.debug(f"Extracted {len(markets)} markets")
            
        except Exception as e:
            self.logger.error(f"Error extracting odds: {e}")
        
        return markets
    
    async def _determine_market_type(self, section) -> str:
        """Determine market type from section element"""
        try:
            # Try class attribute first
            class_attr = await section.get_attribute('class')
            if class_attr:
                for pattern, market_name in self.market_type_map.items():
                    if pattern in class_attr:
                        return market_name
            
            # Try data attributes
            data_market = await section.get_attribute('data-market')
            if data_market:
                return data_market
            
            # Try to infer from structure
            header = await section.query_selector('div.market-header')
            if header:
                header_text = await header.inner_text()
                if header_text:
                    return header_text.strip()
            
            return "Unknown"
            
        except Exception:
            return "Unknown"
    
    def _parse_market_type(self, class_attr: str) -> str:
        """Parse market type from class attribute (legacy method)"""
        if not class_attr:
            return "Unknown"
        
        for pattern, market in self.market_type_map.items():
            if pattern in class_attr:
                return market
        
        return "Unknown"
    
    async def _get_timer_value(self) -> Optional[str]:
        """Get current timer value with fallback"""
        try:
            timer_elements = await self.page.query_selector_all(selectors.TIMER_SLOT)
            
            if self.match_index < len(timer_elements):
                timer_text = await timer_elements[self.match_index].inner_text()
                return timer_text.strip() if timer_text else None
            
            # Fallback: try alternative selector
            fallback_timers = await self.page.query_selector_all('.timer, .match-time, .time')
            if self.match_index < len(fallback_timers):
                timer_text = await fallback_timers[self.match_index].inner_text()
                return timer_text.strip() if timer_text else None
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Error getting timer value: {e}")
            return None
    
    def _is_duplicate_data(self, matchday_data: MatchdayData) -> bool:
        """Check if data is duplicate of previous scrape"""
        try:
            # Create hash of key data fields
            data_str = (
                f"{matchday_data.home_team.name}"
                f"{matchday_data.away_team.name}"
                f"{matchday_data.timer}"
            )
            
            for market in matchday_data.markets:
                data_str += f"{market.market_type}"
                for label, odds_data in market.options.items():
                    data_str += f"{label}{odds_data['odds']}"
            
            data_hash = hashlib.md5(data_str.encode()).hexdigest()
            
            if data_hash == self._last_data_hash:
                self._consecutive_duplicates += 1
                
                # Adaptive interval based on consecutive duplicates
                if self._consecutive_duplicates >= 3:
                    self.scrape_interval = min(30.0, self.scrape_interval * 1.5)
                    self.logger.debug(
                        f"Consecutive duplicates: {self._consecutive_duplicates}, "
                        f"interval increased to {self.scrape_interval}"
                    )
                
                return True
            else:
                self._last_data_hash = data_hash
                self._consecutive_duplicates = 0
                self.scrape_interval = 5.0  # Reset to default
                return False
                
        except Exception as e:
            self.logger.error(f"Error in duplicate detection: {e}")
            return False
    
    async def scrape_all_markets(self) -> List[OddsData]:
        """
        Scrape all available markets by clicking through filters
        This is a more comprehensive scrape
        """
        all_markets = []
        original_market = None
        
        try:
            # Get market filter buttons
            filter_buttons = await self.page.query_selector_all(selectors.MARKET_BUTTON)
            
            for i, button in enumerate(filter_buttons):
                try:
                    # Get market name
                    market_name = await button.inner_text()
                    market_name = market_name.strip()
                    
                    # Store first market as original
                    if i == 0:
                        original_market = market_name
                    
                    # Click to activate
                    await button.click()
                    await asyncio.sleep(0.8)  # Wait for odds to update
                    
                    # Scrape odds for this market
                    game_containers = await self.page.query_selector_all(selectors.GAME_CONTAINER)
                    if self.match_index < len(game_containers):
                        game_elem = game_containers[self.match_index]
                        markets = await self._extract_odds(game_elem)
                        
                        # Update market type with actual name
                        for market in markets:
                            market.market_type = market_name
                        
                        all_markets.extend(markets)
                    
                    self.logger.debug(f"Scraped market: {market_name}", count=len(markets))
                    
                except Exception as e:
                    self.logger.error(f"Error scraping market {i}: {e}")
                    continue
            
            # Return to original market if available
            if original_market and filter_buttons:
                try:
                    await filter_buttons[0].click()
                    await asyncio.sleep(0.5)
                except Exception:
                    pass
            
            self.logger.info(f"Scraped {len(all_markets)} markets from {len(filter_buttons)} filters")
            
        except Exception as e:
            self.logger.error(f"Error in scrape_all_markets: {e}", exc_info=True)
        
        return all_markets
    
    async def _wait_for_loop_completion(self, timeout: float = 10.0):
        """Wait for current scrape iteration to complete"""
        start_time = datetime.now()
        
        while self._scraping_in_progress:
            if (datetime.now() - start_time).total_seconds() > timeout:
                self.logger.warning("Timeout waiting for scrape to complete")
                break
            await asyncio.sleep(0.1)
    
    async def stop(self):
        """Stop matchday scraping with graceful shutdown"""
        if self.state == AgentState.STOPPED:
            return
        
        self.logger.state_change(self.state.value, AgentState.STOPPING.value)
        self.state = AgentState.STOPPING
        self.running = False
        
        try:
            # Wait for current scrape to complete
            await asyncio.wait_for(
                self._wait_for_loop_completion(),
                timeout=self.scrape_interval * 2
            )
        except asyncio.TimeoutError:
            self.logger.warning("Timeout waiting for loop to complete")
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
        
        self.state = AgentState.STOPPED
        self.logger.state_change(AgentState.STOPPING.value, self.state.value)
        
        # Log final metrics
        self.logger.info(
            "MatchdayAgent stopped",
            metrics=self.metrics,
            total_runtime=f"{self.metrics['total_runtime']:.2f}s"
        )
    
    def get_metrics(self) -> Dict:
        """Return current metrics"""
        metrics = self.metrics.copy()
        metrics.update({
            'state': self.state.value,
            'running': self.running,
            'scrape_interval': self.scrape_interval,
            'consecutive_duplicates': self._consecutive_duplicates,
            'match_id': self.match_id,
            'league': self.league
        })
        return metrics
    
    def get_status(self) -> Dict:
        """Return agent status summary"""
        return {
            'agent_name': self.agent_name,
            'state': self.state.value,
            'match_id': self.match_id,
            'league': self.league,
            'match_index': self.match_index,
            'running': self.running,
            'scrape_interval': self.scrape_interval,
            'last_scrape': self.metrics['last_scrape_time'].isoformat() 
                         if self.metrics['last_scrape_time'] else None,
            'scrapes_completed': self.metrics['scrapes_completed'],
            'scrapes_failed': self.metrics['scrapes_failed']
        }


async def main():
    """Independent runner for MatchdayAgent"""
    from playwright.async_api import async_playwright
    from data_agent import DataAgent
    import asyncio
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        data_agent = DataAgent(data_dir="test_data")
        await data_agent.initialize()
        
        # Test parameters
        agent = MatchdayAgent(
            page=page,
            data_agent=data_agent,
            league="english",
            match_index=0,
            match_id="test_match_001"
        )
        
        print(f"Navigating to {config.TARGET_URL}...")
        try:
            await page.goto(config.TARGET_URL, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(5)
            
            # Dismiss popup
            popup = await page.query_selector(selectors.POPUP_CLOSE)
            if popup:
                await popup.click()
            
            await agent.start()
            # Run for 60 seconds then stop
            await asyncio.sleep(60)
            await agent.stop()
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await data_agent.shutdown()
            await browser.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())