import json
import os
import numpy as np
from typing import Dict, Any, List
from openai import OpenAI
from pathlib import Path
from ..utils.data_loader import DataLoader


class CreativeCalendarAgent:
    """
    Agent Strategist: Creative Intelligence for Promotion Calendar Generation

    Takes causal parameters from Agent A and generates optimized promotion calendars
    based on business objectives (Volume/Profit maximization).
    """

    def __init__(self, api_key: str = None):
        """
        Initialize the Creative Calendar Agent.

        Args:
            api_key: API key (defaults to API_KEY env var)
        """
        self.client = OpenAI(api_key=api_key or os.getenv("API_KEY"))
        self.model = "gemini-2.5-flash"
        data_loader = DataLoader(str(Path("case-data")))
        self.sales_data = self.data_loader.load_sales()
        self.retailer_list = self.sales_data['Retailer'].unique().tolist()
        self.ppg_list = self.sales_data['PPG'].unique().tolist()

    def _load_causal_parameters(self, filepath: str) -> Dict[str, Any]:
        """Load causal parameters from Agent A."""
        with open(filepath, 'r') as f:
            return json.load(f)

    def _load_display_config(self, filepath: str) -> str:
        """Load display configuration CSV as text."""
        with open(filepath, 'r') as f:
            return f.read()

    def _load_objective_prompt(self, filepath: str) -> str:
        """Load business objective prompt."""
        with open(filepath, 'r') as f:
            return f.read()

    def _define_tools(self) -> List[Dict[str, Any]]:
        """
        Define tools available to Agent B for calendar construction.

        Returns:
            List of tool definitions in OpenAI format
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "add_promotion_event",
                    "description": "Add a promotion event to the draft calendar. Use this to build the calendar event by event.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "retailer": {
                                "type": "string",
                                "description": "Retailer to run promotion at",
                                "enum": self.retailer_list
                            },
                            "week": {
                                "type": "integer",
                                "description": "Week number (1-52) for the promotion",
                                "enum": np.range(53)
                            },
                            "ppg": {
                                "type": "string",
                                "description": "ppg identifier for the product",
                                "enum": self.ppg_list
                            },
                            "discount_depth": {
                                "type": "number",
                                "description": "Discount depth as decimal (e.g., 0.30 for 30%)"
                            },
                            "display_active": {
                                "type": "boolean",
                                "description": "Whether display/merchandising is active"
                            },
                            "display_tier": {
                                "type": "string",
                                "description": "Display tier if applicable (Platinum, Gold, Silver, Bronze)",
                                "enum": ["Platinum", "Gold", "Silver", "Bronze", "None"]
                            },
                            "promo_feature": {
                                "type": "boolean",
                                "description": "Whether feature/advertising is active"
                            },
                            "reasoning": {
                                "type": "string",
                                "description": "Strategic reasoning for this promotion event"
                            }
                        },
                        "required": ["retailer", "week", "ppg", "discount_depth", "display_active", "reasoning"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "calculate_event_cost",
                    "description": "Calculate the projected cost of a promotion event based on causal parameters.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "retailer": {
                                "type": "string",
                                "description": "Retailer to run promotion at",
                            },
                            "week": {
                                "type": "integer",
                                "description": "Week number"
                            },
                            "ppg": {
                                "type": "string",
                                "description": "PPG identifier"
                            },
                            "discount_depth": {
                                "type": "number",
                                "description": "Discount depth as decimal"
                            },
                            "display_active": {
                                "type": "boolean",
                                "description": "Whether display is active"
                            },
                            "display_tier": {
                                "type": "string",
                                "description": "Display tier if applicable (Platinum, Gold, Silver, Bronze)",
                                "enum": ["Platinum", "Gold", "Silver", "Bronze", "None"]
                            },
                            "promo_feature": {
                                "type": "boolean",
                                "description": "Whether feature/advertising is active"
                            },
                        },
                        "required": ["retailer","week", "ppg", "discount_depth", "display_active","display_tier","promo_feature"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "finalize_calendar",
                    "description": "Finalize and save the promotion calendar. Call this once all events are added.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "objective_summary": {
                                "type": "string",
                                "description": "Summary of the objective that was optimized for"
                            }
                        },
                        "required": ["objective_summary"]
                    }
                }
            }
        ]

    def _execute_tool(self, tool_name: str, arguments: Dict[str, Any],
                      causal_params: Dict[str, Any],
                      calendar_state: Dict[str, Any]) -> str:
        """
        Execute a tool call and return the result.

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            causal_params: Causal parameters from Agent A
            calendar_state: Current calendar construction state

        Returns:
            JSON string with tool execution result
        """
        if tool_name == "add_promotion_event":
            # Add event to calendar
            event = {
                "retailer": arguments["retailer"],
                "week": calendar_state["next_week"],
                "ppg": arguments["ppg"],
                "discount_depth": arguments["discount_depth"],
                "display_active": arguments["display_active"],
                "display_tier": arguments.get("display_tier", "None"),
                "promo_feature": arguments.get("feature_active", False),
                "reasoning": arguments["reasoning"],
                "projected_outcome": self._calculate_projected_outcome(
                    arguments, causal_params
                )
            }

            retail_ppg_week_key = f"{event["retailer"]}.{event["ppg"]}.{event["week"]}"
            if  retail_ppg_week_key not in calendar_state["used_combos"]:
                calendar_state["events"].append(event)
                # Calculate running spend
                cost = self._estimate_event_cost(arguments, causal_params)
                calendar_state["total_spend"] += cost
                calendar_state["used_combos"].append(retail_ppg_week_key)

                return json.dumps({
                    "success": True,
                    "event_added": event,
                    "running_total_spend": calendar_state["total_spend"],
                    "events_count": len(calendar_state["events"])
                })
            
            else:
                return json.dumps({
                    "success": False,
                    "error": f"{retail_ppg_week_key} has already been assigned."
                })

        elif tool_name == "calculate_event_cost":
            # Calculate projected cost
            cost = self._estimate_event_cost(arguments, causal_params)
            outcome = self._calculate_projected_outcome(
                arguments, causal_params)

            return json.dumps({
                "projected_cost": cost,
                "projected_outcome": outcome,
                "spend_remaining": calendar_state["budget_limit"] - calendar_state["total_spend"]
            })

        elif tool_name == "finalize_calendar":
            # Finalize the calendar
            calendar_state["objective"] = arguments["objective_summary"]
            calendar_state["finalized"] = True

            return json.dumps({
                "success": True,
                "total_events": len(calendar_state["events"]),
                "total_spend": calendar_state["total_spend"],
                "budget_limit": calendar_state["budget_limit"],
                "budget_utilization": calendar_state["total_spend"] / calendar_state["budget_limit"]
            })

        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})

    def _calculate_projected_outcome(self, event: Dict[str, Any],
                                     causal_params: Dict[str, Any]) -> str:
        """Calculate projected outcome for an event using causal parameters."""
        # Extract parameters
        retailer =event["retailer"]
        ppg = event["ppg"]
        week = event["week"]
        discount = event["discount_depth"]
        display = event.get("display_active", False)
        display_tier =event.get("display_tier", "")
        promo_feature = event.get("promo_feature", False)

        # Get baseline (simplified - you'd lookup actual PPG baseline)
        baseline = causal_params.get("baseline_velocity_avg")+causal_params.get("elasticity_model",{}).get("seasonality_factors",{}).get(week,"")
        base_price = self.sales_data[(self.sales_data["Retailer"]==retailer) &
                                        (self.sales_data["PPG"]==ppg)]["Calculated_Based_Price"].mean()

        # Get elasticity
        elasticity = causal_params.get("elasticity_model", {}).get("base_price_elasticity", -2.0)
        discount_depth = ""
        if discount <15:
            discount_depth="0-15"  
        elif discount < 25:
            discount_depth="15-25"
        elif discount < 35:
            discount_depth="25-35" 
        elif discount < 45:
            discount_depth="35-45"
        elif discount > 45:
            discount_depth="45+"
        else:
            discount=""
    
        discount_lift = causal_params.get("elasticity_model",{}).get("discount_lift_factors",{}).get(discount_depth,1.5)

        # Calculate discount lift
        price_lift = (base_price-base_price*discount) ** elasticity

        # Get display lift
        display_lift = 1.0
        if display:
            display_lift = causal_params.get("elasticity_model",{}).get("tier_specific_display_lifts",{}).get(display_tier, 4.3)
            
        # Get Feature Lift
        feature_lift = 1.0
        if promo_feature:
            feature_lift = causal_params.get("elasticity_model",{}).get("feature_lift_multiplier",1.0)
            
        # Promo Combo Effect
        combo_lift = 0
        if discount and not display and not promo_feature:
            combo_lift = causal_params.get("elasticity_model",{}).get("tactic_combination_effects",{}).get("tpr_only",0)
        elif discount and display and not promo_feature:
            combo_lift = causal_params.get("elasticity_model",{}).get("tactic_combination_effects",{}).get("tpr_plus_display",0)
        elif discount and not display and promo_feature:
            combo_lift = causal_params.get("elasticity_model",{}).get("tactic_combination_effects",{}).get("tpr_plus_feature",0)
        elif discount and display and promo_feature:
            combo_lift = causal_params.get("elasticity_model",{}).get("tactic_combination_effects",{}).get("tpr_plus_both",0)

        # Calculate total lift
        total_lift = price_lift + discount_lift + display_lift + combo_lift
        lift = total_lift/baseline

        return f"Lift of {lift:.1f}x baseline (~{int(baseline * total_lift)} units)"

    def _estimate_event_cost(self, event: Dict[str, Any],
                             causal_params: Dict[str, Any]) -> float:
        """Estimate cost of a promotion event."""
        # Simplified cost calculation
        # In reality, you'd use: discount_cost + display_cost + feature_cost
        baseline = causal_params.get("baseline_velocity_avg")+causal_params.get("elasticity_model",{}).get("seasonality_factors",{}).get(event["week"],"")
        discount = event["discount_depth"]
        # TODO --- Add Financials file and fix cost calculation
        # Rough estimate: baseline units * lift * discount depth * unit price
        unit_price = 10  # You'd get this from product data
        elasticity = causal_params.get("elasticity", {}).get("mean", -2.0)
        lift = (1 + discount) ** elasticity

        display_cost = 5000 if event.get("display_active") else 0

        return (baseline * lift * discount * unit_price) + display_cost

    def generate_calendar(self,
                          causal_parameters_path: str,
                          budget_limit: float,
                          display_config_path: str,
                          objective_prompt_path: str,
                          output_path: str = "outputs/draft_calendar_candidate.json") -> Dict[str, Any]:
        """
        Generate promotion calendar using Gemini.

        Args:
            causal_parameters_path: Path to causal_parameters.json from Agent A
            budget_limit: Total budget constraint
            display_config_path: Path to display_config.csv
            objective_prompt_path: Path to objective prompt file
            output_path: Where to save the draft calendar

        Returns:
            Generated calendar dictionary
        """
        # Load inputs
        causal_params = self._load_causal_parameters(causal_parameters_path)
        display_config = self._load_display_config(display_config_path)
        objective_prompt = self._load_objective_prompt(objective_prompt_path)

        # Initialize calendar state
        calendar_state = {
            "events": [],
            "total_spend": 0,
            "budget_limit": budget_limit,
            "objective": "",
            "used_combos": [],
            "finalized": False
        }

        # Construct system prompt
        system_prompt = f"""You are a CPG Trade Promotion Optimization data analyst. Your role is to generate an optimized promotion calendar that maximizes the business objective while respecting budget constraints.

