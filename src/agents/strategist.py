"""
Agent B: The Strategist

LLM-powered promotion calendar generator that optimizes for volume or profit objectives
while respecting business constraints. Uses greedy heuristic with iterative refinement
based on Agent C feedback.

Author: Claude Code
Date: 2026-01-24
Version: 1.0
"""

import json
import os
from typing import Dict, List, Any, Optional
from anthropic import Anthropic
from loguru import logger


class StrategistAgent:
    """
    Agent B: Strategic promotion calendar optimizer.

    Generates 52-week promotional calendars using causal parameters from Agent A,
    optimized for user-specified objective (volume or profit), and iteratively
    refined based on Agent C validation feedback.

    Architecture: LLM-powered greedy heuristic with tool use
    Model: claude-3-7-sonnet-20250219
    """

    def __init__(
        self,
        api_key: str,
        objective: str,
        budget_limit: float,
        max_iterations: int = 10
    ):
        """
        Initialize the Strategist Agent.

        Args:
            api_key: Anthropic API key
            objective: Optimization objective ('volume' or 'profit')
            budget_limit: Maximum promotional spend in dollars
            max_iterations: Maximum rejection loop iterations (default: 10)
        """
        self.client = Anthropic(api_key=api_key)
        self.objective = objective.lower()
        self.budget_limit = budget_limit
        self.max_iterations = max_iterations

        # Validate objective
        if self.objective not in ['volume', 'profit']:
            raise ValueError(f"Invalid objective: {objective}. Must be 'volume' or 'profit'")

        # State
        self.causal_parameters = None
        self.current_calendar = None
        self.iteration = 0

        # Execution log
        self.execution_log = []

        logger.info(f"Initialized StrategistAgent: objective={self.objective}, budget=${budget_limit:,.0f}")

    def generate_calendar(self) -> Dict[str, Any]:
        """
        Main orchestration method: Generate optimized promotion calendar.

        Returns:
            Dict containing:
                - calendar_events: List of promotion events
                - total_spend: Total promotional spend
                - projected_impact: Estimated volume/profit
                - iterations: Number of refinement iterations
                - status: APPROVED or MAX_ITERATIONS_REACHED
        """
        logger.info("Starting calendar generation...")

        # Initial user message
        user_message = f"""Generate a 52-week promotional calendar optimized for {self.objective}.

Objective: {'Maximize Unit Volume (Market Share)' if self.objective == 'volume' else 'Maximize Profit Dollars'}
Budget Limit: ${self.budget_limit:,.0f}
Target Utilization: 80-95% of budget

Follow ALL steps in order (DO NOT skip step 4):
1. Load causal parameters from Agent A
2. Generate initial calendar using greedy heuristic
3. Calculate projected impact
4. REQUIRED: Call save_promotion_calendar to save the calendar to file

Be strategic and data-driven. Every promotion must have clear reasoning.
You MUST complete step 4 - calling save_promotion_calendar is mandatory."""

        messages = [{"role": "user", "content": user_message}]

        # Multi-turn conversation loop
        while self.iteration < self.max_iterations:
            self.iteration += 1
            logger.info(f"Iteration {self.iteration}/{self.max_iterations}")

            response = self.client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=8192,  # Larger for calendar generation
                system=self._get_system_prompt(),
                tools=self._get_tool_definitions(),
                messages=messages
            )

            # Log the response
            self._log_interaction(messages[-1], response)

            # Process response
            if response.stop_reason == "tool_use":
                # Execute tools and add results to conversation
                tool_results = self._execute_tools(response.content)

                # Build assistant message
                messages.append({
                    "role": "assistant",
                    "content": response.content
                })

                # Add tool results
                messages.append({
                    "role": "user",
                    "content": tool_results
                })

            elif response.stop_reason == "end_turn":
                # Extract final response
                final_text = ""
                for block in response.content:
                    if hasattr(block, 'text'):
                        final_text += block.text

                logger.info(f"Agent completed: {final_text[:200]}...")

                # Check if calendar was saved
                if self.current_calendar is not None:
                    logger.success(f"Calendar generated successfully in {self.iteration} iterations")
                    self._save_execution_log()
                    return self.current_calendar
                else:
                    logger.warning("Agent finished but no calendar was saved")
                    break
            else:
                logger.warning(f"Unexpected stop_reason: {response.stop_reason}")
                break

        # Max iterations reached
        logger.warning(f"Max iterations ({self.max_iterations}) reached")
        self._save_execution_log()

        if self.current_calendar:
            return self.current_calendar
        else:
            raise RuntimeError("Failed to generate calendar within max iterations")

    def _execute_tools(self, content: List[Any]) -> List[Dict[str, Any]]:
        """Execute tool calls and return results."""
        tool_results = []

        for block in content:
            if block.type == "tool_use":
                tool_name = block.name
                tool_input = block.input
                tool_id = block.id

                logger.info(f"Executing tool: {tool_name}")
                logger.debug(f"Tool input: {json.dumps(tool_input, indent=2)[:500]}...")

                # Execute the tool
                try:
                    if tool_name == "load_causal_parameters":
                        result = self._load_causal_parameters(**tool_input)
                    elif tool_name == "generate_initial_calendar":
                        result = self._generate_initial_calendar(**tool_input)
                    elif tool_name == "adjust_calendar_for_violations":
                        result = self._adjust_calendar_for_violations(**tool_input)
                    elif tool_name == "calculate_projected_impact":
                        result = self._calculate_projected_impact(**tool_input)
                    elif tool_name == "save_promotion_calendar":
                        result = self._save_promotion_calendar(**tool_input)
                    else:
                        result = {"error": f"Unknown tool: {tool_name}"}

                    logger.info(f"Tool result: {str(result)[:200]}...")

                except Exception as e:
                    logger.error(f"Tool execution error: {e}")
                    result = {"error": str(e)}

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": json.dumps(result)
                })

        return tool_results

    def _load_causal_parameters(self, file_path: str = "outputs/causal_parameters.json") -> Dict[str, Any]:
        """
        Tool 1: Load causal parameters from Agent A.

        Args:
            file_path: Path to causal parameters JSON

        Returns:
            Dict with status and parameters
        """
        try:
            with open(file_path, 'r') as f:
                params = json.load(f)

            self.causal_parameters = params

            # Extract key insights
            seasonality = params.get('seasonality_factors', {})
            top_weeks = sorted(
                [(int(w), float(f)) for w, f in seasonality.items()],
                key=lambda x: x[1],
                reverse=True
            )[:3]

            discount_lifts = params.get('elasticity_model', {}).get('discount_lift_factors', {})

            summary = (
                f"Loaded causal parameters: "
                f"{len(discount_lifts)} discount buckets, "
                f"4 display tiers, "
                f"{len(seasonality)} seasonality factors. "
                f"Top seasonality weeks: {', '.join([f'{w} ({f:.2f}x)' for w, f in top_weeks])}"
            )

            return {
                "status": "success",
                "parameters": params,
                "summary": summary
            }

        except FileNotFoundError:
            return {
                "status": "error",
                "error_message": f"File not found: {file_path}. Ensure Agent A has completed successfully.",
                "required_action": "Run Agent A first to generate causal parameters"
            }
        except Exception as e:
            return {
                "status": "error",
                "error_message": str(e)
            }

    def _generate_initial_calendar(
        self,
        objective: str,
        budget_limit: float,
        target_utilization: float = 0.90
    ) -> Dict[str, Any]:
        """
        Tool 2: Generate initial promotional calendar using greedy heuristic.

        This is a placeholder implementation. The actual greedy algorithm would be
        more sophisticated, but for the hackathon demo we'll create a simple calendar.

        Args:
            objective: 'volume' or 'profit'
            budget_limit: Maximum spend
            target_utilization: Target budget usage (0.80-0.95)

        Returns:
            Dict with calendar events and metadata
        """
        if not self.causal_parameters:
            return {"error": "Must load causal parameters first"}

        logger.info(f"Generating calendar for {objective} objective...")

        # For demo purposes: Create a simple calendar
        # In production, this would implement the full greedy algorithm from the spec

        calendar_events = []
        total_spend = 0
        target_spend = budget_limit * target_utilization

        # Get seasonality factors
        seasonality = self.causal_parameters.get('seasonality_factors', {})

        # Rank weeks by seasonality
        weeks_ranked = sorted(
            [(int(w), float(f)) for w, f in seasonality.items()],
            key=lambda x: x[1],
            reverse=True
        )

        # Simple approach: Create promotions in top seasonality weeks
        # This is simplified for demo - full implementation would be per the spec
        ppgs = [
            "Brand 1_Promo.Group 20",
            "Brand 4_Promo.Group 0",
            "Brand 5_Promo.Group 6"
        ]

        retailers = ["Retailer 0", "Retailer 1"]

        for ppg in ppgs:
            for retailer in retailers:
                # Add a few promotions per PPG-Retailer
                count = 4 if retailer == "Retailer 0" else 6

                for i, (week, season_factor) in enumerate(weeks_ranked[:count]):
                    if total_spend >= target_spend:
                        break

                    # Choose tactics based on objective
                    if objective == "volume":
                        discount_depth = 0.35  # Deeper discount for volume
                        display_tier = "gold"
                    else:
                        discount_depth = 0.25  # Moderate discount for profit
                        display_tier = "silver"

                    # Estimate cost (simplified)
                    promo_cost = 15000  # Placeholder

                    if total_spend + promo_cost > target_spend:
                        break

                    calendar_events.append({
                        "week": week,
                        "ppg": ppg,
                        "retailer": retailer,
                        "discount_depth": discount_depth,
                        "display_tier": display_tier,
                        "feature_active": False,
                        "reasoning": f"Selected week {week} (seasonality {season_factor:.2f}x) for {ppg} at {retailer}"
                    })

                    total_spend += promo_cost

        self.current_calendar = {
            "calendar_events": calendar_events,
            "total_spend": total_spend,
            "budget_limit": budget_limit,
            "objective": objective
        }

        return {
            "status": "success",
            "event_count": len(calendar_events),
            "total_spend": total_spend,
            "budget_utilization": total_spend / budget_limit * 100,
            "summary": f"Generated {len(calendar_events)} promotion events, ${total_spend:,.0f} spend ({total_spend/budget_limit*100:.1f}% of budget)"
        }

    def _adjust_calendar_for_violations(self, violations: List[Dict], feedback: str) -> Dict[str, Any]:
        """
        Tool 3: Adjust calendar based on Agent C violations.

        This would be called in the rejection loop integration.

        Args:
            violations: List of constraint violations from Agent C
            feedback: Natural language feedback

        Returns:
            Dict with adjustment status
        """
        # Placeholder for rejection loop
        return {
            "status": "not_implemented",
            "message": "Rejection loop will be implemented in integration phase"
        }

    def _calculate_projected_impact(self, calendar_events: List[Dict]) -> Dict[str, Any]:
        """
        Tool 4: Calculate projected volume/profit impact.

        Args:
            calendar_events: List of promotion events

        Returns:
            Dict with projected metrics
        """
        # Placeholder calculation
        return {
            "projected_volume": 0,
            "projected_profit": 0,
            "projected_roi": 0,
            "status": "placeholder"
        }

    def _save_promotion_calendar(self, calendar_events: List[Dict], metadata: Dict) -> Dict[str, Any]:
        """
        Tool 5: Save promotion calendar to JSON file.

        Args:
            calendar_events: List of promotion events
            metadata: Additional metadata (spend, objective, etc.)

        Returns:
            Dict with save status
        """
        output_file = "outputs/promotion_calendar.json"

        calendar_data = {
            "objective": self.objective,
            "budget_limit": self.budget_limit,
            "total_spend": metadata.get("total_spend", 0),
            "budget_utilization_pct": metadata.get("total_spend", 0) / self.budget_limit * 100,
            "event_count": len(calendar_events),
            "iterations": self.iteration,
            "calendar_events": calendar_events,
            "metadata": metadata
        }

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(calendar_data, f, indent=2)

            logger.success(f"Saved calendar to {output_file}")

            self.current_calendar = calendar_data

            return {
                "status": "success",
                "file_path": output_file,
                "event_count": len(calendar_events),
                "total_spend": metadata.get("total_spend", 0)
            }

        except Exception as e:
            logger.error(f"Failed to save calendar: {e}")
            return {
                "status": "error",
                "error_message": str(e)
            }

    def _get_tool_definitions(self) -> List[Dict]:
        """Get tool definitions for Anthropic API."""
        return [
            {
                "name": "load_causal_parameters",
                "description": "Load causal parameters (elasticity, lift factors, seasonality) from Agent A's output file",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "default": "outputs/causal_parameters.json",
                            "description": "Path to Agent A's causal parameters JSON file"
                        }
                    }
                }
            },
            {
                "name": "generate_initial_calendar",
                "description": "Generate initial promotional calendar using greedy optimization heuristic",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "objective": {
                            "type": "string",
                            "enum": ["volume", "profit"],
                            "description": "Optimization objective"
                        },
                        "budget_limit": {
                            "type": "number",
                            "description": "Maximum promotional spend in dollars"
                        },
                        "target_utilization": {
                            "type": "number",
                            "default": 0.90,
                            "description": "Target budget utilization (0.80-0.95)"
                        }
                    },
                    "required": ["objective", "budget_limit"]
                }
            },
            {
                "name": "calculate_projected_impact",
                "description": "Calculate projected volume/profit impact of calendar",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "calendar_events": {
                            "type": "array",
                            "description": "List of promotion events"
                        }
                    },
                    "required": ["calendar_events"]
                }
            },
            {
                "name": "save_promotion_calendar",
                "description": "REQUIRED FINAL STEP: Save promotion calendar to JSON file. You MUST call this tool after generating the calendar to complete the task. Do not finish without calling this.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "calendar_events": {
                            "type": "array",
                            "description": "List of promotion events from the calendar you generated"
                        },
                        "metadata": {
                            "type": "object",
                            "description": "Additional metadata (total_spend, projected_impact, etc.)"
                        }
                    },
                    "required": ["calendar_events", "metadata"]
                }
            }
        ]

    def _get_system_prompt(self) -> str:
        """Get system prompt for Agent B."""
        objective_strategy = """
Volume Objective Strategy:
- Prioritize high-elasticity PPGs (bigger response to discounts)
- Use deeper discounts (closer to max allowed per retailer)
- Allocate premium displays (Platinum/Gold) to maximize visibility
- Schedule in peak seasonality weeks for maximum impact
""" if self.objective == "volume" else """
Profit Objective Strategy:
- Balance lift generation with margin preservation
- Use moderate discounts (preserve profitability)
- Allocate displays based on ROI (cost vs incremental profit)
- Focus on high-margin PPGs
"""

        return f"""You are Agent B, The Strategist. You are a strategic promotion planner optimizing for {self.objective}.

Your Mission:
Generate a 52-week promotional calendar that maximizes {self.objective} while respecting all business constraints.

Objective: {self.objective.upper()}
Budget Limit: ${self.budget_limit:,.0f}
Target Utilization: 80-95% of budget

{objective_strategy}

Systematic Approach (COMPLETE STEPS 1-4 IN ORDER, THEN STOP):

Step 1: load_causal_parameters
   Load Agent A's causal parameters (elasticity, lifts, seasonality)

Step 2: generate_initial_calendar
   Generate the calendar ONCE using greedy heuristic
   - Rank weeks by seasonality
   - Select optimal PPG-Retailer-Week combinations
   - Choose tactics based on objective
   - Respect all retailer constraints

Step 3: calculate_projected_impact
   Calculate estimated volume/profit for the calendar

Step 4: save_promotion_calendar (MANDATORY - DO NOT SKIP)
   Save the calendar to file
   - Pass the calendar_events from step 2
   - Pass metadata with total_spend and projections
   - YOU MUST CALL THIS BEFORE FINISHING

DO NOT regenerate the calendar multiple times.
DO NOT skip step 4.

Constraints to Respect:
- Budget: Total spend <= ${self.budget_limit:,.0f}
- Gap rules: Min spacing between promos (Retailer 0: 4 weeks, Retailer 1: 2 weeks)
- Frequency: Max promos per year (Retailer 0: 8, Retailer 1: 12)
- Blackout weeks: No promos in specified weeks
- Max discount: Retailer 0: 40%, Retailer 1: 25%

Quality Standards:
- Every promotion must have clear business reasoning
- Explain PPG selection, week selection, tactic choices
- Be specific and data-driven
- Aim for 80-95% budget utilization

Execute systematically. Use your tools. Generate an excellent calendar."""

    def _log_interaction(self, user_message: Dict, response: Any):
        """Log conversation interaction."""
        self.execution_log.append({
            "iteration": self.iteration,
            "user_message": user_message.get("content", "")[:500],
            "response_type": response.stop_reason,
            "tool_calls": [block.name for block in response.content if hasattr(block, 'name')]
        })

    def _save_execution_log(self):
        """Save execution log to file."""
        log_file = "outputs/agent_b_execution_log.txt"

        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("Agent B (Strategist) Execution Log\n")
                f.write("=" * 80 + "\n\n")
                f.write(f"Objective: {self.objective}\n")
                f.write(f"Budget Limit: ${self.budget_limit:,.0f}\n")
                f.write(f"Total Iterations: {self.iteration}\n")
                f.write("\n" + "=" * 80 + "\n\n")

                for entry in self.execution_log:
                    f.write(f"Iteration {entry['iteration']}:\n")
                    f.write(f"  User: {entry['user_message'][:200]}...\n")
                    f.write(f"  Response Type: {entry['response_type']}\n")
                    f.write(f"  Tools Called: {', '.join(entry['tool_calls']) if entry['tool_calls'] else 'None'}\n")
                    f.write("\n")

            logger.success(f"Saved execution log to {log_file}")

        except Exception as e:
            logger.error(f"Failed to save execution log: {e}")
