# TPO AI Agents Hackathon - Development Guide

## Project Overview

This is a **multi-agent LLM system** for Trade Promotion Optimization (TPO) built for the AI Agents Hackathon. The system uses **Claude API** to power three autonomous agents that collaborate through an iterative feedback loop to generate optimized 52-week promotion calendars.

## ⚠️ CRITICAL ARCHITECTURE REQUIREMENT

**ALL THREE AGENTS MUST BE LLM-POWERED USING CLAUDE API.**

This is not optional. The judging criteria allocates 40% of the score to "Architecture & Agentic Design", which explicitly evaluates:
- **Agent autonomy and decision-making** (LLM reasoning, not hardcoded logic)
- **Visible agent interactions in logs** (shows Claude's reasoning process)
- **Appropriate use of agentic patterns** (tool use, multi-turn conversations)

**Hardcoded Python classes with pandas/sklearn logic = 0/40 points.**

## Agent Architecture: LLM-Powered Reasoning

### Agent A: The Analyst (LLM-Powered Data Scientist)

**Implementation**: Uses Anthropic Python SDK with tool use for data analysis.

```python
from anthropic import Anthropic

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

class AnalystAgent:
    def analyze(self, sales_data, promo_data):
        """Agent A uses Claude to reason about data and call analysis tools."""

        tools = [
            {
                "name": "load_sales_preview",
                "description": "Load sales data and return first 10 rows for inspection",
                "input_schema": {"type": "object", "properties": {}}
            },
            {
                "name": "calculate_baseline_regression",
                "description": "Calculate baseline using regression approach",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "features": {"type": "array", "items": {"type": "string"}},
                        "validation_weeks": {"type": "number"}
                    }
                }
            },
            {
                "name": "calculate_baseline_sku_averages",
                "description": "Calculate baseline using SKU-specific averages",
                "input_schema": {"type": "object", "properties": {}}
            },
            {
                "name": "validate_forecast_mape",
                "description": "Validate baseline forecast and return MAPE",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "baseline_values": {"type": "object"},
                        "holdout_weeks": {"type": "number"}
                    }
                }
            },
            {
                "name": "save_causal_parameters",
                "description": "Save final causal parameters to JSON",
                "input_schema": {
                    "type": "object",
                    "properties": {"parameters": {"type": "object"}}
                }
            }
        ]

        system_prompt = """You are Agent A, a professional data scientist analyzing trade promotion data.

Your task: Generate causal parameters for promotion optimization.

Approach:
1. Conduct EDA first - load data preview, understand distributions
2. Try multiple approaches for baseline forecasting:
   - Regression-based (most sophisticated)
   - SKU-specific averages (more robust)
   - Global average (fallback)
3. Validate each approach with MAPE on holdout data
4. NEVER accept MAPE > 15% without trying all approaches
5. Calculate elasticity, display lift, seasonality
6. Save final parameters with approach_log documenting what you tried

Use tools iteratively. Be methodical. Explain your reasoning at each step."""

        messages = [
            {
                "role": "user",
                "content": f"Analyze sales data and generate causal parameters. Sales data has {len(sales_data)} records."
            }
        ]

        # Multi-turn conversation with tool use
        while True:
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                system=system_prompt,
                tools=tools,
                messages=messages
            )

            # Process tool calls
            if response.stop_reason == "tool_use":
                # Execute tools, add results to messages
                # Continue conversation
                pass
            elif response.stop_reason == "end_turn":
                # Extract final parameters
                break

        return causal_parameters
```

**Key Behaviors (Guided by System Prompt)**:
1. **Exploration First**: Claude conducts EDA before modeling
2. **Multiple Approaches**: Claude tries different methods, validates each
3. **Quality Gates**: Claude checks MAPE < 15%, tries alternatives if needed
4. **Explainability**: Claude documents reasoning in natural language
5. **Tool Use**: Claude calls Python functions for actual computation

**Why LLM vs. Hardcoded**:
- ✅ **Reasoning visible in logs** (critical for judging)
- ✅ **Adaptive to data quality** (handles edge cases intelligently)
- ✅ **Natural language explanations** (better than code comments)
- ✅ **True agent autonomy** (makes decisions, not just executes)

### Agent B: The Strategist (LLM-Powered Optimizer)

**Implementation**: Uses Claude API with tools for calendar generation and adjustment.

**System Prompt Philosophy**:
```
You are Agent B, the strategist. Your goal is to generate a 52-week promotion calendar.

Objective: {volume or profit}
Budget: ${budget}

You have causal parameters from Agent A. Use them to:
1. Select high-leverage SKUs (high elasticity for volume, high margin for profit)
2. Choose optimal discount depths using lift factors
3. Schedule in high-seasonality weeks
4. Add displays where ROI is positive
5. Stay within budget

If Auditor rejects your plan:
- Read violations carefully
- Make MATERIAL adjustments (not cosmetic)
- Explain what you changed and why

Generate calendar as JSON with reasoning for each promotion.
```

**Tools**:
- `calculate_promotion_lift()` - Estimate lift for SKU + discount + display
- `calculate_promotion_cost()` - Calculate TPR + display costs
- `save_draft_calendar()` - Save calendar proposal as JSON

**Rejection Loop**: Auditor feedback added to message history, Claude adjusts calendar.

### Agent C: The Auditor (LLM-Powered Validator)

**Implementation**: Uses Claude API with tools for constraint validation.

**System Prompt Philosophy**:
```
You are Agent C, the compliance auditor. You are STRICT and DETERMINISTIC.

Validate the calendar against these constraints:
1. Budget: Total spend <= ${budget}
2. Gap rules: Min {X} weeks between promos for same SKU
3. Frequency: Max {Y} promos per SKU per year
4. Blackout weeks: No promos in weeks {list}
5. Financial: No negative margins

If ANY violation exists: Status = REJECTED
If zero violations: Status = APPROVED

Provide detailed feedback for each violation to help Strategist fix issues.
```

**Tools**:
- `calculate_total_spend()` - Sum TPR + display costs across calendar
- `check_gap_violations()` - Check spacing between promotions per SKU
- `check_frequency_violations()` - Count promos per SKU
- `save_audit_report()` - Save audit results as JSON

## Critical Agent SDK Patterns

### 1. Tool Definition

Each agent has 4-6 tools that execute Python logic. Claude decides WHEN and HOW to call them.

```python
tools = [
    {
        "name": "tool_name",
        "description": "What this tool does (Claude reads this)",
        "input_schema": {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "What param1 means"}
            },
            "required": ["param1"]
        }
    }
]
```

### 2. Multi-Turn Conversations (Rejection Loop)

```python
# Agent B initial proposal
messages = [{"role": "user", "content": "Generate promotion calendar"}]
response_b = client.messages.create(..., messages=messages)

# Agent C audits
messages.append({"role": "assistant", "content": response_b.content})
messages.append({"role": "user", "content": f"Audit this calendar: {calendar_json}"})
response_c = client.messages.create(..., messages=messages)

# If rejected, Agent B adjusts
if audit_status == "REJECTED":
    messages.append({"role": "assistant", "content": response_c.content})
    messages.append({"role": "user", "content": f"Calendar rejected. Violations: {violations}. Regenerate."})
    response_b = client.messages.create(..., messages=messages)
    # Loop continues...
```

### 3. Structured Outputs

Use tool schemas to enforce JSON structure:

```python
{
    "name": "save_calendar",
    "description": "Save calendar in required format",
    "input_schema": {
        "type": "object",
        "properties": {
            "calendar_events": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "week": {"type": "number"},
                        "sku": {"type": "string"},
                        "discount_depth": {"type": "number"},
                        "display_active": {"type": "boolean"},
                        "reasoning": {"type": "string"}
                    },
                    "required": ["week", "sku", "discount_depth", "display_active", "reasoning"]
                }
            }
        }
    }
}
```

## Data Files

Located in `case-data/`:

- `Sales.xlsx` - Historical sales (source of truth) - **Use 'Sales' sheet**
- `PromotionData.xlsx` - Promotion tactics and costs
- `Finance.xlsx` - Unit economics - **Warning: Avg Price has errors, use List Price**
- `Promo_config.csv` - Display fees
- `Constraints.json` - Validation rules - **Note: Malformed JSON, hardcoded in DataLoader**

**Complete Schema Documentation**: See [docs/DATA_SCHEMA.md](docs/DATA_SCHEMA.md) for full details

## Project Standards

### Code Style

- **Python Style**: PEP 8 compliant, type hints required
- **Docstrings**: Google-style docstrings for all classes and functions
- **Logging**: Use loguru for all logging, appropriate levels (DEBUG/INFO/WARNING/ERROR)
- **Error Handling**: Explicit error handling with informative messages

### Agent Communication Format

All inter-agent communication uses **JSON**:

```python
# Agent A output (saved by tool call)
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
  "seasonality_factors": {1: 0.87, 2: 0.95, ...},
  "approach_log": [
    {"approach": "regression", "mape": 0.31, "status": "ACCEPTED"}
  ]
}

# Agent B output
{
  "objective": "Maximize Unit Volume",
  "total_projected_spend": 950000,
  "budget_limit": 1000000,
  "iteration": 1,
  "calendar_events": [
    {
      "week": 12,
      "sku": "APN_123",
      "discount_depth": 0.30,
      "display_active": true,
      "reasoning": "High elasticity SKU during peak seasonality week",
      "projected_outcome": "3.8x baseline lift"
    }
  ]
}

# Agent C output
{
  "status": "REJECTED",
  "violations": [
    {
      "type": "Gap Rule Violation",
      "details": "Week 12 and 14 for APN_123 violate 4-week gap",
      "severity": "high"
    }
  ],
  "feedback": "Increase spacing between promotions to meet minimum gap requirements."
}
```

## Output Requirements

Must generate in `outputs/`:
1. `optimized_calendar.csv` - 52-week schedule
2. `financial_impact_report.json` - Base vs. Optimized comparison
3. `baseline_validation.csv` - Forecast accuracy (MAPE)
4. `agent_execution_log.txt` - Full conversation log showing rejection loop

## Progress Tracking

### Phase 0: Project Setup ✅ COMPLETE

- ✅ Initial skeleton code created
- ✅ Git repository initialized
- ❌ **INCORRECT**: Implemented agents as Python classes instead of LLM agents
- ⚠️ **REQUIRES REBUILD**: All three agents need to be rewritten

### Phase 1: Data Exploration ✅ COMPLETE

- ✅ Comprehensive data quality assessment performed
- ✅ Schema documented in [docs/DATA_SCHEMA.md](docs/DATA_SCHEMA.md)
- ✅ Validation script created: `scripts/validate_data.py`

### Phase 2: Agent A Implementation 🔄 IN PROGRESS (REBUILD REQUIRED)

**Status**: Previous implementation was hardcoded Python logic. **MUST REBUILD AS LLM AGENT.**

**New Approach**:
1. Delete `src/agents/analyst.py` (757 lines of wrong approach)
2. Create new `AnalystAgent` class with:
   - `self.client = Anthropic()`
   - System prompt defining data scientist behavior
   - Tools for: load_data, calculate_baseline, run_regression, validate_mape, save_parameters
   - `.analyze()` method that runs multi-turn Claude conversation
3. Test with actual API calls to verify:
   - Claude tries multiple approaches
   - Reasoning appears in logs
   - Tools get called correctly
   - MAPE validation works

### Future Phases (See [ROADMAP.md](ROADMAP.md))

- **Phase 3: Agent C Implementation** (LLM-based, before Agent B)
- **Phase 4: Agent B Implementation** (LLM-based with rejection loop)
- **Phase 5: Integration & Orchestration**
- **Phase 6: Deliverables Generation**
- **Phase 7: Testing & QA**
- **Phase 8: Demo Preparation**

### Known Issues

**CRITICAL: Incorrect Architecture Implemented**

All three agents were implemented as deterministic Python classes instead of LLM-powered agents. This violates the core requirement and will score 0/40 on "Architecture & Agentic Design".

**Files to Delete**:
- `src/agents/analyst.py` (757 lines of hardcoded logic)
- `test_agent_a.py` (tests wrong implementation)
- `debug_agent_a.py` (tests wrong implementation)
- `outputs/causal_parameters.json` (from wrong implementation)

**Rebuild Required**: All agents must be rewritten to use Claude API with tool use.

### Architecture Decisions

- ✅ Using Anthropic Python SDK for all agents
- ✅ Tool use pattern for agent-data interaction
- ✅ Multi-turn conversations for rejection loop
- ✅ Rejection loop capped at 10 iterations (configurable)
- ✅ Logging both to console and file for transparency
- ✅ JSON schema validation for all inter-agent messages
- ✅ Single-purpose conversations (one phase per session)
- ✅ Context transfer via CLAUDE.md updates

## Development Commands

```bash
# Setup
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Set API key
set ANTHROPIC_API_KEY=your_key_here  # Windows
# OR
export ANTHROPIC_API_KEY=your_key_here  # Unix

# Run optimization
python main.py --objective volume --budget 1000000
python main.py --objective profit --budget 1500000

# With debug logging (to see Claude's reasoning)
python main.py --objective volume --budget 1000000 --log-level DEBUG

# Testing
pytest tests/ -v
pytest tests/ --cov=src --cov-report=html
```

## Important Notes

- **The rejection loop is the key differentiator**: A valid first-try calendar scores LOW
- **Explainability > Optimization**: Better to show clear reasoning than marginal gains
- **Separation of concerns matters**: Agent A analyzes, Agent B strategizes, Agent C validates (no crossover)
- **Every decision needs a "why"**: Reasoning strings are not optional
- **LLM reasoning must be visible**: agent_execution_log.txt should show Claude's thought process

---

## Session Summary (2026-01-23 - Session 2)

### What Was Completed ✅

1. **LLM-Powered Agent A Implementation - COMPLETE**
   - Created [src/agents/analyst.py](src/agents/analyst.py) (~650 lines) using Anthropic Python SDK
   - 10 tool definitions for data analysis (load, calculate baseline, validate, elasticity, display, seasonality)
   - Multi-turn conversation loop (16 iterations in test run)
   - System prompt guiding methodical data science approach

2. **Real Data Calculations - 100% VERIFIED**
   - ✅ Elasticity calculated from actual TPR column (discount buckets: 0-15%, 15-25%, 25-35%, 35-45%, 45%+)
   - ✅ Display lift calculated by merging PromotionData.xlsx display columns with sales data (2.04x)
   - ✅ Seasonality factors calculated from historical weekly sales patterns (52 weeks)
   - ✅ Baseline using regression/SKU averages/global average from actual sales data
   - ❌ **NO dummy/industry standard values** - all calculations from real data

3. **Agent Autonomy Demonstrated**
   - Tried 3 baseline approaches (regression, SKU averages, global average)
   - Validated each with 12-week holdout (MAPE: 185-220%)
   - Autonomously decided to retry with 6-week holdout
   - Re-validated all 3 approaches with new parameters
   - Made reasoned decision to use regression approach despite high MAPE
   - Documented 6 attempts in approach_log with clear reasoning

4. **Outputs Generated**
   - [outputs/causal_parameters.json](outputs/causal_parameters.json) (3,148 bytes)
     - Baseline velocity: 3,014.94 units
     - Price elasticity: 12.27
     - Discount lift factors (5 buckets from real data)
     - Display lift: 2.04x
     - 52-week seasonality factors
     - approach_log with 6 documented attempts
     - model_quality_warning (transparency about MAPE issues)
   - [outputs/agent_a_execution_log.txt](outputs/agent_a_execution_log.txt) (141 lines)
     - Shows Claude's reasoning at each iteration
     - Visible tool calls and decisions
     - Perfect for judging criteria: "Visible agent interactions in logs"

5. **Testing**
   - Created [test_agent_a_llm.py](test_agent_a_llm.py)
   - Verified end-to-end execution (~13 minutes)
   - All tools working correctly
   - JSON output validated

### Known Issues ⚠️

1. **High MAPE Values (185-265%)**
   - All baseline approaches show very high error rates
   - Indicates data quality issues or missing factors
   - Agent correctly identifies and documents this limitation
   - **REQUIRES RESEARCH**: Need to investigate alternative baseline calculation methods

2. **Approach Concerns**
   - Current baseline methods may be too simplistic for this data
   - Elasticity calculation is basic (% change in qty / % change in price)
   - Lift calculation doesn't account for confounding factors
   - **NEXT SESSION FOCUS**: Research and implement more sophisticated approaches

### What's Next ⏭️

**Next Session Goal**: "Research and implement improved baseline & lift calculation methods"

**Priority Tasks**:
1. **Research Alternative Baseline Approaches**:
   - Time series decomposition (STL, seasonal decomposition)
   - More sophisticated regression (ARIMAX, SARIMAX)
   - Causal inference methods (difference-in-differences, synthetic control)
   - Mixed effects models (account for SKU-level and time effects)
   - Quantile regression for robustness

2. **Research Better Lift Calculation Methods**:
   - Matched control groups (propensity score matching)
   - Regression discontinuity design
   - Bayesian hierarchical models
   - Elasticity estimation with instrumental variables
   - Account for cannibalization and halo effects

3. **Add More Sophisticated Tools to Agent A**:
   - Additional baseline calculation methods
   - Improved validation metrics (beyond MAPE)
   - Cross-validation approaches
   - Statistical significance testing

4. **Expected Deliverables**:
   - Research document or comments in code explaining approaches
   - Updated tool implementations with better methods
   - Lower MAPE (target: <50% as intermediate goal, <15% as final)
   - More robust causal parameter estimates

**Research Resources**:
- Promotional lift modeling literature
- Causal inference textbooks (Pearl, Imbens & Rubin)
- Time series forecasting methods (Hyndman)
- Retail analytics case studies

---

**Last Updated**: 2026-01-23 (End of Session 2)
**Current Branch**: `dev-claude`
**Session Completed**: Agent A LLM implementation with real data calculations
**Next Session**: Research and implement improved baseline/lift methods
