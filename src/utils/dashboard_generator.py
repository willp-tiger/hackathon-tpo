"""
Dashboard Generator for TPO AI Agents Hackathon

Generates an interactive HTML dashboard from journey logs and optimization outputs.
Provides user-friendly visualization of agent decisions, rejection loop, and results.

Created: 2026-01-25 (Session 14)
Specification: docs/specs/dashboard_generator_spec.md
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


def generate_dashboard(
    journey_log_path: str = "outputs/OPTIMIZATION_JOURNEY.txt",
    execution_summary_path: str = "outputs/EXECUTION_SUMMARY.txt",
    calendar_path: str = "outputs/promotion_calendar.json",
    causal_params_path: str = "outputs/causal_parameters.json",
    output_path: str = "outputs/journey_dashboard.html"
) -> None:
    """
    Generate interactive HTML dashboard from optimization journey artifacts.

    Args:
        journey_log_path: Path to journey log file
        execution_summary_path: Path to execution summary report
        calendar_path: Path to promotion calendar JSON
        causal_params_path: Path to causal parameters JSON
        output_path: Path to save HTML dashboard
    """
    print(f"Generating dashboard from {journey_log_path}...")

    # Parse all input sources
    journey_data = parse_journey_log(journey_log_path) if Path(journey_log_path).exists() else {}
    summary_data = parse_execution_summary(execution_summary_path) if Path(execution_summary_path).exists() else {}
    calendar_data = load_json(calendar_path) if Path(calendar_path).exists() else {}
    causal_data = load_json(causal_params_path) if Path(causal_params_path).exists() else {}

    # Generate HTML
    html = create_dashboard_html(journey_data, summary_data, calendar_data, causal_data)

    # Write to file
    Path(output_path).write_text(html, encoding='utf-8')
    print(f"Dashboard saved: {output_path}")


def load_json(file_path: str) -> Dict[str, Any]:
    """Load JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def parse_journey_log(log_path: str) -> Dict[str, Any]:
    """
    Parse journey log into structured data.

    Returns:
        {
            'phases': [
                {
                    'step': 1,
                    'name': 'DATA LOADING',
                    'events': [
                        {'timestamp': '02:19:09', 'elapsed': '+0.0s', 'type': 'INFO', 'message': '...', 'details': '...'}
                    ]
                }
            ],
            'iterations': [
                {'iteration': 1, 'calendar_info': {...}, 'violations': [...]}
            ]
        }
    """
    content = Path(log_path).read_text(encoding='utf-8')

    phases = []
    iterations = []
    current_phase = None
    current_iteration_data = {}

    # Parse line by line
    for line in content.split('\n'):
        line = line.rstrip()

        # Detect phase headers
        if line.startswith('=' * 40):
            continue
        if line.startswith('STEP '):
            match = re.match(r'STEP (\d+): (.+)', line)
            if match:
                if current_phase:
                    phases.append(current_phase)
                current_phase = {
                    'step': int(match.group(1)),
                    'name': match.group(2),
                    'events': []
                }
            continue

        # Detect event lines
        event_match = re.match(r'\[(.)\] \[(\d{2}:\d{2}:\d{2}) \| (.+?)\] (.+)', line)
        if event_match and current_phase:
            event_type_icon = event_match.group(1)
            timestamp = event_match.group(2)
            elapsed = event_match.group(3)
            message = event_match.group(4)

            event_type = {'>': 'INFO', '+': 'SUCCESS', '!': 'WARNING', 'X': 'ERROR'}.get(event_type_icon, 'INFO')

            event = {
                'timestamp': timestamp,
                'elapsed': elapsed,
                'type': event_type,
                'message': message,
                'details': ''
            }
            current_phase['events'].append(event)

            # Check for iteration info
            if 'Iteration' in message and 'Calendar composition' in message:
                iter_match = re.search(r'Iteration (\d+)', message)
                if iter_match:
                    if current_iteration_data:
                        iterations.append(current_iteration_data)
                    current_iteration_data = {'iteration': int(iter_match.group(1)), 'calendar_info': {}, 'violations': []}

        # Detect detail lines (indented)
        elif line.startswith('    ') and current_phase and current_phase['events']:
            current_phase['events'][-1]['details'] += line.strip() + '\n'

            # Extract iteration details
            if current_iteration_data:
                if 'ppgs:' in line:
                    current_iteration_data['calendar_info']['ppgs'] = line.split(':', 1)[1].strip()
                elif 'ppg_count:' in line:
                    current_iteration_data['calendar_info']['ppg_count'] = line.split(':', 1)[1].strip()
                elif 'total_spend:' in line:
                    current_iteration_data['calendar_info']['total_spend'] = line.split(':', 1)[1].strip()
                elif 'violations:' in line and 'Top violations' in current_phase['events'][-1]['message']:
                    viols = line.split(':', 1)[1].strip()
                    current_iteration_data['violations'] = eval(viols) if viols.startswith('[') else [viols]

    # Add last phase
    if current_phase:
        phases.append(current_phase)
    if current_iteration_data:
        iterations.append(current_iteration_data)

    return {'phases': phases, 'iterations': iterations}


