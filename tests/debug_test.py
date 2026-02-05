"""
Debug and test script for individual agents
Run this to test components before full system launch
"""
import asyncio
from playwright.async_api import async_playwright

from config import config, selectors
from logger import AgentLogger
from data_agent import DataAgent

async def test_browser_connection():
    """Test 1: Browser connection and navigation"""
    logger = AgentLogger("Test-Browser")
    logger.info("=" * 60)
    logger.info("TEST 1: Browser Connection")
    logger.info("=" * 60)
    
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        logger.info(f"Navigating to {config.TARGET_URL}...")
        await page.goto(config.TARGET_URL, wait_until='networkidle')
        await asyncio.sleep(2)
        
        logger.info("✓ Navigation successful")
        
        # Check for popup
        popup = await page.query_selector(selectors.POPUP_CLOSE)
        if popup:
            logger.info("Popup detected - closing...")
            await popup.click()
            await asyncio.sleep(1)
            logger.info("✓ Popup closed")
        
        # Check for league logos
        logos = await page.query_selector_all(selectors.LEAGUE_LOGO)
        logger.info(f"✓ Found {len(logos)} league logos")
        
        # Check for timers
        timers = await page.query_selector_all(selectors.TIMER_SLOT)
        logger.info(f"✓ Found {len(timers)} timer slots")
        
        # Check for games
        games = await page.query_selector_all(selectors.GAME_CONTAINER)
        logger.info(f"✓ Found {len(games)} game containers")
        
        logger.info("✓ TEST 1 PASSED")
        
        # Keep browser open for inspection
        logger.info("Browser will stay open for 10 seconds...")
        await asyncio.sleep(10)
        
        await browser.close()
        await playwright.stop()
        
        return True
        
    except Exception as e:
        logger.error(f"✗ TEST 1 FAILED: {e}")
        return False


async def test_data_agent():
    """Test 2: Data Agent"""
    logger = AgentLogger("Test-DataAgent")
    logger.info("=" * 60)
    logger.info("TEST 2: Data Agent")
    logger.info("=" * 60)
    
    try:
        # Initialize data agent
        data_agent = DataAgent(data_dir="test_data")
        await data_agent.initialize()
        logger.info("✓ Data agent initialized")
        
        # Test save matchday data
        test_matchday = {
            'match_id': 'test_001',
            'league': 'english',
            'home_team': {'name': 'Test Home', 'logo_url': None},
            'away_team': {'name': 'Test Away', 'logo_url': None},
            'timer': '05:00',
            'markets': []
        }
        
        await data_agent.save_matchday_data('test_001', test_matchday)
        logger.info("✓ Matchday data saved")
        
        # Test retrieve
        retrieved = await data_agent.get_match_data('test_001')
        if retrieved:
            logger.info("✓ Data retrieved successfully")
        
        # Test stats
        stats = await data_agent.get_stats()
        logger.info(f"✓ Stats: {stats}")
        
        # Cleanup
        await data_agent.shutdown()
        logger.info("✓ Data agent shutdown")
        
        logger.info("✓ TEST 2 PASSED")
        return True
        
    except Exception as e:
        logger.error(f"✗ TEST 2 FAILED: {e}")
        return False


async def test_timer_detection():
    """Test 3: Timer detection"""
    logger = AgentLogger("Test-Timer")
    logger.info("=" * 60)
    logger.info("TEST 3: Timer Detection")
    logger.info("=" * 60)
    
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        await page.goto(config.TARGET_URL, wait_until='networkidle')
        await asyncio.sleep(2)
        
        # Close popup
        popup = await page.query_selector(selectors.POPUP_CLOSE)
        if popup:
            await popup.click()
            await asyncio.sleep(1)
        
        # Get timers
        timers = await page.query_selector_all(selectors.TIMER_SLOT)
        logger.info(f"Found {len(timers)} timers")
        
        # Read timer values
        for i, timer in enumerate(timers[:5]):  # First 5 only
            text = await timer.inner_text()
            is_active = await timer.evaluate("el => el.classList.contains('active')")
            logger.info(f"Timer {i}: {text.strip()} (active={is_active})")
        
        logger.info("✓ TEST 3 PASSED")
        
        await asyncio.sleep(5)
        await browser.close()
        await playwright.stop()
        
        return True
        
    except Exception as e:
        logger.error(f"✗ TEST 3 FAILED: {e}")
        return False


