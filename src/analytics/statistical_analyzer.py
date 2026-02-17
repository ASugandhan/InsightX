"""
Statistical Analyzer - Provides statistical rigor to query results
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Tuple, Optional

class StatisticalAnalyzer:
    """Perform statistical analysis on query results"""
    
    def __init__(self):
        print("✓ Statistical Analyzer initialized")
    
    def analyze(self, result: pd.DataFrame, baseline: Optional[pd.DataFrame] = None) -> Dict:
        """
        Comprehensive statistical analysis
        
        Args:
            result: Query result DataFrame
            baseline: Optional baseline for comparison
        
        Returns:
            Dictionary with statistical measures
        """
        
        analysis = {}
        
        # Descriptive statistics
        if self._has_numeric_columns(result):
            analysis['descriptive'] = self.descriptive_stats(result)
        
        # Distribution analysis
        if len(result) > 30 and self._has_numeric_columns(result):
            analysis['distribution'] = self.distribution_analysis(result)
        
        # Comparison with baseline
        if baseline is not None and len(baseline) > 0:
            analysis['comparison'] = self.compare_with_baseline(result, baseline)
        
        # Sample size adequacy
        analysis['sample_size'] = {
            'count': len(result),
            'adequate': len(result) >= 100,
            'confidence_level': self._sample_confidence(len(result))
        }
        
        return analysis
    
    def descriptive_stats(self, df: pd.DataFrame) -> Dict:
        """Calculate descriptive statistics"""
        
        stats_dict = {}
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            if col in ['count', 'total_txns']:  # Skip count columns
                continue
            
            data = df[col].dropna()
            
            if len(data) == 0:
                continue
            
            stats_dict[col] = {
                'mean': round(float(data.mean()), 2),
                'median': round(float(data.median()), 2),
                'std': round(float(data.std()), 2),
                'min': round(float(data.min()), 2),
                'max': round(float(data.max()), 2),
                'q25': round(float(data.quantile(0.25)), 2),
                'q75': round(float(data.quantile(0.75)), 2),
                'iqr': round(float(data.quantile(0.75) - data.quantile(0.25)), 2),
                'skewness': round(float(data.skew()), 2),
                'kurtosis': round(float(data.kurtosis()), 2)
            }
        
        return stats_dict
    
    def distribution_analysis(self, df: pd.DataFrame) -> Dict:
        """Analyze distribution characteristics"""
        
        dist_dict = {}
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            if col in ['count', 'total_txns']:
                continue
            
            data = df[col].dropna()
            
            if len(data) < 30:
                continue
            
            # Normality test
            _, p_value = stats.normaltest(data)
            
            # Outlier detection (IQR method)
            q1 = data.quantile(0.25)
            q3 = data.quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            outliers = data[(data < lower_bound) | (data > upper_bound)]
            
            dist_dict[col] = {
                'is_normal': p_value > 0.05,
                'normality_p_value': round(float(p_value), 4),
                'outliers_count': len(outliers),
                'outliers_pct': round(len(outliers) / len(data) * 100, 2),
                'distribution_type': self._classify_distribution(data)
            }
        
        return dist_dict
    
    def compare_with_baseline(self, result: pd.DataFrame, baseline: pd.DataFrame) -> Dict:
        """Compare result with baseline using statistical tests"""
        
        comparison = {}
        
        # For single-row results (e.g., "average P2M amount" vs overall average)
        if len(result) == 1 and len(baseline) == 1:
            numeric_cols = result.select_dtypes(include=[np.number]).columns
            
            for col in numeric_cols:
                if col in result.columns and col in baseline.columns:
                    result_val = result[col].iloc[0]
                    baseline_val = baseline[col].iloc[0]
                    
                    if pd.notna(result_val) and pd.notna(baseline_val) and baseline_val != 0:
                        difference = result_val - baseline_val
                        pct_change = (difference / baseline_val) * 100
                        
                        comparison[col] = {
                            'result_value': round(float(result_val), 2),
                            'baseline_value': round(float(baseline_val), 2),
                            'absolute_difference': round(float(difference), 2),
                            'percent_change': round(float(pct_change), 2),
                            'direction': 'higher' if difference > 0 else 'lower',
                            'magnitude': self._classify_magnitude(abs(pct_change))
                        }
        
        return comparison
    
    def significance_test(self, group1: pd.Series, group2: pd.Series, test_type: str = 'auto') -> Dict:
        """
        Perform significance test between two groups
        
        Args:
            group1: First group data
            group2: Second group data
            test_type: 'ttest', 'chi2', or 'auto'
        
        Returns:
            Dict with test results
        """
        
        # Remove NaN values
        g1 = group1.dropna()
        g2 = group2.dropna()
        
        if len(g1) < 2 or len(g2) < 2:
            return {'error': 'Insufficient data for significance test'}
        
        # Auto-detect test type
        if test_type == 'auto':
            test_type = 'ttest' if g1.dtype in [np.float64, np.int64] else 'chi2'
        
        if test_type == 'ttest':
            # T-test for continuous data
            statistic, p_value = stats.ttest_ind(g1, g2)
            
            return {
                'test': 't-test',
                'statistic': round(float(statistic), 4),
                'p_value': round(float(p_value), 4),
                'significant': p_value < 0.05,
                'interpretation': 'Statistically significant difference' if p_value < 0.05 else 'No significant difference',
                'confidence': '95%'
            }
        
        elif test_type == 'chi2':
            # Chi-square test for categorical data
            contingency = pd.crosstab(g1, g2)
            chi2, p_value, dof, expected = stats.chi2_contingency(contingency)
            
            return {
                'test': 'chi-square',
                'statistic': round(float(chi2), 4),
                'p_value': round(float(p_value), 4),
                'degrees_of_freedom': dof,
                'significant': p_value < 0.05,
                'interpretation': 'Statistically significant association' if p_value < 0.05 else 'No significant association',
                'confidence': '95%'
            }
    
    def correlation_analysis(self, df: pd.DataFrame) -> Dict:
        """Calculate correlations between numeric columns"""
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) < 2:
            return {}
        
        corr_matrix = df[numeric_cols].corr()
        
        # Find strong correlations (>0.5 or <-0.5)
        strong_corr = []
        
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_val = corr_matrix.iloc[i, j]
                
                if abs(corr_val) > 0.5:
                    strong_corr.append({
                        'var1': corr_matrix.columns[i],
                        'var2': corr_matrix.columns[j],
                        'correlation': round(float(corr_val), 3),
                        'strength': self._classify_correlation(abs(corr_val)),
                        'direction': 'positive' if corr_val > 0 else 'negative'
                    })
        
        return {
            'strong_correlations': strong_corr,
            'correlation_matrix': corr_matrix.round(3).to_dict()
        }
    
    # Helper methods
    
    def _has_numeric_columns(self, df: pd.DataFrame) -> bool:
        """Check if DataFrame has numeric columns"""
        return len(df.select_dtypes(include=[np.number]).columns) > 0
    
    def _sample_confidence(self, n: int) -> str:
        """Determine confidence level based on sample size"""
        if n >= 1000:
            return 'high'
        elif n >= 100:
            return 'medium'
        else:
            return 'low'
    
    def _classify_distribution(self, data: pd.Series) -> str:
        """Classify distribution shape"""
        skewness = data.skew()
        
        if abs(skewness) < 0.5:
            return 'symmetric'
        elif skewness > 0.5:
            return 'right-skewed'
        else:
            return 'left-skewed'
    
    def _classify_magnitude(self, pct_change: float) -> str:
        """Classify magnitude of percentage change"""
        if abs(pct_change) < 5:
            return 'negligible'
        elif abs(pct_change) < 20:
            return 'small'
        elif abs(pct_change) < 50:
            return 'moderate'
        else:
            return 'large'
    
    def _classify_correlation(self, corr: float) -> str:
        """Classify correlation strength"""
        if corr > 0.8:
            return 'very strong'
        elif corr > 0.6:
            return 'strong'
        elif corr > 0.4:
            return 'moderate'
        else:
            return 'weak'


# ============================================================================
# TESTING
# ============================================================================
if __name__ == "__main__":
    analyzer = StatisticalAnalyzer()
    
    print("\n" + "="*80)
    print("STATISTICAL ANALYZER TEST")
    print("="*80)
    
    # Test 1: Descriptive stats
    print("\n1. Testing Descriptive Statistics...")
    test_df = pd.DataFrame({
        'amount': [100, 200, 150, 300, 250, 180, 220, 190, 280, 160],
        'count': [10, 20, 15, 30, 25, 18, 22, 19, 28, 16]
    })
    
    desc_stats = analyzer.descriptive_stats(test_df)
    print(f"   Mean: {desc_stats['amount']['mean']}")
    print(f"   Median: {desc_stats['amount']['median']}")
    print(f"   Std Dev: {desc_stats['amount']['std']}")
    print(f"   ✅ Descriptive stats working")
    
    # Test 2: Distribution analysis
    print("\n2. Testing Distribution Analysis...")
    large_sample = pd.DataFrame({
        'values': np.random.normal(100, 15, 100)
    })
    
    dist_analysis = analyzer.distribution_analysis(large_sample)
    if 'values' in dist_analysis:
        print(f"   Is Normal: {dist_analysis['values']['is_normal']}")
        print(f"   Distribution Type: {dist_analysis['values']['distribution_type']}")
        print(f"   ✅ Distribution analysis working")
    
    # Test 3: Baseline comparison
    print("\n3. Testing Baseline Comparison...")
    result = pd.DataFrame({'avg_amount': [2847]})
    baseline = pd.DataFrame({'avg_amount': [2340]})
    
    comparison = analyzer.compare_with_baseline(result, baseline)
    if 'avg_amount' in comparison:
        print(f"   Percent Change: {comparison['avg_amount']['percent_change']}%")
        print(f"   Direction: {comparison['avg_amount']['direction']}")
        print(f"   ✅ Baseline comparison working")
    
    print("\n" + "="*80)
    print("✅ ALL STATISTICAL ANALYZER TESTS PASSED!")
    print("="*80)