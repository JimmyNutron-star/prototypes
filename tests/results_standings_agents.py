"""
Results Agent - validates and archives final match results
"""
import asyncio
from typing import Optional
from playwright.async_api import Page

from models import AgentState, ResultData
from logger import AgentLogger
from config import selectors
from data_agent import DataAgent

class ResultsAgent:
    """
    Scrapes and validates final match results
    Compares live data with results tab data
    """
    
    def __init__(
        self,
        page: Page,
        data_agent: DataAgent,
        league: str,
        match_id: str,
        home_team: str,
        away_team: str
    ):
        self.agent_name = f"ResultsAgent-{league}"
        self.logger = AgentLogger(self.agent_name)
        self.state = AgentState.INITIALIZING
        
        self.page = page
        self.data_agent = data_agent
        self.league = league
        self.match_id = match_id
        self.home_team = home_team
        self.away_team = away_team
        
        self.logger.info("ResultsAgent initialized", match_id=match_id)
    
    async def validate_and_save(self) -> bool:
        """
        Validate match result and save
        
        Returns:
            True if validation successful
        """
        self.logger.state_change(self.state.value, AgentState.RUNNING.value)
        self.state = AgentState.RUNNING
        
        try:
            # Navigate to Results tab
            await self._navigate_to_results()
            
            # Find and scrape result
            result_data = await self._scrape_result()
            
            if not result_data:
                self.logger.error("Failed to scrape result data")
                return False
            
            # Get live data for comparison
            match_data = await self.data_agent.get_match_data(self.match_id)
            
            if match_data and 'live_data' in match_data:
                # Validate
                is_valid = self._validate_result(result_data, match_data['live_data'])
                
                if is_valid:
                    self.logger.info("✓ Result validated successfully")
                    result_data.validated = True
                else:
                    self.logger.warning("⚠ Result validation mismatch!")
                    result_data.validated = False
            else:
                self.logger.warning("No live data to validate against")
                result_data.validated = False
            
            # Save result
            await self.data_agent.save_result(self.match_id, result_data.to_dict())
            
            if result_data.validated:
                await self.data_agent.mark_validated(self.match_id)
            
            self.state = AgentState.STOPPED
            return True
            
        except Exception as e:
            self.logger.error(f"Error in validate_and_save: {e}")
            self.state = AgentState.ERROR
            return False
    
    async def _navigate_to_results(self):
        """Navigate to Results tab"""
        try:
            results_tab = await self.page.query_selector(selectors.TAB_RESULTS)
            if results_tab:
                await results_tab.click()
                await asyncio.sleep(1)
                self.logger.agent_action("Navigated to Results tab")
            
        except Exception as e:
            self.logger.error(f"Error navigating to Results: {e}")
    
    async def _scrape_result(self) -> Optional[ResultData]:
        """Scrape result from Results tab"""
        try:
            # Get all result containers
            result_containers = await self.page.query_selector_all(selectors.RESULTS_CONTAINER)
            
            # Search for our match
            for container in result_containers:
                # Get match title/info
                title_elem = await container.query_selector(selectors.RESULTS_TITLE)
                time_elem = await container.query_selector(selectors.RESULTS_TIME)
                
                if title_elem and time_elem:
                    title_text = await title_elem.inner_text()
                    time_text = await time_elem.inner_text()
                    
                    # Extract week info
                    week = self._extract_week(title_text)
                    
                    # Get all matches in this result block
                    match_elems = await container.query_selector_all(selectors.RESULTS_MATCH)
                    
                    for match_elem in match_elems:
                        # Extract teams and scores
                        team_elems = await match_elem.query_selector_all(selectors.RESULTS_TEAM)
                        score_elems = await match_elem.query_selector_all(selectors.RESULTS_SCORE)
                        
                        if len(team_elems) >= 2 and len(score_elems) >= 2:
                            home = await team_elems[0].inner_text()
                            away = await team_elems[1].inner_text()
                            home_score_text = await score_elems[0].inner_text()
                            away_score_text = await score_elems[1].inner_text()
                            
                            # Check if this is our match
                            if (home.strip() == self.home_team and 
                                away.strip() == self.away_team):
                                
                                # Found our match!
                                result_data = ResultData(
                                    match_id=self.match_id,
                                    league=self.league,
                                    week=week,
                                    match_time=time_text.strip(),
                                    home_team=home.strip(),
                                    away_team=away.strip(),
                                    home_score=int(home_score_text.strip()),
                                    away_score=int(away_score_text.strip())
                                )
                                
                                self.logger.data_collected("result")
                                return result_data
            
            self.logger.warning("Match not found in results")
            return None
            
        except Exception as e:
            self.logger.error(f"Error scraping result: {e}")
            return None
    
    def _extract_week(self, title_text: str) -> str:
        """Extract week number from title"""
        try:
            # Format: "English League WEEK 16 - #2026012209"
            if "WEEK" in title_text:
                parts = title_text.split("WEEK")
                if len(parts) > 1:
                    week_part = parts[1].split("-")[0].strip()
                    return f"WEEK {week_part}"
            return "Unknown"
            
        except Exception:
            return "Unknown"
    
    def _validate_result(self, result_data: ResultData, live_data: dict) -> bool:
        """
        Validate result against live data
        
        Returns:
            True if scores match
        """
        try:
            live_home_score = live_data.get('home_score')
            live_away_score = live_data.get('away_score')
            
            if (result_data.home_score == live_home_score and 
                result_data.away_score == live_away_score):
                return True
            else:
                self.logger.warning(
                    f"Score mismatch: Live={live_home_score}-{live_away_score}, "
                    f"Result={result_data.home_score}-{result_data.away_score}"
                )
                return False
                
        except Exception as e:
            self.logger.error(f"Error validating result: {e}")
            return False


