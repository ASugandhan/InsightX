"""
Trust Builder
Adds validation, quality badges, and reasonableness checks
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from scipy import stats


class TrustBuilder:
    """Build trust through validation and transparency"""
    
    def __init__(self):
        # Expected ranges for reasonableness checks
        self.expected_ranges = {
            'avg_amount': {
                'P2P': (500, 3000),
                'P2M': (1000, 5000),
                'Bill Payment': (200, 2000),
                'Recharge': (100, 1000)
            },
            'success_rate': (85, 99),
            'failure_rate': (1, 15),
            'fraud_flag_rate': (0, 20)
        }
        
        print("✓ Trust Builder initialized")
    
    def get_data_quality_badge(self, sample_size: int, confidence: float) -> str:
        """Get visual data quality indicator"""
        
        # Sample size score
        if sample_size >= 10000:
            size_badge = "🟢 Large"
        elif sample_size >= 1000:
            size_badge = "🟡 Medium"
        elif sample_size >= 100:
            size_badge = "🟠 Small"
        else:
            size_badge = "🔴 Very Small"
        
        # Confidence score
        if confidence >= 0.90:
            conf_badge = "🟢 High"
        elif confidence >= 0.75:
            conf_badge = "🟡 Medium"
        else:
            conf_badge = "🔴 Low"
        
        return f"{size_badge} Sample | {conf_badge} Confidence"
    
    def calculate_confidence_interval(self, value: float, sample_size: int, 
                                     std_dev: float = None) -> Tuple[float, float]:
        """Calculate 95% confidence interval"""
        
        if sample_size < 2:
            return None, None
        
        # Estimate std dev if not provided (conservative: 20% of mean)
        if std_dev is None:
            std_dev = value * 0.20
        
        # Standard error
        std_err = std_dev / np.sqrt(sample_size)
        
        # 95% CI
        margin = 1.96 * std_err  # Z-score for 95%
        
        return round(value - margin, 2), round(value + margin, 2)
    
    def check_reasonableness(self, metric: str, value: float, filters: Dict) -> str:
        checks = []

        # Normalize transaction_type (RAG-safe)
        txn_type = filters.get('transaction_type')
        if isinstance(txn_type, dict):
            txn_type = txn_type.get('value')

        if metric == 'avg_amount' and txn_type:
            expected = self.expected_ranges['avg_amount'].get(txn_type)

            if expected:
                min_val, max_val = expected
                if min_val <= value <= max_val:
                    checks.append(f"✓ Within expected range for {txn_type} (₹{min_val:,}-₹{max_val:,})")
                elif value < min_val:
                    checks.append(f"⚠️ Below typical {txn_type} range (₹{min_val:,}-₹{max_val:,})")
                else:
                    checks.append(f"⚠️ Above typical {txn_type} range (₹{min_val:,}-₹{max_val:,})")

        elif metric in ['success_rate', 'failure_rate', 'fraud_flag_rate']:
            expected = self.expected_ranges.get(metric)
            if expected:
                min_val, max_val = expected
                if min_val <= value <= max_val:
                    checks.append(f"✓ {metric.replace('_',' ').title()} within normal range")
                else:
                    checks.append(f"⚠️ {metric.replace('_',' ').title()} outside typical range")

        return " | ".join(checks) if checks else ""

    def run_sanity_checks(self, result: pd.DataFrame, filters: Dict, 
                         metrics: List[str], sample_size: int) -> List[str]:
        """Run comprehensive sanity checks"""
        
        checks = []
        
        # Check 1: Sample size
        if sample_size >= 10000:
            checks.append("✓ Large sample (10K+) - highly reliable")
        elif sample_size >= 1000:
            checks.append("✓ Good sample size (1K+) - statistically valid")
        elif sample_size >= 100:
            checks.append("⚠️ Small sample (100+) - interpret with caution")
        else:
            checks.append("🔴 Very small sample (<100) - results may not be representative")
        
        # Check 2: Value ranges
        for col in result.columns:
            if 'amount' in col.lower() and len(result) == 1:
                value = result[col].iloc[0]
                if pd.notna(value):
                    if value > 50000:
                        checks.append("⚠️ Unusually high amount detected - may include outliers or high-value transactions")
                    elif value < 10:
                        checks.append("⚠️ Unusually low amount - check if filters are too restrictive")
                    else:
                        checks.append("✓ Amount value in reasonable range")
        
        # Check 3: Rates consistency
        rate_cols = [c for c in result.columns if 'rate' in c.lower()]
        if len(rate_cols) >= 2 and len(result) == 1:
            total = sum(result[c].iloc[0] for c in rate_cols if pd.notna(result[c].iloc[0]))
            if 95 <= total <= 105:
                checks.append("✓ Rates sum to ~100% (internally consistent)")
            else:
                checks.append(f"⚠️ Rates sum to {total:.1f}% (expected ~100%)")
        
        # Check 4: Filter consistency
        if filters:
            if 'amount_inr' in filters:
                amount_filter = filters['amount_inr']
                if isinstance(amount_filter, dict) and 'min' in amount_filter:
                    checks.append(f"✓ Filtered to amounts ≥ ₹{amount_filter['min']:,}")
        
        return checks
    
    def get_actual_sample_size(self, analytics_engine, filters: Dict) -> int:
        """Get actual number of rows matching filters"""
    
        try:
            # Build count query
            import sys
            sys.path.append('..')
        
            from analytics.sql_generator import SQLGenerator
            from nlp.parser import ParsedQuery, QueryIntent
        
            gen = SQLGenerator()
        
            # Create a count query with same filters
            count_query = ParsedQuery(
                intent=QueryIntent.DESCRIPTIVE,
                metrics=['count'],
                dimensions=[],
                filters=filters,
                original_query='count',
                confidence=1.0
            )
        
            sql = gen.generate(count_query)
            print(f"🔍 DEBUG: Counting with SQL: {sql[:100]}...")  # Debug
        
            result = analytics_engine.query(sql)
        
            if not result.empty and 'count' in result.columns:
                count = int(result['count'].iloc[0])
                print(f"✓ Sample size: {count:,}")  # Debug
                return count
            else:
                print(f"⚠️ No count column in result: {result.columns.tolist()}")  # Debug
                return None

        except Exception as e:
            print(f"⚠️ Sample size calculation error: {e}")  # Debug - THIS WAS SILENT!
            import traceback
            traceback.print_exc()  # Show full error
            return None


# ============================================================================
# TESTING
# ============================================================================
if __name__ == "__main__":
    print("\n" + "="*80)
    print("TRUST BUILDER TEST")
    print("="*80)
    
    builder = TrustBuilder()
    
    # Test 1: Data quality badges
    print("\n--- Test 1: Data Quality Badges ---")
    test_cases = [
        (50000, 0.95),
        (5000, 0.85),
        (500, 0.75),
        (50, 0.60)
    ]
    
    for size, conf in test_cases:
        badge = builder.get_data_quality_badge(size, conf)
        print(f"Sample: {size:>6}, Confidence: {conf:.2f} → {badge}")
    
    # Test 2: Confidence intervals
    print("\n--- Test 2: Confidence Intervals ---")
    test_values = [
        (1320, 87660),
        (2500, 1000),
        (500, 100)
    ]
    
    for value, size in test_values:
        lower, upper = builder.calculate_confidence_interval(value, size)
        if lower and upper:
            print(f"Value: ₹{value:,}, Sample: {size:,}")
            print(f"  95% CI: ₹{lower:,} - ₹{upper:,}")
    
    # Test 3: Reasonableness checks
    print("\n--- Test 3: Reasonableness Checks ---")
    checks = [
        ('avg_amount', 1320, {'transaction_type': 'P2M'}),
        ('avg_amount', 15000, {'transaction_type': 'P2P'}),
        ('success_rate', 92, {}),
        ('fraud_flag_rate', 8, {})
    ]
    
    for metric, value, filters in checks:
        result = builder.check_reasonableness(metric, value, filters)
        print(f"\n{metric} = {value}, filters = {filters}")
        print(f"  {result if result else 'No specific check'}")
    
    print("\n" + "="*80)
    print("✓ TRUST BUILDER TEST COMPLETE")
    print("="*80)