def parse_execution_summary(summary_path: str) -> Dict[str, Any]:
    """
    Parse execution summary report.

    Returns:
        {
            'config': {'objective': '...', 'budget': '...', 'timestamp': '...'},
            'metrics': {'mape': '...', 'iterations': '...', 'events': '...', 'spend': '...'},
            'insights': ['...']
        }
    """
    content = Path(summary_path).read_text(encoding='utf-8')

    data = {'config': {}, 'metrics': {}, 'insights': []}

    # Extract configuration
    if 'Objective:' in content:
        data['config']['objective'] = re.search(r'Objective:\s*(.+)', content).group(1).strip()
    if 'Budget:' in content:
        data['config']['budget'] = re.search(r'Budget:\s*\$?([\d,]+)', content).group(1).strip()
    if 'Timestamp:' in content:
        data['config']['timestamp'] = re.search(r'Timestamp:\s*(.+)', content).group(1).strip()

    # Extract metrics
    if 'MAPE:' in content:
        mape_match = re.search(r'MAPE:\s*([\d.]+)%', content)
        if mape_match:
            data['metrics']['mape'] = mape_match.group(1)

    if 'Total Iterations:' in content:
        iter_match = re.search(r'Total Iterations:\s*(\d+)', content)
        if iter_match:
            data['metrics']['iterations'] = iter_match.group(1)

    if 'Total Events:' in content:
        events_match = re.search(r'Total Events:\s*(\d+)', content)
        if events_match:
            data['metrics']['events'] = events_match.group(1)

    if 'Total Spend:' in content:
        spend_match = re.search(r'Total Spend:\s*\$?([\d,]+)', content)
        if spend_match:
            data['metrics']['spend'] = spend_match.group(1)

    # Extract key insights (look for numbered list or bullet points)
    insights_section = re.search(r'KEY INSIGHTS.+?(?=\n\n|\Z)', content, re.DOTALL)
    if insights_section:
        insight_lines = insights_section.group(0).split('\n')[2:]  # Skip header and separator
        for line in insight_lines:
            if line.strip() and (line.strip().startswith('-') or line.strip()[0].isdigit()):
                data['insights'].append(line.strip().lstrip('-0123456789. '))

    return data


def create_dashboard_html(
    journey_data: Dict[str, Any],
    summary_data: Dict[str, Any],
    calendar_data: Dict[str, Any],
    causal_data: Dict[str, Any]
) -> str:
    """Generate complete HTML dashboard."""

    # Extract key metrics
    config = summary_data.get('config', {})
    metrics = summary_data.get('metrics', {})
    phases = journey_data.get('phases', [])
    iterations = journey_data.get('iterations', [])
    calendar_events = calendar_data.get('calendar_events', [])

    # Build HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TPO AI Agents - Optimization Dashboard</title>
    <style>
        {get_css_styles()}
    </style>
</head>
<body>
    <div class="container">
        {create_header_html(config)}
        {create_executive_summary_html(metrics, config)}
        {create_timeline_html(phases)}
        {create_agent_a_summary_html(causal_data)}
        {create_rejection_loop_html(iterations)}
        {create_calendar_table_html(calendar_events)}
        {create_financial_impact_html(metrics)}
    </div>

    <script>
        {get_javascript()}
    </script>
