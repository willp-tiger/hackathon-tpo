"""
TPO AI Agents - Interactive Dashboard Backend

Flask server providing API for running optimizations and viewing results.

Usage:
    python app.py

Then open: http://localhost:5000

Created: 2026-01-25 (Session 14)
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import threading
import uuid
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Import orchestrator
from src.orchestrator import TPOOrchestrator

app = Flask(__name__, static_folder='static')
CORS(app)

# Store active runs
active_runs: Dict[str, Dict[str, Any]] = {}
RUNS_DIR = Path("outputs/")
RUNS_DIR.mkdir(parents=True, exist_ok=True)


@app.route('/')
def index():
    """Serve the main dashboard."""
    return send_from_directory('static', 'dashboard.html')


@app.route('/api/run', methods=['POST'])
def run_optimization():
    """
    Start a new optimization run.

    Request JSON:
        {
            "objective": "volume" | "profit",
            "budget": 1000000
        }

    Returns:
        {"run_id": "uuid", "status": "started"}
    """
    try:
        params = request.json
        objective = params.get('objective', 'volume')
        budget = params.get('budget', 1000000)

        # Validate parameters
        if objective not in ['volume', 'profit']:
            return jsonify({'error': 'Invalid objective'}), 400

        if not (100000 <= budget <= 5000000):
            return jsonify({'error': 'Budget must be between $100K and $5M'}), 400

        # Generate run ID
        run_id = str(uuid.uuid4())[:8]  # Short ID for readability
        run_dir = RUNS_DIR / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        # Store run metadata
        active_runs[run_id] = {
            'status': 'running',
            'params': {
                'objective': objective,
                'budget': budget
            },
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'error': None
        }

        # Save metadata
        with open(run_dir / 'metadata.json', 'w') as f:
            json.dump(active_runs[run_id], f, indent=2)

        # Start optimization in background thread
        thread = threading.Thread(
            target=run_optimization_worker,
            args=(run_id, objective, budget, str(run_dir)),
            daemon=True
        )
        thread.start()

        return jsonify({
            'run_id': run_id,
            'status': 'started',
            'message': 'Optimization started successfully'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/status/<run_id>')
def get_status(run_id):
    """
    Get current status of a run.

    Returns:
        {
            "status": "running" | "completed" | "failed",
            "params": {...},
            "start_time": "...",
            "end_time": "...",
            "error": "..." (if failed)
        }
    """
    if run_id not in active_runs:
        # Try to load from disk
        metadata_file = RUNS_DIR / run_id / 'metadata.json'
        if metadata_file.exists():
            with open(metadata_file) as f:
                return jsonify(json.load(f))
        return jsonify({'error': 'Run not found'}), 404

    return jsonify(active_runs[run_id])


@app.route('/api/journey/<run_id>')
def get_journey(run_id):
    """
    Get live journey log for a run.

    Returns:
        {
            "journey": "...", (full text)
            "last_update": "..."
        }
    """
    journey_file = RUNS_DIR / run_id / 'OPTIMIZATION_JOURNEY.txt'

    if not journey_file.exists():
        return jsonify({
            'journey': 'Waiting for optimization to start...',
            'last_update': datetime.now().isoformat()
        })

    content = journey_file.read_text(encoding='utf-8')

    return jsonify({
        'journey': content,
        'last_update': datetime.now().isoformat(),
        'file_size': len(content)
    })


@app.route('/api/results/<run_id>')
def get_results(run_id):
    """
    Get final results for a run.

    Returns:
        {
            "calendar": {...},
            "summary": {...},
            "causal_params": {...}
        }
    """
    run_dir = RUNS_DIR

    if not run_dir.exists():
        return jsonify({'error': 'Run not found'}), 404

    results = {}

    # Load calendar
    calendar_file = run_dir / 'promotion_calendar.json'
    if calendar_file.exists():
        with open(calendar_file) as f:
            results['calendar'] = json.load(f)

    # Load causal parameters
    causal_file = run_dir / 'causal_parameters.json'
    if causal_file.exists():
        with open(causal_file) as f:
            results['causal_params'] = json.load(f)

    # Parse execution summary for key metrics
    summary_file = run_dir / 'EXECUTION_SUMMARY.txt'
    if summary_file.exists():
        summary_text = summary_file.read_text(encoding='utf-8')
        results['summary_text'] = summary_text

        # Extract key metrics
        import re
        metrics = {}
        if 'MAPE:' in summary_text:
            match = re.search(r'MAPE:\s*([\d.]+)%', summary_text)
            if match:
                metrics['mape'] = float(match.group(1))

        if 'Total Events:' in summary_text:
            match = re.search(r'Total Events:\s*(\d+)', summary_text)
            if match:
                metrics['total_events'] = int(match.group(1))

        if 'Total Spend:' in summary_text:
            match = re.search(r'Total Spend:\s*\$?([\d,]+)', summary_text)
            if match:
                metrics['total_spend'] = int(match.group(1).replace(',', ''))

        if 'Total Iterations:' in summary_text:
            match = re.search(r'Total Iterations:\s*(\d+)', summary_text)
            if match:
                metrics['total_iterations'] = int(match.group(1))

        results['metrics'] = metrics

    return jsonify(results)


@app.route('/api/runs')
def list_runs():
    """
    List all runs (past and present).

    Returns:
        {
            "runs": [
                {"run_id": "...", "status": "...", "params": {...}, ...}
            ]
        }
    """
    runs = []

    for run_dir in RUNS_DIR.iterdir():
        if run_dir.is_dir():
            metadata_file = run_dir / 'metadata.json'
            if metadata_file.exists():
                with open(metadata_file) as f:
                    metadata = json.load(f)
                    metadata['run_id'] = run_dir.name
                    runs.append(metadata)

    # Sort by start time (most recent first)
    runs.sort(key=lambda x: x.get('start_time', ''), reverse=True)

    return jsonify({'runs': runs})


def run_optimization_worker(run_id: str, objective: str, budget: int, run_dir: str):
    """
    Worker function to run optimization in background.

    Updates active_runs dict with status.
    """
    try:
        print(f"[Run {run_id}] Starting optimization: {objective}, ${budget:,}")

        # Initialize orchestrator
        orchestrator = TPOOrchestrator(
            output_dir=run_dir,
            max_iterations=10
        )

        # Run optimization (method is called 'run', not 'run_optimization')
        result = orchestrator.run(
            objective=objective,
            budget=budget
        )

        # Update status
        active_runs[run_id]['status'] = 'completed'
        active_runs[run_id]['end_time'] = datetime.now().isoformat()

        # Save metadata
        with open(Path(run_dir) / 'metadata.json', 'w') as f:
            json.dump(active_runs[run_id], f, indent=2)

        print(f"[Run {run_id}] Completed successfully")

    except Exception as e:
        print(f"[Run {run_id}] Failed: {str(e)}")

        active_runs[run_id]['status'] = 'failed'
        active_runs[run_id]['error'] = str(e)
        active_runs[run_id]['end_time'] = datetime.now().isoformat()

        # Save metadata
        with open(Path(run_dir) / 'metadata.json', 'w') as f:
            json.dump(active_runs[run_id], f, indent=2)


if __name__ == '__main__':
    print("=" * 70)
    print("  TPO AI Agents - Interactive Dashboard")
    print("=" * 70)
    print()
    print("  Server starting on http://localhost:5000")
    print("  Open this URL in your browser to use the dashboard")
    print()
    print("  Press Ctrl+C to stop the server")
    print("=" * 70)
    print()

    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
