# Multi-League Asynchronous Workflow System

## Overview
This system orchestrates independent, asynchronous scraping workflows for all 4 OdiLeague leagues simultaneously:
- **English League (EL)**
- **Spanish League (SL)**
- **Kenyan League (KL)**
- **Italian League (IL)**

## Workflow Architecture

### Per-League Workflow Phases

Each league runs through the following phases independently:

```
┌─────────────────────────────────────────────────────────────┐
│ PHASE 1: Timer Monitoring & Matchday Scraping              │
│ ─────────────────────────────────────────────────────────── │
│ • Check if timer > 1 minute                                 │
│ • Scrape matchday data every 30 seconds                     │
│ • Scrape multiple markets simultaneously                    │
│ • Continue until timer reaches 10 seconds                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 2: Live Preparation (at 10 seconds)                  │
│ ─────────────────────────────────────────────────────────── │
│ • Stop matchday scraping                                    │
│ • Monitor timer countdown to LIVE                           │
│ • Switch to LIVE tab when timer hits 0                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 3: Live Match Scraping                               │
│ ─────────────────────────────────────────────────────────── │
│ • Scrape live matches every 15 seconds                      │
│ • Collect: scores, goal times, events                       │
│ • Continue for match duration (~90 minutes)                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 4: Results Scraping & Validation                     │
│ ─────────────────────────────────────────────────────────── │
│ • Click Results tab                                         │
│ • Scrape final results                                      │
│ • Validate live data against results                        │
│ • Results data is the absolute truth                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 5: Standings Scraping (every 5 matches)              │
│ ─────────────────────────────────────────────────────────── │
│ • Click Standings tab                                       │
│ • Scrape league table                                       │
│ • Save standings data                                       │
└─────────────────────────────────────────────────────────────┘
```

## Key Features

### 1. **Asynchronous Multi-League Processing**
- All 4 leagues run simultaneously in separate threads
- Each league has its own browser instance
- Independent workflows don't block each other
- Configurable max concurrent workers (default: 4)

### 2. **Intelligent Timer-Based Workflow**
- **> 1 minute**: Full matchday scraping
- **10 seconds**: Stop matchday, prepare for live
- **0 seconds (LIVE)**: Switch to live match tracking
- **Post-match**: Results validation and standings

### 3. **Data Validation**
- Live match data is validated against results
- Results data is the absolute source of truth
- Discrepancies are logged and can be corrected
- Goal times are cross-referenced

### 4. **Comprehensive Data Collection**

#### Matchday Data (Phase 1)
- Match fixtures
- Team names
- Odds for multiple markets
- Timer status
- Scraped every 30 seconds

#### Live Match Data (Phase 3)
- Real-time scores
- Goal times (minute markers)
- Match events
- Half-time scores
- Scraped every 15 seconds

#### Results Data (Phase 4)
- Final scores
- Match week information
- Complete match results
- Used for validation

#### Standings Data (Phase 5)
- League table
- Team positions
- Points, wins, draws, losses
- Recent form

## File Structure

```
data/
└── multi_league/
    ├── EL/  (English League)
    │   ├── EL_matchday_1_143052.json
    │   ├── EL_matchday_2_143122.json
    │   ├── EL_live_1_143200.json
    │   ├── EL_live_2_143215.json
    │   ├── EL_results_145030.json
    │   └── EL_standings_145045.json
    ├── SL/  (Spanish League)
    │   └── ...
    ├── KL/  (Kenyan League)
    │   └── ...
    ├── IL/  (Italian League)
    │   └── ...
    └── workflow_results_20260205_143000.json
```

## Usage

### Basic Usage

```python
from multi_league_orchestrator import MultiLeagueOrchestrator

# Initialize orchestrator
orchestrator = MultiLeagueOrchestrator(max_workers=4)

# Run all leagues
results = orchestrator.run_all_leagues()

# Check results
for result in results:
    print(f"{result['league']}: {result['message']}")
```

### Command Line

```bash
python multi_league_orchestrator.py
```

### Advanced Usage

```python
from multi_league_orchestrator import LeagueWorkflowManager

# Run single league workflow
league_config = {
    "name": "English League",
    "selector_index": 0,
    "code": "EL"
}

manager = LeagueWorkflowManager(league_config)
result = manager.run_workflow()
```

## Configuration

### Timing Parameters

```python
# In the workflow manager
MATCHDAY_SCRAPE_INTERVAL = 30  # seconds
LIVE_SCRAPE_INTERVAL = 15      # seconds
TIMER_CHECK_INTERVAL = 5       # seconds
MAX_LIVE_DURATION = 90 * 60    # 90 minutes
```

### League Configuration

```python
LEAGUES = [
    {"name": "English League", "selector_index": 0, "code": "EL"},
    {"name": "Spanish League", "selector_index": 1, "code": "SL"},
    {"name": "Kenyan League", "selector_index": 2, "code": "KL"},
    {"name": "Italian League", "selector_index": 3, "code": "IL"}
]
```

