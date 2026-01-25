# AI Agents Hackathon - Trade Promotion Optimization (TPO)

## Overview

This project implements a multi-agent system to automate trade promotion planning for CPG brands. The system uses AI agents to analyze historical data, generate optimized promotion calendars, and ensure compliance with business constraints.

## Business Context

Trade promotions represent one of the largest discretionary investments for CPG brands, directly impacting volume, margin, and retailer relationships. Yet promotion planning is still largely manual, backward-looking, and fragmented across functions, making it slow to adapt to changing consumer demand, competitive intensity, and macroeconomic conditions.

## Objective

- **Automate Strategy**: Move from manual, repetitive planning to autonomous, intelligent schedule generation
- **Optimize Trade-Offs**: Dynamically balance conflicting business goals (e.g., Volume vs. Profit) without human bias
- **Guarantee Feasibility**: Ensure every proposed plan is operationally executable and financially compliant by design
- **Build Trust**: Provide clear, human-readable reasoning for every automated decision

## Expected Outcomes

1. A 52-week execution-ready calendar optimized for the chosen objective
2. A "Reasoning Log" proving the agents negotiated the trade-offs between strategy and constraints
3. A Financial Validation report quantifying the impact against the baseline

## System Architecture

### Three-Agent System

#### Agent A: The Analyst (LLM-Powered Causal Inference Engine)
**Purpose**: The "Data Scientist" - uses Claude API to analyze historical data and generate causal parameters

**Implementation**: Uses Anthropic Python SDK with tool use for data analysis
- Claude reasons about which approaches to try (regression, averages, decomposition)
- Tools execute pandas/sklearn computations
- Claude validates MAPE < 15%, tries alternatives if needed
- Reasoning visible in agent_execution_log.txt

**Responsibilities**:
- Decompose historical sales into Baseline (Seasonality/Trend) and Incremental (Lift) volume
- Calculate Price Elasticity Coefficients for different discount depths (e.g., 15%, 20%, 30%)
- Quantify the impact of Display mechanics (Lift Multipliers)
- Self-validate outputs using quality thresholds

**Inputs**:

- `case-data/sales_v2.xlsx` (use 'Sales ' sheet with trailing space)
- `case-data/PromotionData.xlsx`

**Outputs** (saved via tool call):
```json
{
  "baseline_velocity_avg": 3014.94,
  "elasticity_model": {
    "base_price_elasticity": 1.29,
    "discount_lift_factors": {
      "depth_15_pct": 1.5,
      "depth_20_pct": 2.0,
      "depth_30_pct": 3.0
    },
    "display_lift_multiplier": 1.3
  },
  "approach_log": [
    {"approach": "regression", "mape": 0.31, "status": "ACCEPTED"}
  ]
}
```

#### Agent B: The Strategist (LLM-Powered Optimizer)
**Purpose**: The creative intelligence that constructs a future calendar meeting specific business objectives

**Implementation**: Uses Claude API with tools for calendar generation
- Claude selects SKUs, discount depths, weeks based on causal parameters
- Tools calculate costs and projected outcomes
- Claude responds to Auditor feedback by adjusting strategy
- Reasoning visible in rejection loop logs

**Responsibilities**:
- Ingest "Physics" from Agent A
- Generate promotion calendar optimized for Volume or Profit objective
- Iterate based on feedback from Agent C (Auditor)

**Inputs**:
- `causal_parameters.json` (from Agent A)
- Total budget limit
- `case-data/Promo_config.csv`
- Objective Prompt (Volume vs. Profit)

**Outputs**:
```json
{
  "objective": "Maximize Unit Volume (Market Share)",
  "total_projected_spend": 1150000,
  "calendar_events": [
    {
      "week": 12,
      "sku": "SKU_123",
      "discount_depth": 0.30,
      "display_active": true,
      "reasoning": "Selected 30% depth to maximize unit velocity during Q1 peak.",
      "projected_outcome": "Lift of 3.8x baseline."
    }
  ]
}
```