</body>
</html>"""

    return html


def get_css_styles() -> str:
    """Return embedded CSS styles."""
    return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #F9FAFB;
            color: #111827;
            line-height: 1.6;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }

        header {
            background: linear-gradient(135deg, #1E40AF 0%, #3B82F6 100%);
            color: white;
            padding: 40px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        header .config {
            opacity: 0.9;
            font-size: 1.1em;
        }

        .section {
            background: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }

        .section h2 {
            font-size: 1.8em;
            color: #1E40AF;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #E5E7EB;
        }

        .cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }

        .card {
            background: linear-gradient(135deg, #F3F4F6 0%, #E5E7EB 100%);
            padding: 25px;
            border-radius: 10px;
            border-left: 5px solid #1E40AF;
        }

        .card h3 {
            font-size: 0.9em;
            color: #6B7280;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 10px;
        }

        .card .value {
            font-size: 2.2em;
            font-weight: bold;
            color: #1E40AF;
        }

        .card.success {
            border-left-color: #059669;
        }

        .card.success .value {
            color: #059669;
        }

        .card.warning {
            border-left-color: #D97706;
        }

        .card.warning .value {
            color: #D97706;
        }

        .timeline {
            position: relative;
            padding-left: 40px;
        }

        .timeline::before {
            content: '';
            position: absolute;
            left: 10px;
            top: 0;
            bottom: 0;
            width: 3px;
            background: #E5E7EB;
        }

        .timeline-item {
            position: relative;
            margin-bottom: 30px;
        }

        .timeline-item::before {
            content: '';
            position: absolute;
            left: -34px;
            top: 5px;
            width: 15px;
            height: 15px;
            border-radius: 50%;
            background: #1E40AF;
            border: 3px solid white;
            box-shadow: 0 0 0 3px #E5E7EB;
        }

        .timeline-header {
            cursor: pointer;
            padding: 15px;
            background: #F3F4F6;
            border-radius: 8px;
            transition: background 0.2s;
        }

        .timeline-header:hover {
            background: #E5E7EB;
        }

        .timeline-header h3 {
            font-size: 1.3em;
            color: #1E40AF;
        }

        .timeline-events {
            margin-top: 15px;
            padding-left: 20px;
            display: none;
        }

        .timeline-item.expanded .timeline-events {
            display: block;
        }

        .event {
            padding: 12px;
            margin-bottom: 10px;
            border-left: 3px solid #E5E7EB;
            background: #FAFAFA;
            border-radius: 4px;
        }

        .event.info {
            border-left-color: #3B82F6;
        }

        .event.success {
            border-left-color: #059669;
            background: #F0FDF4;
        }

        .event.warning {
            border-left-color: #D97706;
            background: #FFFBEB;
        }

        .event.error {
            border-left-color: #DC2626;
            background: #FEF2F2;
        }

        .event-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
        }

        .event-time {
            color: #6B7280;
            font-size: 0.9em;
        }

        .event-details {
            font-size: 0.9em;
            color: #4B5563;
            white-space: pre-wrap;
            margin-top: 8px;
            padding: 8px;
            background: white;
            border-radius: 4px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }

        thead {
            background: #F3F4F6;
        }

        th {
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #374151;
            border-bottom: 2px solid #E5E7EB;
        }

        td {
            padding: 12px;
            border-bottom: 1px solid #E5E7EB;
        }

        tbody tr:hover {
            background: #F9FAFB;
        }

        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }

        .badge.yes {
            background: #D1FAE5;
            color: #065F46;
        }

        .badge.no {
            background: #FEE2E2;
            color: #991B1B;
        }

        .iteration-box {
            background: #F9FAFB;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            border: 2px solid #E5E7EB;
        }

        .iteration-box h3 {
            color: #1E40AF;
            margin-bottom: 15px;
        }

        .iteration-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }

        .iteration-section {
            background: white;
            padding: 15px;
            border-radius: 6px;
        }

        .iteration-section h4 {
            color: #374151;
            margin-bottom: 10px;
            font-size: 1.1em;
        }

        .violation-item {
            padding: 8px;
            background: #FEF2F2;
            border-left: 3px solid #DC2626;
            margin-bottom: 8px;
            border-radius: 4px;
            font-size: 0.9em;
        }

        .params-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }

        .param-item {
            padding: 12px;
            background: #F9FAFB;
            border-radius: 6px;
        }

        .param-label {
            font-size: 0.9em;
            color: #6B7280;
            margin-bottom: 5px;
        }

        .param-value {
            font-size: 1.3em;
            font-weight: 600;
            color: #1E40AF;
        }

        @media (max-width: 768px) {
            .cards, .params-grid, .iteration-grid {
                grid-template-columns: 1fr;
            }

            header h1 {
                font-size: 1.8em;
            }

            .section {
                padding: 20px;
            }
        }
    """


