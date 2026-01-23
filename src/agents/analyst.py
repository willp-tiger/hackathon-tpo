"""
Agent A: The Analyst (LLM-Powered Data Scientist)

This agent uses Claude API to reason about promotion data and generate causal parameters
through an iterative, tool-based approach. It conducts exploratory data analysis,
tries multiple baseline forecasting approaches, and validates results before finalizing.
"""

import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional
from loguru import logger
from anthropic import Anthropic
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_percentage_error

from ..utils.data_loader import DataLoader
from ..utils.metrics import calculate_mape


class AnalystAgent:
    """
    LLM-powered analyst that generates causal parameters for promotion optimization.

    Uses Claude API with tool use to:
    1. Conduct exploratory data analysis
    2. Try multiple baseline forecasting approaches
    3. Validate forecasts with MAPE
    4. Calculate elasticity and lift factors
    5. Save final causal parameters
    """

    def __init__(self, data_dir: str = "case-data", output_dir: str = "outputs"):
        """
        Initialize the Analyst Agent.

        Args:
            data_dir: Directory containing input data files
            output_dir: Directory for output files
        """
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Anthropic client
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        self.client = Anthropic(api_key=api_key)

        # Initialize data loader
        self.data_loader = DataLoader(str(self.data_dir))

        # Storage for data used by tools
        self.sales_data: Optional[pd.DataFrame] = None
        self.promo_data: Optional[pd.DataFrame] = None
        self.financial_data: Optional[pd.DataFrame] = None
        self.baseline_results: Dict[str, Any] = {}

        # Execution log
        self.execution_log: List[str] = []

    def _log(self, message: str):
        """Add message to execution log and logger."""
        self.execution_log.append(message)
        logger.info(message)

    def _define_tools(self) -> List[Dict[str, Any]]:
        """
        Define tools available to Agent A for data analysis.

        Returns:
            List of tool definitions in Anthropic API format
        """
        return [
            {
                "name": "load_sales_preview",
                "description": "Load sales data and return preview statistics including shape, columns, data types, missing values, and first 10 rows. Use this first to understand the data structure.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "load_promotion_preview",
                "description": "Load promotion data and return preview statistics. Use this to understand promotion tactics and history.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "calculate_baseline_global_avg",
                "description": "Calculate baseline using simple global average of non-promoted sales. Fallback approach with lowest accuracy but highest robustness.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "calculate_baseline_sku_averages",
                "description": "Calculate baseline using SKU-specific averages from non-promoted periods. More accurate than global average, balances accuracy with robustness.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "calculate_baseline_regression",
                "description": "Calculate baseline using regression model with features like trend, seasonality. Most sophisticated approach but requires sufficient data quality.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "include_trend": {
                            "type": "boolean",
                            "description": "Include time trend feature"
                        },
                        "include_seasonality": {
                            "type": "boolean",
                            "description": "Include week-of-year seasonality"
                        }
                    },
                    "required": ["include_trend", "include_seasonality"]
                }
            },
            {
                "name": "validate_baseline_forecast",
                "description": "Validate a baseline forecast approach using holdout data and calculate MAPE. Use to compare different approaches. Target MAPE < 15%.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "approach_name": {
                            "type": "string",
                            "description": "Name of the approach being validated (e.g., 'regression', 'sku_averages', 'global_avg')"
                        },
                        "holdout_weeks": {
                            "type": "number",
                            "description": "Number of weeks to hold out for validation (default 12)"
                        }
                    },
                    "required": ["approach_name"]
                }
            },
            {
                "name": "calculate_elasticity_and_lift",
                "description": "Calculate price elasticity and discount lift factors from historical promotion data. Use after baseline is established.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "calculate_display_lift",
                "description": "Calculate display lift multiplier from historical data comparing promoted weeks with/without displays.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "calculate_seasonality_factors",
                "description": "Calculate week-of-year seasonality factors from historical sales data. Returns multiplier for each week (1-52).",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "save_causal_parameters",
                "description": "Save final causal parameters to JSON file. Call this once after all analysis is complete.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "parameters": {
                            "type": "object",
                            "description": "Complete causal parameters object with baseline, elasticity, lift factors, seasonality, and approach_log"
                        }
                    },
                    "required": ["parameters"]
                }
            }
        ]

    def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool call from Claude.

        Args:
            tool_name: Name of the tool to execute
            tool_input: Input parameters for the tool

        Returns:
            Tool execution result
        """
        self._log(f"Executing tool: {tool_name} with input: {tool_input}")

        try:
            if tool_name == "load_sales_preview":
                return self._tool_load_sales_preview()
            elif tool_name == "load_promotion_preview":
                return self._tool_load_promotion_preview()
            elif tool_name == "calculate_baseline_global_avg":
                return self._tool_calculate_baseline_global_avg()
            elif tool_name == "calculate_baseline_sku_averages":
                return self._tool_calculate_baseline_sku_averages()
            elif tool_name == "calculate_baseline_regression":
                return self._tool_calculate_baseline_regression(
                    tool_input.get("include_trend", True),
                    tool_input.get("include_seasonality", True)
                )
            elif tool_name == "validate_baseline_forecast":
                return self._tool_validate_baseline_forecast(
                    tool_input["approach_name"],
                    tool_input.get("holdout_weeks", 12)
                )
            elif tool_name == "calculate_elasticity_and_lift":
                return self._tool_calculate_elasticity_and_lift()
            elif tool_name == "calculate_display_lift":
                return self._tool_calculate_display_lift()
            elif tool_name == "calculate_seasonality_factors":
                return self._tool_calculate_seasonality_factors()
            elif tool_name == "save_causal_parameters":
                return self._tool_save_causal_parameters(tool_input["parameters"])
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            error_msg = f"Tool execution error in {tool_name}: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}

    # Tool implementation methods

    def _tool_load_sales_preview(self) -> Dict[str, Any]:
        """Load and preview sales data."""
        self.sales_data = self.data_loader.load_sales()

        return {
            "shape": {"rows": len(self.sales_data), "columns": len(self.sales_data.columns)},
            "columns": list(self.sales_data.columns),
            "dtypes": {col: str(dtype) for col, dtype in self.sales_data.dtypes.items()},
            "missing_values": self.sales_data.isnull().sum().to_dict(),
            "date_range": {
                "min": str(self.sales_data['Date'].min()),
                "max": str(self.sales_data['Date'].max()),
                "unique_weeks": int(self.sales_data['Date'].nunique())
            },
            "unique_counts": {
                "retailers": int(self.sales_data['Retailer'].nunique()),
                "apns": int(self.sales_data['APN'].nunique()),
                "promo_groups": int(self.sales_data['Promo.Group'].nunique())
            },
            "tpr_distribution": self.sales_data['TPR'].value_counts().to_dict(),
            "sample_rows": self.sales_data.head(10).to_dict(orient='records')
        }

    def _tool_load_promotion_preview(self) -> Dict[str, Any]:
        """Load and preview promotion data."""
        self.promo_data = self.data_loader.load_promotions()

        return {
            "shape": {"rows": len(self.promo_data), "columns": len(self.promo_data.columns)},
            "columns": list(self.promo_data.columns),
            "sample_rows": self.promo_data.head(10).to_dict(orient='records')
        }

    def _tool_calculate_baseline_global_avg(self) -> Dict[str, Any]:
        """Calculate baseline using global average."""
        if self.sales_data is None:
            return {"error": "Must load sales data first"}

        # Filter non-promoted sales
        non_promo = self.sales_data[self.sales_data['TPR'] == 0]

        if len(non_promo) == 0:
            return {"error": "No non-promoted periods found"}

        baseline_avg = float(non_promo['Unit.Sales'].mean())

        self.baseline_results['global_avg'] = {
            "method": "global_average",
            "baseline_velocity_avg": baseline_avg,
            "n_observations": len(non_promo)
        }

        return {
            "method": "global_average",
            "baseline_velocity_avg": baseline_avg,
            "n_observations": len(non_promo),
            "status": "calculated"
        }

    def _tool_calculate_baseline_sku_averages(self) -> Dict[str, Any]:
        """Calculate baseline using SKU-specific averages."""
        if self.sales_data is None:
            return {"error": "Must load sales data first"}

        # Filter non-promoted sales
        non_promo = self.sales_data[self.sales_data['TPR'] == 0]

        if len(non_promo) == 0:
            return {"error": "No non-promoted periods found"}

        # Calculate SKU-level baselines
        sku_baselines = non_promo.groupby('APN')['Unit.Sales'].mean()
        baseline_avg = float(sku_baselines.mean())

        self.baseline_results['sku_averages'] = {
            "method": "sku_specific_averages",
            "baseline_velocity_avg": baseline_avg,
            "sku_baselines": sku_baselines.to_dict(),
            "n_skus": len(sku_baselines)
        }

        return {
            "method": "sku_specific_averages",
            "baseline_velocity_avg": baseline_avg,
            "n_skus": len(sku_baselines),
            "min_sku_baseline": float(sku_baselines.min()),
            "max_sku_baseline": float(sku_baselines.max()),
            "status": "calculated"
        }

    def _tool_calculate_baseline_regression(self, include_trend: bool, include_seasonality: bool) -> Dict[str, Any]:
        """Calculate baseline using regression model."""
        if self.sales_data is None:
            return {"error": "Must load sales data first"}

        # Prepare features
        df = self.sales_data[self.sales_data['TPR'] == 0].copy()

        if len(df) == 0:
            return {"error": "No non-promoted periods found"}

        # Add time features
        df['week_index'] = pd.to_datetime(df['Date']).rank(method='dense').astype(int)
        df['week_of_year'] = pd.to_datetime(df['Date']).dt.isocalendar().week

        # Build feature matrix
        features = []
        feature_names = []

        if include_trend:
            features.append(df['week_index'].values.reshape(-1, 1))
            feature_names.append('trend')

        if include_seasonality:
            # One-hot encode week of year
            week_dummies = pd.get_dummies(df['week_of_year'], prefix='week')
            features.append(week_dummies.values)
            feature_names.extend(list(week_dummies.columns))

        if not features:
            return {"error": "Must include at least one feature"}

        X = np.hstack(features)
        y = df['Unit.Sales'].values

        # Fit regression
        model = LinearRegression()
        model.fit(X, y)

        # Predict baseline
        y_pred = model.predict(X)
        baseline_avg = float(y_pred.mean())

        self.baseline_results['regression'] = {
            "method": "regression",
            "baseline_velocity_avg": baseline_avg,
            "features": feature_names,
            "include_trend": include_trend,
            "include_seasonality": include_seasonality,
            "r_squared": float(model.score(X, y))
        }

        return {
            "method": "regression",
            "baseline_velocity_avg": baseline_avg,
            "features_used": len(feature_names),
            "r_squared": float(model.score(X, y)),
            "status": "calculated"
        }

    def _tool_validate_baseline_forecast(self, approach_name: str, holdout_weeks: int) -> Dict[str, Any]:
        """Validate baseline forecast using holdout data."""
        if approach_name not in self.baseline_results:
            return {"error": f"Approach '{approach_name}' not calculated yet"}

        if self.sales_data is None:
            return {"error": "Sales data not loaded"}

        # Split data
        train_df, test_df = self.data_loader.split_train_test(
            self.sales_data,
            date_column='Date',
            test_weeks=holdout_weeks
        )

        # Get baseline value
        baseline_avg = self.baseline_results[approach_name]['baseline_velocity_avg']

        # Filter test data to non-promoted periods
        test_non_promo = test_df[test_df['TPR'] == 0]

        if len(test_non_promo) == 0:
            return {"error": "No non-promoted periods in test set"}

        # Calculate MAPE
        actual = test_non_promo['Unit.Sales'].values
        predicted = np.full(len(actual), baseline_avg)

        mape = calculate_mape(actual, predicted)

        # Store validation result
        self.baseline_results[approach_name]['validation'] = {
            "mape": float(mape),
            "holdout_weeks": holdout_weeks,
            "test_observations": len(test_non_promo)
        }

        return {
            "approach": approach_name,
            "mape": float(mape),
            "mape_percent": float(mape * 100),
            "holdout_weeks": holdout_weeks,
            "test_observations": len(test_non_promo),
            "status": "ACCEPTED" if mape < 0.15 else "REJECTED",
            "target_mape": 0.15
        }

    def _tool_calculate_elasticity_and_lift(self) -> Dict[str, Any]:
        """Calculate elasticity and discount lift factors from actual data."""
        if self.sales_data is None:
            return {"error": "Sales data not loaded"}

        # TPR column contains discount percentage (0-100)
        # TPR > 0 indicates promotion
        promo_data = self.sales_data[self.sales_data['TPR'] > 0].copy()
        non_promo_data = self.sales_data[self.sales_data['TPR'] == 0].copy()

        if len(promo_data) == 0 or len(non_promo_data) == 0:
            return {"error": "Insufficient promo/non-promo data"}

        # Calculate baseline average
        baseline_avg = non_promo_data['Unit.Sales'].mean()

        # Create discount depth buckets and calculate lift factors
        promo_data['discount_bucket'] = pd.cut(
            promo_data['TPR'],
            bins=[0, 15, 25, 35, 45, 100],
            labels=['0-15', '15-25', '25-35', '35-45', '45+']
        )

        # Calculate average lift for each discount bucket
        discount_lift_factors = {}
        for bucket in promo_data['discount_bucket'].unique():
            if pd.notna(bucket):
                bucket_data = promo_data[promo_data['discount_bucket'] == bucket]
                avg_sales = bucket_data['Unit.Sales'].mean()
                lift = avg_sales / baseline_avg if baseline_avg > 0 else 1.0
                discount_lift_factors[str(bucket)] = float(lift)

        # Calculate overall average lift
        overall_avg_promo = promo_data['Unit.Sales'].mean()
        overall_lift = overall_avg_promo / baseline_avg if baseline_avg > 0 else 1.0

        # Calculate price elasticity (simplified: % change in quantity / % change in price)
        # Using TPR as proxy for price change
        avg_discount_pct = promo_data['TPR'].mean() / 100  # Convert to decimal
        pct_quantity_change = (overall_avg_promo - baseline_avg) / baseline_avg if baseline_avg > 0 else 0

        price_elasticity = pct_quantity_change / avg_discount_pct if avg_discount_pct > 0 else 0

        return {
            "base_price_elasticity": float(price_elasticity),
            "discount_lift_factors": discount_lift_factors,
            "overall_lift": float(overall_lift),
            "baseline_avg_sales": float(baseline_avg),
            "promo_avg_sales": float(overall_avg_promo),
            "n_promo_observations": int(len(promo_data)),
            "n_baseline_observations": int(len(non_promo_data)),
            "avg_discount_pct": float(promo_data['TPR'].mean()),
            "status": "calculated_from_actual_data"
        }

    def _tool_calculate_display_lift(self) -> Dict[str, Any]:
        """Calculate display lift multiplier from promotion data."""
        if self.promo_data is None:
            # Load promotion data if not already loaded
            self.promo_data = self.data_loader.load_promotions()

        # Check for display columns
        display_cols = ['display_platinum', 'display_gold', 'display_silver', 'display_bronze']
        has_displays = all(col in self.promo_data.columns for col in display_cols)

        if not has_displays:
            return {
                "error": "Promotion data lacks display indicators",
                "status": "failed"
            }

        # Merge promo data with sales data to get display lift
        # Create a display indicator (any display type)
        promo_with_display = self.promo_data.copy()
        promo_with_display['has_display'] = (
            (promo_with_display['display_platinum'] == 1) |
            (promo_with_display['display_gold'] == 1) |
            (promo_with_display['display_silver'] == 1) |
            (promo_with_display['display_bronze'] == 1)
        )

        # Merge with sales data on Date and Retailer
        merged = self.sales_data.merge(
            promo_with_display[['Date', 'Retailer', 'Promo.Group', 'has_display']],
            on=['Date', 'Retailer', 'Promo.Group'],
            how='left'
        )

        # Fill NaN in has_display with False
        merged['has_display'] = merged['has_display'].fillna(False)

        # Calculate lift: compare TPR with display vs TPR without display
        promo_with_display_sales = merged[(merged['TPR'] > 0) & (merged['has_display'] == True)]['Unit.Sales'].mean()
        promo_no_display_sales = merged[(merged['TPR'] > 0) & (merged['has_display'] == False)]['Unit.Sales'].mean()

        if promo_no_display_sales > 0 and not pd.isna(promo_with_display_sales):
            display_lift = promo_with_display_sales / promo_no_display_sales
        else:
            # Fallback: use overall display presence
            with_display = merged[merged['has_display'] == True]['Unit.Sales'].mean()
            without_display = merged[merged['has_display'] == False]['Unit.Sales'].mean()
            display_lift = with_display / without_display if without_display > 0 else 1.0

        return {
            "display_lift_multiplier": float(display_lift),
            "n_with_display": int(merged['has_display'].sum()),
            "n_without_display": int((~merged['has_display']).sum()),
            "avg_sales_with_display": float(promo_with_display_sales) if not pd.isna(promo_with_display_sales) else 0,
            "avg_sales_without_display": float(promo_no_display_sales) if not pd.isna(promo_no_display_sales) else 0,
            "status": "calculated_from_actual_data"
        }

    def _tool_calculate_seasonality_factors(self) -> Dict[str, Any]:
        """Calculate seasonality factors by week of year."""
        if self.sales_data is None:
            return {"error": "Sales data not loaded"}

        # Calculate average sales by week of year
        df = self.sales_data.copy()
        df['week_of_year'] = pd.to_datetime(df['Date']).dt.isocalendar().week

        weekly_avg = df.groupby('week_of_year')['Unit.Sales'].mean()
        overall_avg = df['Unit.Sales'].mean()

        # Calculate seasonality factor (ratio to overall average)
        seasonality_factors = (weekly_avg / overall_avg).to_dict()

        # Ensure all 52 weeks are represented
        for week in range(1, 53):
            if week not in seasonality_factors:
                seasonality_factors[week] = 1.0

        return {
            "seasonality_factors": {int(k): float(v) for k, v in seasonality_factors.items()},
            "n_weeks_with_data": len(weekly_avg),
            "status": "calculated"
        }

    def _tool_save_causal_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Save causal parameters to JSON file."""
        output_path = self.output_dir / "causal_parameters.json"

        with open(output_path, 'w') as f:
            json.dump(parameters, f, indent=2)

        self._log(f"Saved causal parameters to {output_path}")

        return {
            "status": "saved",
            "file_path": str(output_path),
            "parameter_keys": list(parameters.keys())
        }

    def analyze(self, retailer: Optional[str] = None) -> Dict[str, Any]:
        """
        Run the LLM-powered analysis to generate causal parameters.

        Args:
            retailer: Optional retailer filter

        Returns:
            Causal parameters dictionary
        """
        self._log("=" * 80)
        self._log("AGENT A: ANALYST - Starting causal parameter generation")
        self._log("=" * 80)

        # Define system prompt
        system_prompt = """You are Agent A, a professional data scientist analyzing trade promotion data.

Your task: Generate causal parameters for promotion optimization.

Methodology:
1. Start with EDA - load sales and promotion data previews to understand structure
2. Try multiple baseline forecasting approaches in order of sophistication:
   a. Regression-based (most sophisticated - try this first)
   b. SKU-specific averages (more robust - try if regression fails)
   c. Global average (fallback - only if others fail)
3. Validate EACH approach with holdout data - calculate MAPE
4. NEVER accept MAPE > 15% without trying alternative approaches
5. Once baseline is validated, calculate:
   - Elasticity and discount lift factors
   - Display lift multiplier
   - Seasonality factors (week 1-52)
6. Save final parameters with approach_log documenting what you tried

Quality gates:
- Target MAPE < 15% on holdout validation
- Must try at least 2 approaches before accepting results
- Document reasoning for final approach selection

Use tools iteratively. Be methodical. Explain your reasoning at each step.

When ready, call save_causal_parameters with a complete JSON object containing:
- baseline_velocity_avg
- elasticity_model (with base_price_elasticity and discount_lift_factors)
- display_lift_multiplier
- seasonality_factors (week 1-52 as keys)
- approach_log (array of what you tried)
"""

        # Initial message
        messages = [
            {
                "role": "user",
                "content": "Analyze the trade promotion data and generate causal parameters. Start by loading the sales data preview to understand the data structure."
            }
        ]

        # Multi-turn conversation with Claude
        iteration = 0
        max_iterations = 20

        while iteration < max_iterations:
            iteration += 1
            self._log(f"\n--- Iteration {iteration} ---")

            try:
                response = self.client.messages.create(
                    model="claude-3-7-sonnet-20250219",
                    max_tokens=4096,
                    system=system_prompt,
                    tools=self._define_tools(),
                    messages=messages
                )

                self._log(f"Claude stop reason: {response.stop_reason}")

                # Log Claude's text response
                for block in response.content:
                    if block.type == "text":
                        self._log(f"Claude: {block.text}")

                # Process tool calls
                if response.stop_reason == "tool_use":
                    # Add assistant message
                    messages.append({
                        "role": "assistant",
                        "content": response.content
                    })

                    # Execute tools and collect results
                    tool_results = []
                    for block in response.content:
                        if block.type == "tool_use":
                            result = self._execute_tool(block.name, block.input)
                            # Convert result to JSON string, handling pandas types
                            result_json = json.dumps(result, default=str)
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": result_json
                            })

                    # Add tool results to messages
                    messages.append({
                        "role": "user",
                        "content": tool_results
                    })

                elif response.stop_reason == "end_turn":
                    self._log("Claude finished analysis")
                    break

                else:
                    self._log(f"Unexpected stop reason: {response.stop_reason}")
                    break

            except Exception as e:
                logger.error(f"Error in conversation: {e}")
                raise

        # Save execution log
        log_path = self.output_dir / "agent_a_execution_log.txt"
        with open(log_path, 'w') as f:
            f.write('\n'.join(self.execution_log))

        logger.info(f"Saved execution log to {log_path}")

        # Load and return saved parameters
        params_path = self.output_dir / "causal_parameters.json"
        if params_path.exists():
            with open(params_path, 'r') as f:
                parameters = json.load(f)
            return parameters
        else:
            raise RuntimeError("Agent A did not save causal parameters")
