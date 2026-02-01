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
        max_iterations: int = 20,
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
        self.client = Anthropic(api_key=api_key, base_url='https://api.ai-gateway.tigeranalytics.com')
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

        self.sales_data = loader.load_sales()
        self.finance_data = loader.load_financials()
        self.promo_config = loader.load_promo_config()

        logger.info(f"Initialized StrategistAgent: objective={self.objective}, budget=${budget_limit:,.0f}")
        logger.info(f"Loaded sales data: {len(self.sales_data)} rows")
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
        Get average unit price for PPG from sales_v2.xlsx.

        Uses actual transaction prices from historical sales data.

        Args:
            ppg: Product group identifier (e.g., "Brand 5_Promo.Group 6")

        Returns:
            Average unit price from sales transactions
        """
        if self.sales_data is None:
            raise ValueError("Sales data not loaded - cannot calculate TPR costs")

        # Filter sales data for this PPG
        ppg_sales = self.sales_data[self.sales_data["PPG"] == ppg.replace("'","")]

        if ppg_sales.empty:
            logger.warning(f"PPG '{ppg}' not found in sales data - using default price $2.50")
            return 2.50

        # Average unit price across all transactions for this PPG
        unit_price = ppg_sales["Unit Price"].mean()
        logger.debug(f"PPG '{ppg}': {len(ppg_sales)} sales records, avg price ${unit_price:.2f}")
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

    def _get_unit_margin(self, ppg: str, retailer: str) -> float:
        """
        Get retailer margin for PPG from Finance.xlsx.

        Args:
            ppg: Product group identifier (from Sales data, without APN)
            retailer: Retailer identifier (e.g., "Retailer 0")

        Returns:
            Retailer margin as decimal (e.g., 0.39 for 39% margin)
        """
        if self.finance_data is None:
            logger.warning("Finance data not loaded - using default margin 30%")
            return 0.30

        # Match PPGs by prefix and retailer
        ppg_finance = self.finance_data[
            (self.finance_data["PPG"].str.startswith(ppg + "_", na=False)) &
            (self.finance_data["Retailer"] == retailer)
        ]

        if ppg_finance.empty:
            logger.warning(f"PPG '{ppg}' at '{retailer}' not found in Finance.xlsx - using default margin 30%")
            return 0.30

        # Average margin across all APNs for this PPG-Retailer combination
        unit_margin = ppg_finance["Retailer Margin"].mean()
        logger.debug(f"PPG '{ppg}' at '{retailer}': {len(ppg_finance)} APNs found, avg margin {unit_margin:.2%}")
        return unit_margin

    def _select_optimal_display_tier(self, ppg: str, baseline_velocity: float, unit_price: float, objective: str, budget_remaining: float = float('inf')) -> str:
        """
        Select optimal display tier based on ROI calculation.

        For each tier, calculates:
        - Incremental units from display (using tier-specific lift from Agent A)
        - Incremental revenue = incremental units × price
        - Display cost (from Promo_config.csv)
        - ROI = (Incremental Revenue - Display Cost) / Display Cost

        Args:
            ppg: Product group identifier
            baseline_velocity: Baseline units per week
            unit_price: Unit price for this PPG
            objective: 'volume' or 'profit'

        Returns:
            Optimal tier name (platinum, gold, silver, bronze, or none)
        """
        if not self.causal_parameters:
            # Fallback to hardcoded if causal params not loaded
            return "gold" if objective == "volume" else "silver"

        tier_lifts = self.causal_parameters.get("tier_specific_display_lifts", {})

        if not tier_lifts:
            # Fallback if no tier data
            return "gold" if objective == "volume" else "silver"

        # Display tier costs (from Promo_config.csv)
        tier_costs = {
            "platinum": 500,
            "gold": 400,
            "silver": 350,
            "bronze": 300,
            "none": 0
        }

        best_tier = "gold"  # Default
        best_roi = -float('inf')

        # Get TPR-only baseline for comparison
        tpr_only_volume = self.causal_parameters.get("tactic_combination_effects", {}).get("tpr_only", baseline_velocity * 1.45)

        # Create a ranked list of tiers by score
        tier_scores = []

        for tier in ["platinum", "gold", "silver", "bronze"]:
            # Get tier-specific lift (these are lifts comparing TPR+Display(tier) vs TPR-only)
            tier_lift = tier_lifts.get(f"{tier}_lift", 1.0)

            # Calculate volume with this tier: TPR-only × tier_lift
            # The tier_lift from Agent A is already relative to TPR-only baseline
            tier_volume = tpr_only_volume * tier_lift

            # Incremental from this specific tier = tier_volume - tpr_only
            incremental_units = tier_volume - tpr_only_volume

            # Incremental revenue
            incremental_revenue = incremental_units * unit_price

            # Display cost
            display_cost = tier_costs.get(tier, 0)

            # Calculate ROI: (Revenue - Cost) / Cost
            if display_cost > 0:
                roi = (incremental_revenue - display_cost) / display_cost
            else:
                roi = 0

            # For volume: maximize incremental units
            # For profit: maximize ROI
            if objective == "volume":
                score = incremental_units  # Prioritize volume
            else:
                score = roi  # Prioritize ROI

            tier_scores.append({
                'tier': tier,
                'score': score,
                'cost': display_cost,
                'roi': roi,
                'incremental_units': incremental_units
            })

        # Sort by score (descending)
        tier_scores.sort(key=lambda x: x['score'], reverse=True)

        # Select best tier that fits budget
        selected = False
        for tier_info in tier_scores:
            if tier_info['cost'] <= budget_remaining:
                best_tier = tier_info['tier']
                best_roi = tier_info['score']
                selected = True
                break

        # If no tier fits budget, select cheapest tier or no display
        if not selected:
            tier_scores.sort(key=lambda x: x['cost'])  # Sort by cost ascending
            if tier_scores and tier_scores[0]['cost'] <= budget_remaining:
                best_tier = tier_scores[0]['tier']
            else:
                best_tier = "none"  # No budget for any display

        logger.debug(f"Selected {best_tier} display for {ppg} (objective={objective}, score={best_roi if selected else 0:.2f})")
        return best_tier

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
3. Calculate projected impact for the adjusted calendar. 
IMPORTANT: Pass the EXACT calendar_events returned by adjust_calendar_for_violations - 
DO NOT create new events.  DO NOT alter schema.
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
3. Calculate projected impact. 
IMPORTANT: Pass the EXACT calendar_events returned by generate_initial_calendar - 
DO NOT create new events. DO NOT alter schema. 
4. REQUIRED: Call save_promotion_calendar to save the calendar to file

Be strategic and data-driven. Every promotion must have clear reasoning.
You MUST complete step 4 - calling save_promotion_calendar is mandatory."""

        messages = [{"role": "user", "content": user_message}]

        # Multi-turn conversation loop
        while self.iteration < self.max_iterations:
            self.iteration += 1
            logger.info(f"Iteration {self.iteration}/{self.max_iterations}")

            response = self.client.messages.create(
                model="gemini-2.0-flash",
                max_tokens=8192,  # Larger for calendar generation
                system=self._get_system_prompt(),
                tools=self._get_tool_definitions(),
                tool_choice={"type": "any"},
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

        # Track last week scheduled per PPG-Retailer to enforce gap constraint
        from collections import defaultdict
        last_week_scheduled = defaultdict(lambda: -10)  # Start at -10 so first event is always valid

        # Generate events with constraint awareness
        MIN_GAP_WEEKS = 4  # Minimum weeks between promotions for same PPG-Retailer

        for ppg in ppgs:
            for retailer in retailers:
                # Target events per PPG-Retailer based on retailer capacity
                target_events = 4 if retailer == "Retailer 0" else 6
                events_added = 0

                # Iterate through weeks in seasonality order
                for week, season_factor in weeks_ranked:
                    if total_spend >= target_spend:
                        break

                    if events_added >= target_events:
                        break

                    # Check gap constraint: has it been at least MIN_GAP_WEEKS since last promo?
                    key = (ppg, retailer)
                    weeks_since_last = week - last_week_scheduled[key]

                    if weeks_since_last < MIN_GAP_WEEKS:
                        continue  # Skip this week, too close to last promotion

                    # Choose tactics based on objective
                    if objective == "volume":
                        discount_depth = 0.35  # Deeper discount for volume
                    else:
                        discount_depth = 0.25  # Moderate discount for profit

                    # Calculate actual cost using real data
                    # TPR cost = baseline_units × discount_depth × unit_price
                    baseline_velocity = self.causal_parameters.get("baseline_velocity_avg", 0)
                    unit_price = self._get_unit_price(ppg)
                    tpr_cost = baseline_velocity * discount_depth * unit_price

                    # Select optimal display tier based on ROI and budget
                    budget_remaining = target_spend - total_spend
                    display_tier = self._select_optimal_display_tier(
                        ppg=ppg,
                        baseline_velocity=baseline_velocity,
                        unit_price=unit_price,
                        objective=objective,
                        budget_remaining=budget_remaining
                    )

                    # Display cost from promo config
                    display_cost = self._get_display_cost(display_tier)

                    promo_cost = tpr_cost + display_cost

                    # Check budget constraint
                    if total_spend + promo_cost > target_spend:
                        continue  # Skip this event, would exceed budget

                    # Add event
                    calendar_events.append({
                        "week": week,
                        "ppg": ppg.replace("'", ""),
                        "retailer": retailer.replace("'", ""),
                        "discount_depth": discount_depth,
                        "display_tier": display_tier.replace("'", ""),
                        "feature_active": False,
                        "reasoning": f"Week {week} (seasonality {season_factor} x) for {ppg} at {retailer}"
                    })

                    total_spend += promo_cost
                    last_week_scheduled[key] = week
                    events_added += 1
                    logger.info(f"Week:{week},PPG:{ppg},Retailer:{retailer},Discount:{discount_depth},Display:{display_tier},Spend:{total_spend}")

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
            "summary": f"Generated {len(calendar_events)} promotion events, ${total_spend:.0f} spend ({total_spend/budget_limit*100:.1f}% of budget)",
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

        calendar_events = self.current_calendar.get("calendar_events", []).copy()
        budget_limit = self.budget_limit
        adjustments_made = []
        baseline_velocity = self.causal_parameters.get("baseline_velocity_avg", 0)

        # Process violations in priority order: budget first, then gaps
        has_budget_violation = any("budget" in v.get("type", "").lower() for v in violations)
        has_gap_violation = any("gap" in v.get("type", "").lower() for v in violations)

        # Fix budget violations by removing highest-cost events
        if has_budget_violation:
            # Calculate cost per event
            events_with_cost = []
            for event in calendar_events:
                ppg = event.get("ppg")
                discount_depth = event.get("discount_depth", 0)
                display_tier = event.get("display_tier", "none")

                unit_price = self._get_unit_price(ppg)
                tpr_cost = baseline_velocity * discount_depth * unit_price
                display_cost = self._get_display_cost(display_tier.replace("'", ""))
                total_cost = tpr_cost + display_cost

                events_with_cost.append((event, total_cost))

            # Sort by cost (highest first) and remove until under budget
            events_with_cost.sort(key=lambda x: x[1], reverse=True)

            # Calculate current total
            current_total = sum(cost for _, cost in events_with_cost)

            # Remove events until under budget
            removed_count = 0
            while current_total > budget_limit and events_with_cost:
                removed_event, removed_cost = events_with_cost.pop(0)
                current_total -= removed_cost
                removed_count += 1

            calendar_events = [event for event, _ in events_with_cost]
            adjustments_made.append(f"Removed {removed_count} highest-cost events to meet budget (now ${current_total:,.0f})")

        # Fix gap violations by spreading out events
        if has_gap_violation:
            # Group events by PPG-Retailer
            from collections import defaultdict
            ppg_retailer_events = defaultdict(list)

            for event in calendar_events:
                key = (event.get("ppg"), event.get("retailer"))
                ppg_retailer_events[key].append(event)

            # For each PPG-Retailer, ensure min 4-week gaps
            fixed_events = []
            gap_fixes = 0

            for (ppg, retailer), events in ppg_retailer_events.items():
                # Sort by week
                events_sorted = sorted(events, key=lambda e: e.get("week", 0))

                # Keep first event, check gaps for rest
                if events_sorted:
                    fixed_events.append(events_sorted[0])
                    last_week = events_sorted[0].get("week", 0)

                    for event in events_sorted[1:]:
                        week = event.get("week", 0)
                        if week - last_week >= 4:  # Min gap is 4 weeks
                            fixed_events.append(event)
                            last_week = week
                        else:
                            gap_fixes += 1
                            # Skip this event (too close to previous)

            calendar_events = fixed_events
            if gap_fixes > 0:
                adjustments_made.append(f"Removed {gap_fixes} events that violated 4-week minimum gap rule")

        # Update current calendar
        self.current_calendar["calendar_events"] = calendar_events

        # Recalculate total spend
        total_spend = 0
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
            "budget_utilization_pct": round(total_spend / budget_limit * 100, 1),
            "message": "Calendar adjusted successfully. Use calculate_projected_impact and save_promotion_calendar to finalize."
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
        tactic_effects = self.causal_parameters.get("tactic_combination_effects", {})
        seasonality_factors = self.causal_parameters.get("seasonality_factors", {})

        # Get actual lift values from tactic combinations (more accurate than multiplicative model)
        tpr_only_volume = tactic_effects.get("tpr_only", baseline_velocity * 1.45)
        tpr_plus_display_volume = tactic_effects.get("tpr_plus_display", baseline_velocity * 5.76)
        tpr_plus_feature_volume = tactic_effects.get("tpr_plus_feature", baseline_velocity * 2.19)
        tpr_plus_both_volume = tactic_effects.get("tpr_plus_both", baseline_velocity * 2.98)

        total_incremental_volume = 0
        total_baseline_volume = 0
        total_cost = 0
        total_incremental_profit = 0

        for event in calendar_events:
            if event != "" and isinstance(event, str) and '{' in event:
                event = json.loads(event)
            elif event != "" and isinstance(event, str):
                event_dict = {}
                event_parts = event.split(',')
                for part in event_parts:
                    if '=' in part:
                        key, val = part.split('=',1)
                        key = key.strip()
                        val = val.strip()
                        # Convert numeric values
                        if key in ['week', 'discount_depth']:
                            try:
                                val = float(val) if '.' in val else int(val)
                            except ValueError:
                                pass
                
                        # Convert boolean values
                        elif key in ['feature_active']:
                            val = val.lower() == 'true'
                
                    event_dict[key] = val
                event = event_dict
            week = event.get("week")
            discount_depth = event.get("discount_depth", 0)
            display_active = event.get("display_active", False)
            feature_active = event.get("feature_active", False)
            ppg = event.get("ppg")
            retailer = event.get("retailer")
            display_tier = event.get("display_tier", "none")

            # Get seasonality factor
            seasonality = seasonality_factors.get(str(week), 1.0)

            # Calculate baseline for this week
            week_baseline = baseline_velocity * seasonality

            # Use tactic combination effects (empirical data) instead of multiplicative model
            # This avoids unrealistic lift compounding
            has_display = display_active or (display_tier and display_tier.lower() != "none")
            has_feature = feature_active

            if has_display and has_feature:
                # TPR + Display + Feature
                promo_volume = week_baseline * (tpr_plus_both_volume / baseline_velocity)
            elif has_display:
                # TPR + Display only
                promo_volume = week_baseline * (tpr_plus_display_volume / baseline_velocity)
            elif has_feature:
                # TPR + Feature only
                promo_volume = week_baseline * (tpr_plus_feature_volume / baseline_velocity)
            else:
                # TPR only
                promo_volume = week_baseline * (tpr_only_volume / baseline_velocity)

            # Incremental volume
            incremental_volume = promo_volume - week_baseline
            total_incremental_volume += incremental_volume
            total_baseline_volume += week_baseline

            # Calculate cost on-the-fly (events don't have cost fields)
            unit_price = self._get_unit_price(ppg)
            tpr_cost = baseline_velocity * discount_depth * unit_price
            display_cost = self._get_display_cost(display_tier)
            event_cost = tpr_cost + display_cost
            total_cost += event_cost

            # Calculate incremental revenue
            # Revenue = Incremental Units × Unit Price
            incremental_revenue = incremental_volume * unit_price
            total_incremental_profit += incremental_revenue  # Using revenue for ROI

        # Calculate projected metrics
        projected_volume = total_baseline_volume + total_incremental_volume

        # ROI = (Incremental Revenue - Total Cost) / Total Cost × 100
        # This shows return per dollar spent on promotions
        projected_roi = ((total_incremental_profit - total_cost) / total_cost * 100) if total_cost > 0 else 0

        return {
            "projected_volume": round(projected_volume, 2),
            "incremental_volume": round(total_incremental_volume, 2),
            "baseline_volume": round(total_baseline_volume, 2),
            "total_cost": round(total_cost, 2),
            "incremental_revenue": round(total_incremental_profit, 2),
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
        calendar_event_dict = []
        for event in calendar_events:
            try:
                if event != "" and isinstance(event, str) and '{' in event:
                    event = json.loads(event)
                elif event != "" and isinstance(event, str):
                    event_dict = {}
                    event_parts = event.split(',')
                    for part in event_parts:
                        if '=' in part:
                            key, val = part.split('=',1)
                            key = key.strip()
                            val = val.strip()
                            # Convert numeric values
                            if key in ['week', 'discount_depth']:
                                try:
                                    val = float(val) if '.' in val else int(val)
                                except ValueError:
                                    pass                   
                            # Convert boolean values
                            elif key in ['feature_active']:
                                val = val.lower() == 'true'                   
                        event_dict[key] = val
                    event = event_dict
            except json.JSONDecodeError as e:
                logger.error(e)                
            calendar_event_dict.append(event)
        calendar_events = calendar_event_dict

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
                try:
                    json.dump(calendar_data, f, indent=2)
                except json.JSONDecodeError as e:
                    logger.error(e.__traceback__)

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
                            "description": "List of promotion event objects",
                            "calendar_events": {
                                "type": "object",
                                "properties": {
                                    "week": {
                                        "type": "integer",
                                        "description": "Week number 1-52"
                                    },
                                    "ppg": {
                                        "type": "string",
                                        "description": "PPG"
                                    },
                                    "retailer": {
                                        "type": "string",
                                        "description": "Retailer"
                                    },
                                    "discount_depth": {
                                        "type": "number",
                                        "description": "Discount depth float/ decimal"
                                    },
                                    "display_tier": {
                                        "type": "string",
                                        "enum": ["platinum", "silver","gold", "bronze"],
                                        "description": "Display tier",
                                    },
                                    "feature_active": {
                                        "type": "boolean",
                                        "description": "Feature Active (true/false)"
                                    },
                                    "reasoning":{
                                        "type": "string",
                                        "description": "Promotion reason"
                                    }
                                },
                                "required": ["week", "ppg", "retailer", "discount_depth", "display_tier", "feature_active", "reasoning"]
                            }
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
                            "description": "Additional metadata (total_spend, projected_impact, etc.)",
                            "metadata": {
                                "total_spend": {
                                    "type": "number",
                                    "description": "Total event cost. IMPORTANT: return total_cost returned in result of calculate_projected_impact"
                                },
                                "projected_impact": {
                                    "type": "number",
                                    "description": "projected_roi returned by calculate_projected_impact"  
                                }
                            },
                            "required": ['total_spend', 'projected_impact']
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
   - calendar_events data structure should be the same as what is in step 2


Step 4: save_promotion_calendar (MANDATORY REQUIREMENT - DO NOT SKIP)
   Save the calendar to file
   - REQUIRED: Pass the EXACT calendar_events array from step 2 (do NOT modify or recreate)
   - REQUIRED: Pass metadata with total_spend and projections result returned by calculate_projected_impact 
   - YOU MUST CALL THIS BEFORE FINISHING

CRITICAL REQUIREMENT: Use the exact calendar_events returned by generate_initial_calendar tool.
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
                    if entry != "" and isinstance(entry, str):
                        entry = json.loads(entry)
                    f.write(f"Iteration {entry['iteration']}:\n")
                    f.write(f"  User: {entry['user_message'][:200]}...\n")
                    f.write(f"  Response Type: {entry['response_type']}\n")
                    f.write(f"  Tools Called: {', '.join(entry['tool_calls']) if entry['tool_calls'] else 'None'}\n")
                    f.write("\n")

            logger.success(f"Saved execution log to {log_file}")

        except Exception as e:
            logger.error(f"Failed to save execution log: {e}")