async def test_matchday_scraping():
    """Test 4: Matchday scraping"""
    logger = AgentLogger("Test-Matchday")
    logger.info("=" * 60)
    logger.info("TEST 4: Matchday Scraping")
    logger.info("=" * 60)
    
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        await page.goto(config.TARGET_URL, wait_until='networkidle')
        await asyncio.sleep(2)
        
        # Close popup
        popup = await page.query_selector(selectors.POPUP_CLOSE)
        if popup:
            await popup.click()
            await asyncio.sleep(1)
        
        # Get first game
        games = await page.query_selector_all(selectors.GAME_CONTAINER)
        if len(games) > 0:
            game = games[0]
            
            # Extract teams
            team_names = await game.query_selector_all(selectors.TEAM_NAMES)
            if len(team_names) >= 2:
                home = await team_names[0].inner_text()
                away = await team_names[1].inner_text()
                logger.info(f"✓ Teams: {home.strip()} vs {away.strip()}")
            
            # Extract odds
            odds_container = await game.query_selector(selectors.ODDS_CONTAINER)
            if odds_container:
                buttons = await odds_container.query_selector_all('button')
                logger.info(f"✓ Found {len(buttons)} odds buttons")
                
                for button in buttons[:3]:
                    label_elem = await button.query_selector('small.o-1')
                    value_elem = await button.query_selector('span.o-2')
                    
                    if label_elem and value_elem:
                        label = await label_elem.inner_text()
                        value = await value_elem.inner_text()
                        logger.info(f"  Odds: {label.strip()} = {value.strip()}")
        
        logger.info("✓ TEST 4 PASSED")
        
        await asyncio.sleep(5)
        await browser.close()
        await playwright.stop()
        
        return True
        
    except Exception as e:
        logger.error(f"✗ TEST 4 FAILED: {e}")
        return False


async def run_all_tests():
    """Run all tests"""
    logger = AgentLogger("TestRunner")
    logger.info("=" * 60)
    logger.info("RUNNING ALL TESTS")
    logger.info("=" * 60)
    
    results = []
    
    # Test 1: Browser
    results.append(("Browser Connection", await test_browser_connection()))
    await asyncio.sleep(2)
    
    # Test 2: Data Agent
    results.append(("Data Agent", await test_data_agent()))
    await asyncio.sleep(2)
    
    # Test 3: Timer Detection
    results.append(("Timer Detection", await test_timer_detection()))
    await asyncio.sleep(2)
    
    # Test 4: Matchday Scraping
    results.append(("Matchday Scraping", await test_matchday_scraping()))
    
    # Summary
    logger.info("=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        logger.info(f"{test_name}: {status}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("✓ ALL TESTS PASSED!")
    else:
        logger.warning(f"⚠ {total - passed} test(s) failed")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("OdiLeague Scraper - Debug & Test Suite")
    print("=" * 60)
    print("\nSelect test to run:")
    print("1. Browser Connection")
    print("2. Data Agent")
    print("3. Timer Detection")
    print("4. Matchday Scraping")
    print("5. Run All Tests")
    print("0. Exit")
    
    choice = input("\nEnter choice (0-5): ").strip()
    
    if choice == "1":
        asyncio.run(test_browser_connection())
    elif choice == "2":
        asyncio.run(test_data_agent())
    elif choice == "3":
        asyncio.run(test_timer_detection())
    elif choice == "4":
        asyncio.run(test_matchday_scraping())
    elif choice == "5":
        asyncio.run(run_all_tests())
    else:
        print("Exiting...")
