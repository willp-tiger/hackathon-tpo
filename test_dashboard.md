# Dashboard Test Scenarios

## How to Test

1. Start the dashboard:
   ```bash
   python app.py
   ```

2. Open browser: `http://localhost:5000`

3. Try each scenario below

---

## Test Scenario 1: Quick Win (Conservative)

**Objective:** Maximize Profit
**Budget:** $500,000

**Expected Results:**
- Completes in 2-3 minutes
- 10-20 calendar events
- Low rejection loop iterations (1-3)
- Budget utilization: 80-95%
- Focus on high-margin PPGs
- Moderate discount depths (15-25%)

**What to Watch:**
- Journey log shows Agent A analyzing data
- Agent B generates conservative calendar
- Agent C validates constraints
- Few rejections due to lower event count

---

## Test Scenario 2: Volume Maximization (Aggressive)

**Objective:** Maximize Volume
**Budget:** $2,000,000

**Expected Results:**
- Completes in 3-5 minutes
- 40-60 calendar events
- Moderate iterations (3-5)
- Budget utilization: 85-100%
- Focus on high-elasticity PPGs
- Deep discount depths (25-35%)
- Heavy display usage

**What to Watch:**
- Agent B tries to pack many promotions
- Agent C catches gap rule violations
- Multiple rejection loop iterations
- Calendar gets refined iteratively

---

## Test Scenario 3: Tight Budget (Rejection Loop Demo)

**Objective:** Maximize Volume
**Budget:** $300,000

**Expected Results:**
- Completes in 3-4 minutes
- 8-15 calendar events (very constrained)
- High iterations (5-8)
- Budget utilization: 95-100%
- Frequent budget violations
- Shows rejection loop clearly

**What to Watch:**
- Agent B generates calendar, exceeds budget
- Agent C rejects for budget violations
- Agent B adjusts, tries again
- Multiple iterations before approval
- Great demo of agent collaboration!

---

## Test Scenario 4: Profit Optimization (Balanced)

**Objective:** Maximize Profit
**Budget:** $1,000,000

**Expected Results:**
- Completes in 2-3 minutes
- 20-30 calendar events
- Low-moderate iterations (2-4)
- Budget utilization: 70-85%
- Selective PPG choices
- Moderate discounts (20-25%)
- Strategic display usage

**What to Watch:**
- Agent A's causal parameters (elasticity model)
- Agent B's profit-focused reasoning
- Lower spend than volume objective
- Quality over quantity approach

---

## Test Scenario 5: Extreme Volume Push

**Objective:** Maximize Volume
**Budget:** $1,500,000

**Expected Results:**
- Completes in 3-4 minutes
- 35-50 calendar events
- Moderate iterations (3-5)
- Budget utilization: 90-100%
- Maximum discount depths (30-40%)
- Display on most events
- High projected volume lift

**What to Watch:**
- Agent B reasoning: "high elasticity", "peak seasonality"
- Gap rule violations (too many promotions per PPG)
- Display lift calculations
- Final calendar optimization

---

## Quick Comparison Test

Run these back-to-back to compare:

### Run A: Volume @ $1M
- Objective: Volume
- Budget: $1,000,000

### Run B: Profit @ $1M
- Objective: Profit
- Budget: $1,000,000

**Compare Results:**
- Volume Run: More events, deeper discounts
- Profit Run: Fewer events, moderate discounts
- Volume Run: Higher spend utilization
- Profit Run: More selective, higher ROI per event

---

## Testing Checklist

After running each scenario, verify:

- [ ] Progress bar updates (0% → 100%)
- [ ] Journey log streams in real-time
- [ ] Status changes: Ready → Running → Completed
- [ ] Results panel populates with metrics
- [ ] Calendar preview shows events
- [ ] Run appears in history panel
- [ ] Can reload previous run from history

---

## Monitoring During Execution

Watch for these in the Journey Log:

### STEP 1: DATA LOADING
```
Loading sales data from case-data/sales_v2.xlsx
Loaded 3,676 records
```

### STEP 2: AGENT A (ANALYST)
```
Using cached causal parameters
baseline_velocity: 11,815.46
price_elasticity: 6.91
```

### STEP 3: REJECTION LOOP
```
Iteration 1: Calendar composition
  ppgs: ['Brand 1_Promo.Group 20', 'Brand 4_Promo.Group 0', ...]
  ppg_count: 8
  total_spend: $1,050,000

Iteration 1: Top violations found
  violations: ['BUDGET: $1,050,000 exceeds $1,000,000']

Iteration 2: Calendar composition
  ppgs: ['Brand 1_Promo.Group 20', 'Brand 5_Promo.Group 6', ...]
  total_spend: $980,000

Iteration 2: No violations - APPROVED
```

### STEP 4-7: FINALIZATION
```
Calendar saved
Reports generated
Optimization complete
```

---

## Expected Metrics by Scenario

| Scenario | Budget | Events | Iterations | Spend % | Time |
|----------|--------|--------|------------|---------|------|
| Conservative | $500K | 10-20 | 1-3 | 80-95% | 2-3m |
| Aggressive | $2M | 40-60 | 3-5 | 85-100% | 3-5m |
| Tight Budget | $300K | 8-15 | 5-8 | 95-100% | 3-4m |
| Balanced | $1M | 20-30 | 2-4 | 70-85% | 2-3m |
| Extreme | $1.5M | 35-50 | 3-5 | 90-100% | 3-4m |

---

## Troubleshooting Test Issues

**"Optimization failed" error:**
- Check ANTHROPIC_API_KEY is set
- Check terminal output for detailed error
- Verify data files in case-data/

**Journey log not updating:**
- Wait 2-3 seconds (polling interval)
- Check browser console (F12) for errors
- Refresh page and retry

**Progress stuck at 0%:**
- Check terminal - optimization may still be starting
- Agent A may be running (takes 30-60s)
- Wait for "STEP 2" in journey log

**No results showing:**
- Wait for "Completed" status
- Results only appear when optimization finishes
- Check run history - may need to click run to load

---

## API Testing (Advanced)

Test the backend API directly:

```bash
# Start a run
curl -X POST http://localhost:5000/api/run \
  -H "Content-Type: application/json" \
  -d '{"objective": "volume", "budget": 1000000}'

# Response: {"run_id": "abc123", "status": "started"}

# Check status
curl http://localhost:5000/api/status/abc123

# Get journey log
curl http://localhost:5000/api/journey/abc123

# Get results
curl http://localhost:5000/api/results/abc123

# List all runs
curl http://localhost:5000/api/runs
```

---

**Created:** 2026-01-25 (Session 14)
**Purpose:** Test scenarios for interactive dashboard validation