class StandingsAgent:
    """
    Scrapes league standings
    Triggered every 5 completed matches
    """
    
    def __init__(
        self,
        page: Page,
        data_agent: DataAgent,
        league: str
    ):
        self.agent_name = f"StandingsAgent-{league}"
        self.logger = AgentLogger(self.agent_name)
        self.state = AgentState.INITIALIZING
        
        self.page = page
        self.data_agent = data_agent
        self.league = league
        
        self.logger.info("StandingsAgent initialized")
    
    async def scrape_and_save(self) -> bool:
        """
        Scrape standings and save
        
        Returns:
            True if successful
        """
        self.logger.state_change(self.state.value, AgentState.RUNNING.value)
        self.state = AgentState.RUNNING
        
        try:
            # Navigate to Standings tab
            await self._navigate_to_standings()
            
            # Scrape standings
            standings_data = await self._scrape_standings()
            
            if standings_data:
                # Save to data agent
                await self.data_agent.save_standings(self.league, standings_data)
                self.logger.info("Standings scraped and saved")
                
                self.state = AgentState.STOPPED
                return True
            else:
                self.logger.error("Failed to scrape standings")
                self.state = AgentState.ERROR
                return False
                
        except Exception as e:
            self.logger.error(f"Error in scrape_and_save: {e}")
            self.state = AgentState.ERROR
            return False
    
    async def _navigate_to_standings(self):
        """Navigate to Standings tab"""
        try:
            standings_tab = await self.page.query_selector(selectors.TAB_STANDINGS)
            if standings_tab:
                await standings_tab.click()
                await asyncio.sleep(1)
                self.logger.agent_action("Navigated to Standings tab")
            
        except Exception as e:
            self.logger.error(f"Error navigating to Standings: {e}")
    
    async def _scrape_standings(self) -> Optional[dict]:
        """Scrape standings table"""
        try:
            # Get standings container
            standings_container = await self.page.query_selector(selectors.STANDINGS_CONTAINER)
            if not standings_container:
                return None
            
            # Get title (contains season info)
            title_elem = await standings_container.query_selector(selectors.STANDINGS_TITLE)
            season = "Unknown"
            if title_elem:
                title_text = await title_elem.inner_text()
                season = title_text.strip()
            
            # Get table rows
            rows = await standings_container.query_selector_all(selectors.STANDINGS_ROW)
            
            entries = []
            for row in rows:
                try:
                    cells = await row.query_selector_all('td')
                    if len(cells) >= 4:
                        position_text = await cells[0].inner_text()
                        team_text = await cells[1].inner_text()
                        points_text = await cells[2].inner_text()
                        
                        # Extract form
                        form_elem = cells[3]
                        form_divs = await form_elem.query_selector_all('div')
                        form = []
                        for div in form_divs:
                            form_letter = await div.inner_text()
                            form.append(form_letter.strip())
                        
                        entry = {
                            'position': int(position_text.strip()),
                            'team': team_text.strip(),
                            'points': int(points_text.strip()),
                            'form': form
                        }
                        entries.append(entry)
                
                except Exception as e:
                    self.logger.error(f"Error parsing row: {e}")
                    continue
            
            standings_data = {
                'league': self.league,
                'season': season,
                'entries': entries
            }
            
            self.logger.data_collected("standings", len(entries))
            return standings_data
            
        except Exception as e:
            self.logger.error(f"Error scraping standings: {e}")
            return None
