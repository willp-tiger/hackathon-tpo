# Quick Test Inputs for Dashboard

## Start the Dashboard

```bash
python app.py
```

Then open: **http://localhost:5000**

---

## 5 Quick Tests (Copy These Settings)

### 1️⃣ CONSERVATIVE (Quick Test - 2 min)
```
Objective: Maximize Profit
Budget: $500,000 (drag slider left)
```
**Expected:** 10-20 events, 1-3 iterations, completes fast

---

### 2️⃣ AGGRESSIVE (Full System Test - 4 min)
```
Objective: Maximize Volume
Budget: $2,000,000 (drag slider all the way right)
```
**Expected:** 40-60 events, 3-5 iterations, shows full workflow

---

### 3️⃣ REJECTION LOOP DEMO (Best for Presentation - 3 min)
```
Objective: Maximize Volume
Budget: $300,000 (drag slider left to ~$300K)
```
**Expected:** 8-15 events, 5-8 iterations, **clearly shows agent collaboration**

---

### 4️⃣ BALANCED (Standard Run - 3 min)
```
Objective: Maximize Profit
Budget: $1,000,000 (default - middle)
```
**Expected:** 20-30 events, 2-4 iterations, typical workflow

---

### 5️⃣ VOLUME VS PROFIT COMPARISON
**Run A:**
```
Objective: Maximize Volume
Budget: $1,000,000
```

**Run B (immediately after):**
```
Objective: Maximize Profit
Budget: $1,000,000
```

**Then compare:** Click on each run in History panel to see differences

---

## Using the Presets (Easy Mode)

Dashboard has 2 built-in presets:

### Conservative Button
- Auto-sets: Profit objective, $500K budget
- Click "Conservative" → Click "Run Optimization"

### Aggressive Button
- Auto-sets: Volume objective, $2M budget
- Click "Aggressive" → Click "Run Optimization"

---

## What to Watch During Execution

### Progress Bar
- Starts at 0%
- Jumps to 15% (Data Loading)
- 30% (Agent A analyzing)
- 50% (Agent B generating calendar)
- 70-95% (Agent C validating, rejection loop)
- 100% (Complete!)

### Journey Log (Auto-scrolls)
Look for these key events:
```
STEP 1: DATA LOADING
[>] Loading sales data...
[+] Loaded 3,676 records

STEP 2: AGENT A (ANALYST)
[>] Using cached causal parameters
    baseline_velocity: 11,815
    price_elasticity: 6.91

STEP 3: REJECTION LOOP
[>] Iteration 1: Calendar composition
    ppgs: ['Brand 1_Promo.Group 20', ...]
    total_spend: $1,050,000

[!] Iteration 1: Top violations found
    violations: ['BUDGET: Exceeds limit']

[>] Iteration 2: Calendar composition
    total_spend: $980,000

[+] Iteration 2: No violations - APPROVED
```

### Results Panel (Appears when complete)
You'll see 4 metric cards:
- **Events:** Number of promotions
- **Total Spend:** How much budget used
- **MAPE:** Forecast accuracy (lower is better)
- **Iterations:** How many times B ↔ C looped

Plus a table showing first 10 calendar events

---

## Test Order Recommendation

**For first-time testing:**

1. **Start with Conservative** (fast, confirms everything works)
2. **Try Rejection Loop Demo** (best showcase of agents working)
3. **Run Volume vs Profit Comparison** (shows different strategies)

**For debugging/development:**

1. Conservative (quick validation)
2. Balanced (standard test)
3. Check run history works (reload previous runs)

**For presentation/demo:**

1. Rejection Loop Demo ($300K volume) - **shows the magic!**
   - Commentate: "Watch Agent B propose a calendar..."
   - "Agent C finds violations..."
   - "Agent B adjusts and tries again..."
   - "Finally approved after X iterations!"

---

## Expected Timing

| Test | Duration | Why |
|------|----------|-----|
| Conservative | 2 min | Small calendar, few constraints |
| Aggressive | 4 min | Large calendar, many iterations |
| Rejection Loop | 3 min | Multiple B ↔ C iterations |
| Balanced | 3 min | Standard complexity |
| Volume vs Profit | 6 min total | Two runs back-to-back |

**Note:** First run takes +30s (Agent A analyzes data), subsequent runs are faster (uses cache)

---

## Validation Checklist

After each test, verify:

✅ Progress bar reached 100%
✅ Status changed to "Optimization completed successfully!"
✅ Journey log shows all 7 steps
✅ Results panel shows 4 metrics
✅ Calendar table shows events
✅ Run appears in History panel (bottom)
✅ Can click run in history to reload it

---

## Common Values You'll See

### MAPE (Forecast Accuracy)
- ~50% = Good for promotional data (volatile)
- <40% = Excellent
- >70% = Check data quality

### Budget Utilization
- Conservative: 80-90%
- Aggressive: 95-100%
- Tight budget: 99-100%

### Iterations
- 1-2 = Easy constraints, well-optimized
- 3-5 = Normal, healthy rejection loop
- 6-10 = Tight constraints, agents working hard

### Calendar Events
- Conservative: 10-20
- Standard: 20-35
- Aggressive: 40-60

---

## Debugging Tips

**If nothing happens after clicking "Run Optimization":**
1. Check terminal running `python app.py`
2. Look for error messages
3. Verify ANTHROPIC_API_KEY is set

**If journey log says "Waiting for optimization to start...":**
1. Wait 5-10 seconds
2. Check terminal for "Starting optimization" message
3. Agent A may be loading data (takes 30s first time)

**If optimization fails:**
1. Check terminal output for full error
2. Common issues:
   - API key not set
   - Data files missing (case-data/)
   - Network issues (Claude API)

---

## Quick Copy-Paste Commands

**Start dashboard:**
```bash
cd "c:\Users\Will Powell\tiger_gen_ai\hackathon-tpo"
python app.py
```

**Set API key (if needed):**
```bash
set ANTHROPIC_API_KEY=your_key_here
```

**Open dashboard:**
```
http://localhost:5000
```

**Stop server:**
```
Ctrl+C in terminal
```

---

**Ready to test!** Start with Conservative, then try Rejection Loop Demo for the best showcase of the multi-agent system.
