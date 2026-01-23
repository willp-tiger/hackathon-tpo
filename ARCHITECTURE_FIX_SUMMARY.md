# Architecture Fix Summary

**Date**: 2026-01-23
**Session**: Critical Architecture Correction

## Problem Identified

The project was implemented with **hardcoded Python classes** instead of **LLM-powered agents**, which violates the core requirement and judging criteria.

### Root Cause

The initial CLAUDE.md mentioned "Use Claude Python SDK" but didn't enforce it strongly enough. The skeleton code in `src/agents/` was implemented as Python classes with pandas/sklearn logic, and we built on top of that instead of questioning the architecture.

### Impact on Judging

- **40% of score** is "Architecture & Agentic Design"
- This explicitly evaluates:
  - Agent autonomy and decision-making (LLM reasoning, not hardcoded logic)
  - Visible agent interactions in logs (shows Claude's reasoning process)
  - Appropriate use of agentic patterns (tool use, multi-turn conversations)
- **Hardcoded Python logic = 0/40 points**

## Files Deleted

All incorrect implementations have been removed:

1. ✅ `src/agents/analyst.py` - 757 lines of hardcoded pandas/sklearn logic
2. ✅ `src/agents/strategist.py` - Placeholder methods with TODOs
3. ✅ `src/agents/auditor.py` - Hardcoded validation logic
4. ✅ `test_agent_a.py` - Tests for wrong implementation
5. ✅ `debug_agent_a.py` - Debug script for wrong implementation
6. ✅ `outputs/causal_parameters.json` - Output from wrong implementation

## Documentation Updated

### ✅ CLAUDE.md - Complete Rewrite

**Key Changes**:
- Added ⚠️ CRITICAL ARCHITECTURE REQUIREMENT section at top
- Made clear: "ALL THREE AGENTS MUST BE LLM-POWERED USING CLAUDE API"
- Replaced behavioral descriptions with LLM implementation examples
- Added complete code examples showing:
  - `Anthropic()` client initialization
  - Tool definitions with JSON schemas
  - System prompts for each agent
  - Multi-turn conversation loops
  - Tool use patterns
- Updated progress tracking to reflect rebuild requirement

**Before**: Vague "Use Claude SDK" suggestion
**After**: Explicit LLM architecture requirement with working code examples

### ✅ README.md - Agent Descriptions Updated

**Key Changes**:
- Each agent now shows **Implementation** section with LLM details
- Added clarifications:
  - "Uses Anthropic Python SDK with tool use"
  - "Claude reasons about which approaches to try"
  - "Tools execute pandas/sklearn computations"
  - "Reasoning visible in agent_execution_log.txt"
- Added "Architecture Pattern" section with complete agent template
- Added "Development Notes" emphasizing LLM requirement

**Before**: Agents described as abstract responsibilities
**After**: Agents described as LLM-powered with specific implementation details

### ✅ ROADMAP.md - Phase 2 Rewritten

**Key Changes**:
- Phase 2 renamed to "🔄 REBUILD REQUIRED"
- Completely new task breakdown:
  1. Delete incorrect implementation (✅ done)
  2. Create LLM agent structure (pending)
  3. Implement analysis tools (pending)
  4. Multi-turn conversation loop (pending)
  5. Testing with real API calls (pending)
  6. Logging & visibility (pending)
- Deliverables changed from "Fully implemented analyst.py" to "LLM-powered analyst.py (200-300 lines)"
- Estimated effort increased: 3-4 hours → 4-5 hours (rebuild from scratch)

**Before**: Implement statistical methods in Python
**After**: Implement LLM agent with Claude API and tool use

## What Remains Unchanged (And Why)

### ✅ Utils Folder - KEEP AS IS

**Files**:
- `src/utils/metrics.py` - Calculate MAPE, RMSE, ROI, lift
- `src/utils/validators.py` - Validate calendar/audit formats
- `src/utils/data_loader.py` - Load Excel files

**Why Keep**:
These are **not agents** - they're utility functions that will be called **as tools** by LLM agents.

Example:
- Old approach: Agent A directly calls `calculate_mape()`
- New approach: Claude decides to use `validate_forecast_mape` tool, which internally calls `calculate_mape()`

These functions are the **execution layer** underneath LLM reasoning.

### ⚠️ Orchestrator.py - NEEDS UPDATE (Next Session)

**Current Status**: Expects old agent classes with `.analyze()`, `.generate_calendar()`, `.audit()` methods

**Required Changes**:
1. Still instantiate agent classes (new LLM-based ones)
2. Agents will still have `.analyze()`, `.generate_calendar()`, `.audit()` methods
3. BUT now those methods will:
   - Initialize Claude API client
   - Run multi-turn conversations
   - Use tools instead of direct computation
   - Log reasoning to execution log

**Action**: Update in next session when implementing new Agent A

## Correct Architecture

### Agent Implementation Pattern

```python
from anthropic import Anthropic
import os

class AnalystAgent:
    def __init__(self, sales_data, promo_data):
        self.client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self.sales_data = sales_data
        self.promo_data = promo_data

        # Define tools that Claude can call
        self.tools = [
            {
                "name": "load_sales_preview",
                "description": "Load first 10 rows of sales data",
                "input_schema": {"type": "object", "properties": {}}
            },
            {
                "name": "calculate_baseline_regression",
                "description": "Calculate baseline using regression",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "validation_weeks": {"type": "number"}
                    }
                }
            },
            # ... more tools
        ]

        self.system_prompt = """You are Agent A, a data scientist.

Your task: Generate causal parameters.

Approach:
1. Conduct EDA - use load_sales_preview tool
2. Try multiple baseline approaches
3. Validate MAPE < 15%
4. Document your reasoning

Use tools iteratively. Explain your choices."""

    def analyze(self):
        """Run LLM-powered analysis using Claude API."""
        messages = [
            {
                "role": "user",
                "content": "Analyze sales data and generate causal parameters."
            }
        ]

        while True:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                system=self.system_prompt,
                tools=self.tools,
                messages=messages
            )

            # Log Claude's reasoning
            for block in response.content:
                if block.type == "text":
                    logger.info(f"Agent A reasoning: {block.text}")

            if response.stop_reason == "tool_use":
                # Execute tools, append results
                tool_results = self._execute_tools(response.content)
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
            else:
                # Extract final parameters
                break

        return self.causal_parameters

    def _execute_tools(self, content):
        """Execute tool calls and return results."""
        # Call actual Python functions in utils/
        # Return results as JSON
        pass
```

### Key Differences

| Old (Hardcoded) | New (LLM-Powered) |
|-----------------|-------------------|
| Direct pandas/sklearn calls | Claude decides which tools to call |
| Hardcoded if/else logic | Claude reasons about approaches |
| Python comments for reasoning | Natural language explanations |
| No visible decision-making | Full reasoning in logs |
| Single-pass execution | Iterative multi-turn conversation |
| 757 lines of computation | ~250 lines (mostly tool definitions) |

## Next Steps

### Immediate (Current Session)
1. ✅ Update all documentation
2. ✅ Delete incorrect implementations
3. ✅ Create this summary

### Next Session: Implement Agent A
1. Create new `src/agents/analyst.py` with LLM architecture
2. Define 6-7 tools for data analysis
3. Implement tool execution functions (call utils/)
4. Test with real Claude API calls
5. Verify reasoning appears in logs

### Subsequent Sessions
- Implement Agent C (Auditor) with LLM
- Implement Agent B (Strategist) with LLM
- Update orchestrator for LLM agents
- Test rejection loop with visible reasoning
- Generate deliverables

## Critical Success Factors

1. **Visible Reasoning**: Every agent decision must appear in `agent_execution_log.txt`
2. **Tool Use**: Claude must decide WHEN to call tools, not just execute predefined logic
3. **Multi-Turn Conversations**: Baseline validation, rejection loop must show iteration
4. **Natural Language**: Explanations in plain English, not code comments

## Estimated Time to Fix

- ✅ **Session 1 (Today)**: Documentation fixes + file cleanup (1 hour) - DONE
- **Session 2**: Agent A rebuild (4-5 hours)
- **Session 3**: Agent C rebuild (3-4 hours)
- **Session 4**: Agent B rebuild (4-5 hours)
- **Session 5**: Integration + testing (3-4 hours)

**Total**: 15-19 hours to fully rebuild with correct architecture

---

**Status**: Documentation corrected, files cleaned, ready for LLM agent implementation.
**Git Status**: Changes staged, ready to commit with message documenting architecture correction.