def create_header_html(config: Dict[str, Any]) -> str:
    """Generate header section."""
    objective = config.get('objective', 'Unknown')
    budget = config.get('budget', 'N/A')
    timestamp = config.get('timestamp', 'N/A')

    return f"""
    <header>
        <h1>TPO AI Agents - Optimization Dashboard</h1>
        <div class="config">
            <strong>Objective:</strong> {objective} &nbsp;|&nbsp;
            <strong>Budget:</strong> ${budget} &nbsp;|&nbsp;
            <strong>Timestamp:</strong> {timestamp}
        </div>
    </header>
    """


def create_executive_summary_html(metrics: Dict[str, Any], config: Dict[str, Any]) -> str:
    """Generate executive summary section."""
    spend = metrics.get('spend', 'N/A')
    budget = config.get('budget', '1000000')
    iterations = metrics.get('iterations', 'N/A')
    events = metrics.get('events', 'N/A')
    mape = metrics.get('mape', 'N/A')

    # Calculate budget utilization
    try:
        budget_pct = int((int(spend.replace(',', '')) / int(budget.replace(',', ''))) * 100)
    except:
        budget_pct = 'N/A'

    return f"""
    <div class="section">
        <h2>Executive Summary</h2>
        <div class="cards">
            <div class="card">
                <h3>Total Spend</h3>
                <div class="value">${spend}</div>
            </div>
            <div class="card success">
                <h3>Budget Utilization</h3>
                <div class="value">{budget_pct}%</div>
            </div>
            <div class="card warning">
                <h3>Rejection Loop Iterations</h3>
                <div class="value">{iterations}</div>
            </div>
            <div class="card">
                <h3>Calendar Events</h3>
                <div class="value">{events}</div>
            </div>
            <div class="card success">
                <h3>Forecast MAPE</h3>
                <div class="value">{mape}%</div>
            </div>
        </div>
    </div>
    """


def create_timeline_html(phases: List[Dict[str, Any]]) -> str:
    """Generate interactive timeline section."""
    if not phases:
        return '<div class="section"><h2>Journey Timeline</h2><p>No journey data available.</p></div>'

    timeline_items = []
    for phase in phases:
        step = phase.get('step', '?')
        name = phase.get('name', 'Unknown')
        events = phase.get('events', [])

        events_html = []
        for event in events:
            event_type = event.get('type', 'INFO').lower()
            timestamp = event.get('timestamp', '')
            elapsed = event.get('elapsed', '')
            message = event.get('message', '')
            details = event.get('details', '').strip()

            details_html = f'<div class="event-details">{details}</div>' if details else ''

            events_html.append(f"""
            <div class="event {event_type}">
                <div class="event-header">
                    <span><strong>[{event_type.upper()}]</strong> {message}</span>
                    <span class="event-time">{timestamp} ({elapsed})</span>
                </div>
                {details_html}
            </div>
            """)

        timeline_items.append(f"""
        <div class="timeline-item">
            <div class="timeline-header" onclick="toggleTimeline(this)">
                <h3>STEP {step}: {name}</h3>
            </div>
            <div class="timeline-events">
                {''.join(events_html)}
            </div>
        </div>
        """)

    return f"""
    <div class="section">
        <h2>Journey Timeline</h2>
        <p style="margin-bottom: 20px; color: #6B7280;">Click on any phase to expand/collapse events</p>
        <div class="timeline">
            {''.join(timeline_items)}
        </div>
    </div>
    """


def create_agent_a_summary_html(causal_data: Dict[str, Any]) -> str:
    """Generate Agent A summary section."""
    if not causal_data:
        return '<div class="section"><h2>Agent A (Analyst) Summary</h2><p>No causal parameters available.</p></div>'

    baseline_velocity = causal_data.get('baseline_velocity_avg', 'N/A')
    elasticity = causal_data.get('elasticity_model', {}).get('base_price_elasticity', 'N/A')
    display_lift = causal_data.get('elasticity_model', {}).get('display_lift_multiplier', 'N/A')
    seasonality_weeks = len(causal_data.get('seasonality_factors', {}))

    return f"""
    <div class="section">
        <h2>Agent A (Analyst) Summary</h2>
        <div class="params-grid">
            <div class="param-item">
                <div class="param-label">Baseline Velocity (avg)</div>
                <div class="param-value">{baseline_velocity:,.0f}</div>
            </div>
            <div class="param-item">
                <div class="param-label">Price Elasticity</div>
                <div class="param-value">{elasticity}</div>
            </div>
            <div class="param-item">
                <div class="param-label">Display Lift Multiplier</div>
                <div class="param-value">{display_lift}</div>
            </div>
            <div class="param-item">
                <div class="param-label">Seasonality Coverage</div>
                <div class="param-value">{seasonality_weeks} weeks</div>
            </div>
        </div>
    </div>
    """


