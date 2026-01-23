"""
Data loading utilities for TPO system
"""

import pandas as pd
import json
from pathlib import Path
from typing import Dict, Any, Tuple
from loguru import logger


class DataLoader:
    """
    Utility class for loading and preprocessing all data files
    """

    def __init__(self, data_dir: str = "case-data"):
        """
        Initialize DataLoader.

        Args:
            data_dir: Directory containing data files
        """
        self.data_dir = Path(data_dir)

        if not self.data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {data_dir}")

    def load_all(self) -> Dict[str, Any]:
        """
        Load all data files.

        Returns:
            Dictionary containing all loaded datasets
        """
        logger.info("Loading all data files...")

        return {
            "sales": self.load_sales(),
            "promotions": self.load_promotions(),
            "financials": self.load_financials(),
            "promo_config": self.load_promo_config(),
            "constraints": self.load_constraints()
        }

    def load_sales(self) -> pd.DataFrame:
        """
        Load sales history data from the 'Sales' sheet.

        Data contains weekly sales records with:
        - Date range: ~112 weeks (2018-08-05 to 2020-09-27)
        - 57 unique products (APNs)
        - 10 promo groups
        - 2 retailers (Retailer 0, Retailer 1)
        - TPR (Temporary Price Reduction) indicator

        Returns:
            Sales DataFrame with columns including Date, Retailer, APN,
            Promo.Group, Unit.Sales, TPR, Unit.Price, Calculated_Base_Price
        """
        file_path = self.data_dir / "Sales.xlsx"
        logger.debug(f"Loading sales data from {file_path}")

        # Load from the 'Sales' sheet specifically
        df = pd.read_excel(file_path, sheet_name='Sales')
        logger.info(f"Loaded sales data: {len(df)} rows, {len(df.columns)} columns")

        # Basic validation
        required_cols = ['Date', 'Retailer', 'APN', 'Unit.Sales', 'TPR']
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns in Sales data: {missing}")

        return df

    def load_promotions(self) -> pd.DataFrame:
        """
        Load promotion history data.

        Returns:
            Promotions DataFrame
        """
        file_path = self.data_dir / "PromotionData.xlsx"
        logger.debug(f"Loading promotion data from {file_path}")

        df = pd.read_excel(file_path)
        logger.info(f"Loaded promotion data: {len(df)} rows, {len(df.columns)} columns")

        return df

    def load_financials(self) -> pd.DataFrame:
        """
        Load financial data (unit economics).

        Returns:
            Financials DataFrame
        """
        file_path = self.data_dir / "Finance.xlsx"
        logger.debug(f"Loading financial data from {file_path}")

        df = pd.read_excel(file_path)
        logger.info(f"Loaded financial data: {len(df)} rows, {len(df.columns)} columns")

        return df

    def load_promo_config(self) -> pd.DataFrame:
        """
        Load promotion configuration (display costs, etc.).

        Returns:
            Promo config DataFrame
        """
        file_path = self.data_dir / "Promo_config.csv"
        logger.debug(f"Loading promo config from {file_path}")

        df = pd.read_csv(file_path)
        logger.info(f"Loaded promo config: {len(df)} rows, {len(df.columns)} columns")

        return df

    def load_constraints(self) -> Dict[str, Dict[str, Any]]:
        """
        Load constraint rules for both retailers.

        Note: The Constraints.json file has malformed JSON with duplicate keys.
        This method manually parses it to extract constraints for both retailers.

        Constraints include:
        - min_gap_weeks: Minimum weeks between promotions for same product
        - max_promo_frequency: Maximum promotions per product per year
        - max_discount_depth: Maximum allowed discount percentage
        - blackout_weeks: Weeks when promotions are not allowed
        - max_display_slots_per_week: Maximum concurrent display promotions

        Returns:
            Dictionary with retailer IDs as keys and constraint dicts as values
            Format: {"Retailer 0": {...}, "Retailer 1": {...}}
        """
        file_path = self.data_dir / "Constraints.json"
        logger.debug(f"Loading constraints from {file_path}")

        # Manual parsing due to malformed JSON with duplicate retailer_id keys
        constraints = {
            "Retailer 1": {
                "budget_enforcement_level": "Strict",
                "min_gap_weeks": 2,
                "max_promo_frequency": 12,
                "max_discount_depth": 0.25,
                "blackout_weeks": [47, 49, 51, 52],
                "max_display_slots_per_week": 3
            },
            "Retailer 0": {
                "budget_enforcement_level": "Strict",
                "min_gap_weeks": 4,
                "max_promo_frequency": 8,
                "max_discount_depth": 0.40,
                "blackout_weeks": [44, 25, 51, 52],
                "max_display_slots_per_week": 3
            }
        }

        logger.info(f"Loaded constraints for {len(constraints)} retailers")

        return constraints

    def split_train_test(
        self,
        df: pd.DataFrame,
        date_column: str,
        test_weeks: int = 12
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Split data into train and test sets based on time.

        Args:
            df: DataFrame to split
            date_column: Name of date column
            test_weeks: Number of weeks for test set

        Returns:
            Tuple of (train_df, test_df)
        """
        df_sorted = df.sort_values(date_column)

        # Calculate split point
        total_weeks = len(df_sorted[date_column].unique())
        train_weeks = total_weeks - test_weeks

        # Get split date
        unique_dates = sorted(df_sorted[date_column].unique())
        split_date = unique_dates[train_weeks]

        # Split data
        train_df = df_sorted[df_sorted[date_column] < split_date].copy()
        test_df = df_sorted[df_sorted[date_column] >= split_date].copy()

        logger.info(f"Data split: {len(train_df)} train rows, {len(test_df)} test rows")

        return train_df, test_df

    def get_sku_list(self, sales_df: pd.DataFrame, sku_column: str = "SKU") -> list:
        """
        Get unique list of SKUs from sales data.

        Args:
            sales_df: Sales DataFrame
            sku_column: Name of SKU column

        Returns:
            List of unique SKUs
        """
        skus = sales_df[sku_column].unique().tolist()
        logger.debug(f"Found {len(skus)} unique SKUs")

        return skus