## Data Validation Logic

### Live vs Results Validation

```python
def _validate_live_vs_results(self):
    """
    Validation rules:
    1. Results data is the absolute truth
    2. Live data scores must match final results
    3. Goal times are cross-referenced
    4. Discrepancies are logged
    5. If mismatch: results data prevails
    """
```

### Validation Checks
- ✅ Final scores match
- ✅ Goal counts match
- ✅ Team names match
- ⚠️ Goal times may vary slightly (live vs final)

## Output Data Format

### Workflow Results
```json
{
  "league": "English League",
  "league_code": "EL",
  "success": true,
  "message": "Workflow completed successfully",
  "matchday_scrapes": 5,
  "live_scrapes": 360,
  "results_scraped": true,
  "standings_scraped": true,
  "validation_complete": true
}
```

### Live Match Data
```json
{
  "matches": [
    {
      "match_index": 0,
      "home_team": "Liverpool",
      "away_team": "Manchester Reds",
      "home_score": "2",
      "away_score": "1",
      "home_goal_times": ["23'", "67'"],
      "away_goal_times": ["45'"]
    }
  ],
  "total_matches": 10
}
```

## Deployment Considerations

### For Local Testing
1. Run with visible browser (set `HEADLESS_MODE = False` in config)
2. Monitor console output for each league
3. Check data files in `data/multi_league/`
4. Verify validation results

### For Web Deployment
1. Set `HEADLESS_MODE = True`
2. Use proper logging instead of print statements
3. Implement error notifications
4. Set up data backup/storage
5. Configure resource limits per league
6. Implement health checks

## Error Handling

### Per-League Isolation
- If one league fails, others continue
- Each league has independent error handling
- Failures are logged and reported
- Partial results are still saved

### Recovery Mechanisms
- Automatic retry on transient errors
- Graceful degradation if data missing
- Cleanup on exceptions
- Browser session management

## Performance Optimization

### Resource Management
- Reuse browser instances within league
- Parallel execution across leagues
- Configurable worker pool size
- Memory-efficient data storage

### Timing Optimization
- Adaptive scraping intervals
- Skip unnecessary phases
- Early termination when appropriate
- Efficient validation algorithms

## Monitoring & Logging

### Console Output
```
✅ [EL] Workflow manager initialized for English League
⏰ [EL] Initial timer: 05:23
📊 [EL] PHASE 1: Matchday Scraping
   ✅ [EL] Matchday scrape #1 - 10 games
🎯 [EL] Timer at 00:10 - Stopping matchday scraping
⏳ [EL] PHASE 2: Preparing for LIVE
🎯 [EL] Timer is LIVE at LIVE!
⚽ [EL] PHASE 3: Live Match Scraping
   ✅ [EL] Live scrape #1 - 10 matches
📋 [EL] PHASE 4: Results Scraping & Validation
🏆 [EL] PHASE 5: Standings Scraping
✅ [EL] Workflow completed: Workflow completed successfully
```

### Data Files
- Timestamped JSON files for each scrape
- Incremental saves during workflow
- Final summary report
- League-specific directories

## Testing

### Local Testing Workflow
```bash
# 1. Test single league first
python -c "from multi_league_orchestrator import LeagueWorkflowManager; \
           m = LeagueWorkflowManager({'name': 'English League', 'selector_index': 0, 'code': 'EL'}); \
           m.run_workflow()"

# 2. Test all leagues
python multi_league_orchestrator.py

# 3. Check output
ls -la data/multi_league/*/
```

### Validation Testing
1. Run workflow during live matches
2. Compare live data with results
3. Verify goal times accuracy
4. Check standings consistency

## Future Enhancements

### Planned Features
- [ ] Real-time notifications
- [ ] Database integration
- [ ] API endpoints for data access
- [ ] Advanced analytics
- [ ] Historical data comparison
- [ ] Automated deployment scripts

### Optimization Opportunities
- [ ] Intelligent scraping intervals based on match state
- [ ] Predictive timer monitoring
- [ ] Compressed data storage
- [ ] Distributed processing
- [ ] Caching mechanisms

## Troubleshooting

### Common Issues

**Issue**: League not selecting properly
- **Solution**: Check selector_index in league config
- **Debug**: Print available league elements

**Issue**: Timer not detected
- **Solution**: Verify CSS selector for timer
- **Debug**: Check if page loaded completely

**Issue**: Live matches not found
- **Solution**: Ensure LIVE tab is clicked
- **Debug**: Check if matches are actually live

**Issue**: Validation fails
- **Solution**: Check data format consistency
- **Debug**: Compare live and results data structures

## Support & Maintenance

### Logs Location
- Console output: Real-time
- Data files: `data/multi_league/`
- Error logs: To be implemented

### Health Checks
- Monitor workflow completion rates
- Check data file timestamps
- Verify validation success rates
- Track scraping intervals

## License & Credits

Created for OdiLeague multi-league scraping system.
Designed for local testing before web deployment.
