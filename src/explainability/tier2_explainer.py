"""
Tier 2 Explainability - Detailed Methodology & Context
"""

import pandas as pd
from typing import Dict, List, Optional
from analytics.statistical_analyzer import StatisticalAnalyzer

class Tier2Explainer:
    """Generate detailed explanations for query results"""
    
    def __init__(self):
        self.stats_analyzer = StatisticalAnalyzer()
        print("✓ Tier 2 Explainer initialized")
    
    def explain(self, 
                query: str,
                result: pd.DataFrame,
                sql: str,
                filters: Dict,
                metrics: List[str]) -> str:
        """
        Generate Tier 2 explanation
        
        Returns:
            Formatted explanation text
        """
        
        explanation_parts = []
        
        # Section 1: How we calculated
        explanation_parts.append(self._explain_methodology(query, sql, filters, metrics))
        
        # Section 2: Statistical context
        if self._has_numeric_data(result):
            explanation_parts.append(self._explain_statistical_context(result, metrics))
        
        # Section 3: Data scope
        explanation_parts.append(self._explain_data_scope(result, filters))
        
        # Section 4: Important caveats
        caveats = self._detect_caveats(result, filters)
        if caveats:
            explanation_parts.append(self._format_caveats(caveats))
        
        return "\n\n".join(explanation_parts)
    
    def _explain_methodology(self, query: str, sql: str, filters: Dict, metrics: List[str]) -> str:
        """Explain how the answer was calculated"""
        
        lines = ["📊 HOW WE CALCULATED THIS:"]
        
        # Explain filters
        if filters:
            lines.append("\nFilters applied:")
            for key, value in filters.items():
                friendly_key = self._humanize_column(key)
                lines.append(f"  • {friendly_key}: {value}")
        else:
            lines.append("\n  • No filters applied (using all transactions)")
        
        # Explain metrics
        if metrics:
            lines.append("\nMetrics calculated:")
            for metric in metrics:
                lines.append(f"  • {self._explain_metric(metric)}")
        
        # Explain aggregation
        if "GROUP BY" in sql.upper():
            lines.append("\n  • Results grouped by specified dimensions")
        
        return "\n".join(lines)
    
    def _explain_statistical_context(self, result: pd.DataFrame, metrics: List[str]) -> str:
        """Provide statistical context"""
        
        lines = ["📈 STATISTICAL CONTEXT:"]
        
        # Get descriptive stats
        stats = self.stats_analyzer.descriptive_stats(result)
        
        for col, col_stats in stats.items():
            lines.append(f"\nFor {self._humanize_column(col)}:")
            lines.append(f"  • Mean: {col_stats['mean']:,.2f}")
            lines.append(f"  • Median: {col_stats['median']:,.2f}")
            
            # Interpret distribution
            if col_stats['mean'] > col_stats['median'] * 1.2:
                lines.append(f"  • Distribution: Right-skewed (high outliers present)")
            elif col_stats['mean'] < col_stats['median'] * 0.8:
                lines.append(f"  • Distribution: Left-skewed (low outliers present)")
            else:
                lines.append(f"  • Distribution: Roughly symmetric")
            
            lines.append(f"  • Std Dev: ±{col_stats['std']:,.2f} ({self._interpret_std_dev(col_stats)})")
            lines.append(f"  • Range: {col_stats['min']:,.2f} to {col_stats['max']:,.2f}")
        
        return "\n".join(lines)
    
    def _explain_data_scope(self, result: pd.DataFrame, filters: Dict) -> str:
        """Explain what data was included/excluded"""
        
        lines = ["🔍 DATA SCOPE:"]
        
        # Sample size
        if len(result) == 1:
            lines.append(f"\n  • Analysis based on aggregated data")
        else:
            lines.append(f"\n  • {len(result):,} records in result")
        
        # What was included
        if filters:
            lines.append(f"\n  • Included: Transactions matching {len(filters)} filter(s)")
        
        # What was excluded
        exclusions = self._detect_exclusions(filters)
        if exclusions:
            lines.append(f"\n  • Excluded: {exclusions}")
        
        return "\n".join(lines)
    
    def _detect_caveats(self, result: pd.DataFrame, filters: Dict) -> List[str]:
        """Detect important caveats about the data"""
        
        caveats = []
        
        # Small sample size
        if len(result) < 100 and len(result) > 1:
            caveats.append(f"Small sample size ({len(result)} records) - results may not be representative")
        
        # Fraud flag interpretation
        if 'fraud_flag' in filters:
            caveats.append("'Fraud flag' means flagged for review, NOT confirmed fraud")
        
        # Merchant category variation
        if 'merchant_category' not in filters and any('merchant' in str(f).lower() for f in filters.values()):
            caveats.append("Results may vary significantly by merchant category")
        
        # Check for high variance
        if self._has_numeric_data(result):
            stats = self.stats_analyzer.descriptive_stats(result)
            for col, col_stats in stats.items():
                cv = col_stats['std'] / col_stats['mean'] if col_stats['mean'] != 0 else 0
                if cv > 0.5:  # Coefficient of variation > 50%
                    caveats.append(f"High variability in {self._humanize_column(col)} (CV={cv:.1%})")
        
        return caveats
    
    def _format_caveats(self, caveats: List[str]) -> str:
        """Format caveats section"""
        
        lines = ["⚠️  IMPORTANT CAVEATS:"]
        for caveat in caveats:
            lines.append(f"\n  • {caveat}")
        
        return "\n".join(lines)
    
    # Helper methods
    
    def _humanize_column(self, col: str) -> str:
        """Convert column name to human-readable"""
        
        mapping = {
            'amount_inr': 'transaction amount',
            'transaction_type': 'transaction type',
            'merchant_category': 'merchant category',
            'sender_age_group': 'sender age group',
            'device_type': 'device type',
            'transaction_status': 'transaction status',
            'fraud_flag': 'fraud flag',
            'is_weekend': 'weekend/weekday',
            'hour_of_day': 'hour of day',
            'avg_amount': 'average amount',
            'total_amount': 'total amount',
            'count': 'transaction count',
            'success_rate': 'success rate',
            'failure_rate': 'failure rate',
        }
        
        return mapping.get(col, col.replace('_', ' ').title())
    
    def _explain_metric(self, metric: str) -> str:
        """Explain what a metric means"""
        
        explanations = {
            'avg_amount': 'Average transaction amount (mean)',
            'total_amount': 'Sum of all transaction amounts',
            'median_amount': 'Median transaction amount (50th percentile)',
            'count': 'Number of transactions',
            'success_rate': 'Percentage of successful transactions',
            'failure_rate': 'Percentage of failed transactions',
            'fraud_flag_rate': 'Percentage of flagged transactions',
        }
        
        return explanations.get(metric, metric.replace('_', ' ').title())
    
    def _interpret_std_dev(self, stats: Dict) -> str:
        """Interpret standard deviation"""
        
        cv = stats['std'] / stats['mean'] if stats['mean'] != 0 else 0
        
        if cv < 0.15:
            return "low variability"
        elif cv < 0.30:
            return "moderate variability"
        else:
            return "high variability"
    
    def _detect_exclusions(self, filters: Dict) -> str:
        """Detect what was excluded by filters"""
        
        exclusions = []
        
        if 'transaction_type' in filters:
            all_types = ['P2P', 'P2M', 'Bill Payment', 'Recharge']
            included = filters['transaction_type']
            excluded = [t for t in all_types if t != included]
            if excluded:
                exclusions.append(f"{', '.join(excluded)} transactions")
        
        if 'is_weekend' in filters:
            if filters['is_weekend'] == 1:
                exclusions.append("weekday transactions")
            else:
                exclusions.append("weekend transactions")
        
        return ", ".join(exclusions) if exclusions else "None"
    
    def _has_numeric_data(self, df: pd.DataFrame) -> bool:
        """Check if DataFrame has numeric columns"""
        return len(df.select_dtypes(include=['number']).columns) > 0


# ============================================================================
# TESTING
# ============================================================================
if __name__ == "__main__":
    import sys
    sys.path.append('..')
    
    print("\n" + "="*80)
    print("TIER 2 EXPLAINER TEST")
    print("="*80)
    
    explainer = Tier2Explainer()
    
    # Mock data
    result = pd.DataFrame({
        'avg_amount': [2847.32],
        'count': [62450]
    })
    
    sql = "SELECT AVG(amount_inr) as avg_amount FROM transactions WHERE transaction_type = 'P2M'"
    filters = {'transaction_type': 'P2M'}
    metrics = ['avg_amount']
    
    # Generate explanation
    explanation = explainer.explain(
        query="What is the average P2M amount?",
        result=result,
        sql=sql,
        filters=filters,
        metrics=metrics
    )
    
    print("\n" + explanation)
    
    print("\n" + "="*80)
    print("✓ TIER 2 EXPLAINER TEST COMPLETE")
    print("="*80)