You have access to causal parameters (physics) generated using an analyst Agent that tells you how promotions affect sales. Use this data to intelligently construct a calendar.

CAUSAL PARAMETERS:
{json.dumps(causal_params, indent=2)}

DISPLAY CONFIGURATION:
{display_config}

BUDGET LIMIT: ${budget_limit:,.2f}

IMPORTANT RULES:
1. Calendar is organized by PPG and RETAILER
2. Weeks are assigned SEQUENTIALLY starting from week 1
4. You cannot manually choose weeks - they are auto-assigned as you add events
5. You have 52 weeks total to work with
6. Holiday weeks are Week 1, Week 22, Week 27, Week 36, Week 47,  and Week 52

Your task: Build a promotion calendar by adding events one at a time for every Retailer, PPG combination using the add_promotion_event tool. Consider:
1. Seasonality patterns (high-demand weeks)
2. Discount depth vs lift tradeoff (elasticity)
3. Display/feature effectiveness
4. Budget constraints
5. SKU-level performance

Be strategic: Don't promote everything and every week. Focus on high-impact opportunities that align with the objective."""

        # User message with objective
        user_message = f"""BUSINESS OBJECTIVE:
{objective_prompt}

Please generate an optimized promotion calendar that achieves this objective within the ${budget_limit:,.2f} budget. 

Build the event calendar week-by-week for every Retailer, PPG combination. Weeks are auto-assigned sequentially. For each event, provide clear reasoning. When finished, call finalize_calendar."""

        # Initialize conversation
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        # Agent loop
        max_iterations = 50
        iteration = 0

        while iteration < max_iterations and not calendar_state["finalized"]:
            iteration += 1

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self._define_tools(),
                tool_choice="auto"
            )

            choice = response.choices[0]
            message = choice.message

            # Add assistant message to conversation
            messages.append(message)

            if choice.finish_reason == "tool_calls":
                # Execute tool calls
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    print(
                        f"[Iteration {iteration}] Calling {function_name}: {function_args}")

                    # Execute the tool
                    result = self._execute_tool(
                        function_name,
                        function_args,
                        causal_params,
                        calendar_state
                    )

                    print(f"[Result] {result}")

                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result
                    })

            elif choice.finish_reason == "stop":
                # Agent finished without tool call
                print(f"[Agent Response] {message.content}")
                break

        # Construct final output
        output = {
            "objective": calendar_state["objective"],
            "total_projected_spend": calendar_state["total_spend"],
            "calendar_events": calendar_state["events"]
        }

        # Save to file
        with open(output_path, 'w') as f:
            json.dumps(output, f, indent=2)

        print(f"\n✓ Calendar saved to {output_path}")
        print(f"✓ Total events: {len(calendar_state['events'])}")
        print(f"✓ Total spend: ${calendar_state['total_spend']:,.2f}")
        print(
            f"✓ Budget utilization: {calendar_state['total_spend']/budget_limit*100:.1f}%")

        return output
