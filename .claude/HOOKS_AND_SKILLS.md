# Recommended Hooks and Skills for TPO Project

This document describes the hooks and skills configured for the TPO AI Agents Hackathon project.

## Hooks

Hooks automate workflow tasks and enforce quality standards during development.

### 1. format-on-save
**File**: `.claude/hooks/format-on-save.json`
**Event**: PostToolUse
**Triggers**: After Write or Edit on `*.py` files
**Action**: Runs `black` formatter automatically
**Purpose**: Maintains consistent code style without manual formatting

### 2. validate-agent-separation
**File**: `.claude/hooks/validate-agent-separation.json`
**Event**: PostToolUse
**Triggers**: After Write or Edit on `src/agents/*.py` files
**Action**: LLM-based validation of separation of concerns
**Purpose**: **Critical for judging criteria** - ensures Agent A (Analyst) doesn't do optimization, Agent B (Strategist) doesn't validate constraints, Agent C (Auditor) doesn't generate strategies
**Blocking**: No (provides feedback)

### 3. test-on-commit
**File**: `.claude/hooks/test-on-commit.json`
**Event**: PreToolUse
**Triggers**: Before `git commit` commands
**Action**: Runs `pytest` test suite
**Purpose**: Prevents committing broken code
**Blocking**: Yes (prevents commit if tests fail)

### 4. log-execution
**File**: `.claude/hooks/log-execution.json`
**Event**: PostToolUse
**Triggers**: After running `python main.py`
**Action**: Logs execution to `.claude/execution-history.log`
**Purpose**: Tracks all optimization runs for debugging and audit

### 5. validate-deliverables
**File**: `.claude/hooks/validate-deliverables.json`
**Event**: PostToolUse
**Triggers**: After Write on `outputs/*.csv` or `outputs/*.json`
**Action**: LLM-based validation against hackathon requirements
**Purpose**: Ensures output files match required format before submission
**Blocking**: No (provides validation feedback)

## Skills

Skills provide specialized domain knowledge for implementing each agent.

### 1. causal-inference
**File**: `.claude/skills/causal-inference/SKILL.md`
**Invoke**: `/causal-inference`
**Purpose**: Statistical methods for Agent A (The Analyst)

**Covers**:
- Baseline decomposition techniques (time series, regression)
- Price elasticity calculation methods
- Display mechanics impact measurement
- Seasonality pattern extraction
- Validation metrics (MAPE, RMSE)
- Output format specifications

**Use when**: Implementing baseline calculation, elasticity modeling, or statistical analysis

### 2. promotion-optimization
**File**: `.claude/skills/promotion-optimization/SKILL.md`
**Invoke**: `/promotion-optimization`
**Purpose**: Optimization strategies for Agent B (The Strategist)

**Covers**:
- Volume vs. Profit optimization objectives
- Constraint satisfaction techniques
- Budget allocation strategies
- Gap rule and frequency limit handling
- Iterative refinement based on feedback
- Greedy vs. optimization-based approaches
- Reasoning generation templates

**Use when**: Implementing calendar generation, optimization logic, or feedback processing

### 3. constraint-validation
**File**: `.claude/skills/constraint-validation/SKILL.md`
**Invoke**: `/constraint-validation`
**Purpose**: Compliance checking for Agent C (The Auditor)

**Covers**:
- Budget validation calculations
- Gap rule checking algorithms
- Frequency limit enforcement
- Slotting constraint validation
- Financial feasibility checks
- Audit report structure
- Feedback generation strategies
- Violation severity classification

**Use when**: Implementing validation logic, constraint checking, or audit reporting

## Usage Patterns

### During Development

```bash
# When implementing Agent A
/causal-inference
# Provides statistical methods and validation techniques

# When implementing Agent B
/promotion-optimization
# Provides optimization strategies and constraint handling

# When implementing Agent C
/constraint-validation
# Provides validation algorithms and audit reporting
```

### Automatic Hook Execution

Hooks run automatically during the workflow:

1. **Write Python code** → `format-on-save` runs black
2. **Modify agent files** → `validate-agent-separation` checks boundaries
3. **Git commit** → `test-on-commit` runs tests (blocks if failing)
4. **Run main.py** → `log-execution` logs the run
5. **Generate outputs** → `validate-deliverables` checks format

## Benefits

### Hooks Benefits
- **Automated formatting**: Never think about code style
- **Separation enforcement**: Catch boundary violations early
- **Quality gates**: Can't commit broken code
- **Audit trail**: All executions logged automatically
- **Format validation**: Deliverables checked before submission

### Skills Benefits
- **Domain expertise**: Statistical and optimization knowledge embedded
- **Consistency**: Standard approaches across all agents
- **Reference**: Quick lookup for formulas and patterns
- **Examples**: Code snippets and templates ready to use
- **Quality**: Best practices from promotion analytics industry

## Notes

- **Hooks are Claude Code specific**: They won't work in standalone SDK agents
- **Skills can be embedded**: For SDK agents, embed skill content in system prompts
- **Blocking vs. Non-blocking**: Only `test-on-commit` blocks execution
- **Skill invocation**: Manual with `/skill-name` or automatic based on context
- **Customization**: All hooks and skills can be modified for project needs

## Recommended Workflow

1. **Planning Phase**: Review relevant skill before implementing
2. **Implementation**: Let hooks handle formatting and validation
3. **Testing**: Hooks prevent commits until tests pass
4. **Validation**: Hooks validate output format automatically
5. **Iteration**: Skills guide refinement based on feedback

This automation and knowledge embedding ensures high-quality, compliant implementations that meet hackathon judging criteria.
