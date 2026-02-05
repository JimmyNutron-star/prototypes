# OdiLeague Agentic Webscraper

An advanced, multi-agent webscraping system for OdiLeague virtual sports platform.

## 🏗️ Architecture

This scraper uses an **agentic architecture** where autonomous agents work independently but coordinate through a central orchestrator.

### Agent Hierarchy

```
Orchestrator Agent (Master)
├── Data Agent (Storage)
├── Timer Agent (Monitor)
└── League Agents (4x - one per league)
    ├── Matchday Agents (spawned per match)
    ├── Live Agents (spawned per live match)
    ├── Results Agents (spawned after match)
    └── Standings Agents (spawned every 5 matches)
```

### Key Features

- ✅ **Fully Asynchronous** - All agents run concurrently
- ✅ **Event-Driven** - Agents communicate via events
- ✅ **Autonomous** - Each agent makes independent decisions
- ✅ **Fault-Tolerant** - Agent failures don't crash the system
- ✅ **Scalable** - Easy to add more leagues or agent types
- ✅ **Data Validation** - Cross-validates live data with results

## 📦 Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Playwright Browsers

```bash
playwright install chromium
```

## 🧪 Testing & Debugging

Before running the full system, test individual components:

```bash
python debug_test.py
```

This will show a menu:
1. **Browser Connection** - Test navigation and element detection
2. **Data Agent** - Test data storage and retrieval
3. **Timer Detection** - Test timer monitoring
4. **Matchday Scraping** - Test odds extraction
5. **Run All Tests** - Complete test suite

## 🚀 Running the Scraper

### Full System

```bash
python orchestrator.py
```

This starts the complete agentic system:
- Opens browser (non-headless by default)
- Initializes all agents
- Monitors all 4 leagues simultaneously
- Scrapes matchday, live, results, and standings data
- Saves everything to JSON files

### Stop the System

Press `Ctrl+C` to gracefully shutdown all agents.

## 📊 Data Output

All data is saved to the `data/` directory:

- **matches.json** - All match data (matchday + live + results)
- **results.json** - Final results only
- **standings.json** - League standings snapshots
- **leagues.json** - League metadata

Backups are automatically created in `data/backups/` on shutdown.

## 🔧 Configuration

Edit `config.py` to customize:

- **Timing thresholds** - When to start/stop scraping
- **Scraping intervals** - How often to check for updates
- **Browser settings** - Headless mode, timeouts
- **Logging levels** - DEBUG, INFO, WARNING, ERROR

## 📝 Logs

Logs are saved to `logs/` directory with colored console output:
- Each agent has its own log file
- Timestamped entries
- Structured logging with context

## 🎯 How It Works

### 1. Initialization
- Orchestrator starts browser
- Data Agent loads existing data
- League Agents select their leagues
- Timer Agent begins monitoring

### 2. Matchday Phase (Timer > 1 minute)
- Timer Agent detects threshold
- League Agent spawns Matchday Agent
- Scrapes teams, logos, and odds
- Saves data continuously

### 3. Pre-Live Phase (Timer < 10 seconds)
- Timer Agent signals stop
- Matchday Agent terminates
- System prepares for live tracking

### 4. Live Phase (Timer = "LIVE")
- Timer Agent detects live state
- League Agent spawns Live Agent
- Tracks scores and goal events in real-time
- Updates data every 2 seconds

### 5. Post-Match Phase
- Live Agent detects match end
- Results Agent validates final score
- Compares live data vs results tab
- Marks match as validated

### 6. Standings Update (Every 5 matches)
- League Agent counts completed matches
- Spawns Standings Agent
- Scrapes league table
- Saves snapshot

## 🛡️ Error Handling

- **Retry Logic** - Failed scrapes retry automatically
- **Graceful Degradation** - Missing data doesn't stop the system
- **Agent Recovery** - Dead agents are detected and can be restarted
- **Data Consistency** - Atomic file writes prevent corruption

## 📈 Monitoring

The system logs statistics every 30 seconds:
- Total matches scraped
- Results collected
- Validated matches

## 🔍 Troubleshooting

### Browser doesn't open
- Check Playwright installation: `playwright install chromium`

### No data being saved
- Check `data/` directory permissions
- Review logs in `logs/` directory

### Agents not starting
- Run debug tests: `python debug_test.py`
- Check CSS selectors in `config.py`

### Popup blocking view
- Popup should auto-close
- Check `selectors.POPUP_CLOSE` in config

## 🎨 Customization

### Add a New League
Edit `config.py`:
```python
LEAGUES = [
    # ... existing leagues
    {
        "name": "New League",
        "selector": "div.logo:nth-child(5)",
        "id": "new_league"
    }
]
```

### Change Scraping Frequency
Edit `config.py`:
```python
TIMER_CHECK_INTERVAL = 0.5  # Check timers every 0.5s
LIVE_MATCH_CHECK_INTERVAL = 2.0  # Update live data every 2s
```

### Add New Markets
Modify `matchday_agent.py` to scrape additional betting markets.

## 📚 Code Structure

```
├── config.py                    # Configuration & selectors
├── models.py                    # Data models & enums
├── logger.py                    # Logging utilities
├── data_agent.py                # Data storage agent
├── timer_agent.py               # Timer monitoring agent
├── matchday_agent.py            # Pre-match scraping agent
├── live_agent.py                # Live match tracking agent
├── results_standings_agents.py  # Results & standings agents
├── league_agent.py              # League coordinator agent
├── orchestrator.py              # Master orchestrator
├── debug_test.py                # Test suite
└── requirements.txt             # Dependencies
```

## 🤝 Contributing

This is an agentic system - each agent is independent and can be enhanced separately:
- Add new agent types
- Improve scraping logic
- Enhance data validation
- Add new data sources

## 📄 License

MIT License - Use freely!

## 🎉 Credits

Built with:
- **Playwright** - Browser automation
- **Python asyncio** - Asynchronous execution
- **Agentic Architecture** - Autonomous agent design

---

**Happy Scraping! 🚀**
