"""
Orchestrator Agent - master coordinator for the entire scraping system
"""
import asyncio
from typing import Dict, List
from playwright.async_api import async_playwright, Page, Browser

from models import AgentState, TimerEvent
from logger import AgentLogger
from config import config, selectors
from data_agent import DataAgent
from timer_agent import TimerAgent
from league_agent import LeagueAgent

class OrchestratorAgent:
    """
    Master coordinator for the agentic scraping system
    Manages browser, spawns league agents, coordinates timer events
    """
    
    def __init__(self):
        self.agent_name = "Orchestrator"
        self.logger = AgentLogger(self.agent_name, level=config.LOG_LEVEL)
        self.state = AgentState.INITIALIZING
        
        # Browser resources
        self.playwright = None
        self.browser: Browser = None
        self.page: Page = None
        
        # Agents
        self.data_agent: DataAgent = None
        self.timer_agent: TimerAgent = None
        self.league_agents: Dict[str, LeagueAgent] = {}
        
        # Control
        self.running = False
        
        self.logger.info("=" * 60)
        self.logger.info("OdiLeague Agentic Scraper System")
        self.logger.info("=" * 60)
    
    async def initialize(self):
        """Initialize the entire system"""
        self.logger.state_change(self.state.value, AgentState.INITIALIZING.value)
        self.state = AgentState.INITIALIZING
        
        try:
            # Initialize browser
            await self._init_browser()
            
            # Initialize data agent
            await self._init_data_agent()
            
            # Navigate to target
            await self._navigate_to_target()
            
            # Handle popup
            await self._handle_popup()
            
            # Initialize timer agent
            await self._init_timer_agent()
            
            # Initialize league agents
            await self._init_league_agents()
            
            self.state = AgentState.RUNNING
            self.logger.state_change(AgentState.INITIALIZING.value, self.state.value)
            self.logger.info("✓ System initialization complete")
            
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
            self.state = AgentState.ERROR
            raise
    
    async def _init_browser(self):
        """Initialize browser"""
        self.logger.info("Initializing browser...")
        
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=config.HEADLESS,
            args=['--start-maximized']
        )
        
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        
        self.page = await context.new_page()
        self.page.set_default_timeout(config.BROWSER_TIMEOUT)
        
        self.logger.info("✓ Browser initialized")
    
    async def _init_data_agent(self):
        """Initialize data agent"""
        self.logger.info("Initializing data agent...")
        
        self.data_agent = DataAgent(
            data_dir=config.DATA_DIR,
            backup_dir=config.BACKUP_DIR
        )
        
        await self.data_agent.initialize()
        
        self.logger.info("✓ Data agent initialized")
    
    async def _navigate_to_target(self):
        """Navigate to target URL"""
        self.logger.info(f"Navigating to {config.TARGET_URL}...")
        
        await self.page.goto(config.TARGET_URL, wait_until='networkidle')
        await asyncio.sleep(2)
        
        self.logger.info("✓ Navigation complete")
    
    async def _handle_popup(self):
        """Handle initial popup"""
        self.logger.info("Checking for popup...")
        
        try:
            popup_close = await self.page.query_selector(selectors.POPUP_CLOSE)
            if popup_close:
                await popup_close.click()
                await asyncio.sleep(1)
                self.logger.info("✓ Popup dismissed")
            else:
                self.logger.info("No popup found")
                
        except Exception as e:
            self.logger.warning(f"Popup handling: {e}")
    
    async def _init_timer_agent(self):
        """Initialize timer agent"""
        self.logger.info("Initializing timer agent...")
        
        self.timer_agent = TimerAgent(
            page=self.page,
            event_callback=self._handle_timer_event
        )
        
        self.logger.info("✓ Timer agent initialized")
    
    async def _init_league_agents(self):
        """Initialize all league agents"""
        self.logger.info(f"Initializing {len(config.LEAGUES)} league agents...")
        
        for league_config in config.LEAGUES:
            league_id = league_config['id']
            
            league_agent = LeagueAgent(
                page=self.page,
                data_agent=self.data_agent,
                league_config=league_config
            )
            
            await league_agent.initialize()
            
            self.league_agents[league_id] = league_agent
        
        self.logger.info(f"✓ {len(self.league_agents)} league agents initialized")
    
    async def _handle_timer_event(self, event: TimerEvent):
        """
        Handle timer event from Timer Agent
        Route to appropriate league agent
        """
        league_id = event.league
        
        if league_id in self.league_agents:
            await self.league_agents[league_id].handle_timer_event(event)
        else:
            self.logger.warning(f"Unknown league: {league_id}")
    
    async def start(self):
        """Start the scraping system"""
        self.logger.info("=" * 60)
        self.logger.info("STARTING SCRAPING SYSTEM")
        self.logger.info("=" * 60)
        
        self.running = True
        
        # Start timer agent
        timer_task = asyncio.create_task(self.timer_agent.start())
        
        self.logger.info("✓ System running - monitoring all leagues")
        self.logger.info("Press Ctrl+C to stop")
        
        try:
            # Keep running until interrupted
            while self.running:
                await asyncio.sleep(1)
                
                # Periodic stats
                if int(asyncio.get_event_loop().time()) % 30 == 0:
                    await self._log_stats()
                    
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
        finally:
            await self.shutdown()
    
    async def _log_stats(self):
        """Log system statistics"""
        try:
            stats = await self.data_agent.get_stats()
            
            self.logger.info(
                "System stats",
                matches=stats['total_matches'],
                results=stats['total_results'],
                validated=stats['validated_matches']
            )
            
        except Exception as e:
            self.logger.error(f"Error logging stats: {e}")
    
    async def shutdown(self):
        """Shutdown the entire system"""
        self.logger.info("=" * 60)
        self.logger.info("SHUTTING DOWN SYSTEM")
        self.logger.info("=" * 60)
        
        self.logger.state_change(self.state.value, AgentState.STOPPING.value)
        self.state = AgentState.STOPPING
        self.running = False
        
        # Stop timer agent
        if self.timer_agent:
            self.logger.info("Stopping timer agent...")
            await self.timer_agent.stop()
        
        # Stop all league agents
        self.logger.info(f"Stopping {len(self.league_agents)} league agents...")
        for league_agent in self.league_agents.values():
            await league_agent.shutdown()
        
        # Shutdown data agent
        if self.data_agent:
            self.logger.info("Shutting down data agent...")
            await self.data_agent.shutdown()
        
        # Close browser
        if self.browser:
            self.logger.info("Closing browser...")
            await self.browser.close()
        
        if self.playwright:
            await self.playwright.stop()
        
        self.state = AgentState.STOPPED
        self.logger.state_change(AgentState.STOPPING.value, self.state.value)
        
        self.logger.info("=" * 60)
        self.logger.info("✓ SHUTDOWN COMPLETE")
        self.logger.info("=" * 60)


async def main():
    """Main entry point"""
    orchestrator = OrchestratorAgent()
    
    try:
        await orchestrator.initialize()
        await orchestrator.start()
        
    except Exception as e:
        print(f"Fatal error: {e}")
        await orchestrator.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
