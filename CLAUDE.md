# TPO AI Agents Hackathon - Development Guide

## Project Overview

This is a **multi-agent system** for Trade Promotion Optimization (TPO) built for the AI Agents Hackathon. The system uses **spec-driven development** with three autonomous agents that collaborate through an iterative feedback loop to generate optimized 52-week promotion calendars.

## Development Philosophy: Spec-Driven Development

This project follows **specification-driven development principles**:

1. **Start with Clear Specifications**: All agent behaviors, interfaces, and outputs are defined in the case study documentation before implementation
2. **Design by Contract**: Each agent has well-defined inputs, outputs, and responsibilities documented in docstrings
3. **Testable Requirements**: Every deliverable (calendar, reports, logs) has explicit format and validation requirements
4. **Iterative Refinement**: Agents iterate until specifications are met (the rejection loop is a feature, not a bug)

### Why This Matters

The judging criteria explicitly looks for:
- **Separation of Concerns**: Each agent must stay within its specification
- **Modularity**: Swapping objectives (Volume ↔ Profit) should work without architectural changes
- **Explainability**: Every decision must map back to a spec-defined reason

## Agent Architecture Using Claude Python SDK

### Recommended Approach: Claude Agent SDK

**Use the [Claude Python SDK (Agent SDK)](https://platform.claude.com/docs/en/agent-sdk/python) to build the three agents.**

The Agent SDK provides:
- **Tool use patterns** for agents to interact with data and each other
- **Message history management** for maintaining conversation state
- **Structured output parsing** for reliable agent-to-agent communication
- **Error handling** for robust agent execution

### Agent Implementation Pattern

```python
from anthropic import Anthropic

client = Anthropic(api_key="...")

# Agent with tool use
messages = [
    {"role": "user", "content": "Analyze sales data and generate causal parameters"}
]

response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=4096,
    tools=[...],  # Define tools for data analysis
    messages=messages
)

# Process tool calls, maintain conversation history
# Implement the feedback loop between agents
```

### Critical Agent SDK Patterns for This Project

1. **Tool Definition**: Define tools for each agent's capabilities
   - Analyst: Data loading, statistical analysis, baseline calculation
   - Strategist: Calendar generation, optimization, adjustment
   - Auditor: Constraint checking, budget validation, violation reporting

2. **Multi-Turn Conversations**: Use message history to implement the rejection loop
   ```python
   # Initial proposal
   messages.append({"role": "user", "content": strategist_prompt})
   response = client.messages.create(...)

   # Auditor feedback
   messages.append({"role": "assistant", "content": response.content})
   messages.append({"role": "user", "content": auditor_feedback})

   # Iteration continues until approved
   ```

3. **Structured Outputs**: Use JSON schema tools to ensure reliable data exchange between agents

## Skills for Agent Support

**Skills** can extend agent capabilities with domain-specific knowledge:

### Recommended Skills for This Project

1. **Data Analysis Skills**: Statistical methods, time series decomposition, elasticity calculation
2. **Optimization Skills**: Constraint satisfaction, budget optimization, calendar scheduling
3. **Financial Modeling Skills**: ROI calculation, margin analysis, spend allocation

### Creating Custom Skills

Skills are stored in `skills/` directory with `SKILL.md` files:

```markdown
---
name: promotion-optimizer
description: Optimization strategies for promotion calendar generation
---

# Promotion Optimization Skill

## Constraint Satisfaction Strategies
[Detailed optimization approaches...]

## Budget Allocation Patterns
[Best practices for staying within budget...]
```

Invoke with: `/promotion-optimizer`

**Note**: Skills are a Claude Code feature. If building standalone agents with the SDK, embed this knowledge directly in system prompts instead.

## SDK Tools
**SDK Tools** = Custom functions your agents can call during execution

For this project, use **SDK tools** to implement:
- Data validation after loading
- Constraint checking after calendar generation
- Logging and monitoring during agent execution

## Hooks and Skills Configuration

This project includes **automated hooks** and **specialized skills** to support development. See [.claude/HOOKS_AND_SKILLS.md](.claude/HOOKS_AND_SKILLS.md) for complete documentation.

### Configured Hooks

1. **format-on-save**: Auto-format Python files with black
2. **validate-agent-separation**: Enforce separation of concerns (critical for judging)
3. **test-on-commit**: Run tests before commits (blocking)
4. **log-execution**: Log all optimization runs
5. **validate-deliverables**: Check output format compliance

### Available Skills

1. **/causal-inference**: Statistical methods for Agent A (baseline, elasticity, seasonality)
2. **/promotion-optimization**: Optimization strategies for Agent B (volume/profit, constraints)
3. **/constraint-validation**: Validation techniques for Agent C (budget, gaps, frequency)

**Usage**: Invoke skills with `/skill-name` when implementing corresponding agents.

## Session Management: Single-Purpose Conversations

### When to End Current Conversation

End the conversation and start fresh when:

1. **Major Context Switch**: Moving from implementation to testing, or from agent development to data exploration
2. **Token Budget Concerns**: The conversation is becoming long and unfocused
3. **Completion of Milestone**: An agent is fully implemented and tested
4. **Need for Fresh Perspective**: Debugging is circular or Claude is stuck on an approach

### Single-Purpose Conversation Patterns

**Good conversation boundaries:**
- ✅ "Implement Agent A (Analyst) with baseline decomposition"
- ✅ "Create and test the rejection loop between Strategist and Auditor"
- ✅ "Generate final deliverables and validate format"
- ✅ "Explore the sales data structure and create data validation"

**Bad conversation mixing:**
- ❌ "Build all three agents, test them, generate reports, and fix any bugs"
- ❌ "Implement Agent A and also refactor the data loader and update docs"

### Context Transfer Between Conversations

**Primary Method: This CLAUDE.md File**

This file is **automatically loaded** at the start of every Claude Code session in this directory. Use it to maintain:
- Architecture decisions
- Coding conventions
- Agent specifications
- Known issues and solutions
- Progress tracking

**Secondary Methods:**

1. **Code Documentation**: Keep agent docstrings and comments up to date
2. **Conversation Summaries**: At the end of a session, ask Claude to update this file with:
   - What was completed
   - What needs work next
   - Any important decisions or learnings
3. **Git Commits**: Detailed commit messages capture intent and context
4. **README Updates**: Keep the main README.md synchronized with implementation progress

**Example End-of-Session Workflow:**

```
You: "Update the Progress Tracking section below with what we completed"
Claude: [Updates CLAUDE.md with session summary]
You: [Commit changes with descriptive message]
[Next session picks up from updated CLAUDE.md]
```

## Project Standards

### Code Style

- **Python Style**: PEP 8 compliant, type hints required
- **Docstrings**: Google-style docstrings for all classes and functions
- **Logging**: Use loguru for all logging, appropriate levels (DEBUG/INFO/WARNING/ERROR)
- **Error Handling**: Explicit error handling with informative messages

### Agent Communication Format

All inter-agent communication uses **JSON with explicit schemas**:

```python
# Example: Strategist output
{
  "objective": str,
  "total_projected_spend": float,
  "budget_limit": float,
  "iteration": int,
  "calendar_events": [
    {
      "week": int,
      "sku": str,
      "discount_depth": float,
      "display_active": bool,
      "reasoning": str,
      "projected_outcome": str
    }
  ]
}
```

### Testing Requirements

- **Unit Tests**: Each agent method tested independently
- **Integration Tests**: Full workflow tested end-to-end
- **Validation Tests**: Output format validation for all deliverables
- **Accuracy Tests**: Baseline MAPE < 15% on holdout data

## Critical Success Criteria

### From Judging Rubric

1. **Architecture & Agentic Design (40%)**
   - The rejection loop MUST be visible in logs
   - Agents MUST NOT cross responsibility boundaries
   - System MUST work when objective changes (Volume ↔ Profit)

2. **Technical Implementation (40%)**
   - Budget calculations MUST be exact
   - Constraints MUST have ZERO violations in final output
   - Baseline forecast MUST show low MAPE

3. **User Experience & Reporting (20%)**
   - All outputs MUST clearly explain "why"
   - Before/After comparison MUST be easy to understand

## Data Files

Located in `case-data/`:
- `Sales.xlsx` - Historical sales (source of truth)
- `PromotionData.xlsx` - Promotion tactics and costs
- `Finance.xlsx` - Unit economics
- `Promo_config.csv` - Display fees
- `Constraints.json` - Validation rules

**Data Loading**: Always use `DataLoader` utility for consistent preprocessing

## Output Requirements

Must generate in `outputs/`:
1. `optimized_calendar.csv` - 52-week schedule
2. `financial_impact_report.json` - Base vs. Optimized comparison
3. `baseline_validation.csv` - Forecast accuracy (MAPE)
4. `agent_execution_log.txt` - Full conversation log showing rejection loop

## Progress Tracking

### Phase 0: Project Setup ✅ COMPLETE

- ✅ Project structure and skeleton code
- ✅ Three agent classes (placeholder implementations)
- ✅ Orchestrator with rejection loop logic
- ✅ Data loader utilities
- ✅ Metrics and validation utilities
- ✅ CLI entry point
- ✅ Git repository initialized on `dev-claude` branch
- ✅ Comprehensive CLAUDE.md development guide
- ✅ 5 automated hooks configured:
  - format-on-save (auto-format Python)
  - validate-agent-separation (enforce boundaries)
  - test-on-commit (quality gate)
  - log-execution (audit trail)
  - validate-deliverables (format checking)
- ✅ 3 specialized skills created:
  - /causal-inference (Agent A guidance)
  - /promotion-optimization (Agent B guidance)
  - /constraint-validation (Agent C guidance)
- ✅ Detailed roadmap with 8 phases (16-24 hour estimate)

### Phase 1: Data Exploration ⏭️ NEXT

**Start new conversation focused on**: "Explore and validate case-data files to understand schema, relationships, and data quality"

**Tasks**:
- Load and examine all data files
- Data quality assessment
- Schema documentation
- Exploratory data analysis
- Create validation scripts

**Estimated**: 1-2 hours

### Future Phases (See ROADMAP.md)

2. **Agent A Implementation** (3-4 hours)
3. **Agent C Implementation** (2-3 hours) - Before Agent B for testing
4. **Agent B Implementation** (4-5 hours)
5. **Integration & Orchestration** (2-3 hours)
6. **Deliverables Generation** (1-2 hours)
7. **Testing & QA** (2-3 hours)
8. **Demo Preparation** (1-2 hours)

### Known Issues
- None yet

### Architecture Decisions
- Using Claude Python SDK for agent implementation (not LangChain)
- Rejection loop capped at 10 iterations (configurable)
- Logging both to console and file for transparency
- JSON schema validation for all inter-agent messages
- Single-purpose conversations (one phase per session)
- Context transfer via CLAUDE.md updates

## Development Commands

```bash
# Setup
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Run optimization
python main.py --objective volume --budget 1000000
python main.py --objective profit --budget 1500000

# With debug logging
python main.py --objective volume --budget 1000000 --log-level DEBUG

# Testing
pytest tests/ -v
pytest tests/ --cov=src --cov-report=html
```

## Important Notes

- **The rejection loop is the key differentiator**: A valid first-try calendar scores LOW
- **Explainability > Optimization**: Better to show clear reasoning than marginal gains
- **Separation of concerns matters**: Agent A should NEVER propose strategies; Agent C should NEVER suggest creative solutions
- **Every decision needs a "why"**: Reasoning strings are not optional

---

**Last Updated**: 2026-01-23
**Current Branch**: `dev-claude`
**Active Session Goal**: Initial project setup and architecture
