@echo off
echo ============================================
echo OdiLeague Agentic Scraper - Setup
echo ============================================
echo.

echo Installing Python dependencies...
pip install -r requirements.txt

echo.
echo Installing Playwright browsers...
playwright install chromium

echo.
echo ============================================
echo Setup Complete!
echo ============================================
echo.
echo Next steps:
echo 1. Run tests: run_tests.bat
echo 2. Start scraper: run_scraper.bat
echo.
pause
