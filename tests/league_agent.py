"""
League Agent - manages a single league end-to-end
"""
import asyncio
from typing import Dict, Optional
from playwright.async_api import Page

from models import AgentState, TimerEvent
from logger import AgentLogger
from config import config, selectors
from data_agent import DataAgent
from matchday_agent import MatchdayAgent
from live_agent import LiveAgent
from results_standings_agents import ResultsAgent, StandingsAgent

class LeagueAgent:
    """
    Manages all scraping activities for a single league
    Spawns and coordinates specialized agents
    """
    
    def __init__(
        self,
        page: Page,
        data_agent: DataAgent,
        league_config: dict
    ):
        self.league_id = league_config['id']
        self.league_name = league_config['name']
        self.league_selector = league_config['selector']
        
        self.agent_name = f"LeagueAgent-{self.league_id}"
        self.logger = AgentLogger(self.agent_name)
        self.state = AgentState.INITIALIZING
        
        self.page = page
        self.data_agent = data_agent
        
        # Active agents
        self.matchday_agents: Dict[int, MatchdayAgent] = {}
        self.live_agents: Dict[int, LiveAgent] = {}
        
        # Match tracking
        self.completed_matches = 0
        self.match_teams: Dict[int, tuple] = {}  # {index: (home, away)}
        
        # Running flag
        self.running = False
        
        self.logger.info(f"LeagueAgent initialized", league=self.league_name)
    
    async def initialize(self):
        """Initialize league agent"""
        self.logger.state_change(self.state.value, AgentState.INITIALIZING.value)
        
        try:
            # Select this league
            await self._select_league()
            
            self.state = AgentState.RUNNING
            self.logger.state_change(AgentState.INITIALIZING.value, self.state.value)
            self.logger.info(f"LeagueAgent ready")
            
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
            self.state = AgentState.ERROR
    
    async def _select_league(self):
        """Select this league in the UI"""
        try:
            # Find league logo
            league_logos = await self.page.query_selector_all(selectors.LEAGUE_LOGO)
            
            # Click the appropriate league
            for logo in league_logos:
                text = await logo.inner_text()
                if self.league_name in text:
                    await logo.click()
                    await asyncio.sleep(1)
                    self.logger.agent_action(f"Selected league: {self.league_name}")
                    return
            
            self.logger.warning(f"Could not find league selector")
            
        except Exception as e:
            self.logger.error(f"Error selecting league: {e}")
    
    async def handle_timer_event(self, event: TimerEvent):
        """
        Handle timer event from Timer Agent
        
        Args:
            event: Timer event
        """
        if event.league != self.league_id:
            return  # Not for this league
        
        match_index = event.match_index
        
        if event.event_type == "MATCHDAY_START":
            await self._start_matchday_scraping(match_index, event.timer_value)
            
        elif event.event_type == "MATCHDAY_STOP":
            await self._stop_matchday_scraping(match_index)
            
        elif event.event_type == "LIVE_START":
            await self._start_live_tracking(match_index)
            
        elif event.event_type == "MATCH_END":
            await self._handle_match_end(match_index)
    
    async def _start_matchday_scraping(self, match_index: int, timer_value: str):
        """Start matchday scraping for a match"""
        if match_index in self.matchday_agents:
            self.logger.debug(f"Matchday agent already running", index=match_index)
            return
        
        try:
            # Generate match ID
            match_id = f"{self.league_id}_{match_index}_{timer_value.replace(':', '')}"
            
            # Create and start matchday agent
            matchday_agent = MatchdayAgent(
                page=self.page,
                data_agent=self.data_agent,
                league=self.league_id,
                match_index=match_index,
                match_id=match_id
            )
            
            self.matchday_agents[match_index] = matchday_agent
            
            # Start agent in background
            asyncio.create_task(matchday_agent.start())
            
            self.logger.info(
                f"Started matchday scraping",
                index=match_index,
                match_id=match_id
            )
            
        except Exception as e:
            self.logger.error(f"Error starting matchday agent: {e}", index=match_index)
    
    async def _stop_matchday_scraping(self, match_index: int):
        """Stop matchday scraping for a match"""
        if match_index not in self.matchday_agents:
            return
        
        try:
            matchday_agent = self.matchday_agents[match_index]
            
            # Get team info before stopping
            await self._cache_team_info(match_index, matchday_agent)
            
            # Stop agent
            await matchday_agent.stop()
            
            # Remove from active agents
            del self.matchday_agents[match_index]
            
            self.logger.info(f"Stopped matchday scraping", index=match_index)
            
        except Exception as e:
            self.logger.error(f"Error stopping matchday agent: {e}", index=match_index)
    
    async def _cache_team_info(self, match_index: int, matchday_agent: MatchdayAgent):
        """Cache team information for later use"""
        try:
            # Get the last scraped data
            match_data = await self.data_agent.get_match_data(matchday_agent.match_id)
            
            if match_data and 'matchday_data' in match_data:
                md = match_data['matchday_data']
                home_team = md.get('home_team', {}).get('name')
                away_team = md.get('away_team', {}).get('name')
                
                if home_team and away_team:
                    self.match_teams[match_index] = (home_team, away_team)
                    self.logger.debug(
                        f"Cached team info",
                        index=match_index,
                        teams=f"{home_team} vs {away_team}"
                    )
            
        except Exception as e:
            self.logger.error(f"Error caching team info: {e}")
    
    async def _start_live_tracking(self, match_index: int):
        """Start live tracking for a match"""
        if match_index in self.live_agents:
            self.logger.debug(f"Live agent already running", index=match_index)
            return
        
        try:
            # Get team info
            if match_index not in self.match_teams:
                self.logger.warning(f"No team info cached", index=match_index)
                return
            
            home_team, away_team = self.match_teams[match_index]
            
            # Get match ID from matchday agent
            match_id = None
            if match_index in self.matchday_agents:
                match_id = self.matchday_agents[match_index].match_id
            else:
                # Generate fallback match ID
                match_id = f"{self.league_id}_{match_index}_live"
            
            # Create and start live agent
            live_agent = LiveAgent(
                page=self.page,
                data_agent=self.data_agent,
                league=self.league_id,
                match_index=match_index,
                match_id=match_id,
                home_team=home_team,
                away_team=away_team
            )
            
            self.live_agents[match_index] = live_agent
            
            # Start agent in background
            asyncio.create_task(live_agent.start())
            
            self.logger.info(
                f"Started live tracking",
                index=match_index,
                match=f"{home_team} vs {away_team}"
            )
            
        except Exception as e:
            self.logger.error(f"Error starting live agent: {e}", index=match_index)
    
    async def _handle_match_end(self, match_index: int):
        """Handle match completion"""
        try:
            # Stop live agent if running
            if match_index in self.live_agents:
                live_agent = self.live_agents[match_index]
                await live_agent.stop()
                
                # Get team info
                home_team = live_agent.home_team
                away_team = live_agent.away_team
                match_id = live_agent.match_id
                
                # Remove from active agents
                del self.live_agents[match_index]
                
                # Validate result
                await self._validate_result(match_id, home_team, away_team)
                
                # Increment completed matches
                self.completed_matches += 1
                self.logger.info(
                    f"Match completed",
                    index=match_index,
                    total_completed=self.completed_matches
                )
                
                # Check if we should scrape standings
                if self.completed_matches % config.STANDINGS_MATCH_TRIGGER == 0:
                    await self._scrape_standings()
            
        except Exception as e:
            self.logger.error(f"Error handling match end: {e}", index=match_index)
    
    async def _validate_result(self, match_id: str, home_team: str, away_team: str):
        """Validate match result"""
        try:
            results_agent = ResultsAgent(
                page=self.page,
                data_agent=self.data_agent,
                league=self.league_id,
                match_id=match_id,
                home_team=home_team,
                away_team=away_team
            )
            
            await results_agent.validate_and_save()
            
        except Exception as e:
            self.logger.error(f"Error validating result: {e}")
    
    async def _scrape_standings(self):
        """Scrape league standings"""
        try:
            self.logger.info(
                f"Scraping standings",
                trigger=f"{self.completed_matches} matches completed"
            )
            
            standings_agent = StandingsAgent(
                page=self.page,
                data_agent=self.data_agent,
                league=self.league_id
            )
            
            await standings_agent.scrape_and_save()
            
        except Exception as e:
            self.logger.error(f"Error scraping standings: {e}")
    
    async def shutdown(self):
        """Shutdown league agent"""
        self.logger.state_change(self.state.value, AgentState.STOPPING.value)
        self.state = AgentState.STOPPING
        
        # Stop all matchday agents
        for agent in list(self.matchday_agents.values()):
            await agent.stop()
        
        # Stop all live agents
        for agent in list(self.live_agents.values()):
            await agent.stop()
        
        self.matchday_agents.clear()
        self.live_agents.clear()
        
        self.state = AgentState.STOPPED
        self.logger.state_change(AgentState.STOPPING.value, self.state.value)
        self.logger.info("LeagueAgent shutdown complete")
