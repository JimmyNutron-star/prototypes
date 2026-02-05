"""
Quick test to verify the By import fix
"""

from scrapers.matchday_scraper import MatchdayScraper

print("🔧 Testing matchday scraper after fix...")

scraper = MatchdayScraper()
try:
    data = scraper.scrape_current_matchday()
    
    if data:
        print(f"✅ Success! Scraped {data.get('total_games', 0)} games")
        
        if data.get('games'):
            # Show first 3 games
            for i, game in enumerate(data['games'][:3], 1):
                print(f"\n{i}. {game.get('home_team', 'N/A')} vs {game.get('away_team', 'N/A')}")
                print(f"   Odds: 1={game.get('home_odds', 'N/A')} | X={game.get('draw_odds', 'N/A')} | 2={game.get('away_odds', 'N/A')}")
                print(f"   GG/NG: Yes={game.get('gg_yes', 'N/A')} | No={game.get('gg_no', 'N/A')}")
    else:
        print("❌ No data scraped")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    
finally:
    scraper.cleanup()