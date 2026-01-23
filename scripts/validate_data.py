"""
Data validation script for TPO system

This script performs comprehensive validation of all input data files:
- Schema validation
- Data quality checks
- Relationship verification
- Time series completeness

Run this before implementing agents to ensure data integrity.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pandas as pd
import numpy as np
from loguru import logger
from utils.data_loader import DataLoader


def validate_sales(sales_df: pd.DataFrame) -> dict:
    """Validate sales data quality and structure."""
    logger.info("Validating sales data...")

    issues = []
    warnings = []

    # Check required columns
    required_cols = ['Date', 'Retailer', 'APN', 'Promo.Group', 'Unit.Sales',
                     'TPR', 'Unit.Price', 'Calculated_Base_Price']
    missing = [col for col in required_cols if col not in sales_df.columns]
    if missing:
        issues.append(f"Missing required columns: {missing}")

    # Check for duplicates
    dup_count = sales_df.duplicated(subset=['Retailer', 'APN', 'Date']).sum()
    if dup_count > 0:
        issues.append(f"Found {dup_count} duplicate retailer-APN-date combinations")

    # Check for negative sales
    neg_sales = (sales_df['Unit.Sales'] < 0).sum()
    if neg_sales > 0:
        warnings.append(f"Found {neg_sales} records with negative sales")

    # Check zero sales
    zero_sales = (sales_df['Unit.Sales'] == 0).sum()
    if zero_sales > 0:
        warnings.append(f"Found {zero_sales} records with zero sales ({zero_sales/len(sales_df)*100:.1f}%)")

    # Check TPR consistency
    promo_sales = sales_df[sales_df['TPR'] > 0]
    if len(promo_sales) > 0:
        inconsistent = (promo_sales['Unit.Price'] >= promo_sales['Calculated_Base_Price']).sum()
        if inconsistent > 0:
            issues.append(f"Found {inconsistent} records with TPR > 0 but price >= base price")

    # Check time series completeness
    for retailer in sales_df['Retailer'].unique():
        for apn in sales_df['APN'].unique()[:5]:  # Sample first 5 APNs
            subset = sales_df[(sales_df['Retailer'] == retailer) &
                             (sales_df['APN'] == apn)].sort_values('Date')
            if len(subset) > 1:
                gaps = subset['Date'].diff().dt.days.dropna()
                avg_gap = gaps.mean()
                if avg_gap > 8:  # More than 1 week + 1 day
                    warnings.append(f"Irregular time series for {retailer}/{apn}: avg gap {avg_gap:.1f} days")

    # Summary stats
    stats = {
        'total_records': len(sales_df),
        'date_range': f"{sales_df['Date'].min().date()} to {sales_df['Date'].max().date()}",
        'unique_retailers': sales_df['Retailer'].nunique(),
        'unique_products': sales_df['APN'].nunique(),
        'promo_records': (sales_df['TPR'] > 0).sum(),
        'promo_rate': f"{(sales_df['TPR'] > 0).sum() / len(sales_df) * 100:.1f}%"
    }

    return {'issues': issues, 'warnings': warnings, 'stats': stats}


def validate_promotions(promo_df: pd.DataFrame) -> dict:
    """Validate promotion history data."""
    logger.info("Validating promotion data...")

    issues = []
    warnings = []

    # Check required columns
    required_cols = ['Date', 'Retailer', 'Promo.Group', 'promo_tpr']
    missing = [col for col in required_cols if col not in promo_df.columns]
    if missing:
        issues.append(f"Missing required columns: {missing}")

    # Count promo types
    promo_types = {
        'TPR': promo_df['promo_tpr'].sum() if 'promo_tpr' in promo_df.columns else 0,
        'Feature': promo_df['promo_feature'].sum() if 'promo_feature' in promo_df.columns else 0,
        'Display_Platinum': promo_df['display_platinum'].sum() if 'display_platinum' in promo_df.columns else 0,
        'Display_Gold': promo_df['display_gold'].sum() if 'display_gold' in promo_df.columns else 0,
        'Display_Silver': promo_df['display_silver'].sum() if 'display_silver' in promo_df.columns else 0,
        'Display_Bronze': promo_df['display_bronze'].sum() if 'display_bronze' in promo_df.columns else 0,
    }

    stats = {
        'total_events': len(promo_df),
        'date_range': f"{promo_df['Date'].min().date()} to {promo_df['Date'].max().date()}",
        'promo_types': promo_types
    }

    return {'issues': issues, 'warnings': warnings, 'stats': stats}


def validate_financials(finance_df: pd.DataFrame) -> dict:
    """Validate financial data."""
    logger.info("Validating financial data...")

    issues = []
    warnings = []

    # Check required columns
    required_cols = ['Retailer', 'PPG', 'List Price']
    missing = [col for col in required_cols if col not in finance_df.columns]
    if missing:
        issues.append(f"Missing required columns: {missing}")

    # Check for ERROR values in Avg Price
    if 'Avg Price' in finance_df.columns:
        error_count = (finance_df['Avg Price'] == '#ERROR!').sum()
        if error_count > 0:
            warnings.append(f"Found {error_count} records with #ERROR! in Avg Price")

    # Check for null retailers
    null_retailers = finance_df['Retailer'].isnull().sum()
    if null_retailers > 0:
        warnings.append(f"Found {null_retailers} records with null Retailer")

    stats = {
        'total_records': len(finance_df),
        'unique_ppgs': finance_df['PPG'].nunique(),
        'unique_retailers': finance_df['Retailer'].nunique()
    }

    return {'issues': issues, 'warnings': warnings, 'stats': stats}


def validate_relationships(sales_df: pd.DataFrame, promo_df: pd.DataFrame,
                          finance_df: pd.DataFrame) -> dict:
    """Validate relationships between datasets."""
    logger.info("Validating data relationships...")

    issues = []
    warnings = []

    # Check retailer consistency
    sales_retailers = set(sales_df['Retailer'].unique())
    promo_retailers = set(promo_df['Retailer'].unique())
    finance_retailers = set(finance_df['Retailer'].dropna().unique())

    if sales_retailers != promo_retailers:
        issues.append(f"Retailer mismatch between Sales and Promotions: "
                     f"Sales={sales_retailers}, Promo={promo_retailers}")

    if sales_retailers != finance_retailers:
        warnings.append(f"Retailer mismatch between Sales and Finance: "
                       f"Sales={sales_retailers}, Finance={finance_retailers}")

    # Check date alignment
    sales_start = sales_df['Date'].min()
    sales_end = sales_df['Date'].max()
    promo_start = promo_df['Date'].min()
    promo_end = promo_df['Date'].max()

    if promo_start < sales_start:
        warnings.append(f"Promotion data starts before Sales data: "
                       f"{promo_start.date()} < {sales_start.date()}")

    stats = {
        'retailers_aligned': sales_retailers == promo_retailers == finance_retailers,
        'sales_date_range': f"{sales_start.date()} to {sales_end.date()}",
        'promo_date_range': f"{promo_start.date()} to {promo_end.date()}"
    }

    return {'issues': issues, 'warnings': warnings, 'stats': stats}


def main():
    """Run all validation checks."""
    logger.info("="*60)
    logger.info("DATA VALIDATION REPORT")
    logger.info("="*60)

    # Load data
    loader = DataLoader()
    data = loader.load_all()

    # Run validations
    results = {
        'sales': validate_sales(data['sales']),
        'promotions': validate_promotions(data['promotions']),
        'financials': validate_financials(data['financials']),
        'relationships': validate_relationships(
            data['sales'], data['promotions'], data['financials']
        )
    }

    # Print results
    total_issues = 0
    total_warnings = 0

    for dataset, result in results.items():
        logger.info(f"\n{dataset.upper()} Validation:")
        logger.info("-" * 40)

        # Issues (critical)
        if result['issues']:
            total_issues += len(result['issues'])
            logger.error(f"Issues ({len(result['issues'])}):")
            for issue in result['issues']:
                logger.error(f"  - {issue}")

        # Warnings (non-critical)
        if result['warnings']:
            total_warnings += len(result['warnings'])
            logger.warning(f"Warnings ({len(result['warnings'])}):")
            for warning in result['warnings']:
                logger.warning(f"  - {warning}")

        # Stats
        if result.get('stats'):
            logger.info("Statistics:")
            for key, value in result['stats'].items():
                logger.info(f"  {key}: {value}")

    # Summary
    logger.info("\n" + "="*60)
    logger.info("VALIDATION SUMMARY")
    logger.info("="*60)
    logger.info(f"Total Issues: {total_issues}")
    logger.info(f"Total Warnings: {total_warnings}")

    if total_issues > 0:
        logger.error("❌ VALIDATION FAILED - Critical issues found")
        return 1
    elif total_warnings > 0:
        logger.warning("⚠️  VALIDATION PASSED WITH WARNINGS")
        return 0
    else:
        logger.success("✅ VALIDATION PASSED - All checks OK")
        return 0


if __name__ == "__main__":
    sys.exit(main())