#### Agent C: The Auditor (LLM-Powered Compliance Validator)
**Purpose**: The "Controller" - strict validator with intelligent feedback

**Implementation**: Uses Claude API with validation tools
- Claude calls tools to check budget, gaps, frequency, blackout weeks
- Tools return violation lists
- Claude generates actionable feedback for Strategist
- Reasoning visible in audit reports

**Responsibilities**:
- Calculate Aggregate Spend (Sum of all weeks)
- Check if Aggregate Spend <= Total Budget
- Check Gap Rules, Frequency, and Slotting constraints
- Reject invalid plans with detailed, actionable feedback

**Inputs**:
- `draft_calendar_candidate.json` (from Agent B)
- `case-data/Constraints.json`
- `case-data/Finance.xlsx`

**Outputs**:
```json
{
  "status": "REJECTED",
  "violations": [
    {
      "type": "Total Budget Exceeded",
      "details": "Total Annual Spend $1.15M exceeds Budget Limit $1.0M by $150k."
    },
    {
      "type": "Gap Rule",
      "details": "Week 12 and 14 violate 4-week gap."
    }
  ],
  "feedback": "Reduce overall frequency or depth to bring Total Spend under $1.0M."
}
```

## Solution Flow

```
Sales.xlsx + PromotionData.xlsx
    |
    v
Agent A: The Analyst
(Causal Inference Engine)
    |
    v
Baseline & Elasticity Parameters
    |
    v
Agent B: The Strategist + Finance.xlsx
(Generate Calendar)
    |
    v
Draft Calendar + Reasoning
    |
    v
Agent C: The Auditor + Constraints.json
(Compliance & Finance)
    |
    +---> [REJECTED] --> Back to Agent B (Rejection Loop)
    |
    +---> [APPROVED]
    |
    v
Final Outputs:
- optimized_calendar.csv
- financial_impact_report.csv
- baseline_validation.csv
```

## Data Files

### Complete Dataset
| File | Purpose |
|------|---------|
| `Sales.xlsx` | Source of truth for historical performance and baseline calculation |
| `PromotionData.xlsx` | Defines available promotion tactics and their costs/mechanics at PPG level |
| `Finance.xlsx` | Unit economics for calculating profitability |
| `Promo_config.csv` | Fixed fee for display |
| `Constraints.json` | Rulebook for Agent C validation |

## Deliverables

### Artifacts (The "What")
1. **optimized_calendar.csv**: The final 52-week schedule
2. **financial_impact_report.json**: Summary comparing Base Plan vs. Optimized Plan across key metrics (Vol, Rev, Margin, Spend)
3. **baseline_validation.csv**: Forecast accuracy metrics (MAPE) for the holdout period

### Architecture Diagram
- **agent_execution_log.txt**: The conversation log showing the Rejection Loop (Strategist proposing → Auditor rejecting → Strategist correcting)
- **prompts_tested.md**: The system prompts used to switch objectives

### Video Demo (2-3 mins)
- Show the code running
- Highlight the Auditor catching a violation and the Strategist fixing it
- Briefly explain the strategy chosen

## Judging Criteria

### Architecture & Agentic Design (40%)
- **The Feedback Loop**: Does the log prove the system is self-correcting?
- **Separation of Concerns**: Are the agents distinct?
- **Modularity**: Can objectives be swapped while the architecture holds up?

### Technical Implementation (40%)
- **Financial Rigor**: Accurate calculation of Variable Spend (TPR) vs. Fixed Spend (Display)
- **Constraint Obedience**: Zero violations in the final file
- **Baseline Quality**: High accuracy (Low MAPE) on holdout validation set

### User Experience & Reporting (20%)
- **Explainability**: Clear articulation of why the plan meets the objective
- **Impact Visibility**: Clear "Before vs. After" view
- **Clarity**: Easy for business users to digest

