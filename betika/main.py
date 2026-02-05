from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
import json

# The target URL
url = "https://www.betika.com/en-ke/ligi-bigi"

def extract_upcoming_matches(html_content):
    """Extract upcoming match odds from the HTML"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find the main container for upcoming matches
    matches_wrapper = soup.find('div', class_='team-selection-wrapper od-wrap')
    
    if not matches_wrapper:
        print("Warning: Could not find upcoming matches wrapper")
        return []
    
    # Find all match containers
    match_containers = matches_wrapper.find_all('div', class_='single-match')
    
    matches_data = []
    
    for match in match_containers:
        # Extract team names
        home_team_elem = match.find('span', class_='team-name-text')
        away_team_elem = match.find_all('span', class_='team-name-text')[1] if len(match.find_all('span', class_='team-name-text')) > 1 else None
        
        home_team = home_team_elem.text.strip() if home_team_elem else "Unknown"
        away_team = away_team_elem.text.strip() if away_team_elem else "Unknown"
        
        # Extract odds (1, X, 2)
        odds_elements = match.find_all('span', class_='ods-given')
        
        if len(odds_elements) >= 3:
            home_odds = odds_elements[0].text.strip()  # 1
            draw_odds = odds_elements[1].text.strip()  # X
            away_odds = odds_elements[2].text.strip()  # 2
        else:
            home_odds = draw_odds = away_odds = "N/A"
        
        # Create match dictionary
        match_data = {
            'home_team': home_team,
            'away_team': away_team,
            'home_odds': home_odds,
            'draw_odds': draw_odds,
            'away_odds': away_odds
        }
        
        matches_data.append(match_data)
        
        # Print for debugging
        print(f"Found: {home_team} vs {away_team} - 1:{home_odds} X:{draw_odds} 2:{away_odds}")
    
    return matches_data

def main():
    with sync_playwright() as p:
        # Launch the browser
        browser = p.chromium.launch(headless=False)  # Change to True later
        page = browser.new_page()
        
        # Navigate to the page
        print(f"Navigating to {url}")
        page.goto(url)
        
        # Wait for the page to load - we'll use a better wait strategy
        page.wait_for_load_state('networkidle')
        time.sleep(2)  # Small additional wait
        
        # Get the page content (HTML)
        html_content = page.content()
        
        # Extract the upcoming matches
        print("\nExtracting upcoming match odds...")
        matches = extract_upcoming_matches(html_content)
        
        # Print summary
        print(f"\nFound {len(matches)} upcoming matches")
        
        # Save to JSON file
        if matches:
            with open('upcoming_matches.json', 'w', encoding='utf-8') as f:
                json.dump(matches, f, indent=2, ensure_ascii=False)
            print("Data saved to 'upcoming_matches.json'")
        
        # Close the browser
        browser.close()
        
        return matches

if __name__ == "__main__":
    matches_data = main()