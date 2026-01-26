# Interactive Dashboard Specification (REVISED)

## Purpose

Create a **web-based interactive interface** that allows users to:
- Configure optimization parameters (objective, budget, constraints)
- Launch optimization runs
- Monitor progress in real-time
- View and compare results
- Adjust parameters and re-run

This replaces the static report viewer with a true user interface.

## User Workflow

```
1. User opens dashboard (http://localhost:5000)
2. User sets parameters:
   - Objective: Volume or Profit
   - Budget: $100K - $2M
   - Constraints: Gap rules, frequency limits, blackout weeks
3. User clicks "Run Optimization"
4. Dashboard shows:
   - Real-time progress (which agent is running)
   - Live journey log updates
   - Iteration-by-iteration rejection loop
5. Results displayed:
   - Final calendar (interactive table)
   - Financial metrics
   - Agent reasoning
6. User can:
   - Adjust parameters
   - Re-run optimization
   - Compare runs
   - Export results
```

## Architecture

### Backend (Flask)

**File**: `app.py`

**Endpoints**:
- `GET /` - Serve dashboard HTML
- `POST /api/run` - Start optimization (async)
- `GET /api/status/<run_id>` - Get run status
- `GET /api/journey/<run_id>` - Get live journey log
- `GET /api/results/<run_id>` - Get final results
- `GET /api/runs` - List all runs

**Technology**:
- Flask + Flask-CORS
- Background jobs with threading
- File-based storage (outputs/runs/<run_id>/)

### Frontend (React-style with vanilla JS)

**File**: `static/dashboard.html`

**Components**:
1. **Configuration Panel** (left sidebar)
   - Objective selector (volume/profit)
   - Budget slider ($100K - $2M)
   - Constraints form (gap rules, frequency, blackout weeks)
   - Run button

2. **Progress Monitor** (center top)
   - Current step indicator (1-7)
   - Progress bar
   - Live status text
   - Elapsed time

3. **Journey Log** (center main)
   - Auto-scrolling log viewer
   - Phase-organized sections
   - Event type filtering (INFO/SUCCESS/WARNING/ERROR)
   - Iteration details

4. **Results Panel** (right sidebar)
   - Key metrics cards
   - Calendar preview (first 10 events)
   - Export buttons (JSON/CSV)
   - View full report link

5. **Run History** (bottom)
   - Table of past runs
   - Load previous run results
   - Compare runs

## Technical Implementation

### Backend Structure

```python
# app.py
from flask import Flask, request, jsonify, send_from_directory
import threading
import uuid
from pathlib import Path
from src.orchestrator import TPOOrchestrator

app = Flask(__name__)

# Store active runs
active_runs = {}

@app.route('/')
def index():
    return send_from_directory('static', 'dashboard.html')

@app.route('/api/run', methods=['POST'])
def run_optimization():
    # Parse request
    params = request.json
    run_id = str(uuid.uuid4())

    # Create run directory
    run_dir = Path(f"outputs/runs/{run_id}")
    run_dir.mkdir(parents=True, exist_ok=True)

    # Start optimization in background thread
    thread = threading.Thread(
        target=run_optimization_worker,
        args=(run_id, params, run_dir)
    )
    thread.start()

    active_runs[run_id] = {
        'status': 'running',
        'params': params,
        'thread': thread
    }

    return jsonify({'run_id': run_id})

@app.route('/api/status/<run_id>')
def get_status(run_id):
    # Return current status
    journey_file = Path(f"outputs/runs/{run_id}/OPTIMIZATION_JOURNEY.txt")
    if journey_file.exists():
        content = journey_file.read_text()
        return jsonify({
            'status': active_runs.get(run_id, {}).get('status', 'unknown'),
            'journey': content
        })
    return jsonify({'status': 'unknown'})

@app.route('/api/results/<run_id>')
def get_results(run_id):
    # Return final results
    calendar_file = Path(f"outputs/runs/{run_id}/promotion_calendar.json")
    if calendar_file.exists():
        with open(calendar_file) as f:
            calendar = json.load(f)
        return jsonify(calendar)
    return jsonify({'error': 'Results not ready'})

def run_optimization_worker(run_id, params, run_dir):
    try:
        orchestrator = TPOOrchestrator(output_dir=str(run_dir))
        result = orchestrator.run_optimization(
            objective=params['objective'],
            budget=params['budget']
        )
        active_runs[run_id]['status'] = 'completed'
    except Exception as e:
        active_runs[run_id]['status'] = 'failed'
        active_runs[run_id]['error'] = str(e)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

### Frontend Structure

```html
<!-- static/dashboard.html -->
<!DOCTYPE html>
<html>
<head>
    <title>TPO AI Agents - Interactive Dashboard</title>
    <style>/* Modern CSS grid layout */</style>
