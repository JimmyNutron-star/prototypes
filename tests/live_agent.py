"""
Live Agent - tracks in-play match data
"""
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from playwright.async_api import Page

from models import AgentState, LiveMatchData, GoalEvent
from logger import AgentLogger
from config import config, selectors
from data_agent import DataAgent

class LiveAgent:
    """
    Tracks live match data
    Active when timer goes "LIVE", stops when match ends
    """
    
    def __init__(
        self,
        page: Page,
        data_agent: DataAgent,
        league: str,
        match_index: int,
        match_id: str,
        home_team: str,
        away_team: str
    ):
        self.agent_name = f"LiveAgent-{league}-{match_index}"
        self.logger = AgentLogger(self.agent_name)
        self.state = AgentState.INITIALIZING
        
        self.page = page
        self.data_agent = data_agent
        self.league = league
        self.match_index = match_index
        self.match_id = match_id
        self.home_team = home_team
        self.away_team = away_team
        
        self.running = False
        self.check_interval = config.LIVE_MATCH_CHECK_INTERVAL
        
        # Track previous state to detect changes
        self.previous_score = (0, 0)
        self.goals: List[GoalEvent] = []
        
        self.logger.info(
            "LiveAgent initialized",
            match_id=match_id,
            home=home_team,
            away=away_team
        )
    
    async def start(self):
        """Start tracking live match"""
        self.logger.state_change(self.state.value, AgentState.RUNNING.value)
        self.state = AgentState.RUNNING
        self.running = True
        
        self.logger.info("LiveAgent started - tracking live match")
        
        # Navigate to LIVE tab
        await self._navigate_to_live_tab()
        
        # Start tracking loop
        await self._tracking_loop()
    
    async def _tracking_loop(self):
        """Main tracking loop"""
        while self.running:
            try:
                # Scrape live data
                live_data = await self._scrape_live_data()
                
                if live_data:
                    # Save to data agent
                    await self.data_agent.save_live_data(
                        self.match_id,
                        live_data.to_dict()
                    )
                    
                    # Check if match ended
                    if live_data.match_phase == "FT":
                        self.logger.info("Match finished - stopping live tracking")
                        await self.stop()
                        break
                
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                self.logger.error(f"Error in tracking loop: {e}")
                await asyncio.sleep(1)
    
    async def _navigate_to_live_tab(self):
        """Navigate to LIVE tab"""
        try:
            live_tab = await self.page.query_selector(selectors.TAB_LIVE)
            if live_tab:
                await live_tab.click()
                await asyncio.sleep(1)  # Wait for content to load
                self.logger.agent_action("Navigated to LIVE tab")
            
        except Exception as e:
            self.logger.error(f"Error navigating to LIVE tab: {e}")
    
    async def _scrape_live_data(self) -> Optional[LiveMatchData]:
        """Scrape live match data"""
        try:
            # Find our match in the live container
            match_elem = await self._find_match_element()
            if not match_elem:
                self.logger.warning("Match element not found in live view")
                return None
            
            # Extract scores
            scores = await self._extract_scores(match_elem)
            if not scores:
                return None
            
            home_score, away_score = scores
            
            # Detect new goals
            if scores != self.previous_score:
                await self._detect_goals(match_elem, home_score, away_score)
                self.previous_score = scores
            
            # Extract halftime score
            halftime_score = await self._extract_halftime_score(match_elem)
            
            # Determine match phase
            match_phase = await self._determine_match_phase(match_elem)
            
            # Create live data object
            live_data = LiveMatchData(
                match_id=self.match_id,
                league=self.league,
                home_team=self.home_team,
                away_team=self.away_team,
                home_score=home_score,
                away_score=away_score,
                halftime_score=halftime_score,
                goals=self.goals.copy(),
                match_phase=match_phase
            )
            
            self.logger.debug(
                f"Live data scraped",
                score=f"{home_score}-{away_score}",
                phase=match_phase
            )
            
            return live_data
            
        except Exception as e:
            self.logger.error(f"Error scraping live data: {e}")
            return None
    
    async def _find_match_element(self):
        """Find the match element in live view"""
        try:
            # Get all live match elements
            match_elements = await self.page.query_selector_all(selectors.LIVE_MATCH)
            
            # Find our match by team names
            for match_elem in match_elements:
                home_elem = await match_elem.query_selector(selectors.LIVE_TEAM_HOME)
                away_elem = await match_elem.query_selector(selectors.LIVE_TEAM_AWAY)
                
                if home_elem and away_elem:
                    home_text = await home_elem.inner_text()
                    away_text = await away_elem.inner_text()
                    
                    if (home_text.strip() == self.home_team and 
                        away_text.strip() == self.away_team):
                        return match_elem
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding match element: {e}")
            return None
    
    async def _extract_scores(self, match_elem) -> Optional[tuple]:
        """Extract current scores"""
        try:
            score_elems = await match_elem.query_selector_all(selectors.LIVE_SCORE)
            
            if len(score_elems) >= 2:
                home_score_text = await score_elems[0].inner_text()
                away_score_text = await score_elems[1].inner_text()
                
                home_score = int(home_score_text.strip())
                away_score = int(away_score_text.strip())
                
                return (home_score, away_score)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting scores: {e}")
            return None
    
    async def _extract_halftime_score(self, match_elem) -> Optional[str]:
        """Extract halftime score"""
        try:
            ht_elem = await match_elem.query_selector(selectors.LIVE_HALFTIME_SCORE)
            if ht_elem:
                ht_text = await ht_elem.inner_text()
                return ht_text.strip()
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting halftime score: {e}")
            return None
    
    async def _detect_goals(self, match_elem, home_score: int, away_score: int):
        """Detect and record new goals"""
        try:
            # Get goal time elements
            goal_time_elems = await match_elem.query_selector_all(selectors.LIVE_GOAL_TIMES)
            
            # Parse goal times
            home_goals = []
            away_goals = []
            
            # The structure has two sections: home goals and away goals
            # We need to determine which goals belong to which team
            
            # Get the parent containers
            hi_containers = await match_elem.query_selector_all('div.gm-h div.hi')
            
            if len(hi_containers) >= 2:
                # First container = home goals, second = away goals
                home_container = hi_containers[0]
                away_container = hi_containers[1]
                
                # Extract home goal times
                home_goal_elems = await home_container.query_selector_all('span')
                for elem in home_goal_elems:
                    minute = await elem.inner_text()
                    home_goals.append(minute.strip())
                
                # Extract away goal times
                away_goal_elems = await away_container.query_selector_all('span')
                for elem in away_goal_elems:
                    minute = await elem.inner_text()
                    away_goals.append(minute.strip())
            
            # Create goal events
            new_goals = []
            
            for minute in home_goals:
                goal = GoalEvent(team="home", minute=minute)
                if not self._goal_exists(goal):
                    new_goals.append(goal)
                    self.logger.info(f"⚽ GOAL! {self.home_team} at {minute}'")
            
            for minute in away_goals:
                goal = GoalEvent(team="away", minute=minute)
                if not self._goal_exists(goal):
                    new_goals.append(goal)
                    self.logger.info(f"⚽ GOAL! {self.away_team} at {minute}'")
            
            # Add new goals to list
            self.goals.extend(new_goals)
            
        except Exception as e:
            self.logger.error(f"Error detecting goals: {e}")
    
    def _goal_exists(self, goal: GoalEvent) -> bool:
        """Check if goal already recorded"""
        for existing_goal in self.goals:
            if existing_goal.team == goal.team and existing_goal.minute == goal.minute:
                return True
        return False
    
    async def _determine_match_phase(self, match_elem) -> str:
        """Determine current match phase"""
        try:
            # Check halftime indicator
            ht_elem = await match_elem.query_selector(selectors.LIVE_HALFTIME_SCORE)
            if ht_elem:
                ht_text = await ht_elem.inner_text()
                if "HT" in ht_text:
                    return "HT"
            
            # Check if match is finished
            # This would be indicated by no active timer or specific marker
            # For now, we'll check if there's a final score indicator
            
            # Default to live
            return "live"
            
        except Exception as e:
            self.logger.error(f"Error determining match phase: {e}")
            return "live"
    
    async def stop(self):
        """Stop live tracking"""
        self.logger.state_change(self.state.value, AgentState.STOPPING.value)
        self.state = AgentState.STOPPING
        self.running = False
        
        await asyncio.sleep(self.check_interval + 0.1)
        
        self.state = AgentState.STOPPED
        self.logger.state_change(AgentState.STOPPING.value, self.state.value)
        self.logger.info("LiveAgent stopped")


async def main():
    """Independent runner for LiveAgent"""
    from playwright.async_api import async_playwright
    from data_agent import DataAgent
    import asyncio
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        data_agent = DataAgent(data_dir="test_data")
        await data_agent.initialize()
        
        # Note: LiveAgent needs team names to find the match
        agent = LiveAgent(
            page=page,
            data_agent=data_agent,
            league="english",
            match_index=0,
            match_id="test_live_001",
            home_team="Manchester Reds",
            away_team="London Blues"
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
            # Run for 120 seconds then stop
            await asyncio.sleep(120)
            await agent.stop()
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await data_agent.shutdown()
            await browser.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