def create_rejection_loop_html(iterations: List[Dict[str, Any]]) -> str:
    """Generate rejection loop visualization."""
    if not iterations:
        return '<div class="section"><h2>Rejection Loop</h2><p>No iteration data available.</p></div>'

    iteration_boxes = []
    for iter_data in iterations:
        iter_num = iter_data.get('iteration', '?')
        calendar_info = iter_data.get('calendar_info', {})
        violations = iter_data.get('violations', [])

        ppgs = calendar_info.get('ppgs', 'N/A')
        ppg_count = calendar_info.get('ppg_count', 'N/A')
        total_spend = calendar_info.get('total_spend', 'N/A')

        violations_html = []
        for v in violations[:5]:  # Top 5
            violations_html.append(f'<div class="violation-item">{v}</div>')

        iteration_boxes.append(f"""
        <div class="iteration-box">
            <h3>Iteration {iter_num}</h3>
            <div class="iteration-grid">
                <div class="iteration-section">
                    <h4>Calendar Composition</h4>
                    <p><strong>PPG Count:</strong> {ppg_count}</p>
                    <p><strong>Total Spend:</strong> {total_spend}</p>
                    <p><strong>PPGs:</strong> {ppgs[:100]}...</p>
                </div>
                <div class="iteration-section">
                    <h4>Violations ({len(violations)})</h4>
                    {''.join(violations_html) if violations_html else '<p>No violations</p>'}
                </div>
            </div>
        </div>
        """)

    return f"""
    <div class="section">
        <h2>Rejection Loop</h2>
        {''.join(iteration_boxes)}
    </div>
    """


def create_calendar_table_html(calendar_events: List[Dict[str, Any]]) -> str:
    """Generate promotion calendar table."""
    if not calendar_events:
        return '<div class="section"><h2>Promotion Calendar</h2><p>No calendar events available.</p></div>'

    rows = []
    for event in calendar_events[:20]:  # Top 20 events
        week = event.get('week', 'N/A')
        ppg = event.get('ppg', 'N/A')
        retailer = event.get('retailer', 'N/A')
        discount = event.get('discount_depth', 0)
        display = event.get('display_active', False)
        reasoning = event.get('reasoning', 'N/A')

        display_badge = '<span class="badge yes">Yes</span>' if display else '<span class="badge no">No</span>'

        rows.append(f"""
        <tr>
            <td>{week}</td>
            <td>{ppg}</td>
            <td>{retailer}</td>
            <td>{int(discount * 100)}%</td>
            <td>{display_badge}</td>
            <td>{reasoning[:80]}...</td>
        </tr>
        """)

    return f"""
    <div class="section">
        <h2>Promotion Calendar</h2>
        <p style="margin-bottom: 15px; color: #6B7280;">Showing {len(rows)} of {len(calendar_events)} events</p>
        <table>
            <thead>
                <tr>
                    <th>Week</th>
                    <th>PPG</th>
                    <th>Retailer</th>
                    <th>Discount</th>
                    <th>Display</th>
                    <th>Reasoning</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
    </div>
    """


def create_financial_impact_html(metrics: Dict[str, Any]) -> str:
    """Generate financial impact section."""
    return f"""
    <div class="section">
        <h2>Financial Impact</h2>
        <p style="color: #6B7280;">Detailed financial analysis available in execution summary report.</p>
        <div class="cards">
            <div class="card">
                <h3>Total Spend</h3>
                <div class="value">${metrics.get('spend', 'N/A')}</div>
            </div>
            <div class="card success">
                <h3>Calendar Events</h3>
                <div class="value">{metrics.get('events', 'N/A')}</div>
            </div>
        </div>
    </div>
    """


def get_javascript() -> str:
    """Return embedded JavaScript."""
    return """
        function toggleTimeline(element) {
            const item = element.parentElement;
            item.classList.toggle('expanded');
        }

        // Auto-expand first timeline item
        document.addEventListener('DOMContentLoaded', function() {
            const firstItem = document.querySelector('.timeline-item');
            if (firstItem) {
                firstItem.classList.add('expanded');
            }
        });
    """


if __name__ == "__main__":
    # Test dashboard generation
    generate_dashboard()
    print("Dashboard generation complete!")
