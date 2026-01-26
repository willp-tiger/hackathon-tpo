# Interactive Dashboard Guide

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set API key:**
   ```bash
   # Windows
   set ANTHROPIC_API_KEY=your_key_here

   # Unix/Mac
   export ANTHROPIC_API_KEY=your_key_here
   ```

3. **Start the dashboard:**
   ```bash
   python app.py
   ```

4. **Open in browser:**
   ```
   http://localhost:5000
   ```

## Using the Dashboard

### Configuration Panel (Left)

- **Optimization Objective:**
  - **Maximize Volume:** Focus on selling the most units
  - **Maximize Profit:** Focus on maximizing profit margins

- **Budget Slider:** Drag to set budget ($100K - $2M)

- **Quick Presets:**
  - **Conservative:** $500K budget, profit objective
  - **Aggressive:** $2M budget, volume objective

- **Run Button:** Click to start optimization

### Execution Monitor (Center)

- **Progress Bar:** Shows completion percentage (0-100%)
- **Status Text:** Current step being executed
- **Journey Log:** Live streaming log of agent activities
  - Auto-scrolls to show latest updates
  - Updates every 2 seconds
  - Shows agent reasoning and decisions

### Results Panel (Right)

Displays when optimization completes:

- **Metrics Cards:**
  - Total Events (promotions in calendar)
  - Total Spend (vs budget)
  - MAPE (forecast accuracy)
  - Iterations (rejection loop count)

- **Calendar Preview:** First 10 events from optimized calendar

### Run History (Bottom)

- Lists all past runs
- Click any run to reload its results
- Color-coded status:
  - Blue = Running
  - Green = Completed
  - Red = Failed

## Features

### Real-Time Monitoring

- Live updates every 2 seconds
- See agent A → B → C workflow in action
- Watch rejection loop iterations
- Monitor progress without refreshing

### Multiple Runs

- Run multiple optimizations with different parameters
- Compare results side-by-side
- Reload previous runs anytime
- All runs saved in `outputs/runs/<run_id>/`

### Run Output Files

Each run creates its own directory with:
- `promotion_calendar.json` - Final calendar
- `causal_parameters.json` - Agent A analysis
- `OPTIMIZATION_JOURNEY.txt` - Complete log
- `EXECUTION_SUMMARY.txt` - Summary report
- `metadata.json` - Run configuration

## Tips

1. **Start with Conservative preset** to see system working quickly
2. **Monitor Journey Log** to understand agent reasoning
3. **Try different budgets** to see how calendar changes
4. **Compare Volume vs Profit** objectives
5. **Check Run History** to review past experiments

## Troubleshooting

**Dashboard won't load:**
- Check Flask is installed: `pip install flask flask-cors`
- Ensure port 5000 is not in use
- Try: `python app.py` and look for errors

**Optimization fails:**
- Check API key is set: `echo %ANTHROPIC_API_KEY%`
- Check data files exist in `case-data/`
- View error in Status Text on dashboard

**Journey log not updating:**
- Wait 2-3 seconds for polling
- Check browser console for errors
- Refresh page and try again

## Architecture

```
Browser (http://localhost:5000)
    |
    | HTTP/JSON
    v
Flask Backend (app.py)
    |
    | Threading
    v
TPOOrchestrator (runs in background)
    |
    +-- Agent A (Analyst)
    |
    +-- Agent B (Strategist)
    |
    +-- Agent C (Auditor)
    |
    v
Outputs (outputs/runs/<run_id>/)
```

## API Endpoints

For programmatic access:

- `POST /api/run` - Start optimization
- `GET /api/status/<run_id>` - Get status
- `GET /api/journey/<run_id>` - Get journey log
- `GET /api/results/<run_id>` - Get results
- `GET /api/runs` - List all runs

Example:
```bash
curl -X POST http://localhost:5000/api/run \
  -H "Content-Type: application/json" \
  -d '{"objective": "volume", "budget": 1000000}'
```

---

**Created:** 2026-01-25 (Session 14)
**For:** TPO AI Agents Hackathon
