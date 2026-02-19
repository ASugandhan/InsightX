"""
Sanity Checker
Verifies results are reasonable
"""
from typing import Dict, List
import pandas as pd
class SanityChecker:
    """Check if results pass sanity tests"""
    
    def check_all(self, result: pd.DataFrame, filters: Dict, metrics: List[str]) -> List[str]:
        """Run all sanity checks"""
        
        checks = []
        
        # Check 1: Sample size adequate
        if len(result) == 1:
            checks.append("✓ Aggregated result (not individual records)")
        elif len(result) >= 30:
            checks.append("✓ Sample size adequate for statistical validity")
        else:
            checks.append("⚠️ Small sample size - interpret with caution")
        
        # Check 2: Values in reasonable range
        for col in result.columns:
            if 'amount' in col.lower():
                values = result[col].dropna()
                if len(values) > 0:
                    max_val = values.max()
                    if max_val > 100000:
                        checks.append("⚠️ Unusually high amounts detected - may include outliers")
                    elif max_val < 10:
                        checks.append("⚠️ Unusually low amounts - check filters")
                    else:
                        checks.append("✓ Amount values in normal range")
        
        # Check 3: Percentages sum to 100 (if applicable)
        rate_cols = [c for c in result.columns if 'rate' in c.lower()]
        if len(rate_cols) >= 2:
            total = sum(result[c].iloc[0] for c in rate_cols if pd.notna(result[c].iloc[0]))
            if 95 <= total <= 105:  # Allow 5% margin
                checks.append("✓ Rates sum to ~100% (internally consistent)")
        
        return checks