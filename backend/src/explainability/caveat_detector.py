"""
Caveat Detection System
Automatically detects and warns about data quality issues
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple


class CaveatDetector:
    """Detect and generate warnings about data limitations"""
    
    def __init__(self):
        self.warning_thresholds = {
            'small_sample': 100,
            'high_null_pct': 0.20,
            'high_cv': 0.50,
            'outlier_pct': 0.05,
        }
        print("✓ Caveat Detector initialized")
    
    def detect_all_caveats(self,
                          result: pd.DataFrame,
                          filters: Dict,
                          metrics: List[str],
                          total_rows: int = 250000) -> List[Dict]:
        """
        Detect all caveats in the data
        
        Returns:
            List of caveat dicts with 'type', 'severity', 'message'
        """
        
        caveats = []
        
        # Caveat 1: Small sample size
        caveat = self._check_sample_size(result, total_rows)
        if caveat:
            caveats.append(caveat)
        
        # Caveat 2: High null percentage
        caveat = self._check_null_values(result)
        if caveat:
            caveats.append(caveat)
        
        # Caveat 3: Fraud flag interpretation
        caveat = self._check_fraud_flag_interpretation(filters)
        if caveat:
            caveats.append(caveat)
        
        # Caveat 4: Skewed distributions
        caveats.extend(self._check_skewed_distributions(result))
        
        # Caveat 5: High variability
        caveats.extend(self._check_high_variability(result))
        
        # Caveat 6: Missing important context
        caveat = self._check_missing_context(filters, metrics)
        if caveat:
            caveats.append(caveat)
        
        # Caveat 7: Outlier impact
        caveats.extend(self._check_outlier_impact(result))
        
        return caveats
    
    def _check_sample_size(self, result: pd.DataFrame, total_rows: int) -> Dict:
        """Check if sample size is adequate"""
        
        sample_size = len(result) if len(result.shape) > 1 and len(result) > 1 else total_rows
        
        if sample_size < self.warning_thresholds['small_sample']:
            severity = 'HIGH' if sample_size < 30 else 'MEDIUM'
            
            return {
                'type': 'small_sample',
                'severity': severity,
                'message': f"Small sample size ({sample_size:,} records) - results may not be representative",
                'recommendation': "Consider using a broader filter or longer time period"
            }
        
        return None
    
    def _check_null_values(self, result: pd.DataFrame) -> Dict:
        """Check for high percentage of null values"""
        
        if result.empty:
            return None
        
        null_pct = result.isnull().sum().sum() / (len(result) * len(result.columns))
        
        if null_pct > self.warning_thresholds['high_null_pct']:
            return {
                'type': 'high_nulls',
                'severity': 'MEDIUM',
                'message': f"High percentage of missing values ({null_pct*100:.1f}%)",
                'recommendation': "Results may be incomplete. Consider data quality checks."
            }
        
        return None
    
    def _check_fraud_flag_interpretation(self, filters: Dict) -> Dict:
        """Clarify fraud flag meaning"""
        
        if 'fraud_flag' in filters or any('fraud' in str(k).lower() for k in filters.keys()):
            return {
                'type': 'fraud_flag_clarification',
                'severity': 'INFO',
                'message': "'Fraud flag' indicates transactions flagged for review, NOT confirmed fraud",
                'recommendation': "These are suspicious patterns detected by algorithms, requiring human verification"
            }
        
        return None
    
    def _check_skewed_distributions(self, result: pd.DataFrame) -> List[Dict]:
        """Check for highly skewed distributions"""
        
        caveats = []
        
        numeric_cols = result.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            if col in ['count', 'total_txns']:
                continue
            
            data = result[col].dropna()
            
            if len(data) < 3:
                continue
            
            # Calculate skewness
            mean = data.mean()
            median = data.median()
            
            if mean > median * 1.5:  # Heavily right-skewed
                caveats.append({
                    'type': 'right_skewed',
                    'severity': 'MEDIUM',
                    'message': f"{col.replace('_', ' ').title()} is heavily right-skewed (mean: {mean:.2f}, median: {median:.2f})",
                    'recommendation': "Consider using median instead of mean for better representation"
                })
            elif mean < median * 0.67:  # Heavily left-skewed
                caveats.append({
                    'type': 'left_skewed',
                    'severity': 'LOW',
                    'message': f"{col.replace('_', ' ').title()} is heavily left-skewed",
                    'recommendation': "Mean may be pulled down by low outliers"
                })
        
        return caveats
    
    def _check_high_variability(self, result: pd.DataFrame) -> List[Dict]:
        """Check for high coefficient of variation"""
        
        caveats = []
        
        numeric_cols = result.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            if col in ['count', 'total_txns']:
                continue
            
            data = result[col].dropna()
            
            if len(data) < 2:
                continue
            
            mean = data.mean()
            std = data.std()
            
            if mean == 0:
                continue
            
            cv = std / mean
            
            if cv > self.warning_thresholds['high_cv']:
                severity = 'HIGH' if cv > 1.0 else 'MEDIUM'
                
                caveats.append({
                    'type': 'high_variability',
                    'severity': severity,
                    'message': f"High variability in {col.replace('_', ' ').title()} (CV: {cv:.1%})",
                    'recommendation': "Results vary widely - consider segmenting by additional dimensions"
                })
        
        return caveats
    
    def _check_missing_context(self, filters: Dict, metrics: List[str]) -> Dict:
        """Check if important contextual filters are missing"""
        
        # P2M without merchant category
        if filters.get('transaction_type') == 'P2M' and 'merchant_category' not in filters:
            return {
                'type': 'missing_context',
                'severity': 'INFO',
                'message': "P2M transactions vary significantly by merchant category",
                'recommendation': "Consider breaking down by merchant_category for better insights"
            }
        
        # Amount queries without time context
        if any('amount' in m for m in metrics) and 'hour_of_day' not in filters and 'is_weekend' not in filters:
            return {
                'type': 'missing_temporal_context',
                'severity': 'INFO',
                'message': "Transaction amounts may vary by time of day and weekend/weekday",
                'recommendation': "Consider temporal patterns (hour, weekend) for deeper insights"
            }
        
        return None
    
    def _check_outlier_impact(self, result: pd.DataFrame) -> List[Dict]:
        """Check if outliers significantly impact results"""
        
        caveats = []
        
        numeric_cols = result.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            if col in ['count', 'total_txns']:
                continue
            
            data = result[col].dropna()
            
            if len(data) < 10:
                continue
            
            # IQR method
            q1 = data.quantile(0.25)
            q3 = data.quantile(0.75)
            iqr = q3 - q1
            
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            outliers = data[(data < lower_bound) | (data > upper_bound)]
            outlier_pct = len(outliers) / len(data)
            
            if outlier_pct > self.warning_thresholds['outlier_pct']:
                caveats.append({
                    'type': 'outlier_impact',
                    'severity': 'MEDIUM',
                    'message': f"{len(outliers)} outliers detected in {col.replace('_', ' ').title()} ({outlier_pct*100:.1f}% of data)",
                    'recommendation': "Outliers may significantly impact average - consider median or investigate extreme values"
                })
        
        return caveats
    
    def format_caveats(self, caveats: List[Dict]) -> str:
        """Format caveats for display"""
        
        if not caveats:
            return "✓ No significant data quality concerns detected"
        
        # Group by severity
        high = [c for c in caveats if c['severity'] == 'HIGH']
        medium = [c for c in caveats if c['severity'] == 'MEDIUM']
        low = [c for c in caveats if c['severity'] == 'LOW']
        info = [c for c in caveats if c['severity'] == 'INFO']
        
        lines = ["⚠️  IMPORTANT CAVEATS:"]
        
        # High severity first
        if high:
            lines.append("\n🔴 HIGH PRIORITY:")
            for caveat in high:
                lines.append(f"  • {caveat['message']}")
                lines.append(f"    → {caveat['recommendation']}")
        
        # Medium severity
        if medium:
            lines.append("\n🟡 MEDIUM PRIORITY:")
            for caveat in medium:
                lines.append(f"  • {caveat['message']}")
                lines.append(f"    → {caveat['recommendation']}")
        
        # Info/Low
        if info or low:
            lines.append("\n🔵 INFORMATIONAL:")
            for caveat in info + low:
                lines.append(f"  • {caveat['message']}")
        
        return "\n".join(lines)


# ============================================================================
# TESTING
# ============================================================================
if __name__ == "__main__":
    print("\n" + "="*80)
    print("CAVEAT DETECTOR TEST")
    print("="*80)
    
    detector = CaveatDetector()
    
    # Test Case 1: Small sample with skewed distribution
    print("\n--- Test 1: Small Sample ---")
    result = pd.DataFrame({
        'avg_amount': [2847, 1650, 3200, 890, 12000, 950, 1200]
    })
    
    caveats = detector.detect_all_caveats(
        result=result,
        filters={'transaction_type': 'P2M'},
        metrics=['avg_amount'],
        total_rows=250000
    )
    
    print(detector.format_caveats(caveats))
    
    # Test Case 2: Fraud flag query
    print("\n\n--- Test 2: Fraud Flag Query ---")
    result = pd.DataFrame({'fraud_flag_rate': [8.5]})
    
    caveats = detector.detect_all_caveats(
        result=result,
        filters={'fraud_flag': 1},
        metrics=['fraud_flag_rate'],
        total_rows=250000
    )
    
    print(detector.format_caveats(caveats))
    
    # Test Case 3: High variability
    print("\n\n--- Test 3: High Variability ---")
    result = pd.DataFrame({
        'avg_amount': [100, 5000, 200, 8000, 300, 12000, 150]
    })
    
    caveats = detector.detect_all_caveats(
        result=result,
        filters={},
        metrics=['avg_amount'],
        total_rows=250000
    )
    
    print(detector.format_caveats(caveats))
    
    print("\n" + "="*80)
    print("✓ CAVEAT DETECTOR TEST COMPLETE")
    print("="*80)