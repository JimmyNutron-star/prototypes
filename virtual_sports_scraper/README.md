# Virtual Sports Scraper System

A complete modular scraping system for Virtual Sports, featuring a strict state machine, UPSERT data storage, and an enhanced GUI for independent component testing.

## 🚀 Quick Start

1.  **Double-click** `START_TEST_MENU.bat` (Windows) or run `python LAUNCH_ENHANCED_TEST_MENU.py`.
2.  The GUI will launch automatically.
3.  Select a **League** and **Market** from the dropdowns.
4.  Click any test button (e.g., **"Test Selected League"** or **"Scrape Odds"**).
5.  View real-time logs in the output window.

## 🏗️ Architecture

The system is built on a strict hierarchy:
1.  **State Manager**: Enforces `NOT_STARTED -> ODDS_SCRAPED -> LIVE -> FINISHED`.
2.  **Core Components**: Independent modules for Popups, Timer, Live Detection, etc.
3.  **Data Storage**: Thread-safe, Append-only/UPSERT JSON storage.

### Directory Structure
- `config/`: Settings and CSS Selectors.
- `core/`: Browser, State, and Data logic.
- `components/`: The logic for each specific part of the page (Odds, Timer, etc.).
- `test_scripts/`: 15+ independent scripts for granular testing.
- `data/`: Where JSON data is stored.
- `test_results/`: Logs and screenshots.

## 🧪 Testing Features or "How to Verify"

The **Enhanced GUI** allows you to:
- Test **Leagues** (switch between English, Spanish, etc.).
- Test **Markets** (26+ markets supported).
- Run **Test Suites** to validate entire subsystems at once.
- **Visual Verification**: Screenshots are saved to `test_results/screenshots`.

### Key Constraints Implemented
- **No Scraping when Timer <= 10s**.
- **No Scraping when Match is LIVE**.
- **Data is never deleted** (UPSERT only).
- **Popups are handled first**.

## 🔧 Configuration

Edit `config/settings.py` for global settings (timeouts, intervals).
Edit `config/selectors.py` to update CSS selectors if the website structure changes.

## 📁 Data Storage

Data is saved in `data/live` and `data/historical`:
- `matches.json`
- `odds.json`
- `goals.json` (Append Only)
- `results.json`
- `standings.json`

## 📦 Requirements

- Python 3.8+
- Chrome Browser installed
- Dependencies (auto-installed): `selenium`, `webdriver-manager`, `tkinter` (built-in).
