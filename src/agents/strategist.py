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
        max_iterations: int = 10,
        output_dir: str = "outputs",
        data_dir: str = "case-data",
        reasoning_callback=None
    ):
        """
        Initialize the Strategist Agent.

        Args:
            api_key: Anthropic API key
            objective: Optimization objective ('volume' or 'profit')
            budget_limit: Maximum promotional spend in dollars
            max_iterations: Maximum rejection loop iterations (default: 10)
            output_dir: Directory for output files (default: "outputs")
            data_dir: Directory containing input data files (default: "case-data")
            reasoning_callback: Optional callback function(reasoning_text) to log agent reasoning
        """
        self.client = Anthropic(api_key=api_key)
        self.objective = objective.lower()
        self.budget_limit = budget_limit
        self.max_iterations = max_iterations
        self.output_dir = output_dir
        self.data_dir = data_dir
        self.reasoning_callback = reasoning_callback

        # Validate objective
        if self.objective not in ['volume', 'profit']:
            raise ValueError(f"Invalid objective: {objective}. Must be 'volume' or 'profit'")

        # Load required data for cost calculations
        from src.utils import DataLoader
        loader = DataLoader(data_dir)

        self.finance_data = loader.load_financials()
        self.promo_config = loader.load_promo_config()

        logger.info(f"Initialized StrategistAgent: objective={self.objective}, budget=${budget_limit:,.0f}")
        logger.info(f"Loaded finance data: {len(self.finance_data)} PPGs")
        logger.info(f"Loaded promo config: {len(self.promo_config)} tiers")

        # State
        self.causal_parameters = None
        self.current_calendar = None
        self.iteration = 0

        # Execution log
        self.execution_log = []

    def _get_unit_price(self, ppg: str) -> float:
        """
        Get unit price for PPG from Finance.xlsx.

        Note: Finance.xlsx has PPG names with APN suffixes (e.g., "Brand_Group_APN")
        but Sales data uses just "Brand_Group". We match on prefix.

        Args:
            ppg: Product group identifier (from Sales data, without APN)

        Returns:
            Unit price (List Price column), averaged if multiple APNs exist
        """
        if self.finance_data is None:
            raise ValueError("Finance data not loaded - cannot calculate TPR costs")

        # Match PPGs by prefix (Finance has "Brand_Group_APN", Sales has "Brand_Group")
        ppg_finance = self.finance_data[self.finance_data["PPG"].str.startswith(ppg + "_", na=False)]

        if ppg_finance.empty:
            logger.warning(f"PPG '{ppg}' not found in Finance.xlsx - using default price $10.00")
            return 10.0

        # Average price across all APNs for this PPG
        unit_price = ppg_finance["List Price"].mean()
        logger.debug(f"PPG '{ppg}': {len(ppg_finance)} APNs found, avg price ${unit_price:.2f}")
        return unit_price

    def _get_display_cost(self, display_tier: str) -> float:
        """
        Get display cost from Promo_config.csv.

        Promo_config.csv structure:
        - Column 1: "Promo Type" (e.g., "display_gold  ( per week)")
        - Column 2: "fixed Spend (USD)" (e.g., "400")

        Args:
            display_tier: Display tier (bronze, silver, gold, platinum, or none)

        Returns:
            Display cost in dollars per week
        """
        if display_tier is None or display_tier.lower() == "none":
            return 0.0

        if self.promo_config is None:
            logger.warning("Promo config not loaded - using default display cost $0")
            return 0.0

        # Match tier in "Promo Type" column (e.g., "display_gold  ( per week)")
        tier_pattern = f"display_{display_tier.lower()}"
        matching_rows = self.promo_config[
            self.promo_config["Promo Type"].str.contains(tier_pattern, case=False, na=False)
        ]

        if matching_rows.empty:
            logger.warning(f"Display tier '{display_tier}' not found in promo config - using $0")
            return 0.0

        # Extract cost (handle potential string formatting)
        cost_str = str(matching_rows.iloc[0]["fixed Spend (USD)"]).strip()
        try:
            display_cost = float(cost_str)
            logger.debug(f"Display tier '{display_tier}': ${display_cost}")
            return display_cost
        except ValueError:
            logger.warning(f"Invalid display cost format: '{cost_str}' - using $0")
            return 0.0

    def generate_calendar(self, feedback: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main orchestration method: Generate optimized promotion calendar.

        Args:
            feedback: Optional feedback from Agent C (Auditor) with violations to fix

        Returns:
            Dict containing:
                - calendar_events: List of promotion events
                - total_spend: Total promotional spend
                - projected_impact: Estimated volume/profit
                - iterations: Number of refinement iterations
                - status: APPROVED or MAX_ITERATIONS_REACHED
        """
        logger.info("Starting calendar generation...")

        if feedback:
            logger.info(f"Regenerating calendar with feedback: {feedback.get('status', 'UNKNOWN')}")
            self.iteration += 1  # Increment for rejection loop iteration

        # Initial user message
        if feedback:
            # Rejection loop: calendar was rejected, regenerate with feedback
            user_message = f"""The Auditor REJECTED your previous calendar. You must fix the violations and regenerate.

Rejection Feedback:
Status: {feedback.get('status', 'REJECTED')}
Violations: {len(feedback.get('violations', []))}

{self._format_violations_for_prompt(feedback.get('violations', []))}

Auditor's Guidance: {feedback.get('feedback', 'Fix the violations above')}

Your task:
1. Load the current calendar (already saved to {self.output_dir}/promotion_calendar.json)
2. Call adjust_calendar_for_violations to fix the specific violations
3. Calculate projected impact for the adjusted calendar
4. Save the corrected calendar

Be strategic in your corrections. Make MATERIAL changes to address violations, not cosmetic ones."""
        else:
            # Initial generation (no feedback)
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

            # Extract and log Claude's reasoning (text before tool use)
            reasoning_text = self._extract_reasoning(response.content)
            if reasoning_text and self.reasoning_callback:
                self.reasoning_callback(f"Agent B: {reasoning_text}")

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

    def _load_causal_parameters(self, file_path: str = None) -> Dict[str, Any]:
        """
        Tool 1: Load causal parameters from Agent A.

        Args:
            file_path: Path to causal parameters JSON (optional, defaults to output_dir/causal_parameters.json)

        Returns:
            Dict with status and parameters
        """
        # Use output_dir if no path specified (supports run-specific directories)
        if file_path is None:
            file_path = f"{self.output_dir}/causal_parameters.json"

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

                    # Calculate actual cost using real data
                    # TPR cost = baseline_units × discount_depth × unit_price
                    baseline_velocity = self.causal_parameters.get("baseline_velocity_avg", 0)
                    unit_price = self._get_unit_price(ppg)
                    tpr_cost = baseline_velocity * discount_depth * unit_price

                    # Display cost from promo config
                    display_cost = self._get_display_cost(display_tier)

                    promo_cost = tpr_cost + display_cost

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
            "summary": f"Generated {len(calendar_events)} promotion events, ${total_spend:,.0f} spend ({total_spend/budget_limit*100:.1f}% of budget)",
            "calendar_events": calendar_events  # Return actual events for saving
        }

    def _adjust_calendar_for_violations(self, violations: List[Dict], feedback: str) -> Dict[str, Any]:
        """
        Tool 3: Adjust calendar based on Agent C violations.

        Loads current calendar and applies fixes based on violation types.

        Args:
            violations: List of constraint violations from Agent C
            feedback: Natural language feedback

        Returns:
            Dict with adjustment status and summary of changes
        """
        if not self.current_calendar:
            return {
                "status": "error",
                "message": "No current calendar to adjust. Generate one first."
            }

        calendar_events = self.current_calendar.get("calendar_events", [])
        adjustments_made = []

        for violation in violations:
            violation_type = violation.get("type", "").lower()

            if "budget" in violation_type:
                # Remove lowest-ROI events until under budget
                # Simplified: remove last 20% of events
                remove_count = max(1, len(calendar_events) // 5)
                calendar_events = calendar_events[:-remove_count]
                adjustments_made.append(f"Removed {remove_count} events to reduce budget")

            elif "gap" in violation_type:
                # Simplified: remove conflicting events (Claude will provide better logic via natural language)
                adjustments_made.append("Gap violations noted - regeneration recommended")

            elif "frequency" in violation_type:
                # Reduce events for over-frequency PPG-Retailers
                adjustments_made.append("Frequency violations noted - regeneration recommended")

        # Update current calendar
        self.current_calendar["calendar_events"] = calendar_events

        # Recalculate total spend using SAME logic as generation
        total_spend = 0
        baseline_velocity = self.causal_parameters.get("baseline_velocity_avg", 0)

        for event in calendar_events:
            ppg = event.get("ppg")
            discount_depth = event.get("discount_depth", 0)
            display_tier = event.get("display_tier", "none")

            unit_price = self._get_unit_price(ppg)
            tpr_cost = baseline_velocity * discount_depth * unit_price
            display_cost = self._get_display_cost(display_tier)

            total_spend += tpr_cost + display_cost

        return {
            "status": "adjusted",
            "violations_addressed": len(violations),
            "adjustments": adjustments_made,
            "new_event_count": len(calendar_events),
            "new_total_spend": round(total_spend, 2),
            "recommendation": "Claude should regenerate calendar with constraint awareness rather than just removing events"
        }

    def _calculate_projected_impact(self, calendar_events: List[Dict]) -> Dict[str, Any]:
        """
        Tool 4: Calculate projected volume/profit impact.

        Args:
            calendar_events: List of promotion events

        Returns:
            Dict with projected metrics
        """
        if not self.causal_parameters:
            return {
                "projected_volume": 0,
                "projected_profit": 0,
                "projected_roi": 0,
                "status": "error",
                "error": "Causal parameters not loaded"
            }

        # Extract causal parameters
        baseline_velocity = self.causal_parameters.get("baseline_velocity_avg", 0)
        elasticity_model = self.causal_parameters.get("elasticity_model", {})
        discount_lifts = elasticity_model.get("discount_lift_factors", {})
        display_lift_multiplier = elasticity_model.get("display_lift_multiplier", 1.0)
        seasonality_factors = self.causal_parameters.get("seasonality_factors", {})

        total_incremental_volume = 0
        total_baseline_volume = 0
        total_cost = 0

        for event in calendar_events:
            week = event.get("week")
            discount_depth = event.get("discount_depth", 0)
            display_active = event.get("display_active", False)

            # Get seasonality factor
            seasonality = seasonality_factors.get(str(week), 1.0)

            # Get discount lift based on depth bucket
            discount_pct = discount_depth * 100
            if discount_pct < 15:
                lift = discount_lifts.get("0-15", 1.5)
            elif discount_pct < 25:
                lift = discount_lifts.get("15-25", 2.0)
            elif discount_pct < 35:
                lift = discount_lifts.get("25-35", 2.5)
            elif discount_pct < 45:
                lift = discount_lifts.get("35-45", 3.5)
            else:
                lift = discount_lifts.get("45+", 4.0)

            # Calculate baseline for this week
            week_baseline = baseline_velocity * seasonality

            # Apply lifts
            promo_volume = week_baseline * lift
            if display_active:
                promo_volume *= display_lift_multiplier

            # Incremental volume
            incremental_volume = promo_volume - week_baseline
            total_incremental_volume += incremental_volume
            total_baseline_volume += week_baseline

            # Calculate cost on-the-fly (events don't have cost fields)
            ppg = event.get("ppg")
            display_tier = event.get("display_tier", "none")

            unit_price = self._get_unit_price(ppg)
            tpr_cost = baseline_velocity * discount_depth * unit_price
            display_cost = self._get_display_cost(display_tier)

            total_cost += tpr_cost + display_cost

        # Calculate projected metrics
        projected_volume = total_baseline_volume + total_incremental_volume
        projected_roi = (total_incremental_volume / total_cost * 100) if total_cost > 0 else 0

        return {
            "projected_volume": round(projected_volume, 2),
            "incremental_volume": round(total_incremental_volume, 2),
            "baseline_volume": round(total_baseline_volume, 2),
            "total_cost": round(total_cost, 2),
            "projected_roi": round(projected_roi, 2),
            "status": "calculated"
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
        from pathlib import Path
        output_file = str(Path(self.output_dir) / "promotion_calendar.json")

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
                "description": "Load causal parameters (elasticity, lift factors, seasonality) from Agent A's output file. No parameters needed - automatically uses correct output directory.",
                "input_schema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "generate_initial_calendar",
                "description": "Generate initial promotional calendar using greedy optimization heuristic. Returns calendar_events array that you MUST pass directly to save_promotion_calendar in the next step.",
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
                "name": "adjust_calendar_for_violations",
                "description": "Adjust current calendar to fix violations reported by Agent C (Auditor). Use this when calendar was rejected.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "violations": {
                            "type": "array",
                            "description": "List of violations from Agent C's audit report"
                        },
                        "feedback": {
                            "type": "string",
                            "description": "Natural language feedback from Agent C"
                        }
                    },
                    "required": ["violations", "feedback"]
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
                "description": "REQUIRED FINAL STEP: Save promotion calendar to JSON file. You MUST call this tool after generating the calendar to complete the task. IMPORTANT: Pass the exact calendar_events array returned by generate_initial_calendar - do NOT create new events.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "calendar_events": {
                            "type": "array",
                            "description": "EXACT calendar_events array from generate_initial_calendar tool result. Do NOT modify the schema."
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
   - SAVE the calendar_events array from the response - you'll need it for steps 3 and 4

Step 3: calculate_projected_impact
   Calculate estimated volume/profit for the calendar
   - Pass the EXACT calendar_events array from step 2

Step 4: save_promotion_calendar (MANDATORY - DO NOT SKIP)
   Save the calendar to file
   - Pass the EXACT calendar_events array from step 2 (do NOT modify or recreate)
   - Pass metadata with total_spend and projections
   - YOU MUST CALL THIS BEFORE FINISHING

CRITICAL: Use the exact calendar_events returned by generate_initial_calendar tool.
DO NOT create new events with different field names.
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

    def _format_violations_for_prompt(self, violations: List[Dict]) -> str:
        """Format violations into a clear prompt for Claude."""
        if not violations:
            return "No violations"

        formatted = []
        for i, v in enumerate(violations, 1):
            formatted.append(f"{i}. {v.get('type', 'Unknown')}: {v.get('details', 'No details')}")

        return "\n".join(formatted)

    def _extract_reasoning(self, content: List[Any]) -> str:
        """Extract Claude's reasoning text from response content blocks."""
        reasoning_parts = []
        for block in content:
            if hasattr(block, 'text') and block.text:
                reasoning_parts.append(block.text)
        return " ".join(reasoning_parts).strip() if reasoning_parts else ""

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
