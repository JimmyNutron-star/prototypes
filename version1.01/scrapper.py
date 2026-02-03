import time
import json
import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import ElementClickInterceptedException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options  # Import Options for headless mode

# Initialize the database
def init_db():
    conn = sqlite3.connect('odibets_v2.db')
    cursor = conn.cursor()

    # Create matches table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            match_id INTEGER PRIMARY KEY,
            external_id TEXT UNIQUE, 
            team_home TEXT,
            team_away TEXT,
            league TEXT,
            start_time DATETIME
        )
    ''')

    # Create market types table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS market_types (
            market_type_id INTEGER PRIMARY KEY,
            name TEXT UNIQUE
        )
    ''')

    # Create odds ticks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS odds_ticks (
            tick_id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id INTEGER,
            market_type_id INTEGER,
            timestamp INTEGER, 
            odds_data TEXT, 
            FOREIGN KEY(match_id) REFERENCES matches(match_id),
            FOREIGN KEY(market_type_id) REFERENCES market_types(market_type_id)
        )
    ''')

    # Create an index for fast lookup
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_time_scroll ON odds_ticks (timestamp DESC)')
    
    conn.commit()
    conn.close()

init_db()

# Function to save the odds in the database
def save_odds(match_data, odds_dict, market_name):
    conn = sqlite3.connect('odibets_v2.db')
    cursor = conn.cursor()

    # Ensure match exists and get ID
    cursor.execute('''
        INSERT OR IGNORE INTO matches (external_id, team_home, team_away, league)
        VALUES (?, ?, ?, ?)
    ''', (match_data['id'], match_data['home'], match_data['away'], match_data['league']))
    
    cursor.execute('SELECT match_id FROM matches WHERE external_id = ?', (match_data['id'],))
    m_id = cursor.fetchone()[0]

    # Ensure market type exists
    cursor.execute('INSERT OR IGNORE INTO market_types (name) VALUES (?)', (market_name,))
    cursor.execute('SELECT market_type_id FROM market_types WHERE name = ?', (market_name,))
    mt_id = cursor.fetchone()[0]

    # Record the "Tick" (Snapshot)
    cursor.execute('''
        INSERT INTO odds_ticks (match_id, market_type_id, timestamp, odds_data)
        VALUES (?, ?, ?, ?)
    ''', (m_id, mt_id, int(time.time()), json.dumps(odds_dict)))

    conn.commit()
    conn.close()

# Function to start the web scraping
def scrape_odds():
    # Setup Chrome options for headless mode
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Enables headless mode
    chrome_options.add_argument("--no-sandbox")  # For Linux environments
    chrome_options.add_argument("--disable-dev-shm-usage")  # For Linux environments

    # Setup the browser and open the page
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get('https://odibets.com/odileague')

    # Wait for the page to load
    time.sleep(5)

    try:
        # Scrape data for the first 5 timestamps
        timestamps = driver.find_elements(By.CSS_SELECTOR, '.ss')[:5]
        
        for i, timestamp in enumerate(timestamps):
            try:
                # Scroll into view and click on the timestamp
                driver.execute_script("arguments[0].scrollIntoView();", timestamp)

                # Wait for any overlay or modal to disappear (if present)
                WebDriverWait(driver, 10).until_not(EC.presence_of_element_located((By.CSS_SELECTOR, '.modal')))
                
                # Wait for the timestamp to be clickable
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable(timestamp))

                timestamp.click()
                time.sleep(2)  # Give time for the data to load

                # Now, scrape the match data for this timestamp
                matches = driver.find_elements(By.CSS_SELECTOR, '.game.e')

                for match in matches:
                    try:
                        # Scrape match data (team names, odds, etc.)
                        team_home = match.find_element(By.CSS_SELECTOR, '.t-l').text
                        team_away = match.find_elements(By.CSS_SELECTOR, '.t-l')[1].text
                        league = 'OdiLeague'  # This could be dynamic if needed
                        match_id = match.get_attribute('data-id')  # Assuming each match has a unique 'data-id'
                        
                        odds_buttons = match.find_elements(By.CSS_SELECTOR, '.odds button')
                        odds_dict = {}
                        for button in odds_buttons:
                            market_type = button.find_element(By.CSS_SELECTOR, 'small').text
                            odds_value = button.find_element(By.CSS_SELECTOR, 'span.o-2').text
                            odds_dict[market_type] = odds_value

                        # Store the data in the database
                        match_data = {
                            'id': match_id,
                            'home': team_home,
                            'away': team_away,
                            'league': league
                        }
                        save_odds(match_data, odds_dict, '1X2')  # '1X2' is the market type in this example

                    except Exception as e:
                        print(f"Error scraping match data: {e}")
            except ElementClickInterceptedException:
                print(f"Error: Element click intercepted at timestamp {i + 1}")
            except StaleElementReferenceException:
                print(f"Error: Stale element reference at timestamp {i + 1}")
            except NoSuchElementException:
                print(f"Error: No such element found at timestamp {i + 1}")
            except Exception as e:
                print(f"Error scraping timestamp {i + 1}: {e}")

    except Exception as e:
        print(f"Error scraping timestamps: {e}")

    finally:
        print("Scraping complete!")
        driver.quit()

# Start the scraping process
scrape_odds()