</head>
<body>
    <div class="dashboard">
        <!-- Configuration Panel -->
        <div class="config-panel">
            <h2>Configuration</h2>
            <form id="config-form">
                <label>Objective:</label>
                <select name="objective">
                    <option value="volume">Maximize Volume</option>
                    <option value="profit">Maximize Profit</option>
                </select>

                <label>Budget: $<span id="budget-value">1,000,000</span></label>
                <input type="range" name="budget" min="100000" max="2000000" step="50000" value="1000000">

                <button type="submit">Run Optimization</button>
            </form>
        </div>

        <!-- Progress Monitor -->
        <div class="progress-panel">
            <div class="progress-bar"></div>
            <div class="status-text">Ready to run</div>
        </div>

        <!-- Journey Log -->
        <div class="journey-panel">
            <h2>Journey Log</h2>
            <div id="journey-log" class="log-viewer"></div>
        </div>

        <!-- Results -->
        <div class="results-panel">
            <h2>Results</h2>
            <div id="results-content">No results yet</div>
        </div>
    </div>

    <script src="/static/dashboard.js"></script>
</body>
</html>
```

### JavaScript (Polling for Updates)

```javascript
// static/dashboard.js
let currentRunId = null;
let pollingInterval = null;

document.getElementById('config-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const params = {
        objective: e.target.objective.value,
        budget: parseInt(e.target.budget.value)
    };

    // Start optimization
    const response = await fetch('/api/run', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(params)
    });

    const data = await response.json();
    currentRunId = data.run_id;

    // Start polling for updates
    startPolling();
});

function startPolling() {
    pollingInterval = setInterval(async () => {
        const response = await fetch(`/api/status/${currentRunId}`);
        const data = await response.json();

        // Update journey log
        document.getElementById('journey-log').textContent = data.journey;

        // Check if complete
        if (data.status === 'completed') {
            stopPolling();
            loadResults();
        }
    }, 2000); // Poll every 2 seconds
}

async function loadResults() {
    const response = await fetch(`/api/results/${currentRunId}`);
    const data = await response.json();

    // Display results
    displayResults(data);
}
```

## File Structure

```
hackathon-tpo/
├── app.py                          # Flask backend
├── static/
│   ├── dashboard.html              # Main UI
│   ├── dashboard.js                # Frontend logic
│   └── dashboard.css               # Styling
├── outputs/
│   └── runs/
│       ├── <run_id_1>/             # Run-specific outputs
│       │   ├── promotion_calendar.json
│       │   ├── OPTIMIZATION_JOURNEY.txt
│       │   └── ...
│       └── <run_id_2>/
└── requirements.txt                # Add Flask dependencies
```

## Key Features

1. **Live Progress Monitoring**
   - Real-time journey log updates
   - Progress bar showing current step
   - Elapsed time counter

2. **Interactive Configuration**
   - Budget slider with live preview
   - Constraint editor
   - Parameter presets (conservative/aggressive)

3. **Results Visualization**
   - Calendar table (sortable/filterable)
   - Metrics comparison (base vs optimized)
   - Download options (JSON/CSV/PDF)

4. **Run History**
   - Save all runs
   - Compare multiple runs side-by-side
   - Reload previous configurations

5. **Error Handling**
   - Show validation errors before running
   - Display agent errors clearly
   - Retry failed runs

## Success Criteria

1. User can configure and run optimization without command line
2. Progress visible in real-time (2s update interval)
3. Results displayed immediately upon completion
4. Can run multiple optimizations and compare
5. Works in Chrome/Firefox/Edge
6. No page refresh needed (SPA behavior)

## Timeline

- Backend API: 1 hour
- Frontend UI: 2 hours
- Integration & testing: 1 hour
- **Total: 4 hours**

---

**Created**: 2026-01-25 (Session 14 - Revised)
**Replaces**: Static dashboard concept
**Status**: Ready for implementation
