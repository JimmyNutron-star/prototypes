# 🚀 QUICK START GUIDE

## Step 1: Setup (First Time Only)

Double-click: **`setup.bat`**

This will:
- Install Python dependencies
- Install Playwright browser
- Prepare the environment

## Step 2: Run Tests (Recommended)

Double-click: **`run_tests.bat`**

Select from menu:
1. Browser Connection - Test if browser opens and navigates
2. Data Agent - Test data storage
3. Timer Detection - Test timer monitoring
4. Matchday Scraping - Test odds extraction
5. Run All Tests - Complete test suite

**Recommendation:** Run option 5 (All Tests) first to verify everything works.

## Step 3: Start Scraping

Double-click: **`run_scraper.bat`**

The system will:
- Open browser (you'll see it)
- Initialize all agents
- Start monitoring all 4 leagues
- Scrape data automatically
- Save to `data/` folder

## Step 4: Monitor Progress

Watch the console for colored logs:
- 🟢 **Green (INFO)** - Normal operations
- 🟡 **Yellow (WARNING)** - Minor issues
- 🔴 **Red (ERROR)** - Problems detected
- 🔵 **Blue (DEBUG)** - Detailed info

## Step 5: Stop Scraping

Press **`Ctrl+C`** in the console window

The system will:
- Gracefully stop all agents
- Save all data
- Create backup
- Close browser

## 📊 View Results

Check the `data/` folder:
- **matches.json** - All match data
- **results.json** - Final results
- **standings.json** - League tables

## 🔍 Troubleshooting

### Problem: Browser doesn't open
**Solution:** Run `setup.bat` again

### Problem: No data being saved
**Solution:** Check `logs/` folder for errors

### Problem: Tests failing
**Solution:** Check internet connection and website availability

## 💡 Tips

1. **First Run:** Always run tests first
2. **Monitor Logs:** Watch console for real-time updates
3. **Check Data:** Data saves every few seconds
4. **Backups:** Automatic backups on shutdown
5. **Headless Mode:** Edit `config.py` to run without browser window

## 📁 File Structure

```
New folder (3)/
├── setup.bat              ← Run this first
├── run_tests.bat          ← Test components
├── run_scraper.bat        ← Start scraping
├── orchestrator.py        ← Main system
├── config.py              ← Settings
├── data/                  ← Scraped data
├── logs/                  ← Log files
└── README.md              ← Full documentation
```

## ⚡ Quick Commands

| Action | Command |
|--------|---------|
| Setup | `setup.bat` |
| Test | `run_tests.bat` |
| Start | `run_scraper.bat` |
| Stop | `Ctrl+C` |

---

**Need Help?** Check `README.md` for detailed documentation.