## Installation

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Unix/MacOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Run the full pipeline
python main.py --objective volume --budget 1000000

# Or for profit optimization
python main.py --objective profit --budget 1000000
```

## Project Status

**Current Phase**: Agent B (Strategist) Implementation
**Completed**: ✅ Agent A (Analyst), ✅ Agent C (Auditor)
**Branch**: `dev-claude-agent-b`

### Implementation Progress

- **Agent A**: Complete (50.38% MAPE, tier-specific display lifts, 52-week seasonality)
- **Agent C**: Complete (100% constraint validation accuracy, 7 test fixtures)
- **Agent B**: Specification complete, implementation in progress
- **Integration**: Pending (Agent A → B → C feedback loop)

## Project Structure

```
hackathon-tpo/
├── case-data/              # Input data files
│   ├── sales_v2.xlsx      # Historical sales (PPG level) ⚠️ Use 'Sales ' sheet
│   ├── PromotionData.xlsx # Promotion tactics and TPR
│   ├── Finance.xlsx       # Unit economics
│   ├── Promo_config.csv   # Display fees
│   └── Constraints.json   # Validation rules (fixed JSON)
├── docs/                   # Documentation
│   ├── specs/             # Agent specifications
│   │   ├── agent_a_analyst_spec.md
│   │   ├── agent_b_strategist_spec.md (NEW)
│   │   └── agent_c_auditor_spec.md
│   ├── archive/           # Historical session docs
│   ├── PROMOTION_CALENDAR_RESEARCH.md (NEW)
│   ├── CONSTRAINT_VALIDATION_RESEARCH.md (NEW)
│   ├── DATA_SCHEMA.md
│   └── case-study-instructions.pptx
├── src/                    # Source code
│   ├── agents/            # Agent implementations
│   │   ├── analyst.py     # ✅ Agent A: Complete
│   │   ├── strategist.py  # 🔄 Agent B: In progress
│   │   └── auditor.py     # ✅ Agent C: Complete
│   └── utils/             # Utility functions
│       └── data_loader.py
├── outputs/               # Generated outputs
│   ├── causal_parameters.json
│   ├── agent_a_execution_log.txt
│   ├── agent_c_execution_log.txt
│   └── test_summary.md
├── tests/                 # Unit tests
│   ├── fixtures/          # Test calendars (7 files)
│   ├── test_agent_a_complete.py
│   └── test_agent_c_auditor.py
├── requirements.txt       # Python dependencies
├── main.py               # Entry point (orchestrator TBD)
├── CLAUDE.md             # Development guide (streamlined)
└── README.md             # This file
```

## Development Notes

- **ALL AGENTS USE CLAUDE API** - This is mandatory for judging criteria (40% of score)
- **Model**: `claude-3-7-sonnet-20250219` (latest as of Jan 2025)
- All agents must be modular and independently testable
- The rejection loop between Agent B and Agent C is critical for demonstrating agentic behavior
- Financial calculations must be precise and auditable (tools handle computation, Claude handles reasoning)
- All decisions must be logged with clear reasoning (Claude's natural language explanations)
- Visible agent interactions in logs are required for demo and judging
- **Data Granularity**: All operations at PPG-Retailer-Week level (11 PPGs × 2 Retailers)

## Architecture Pattern

Each agent follows this pattern:

```python
from anthropic import Anthropic

class AgentX:
    def __init__(self):
        self.client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self.tools = [...]  # Define tools for this agent
        self.system_prompt = "..."  # Define agent behavior

    def execute(self, input_data):
        """Run LLM-powered reasoning with tool use."""
        messages = [{"role": "user", "content": "Task description"}]

        while True:
            response = self.client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=4096,
                system=self.system_prompt,
                tools=self.tools,
                messages=messages
            )

            if response.stop_reason == "tool_use":
                # Execute tools, append results, continue
                pass
            else:
                # Extract final output
                break

        return result
```

## License

Confidential - AI Agents Hackathon 2025
