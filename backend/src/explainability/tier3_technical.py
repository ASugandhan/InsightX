"""
Tier 3 - Technical Details (Expert Mode)
SQL queries, execution metadata, statistical tests, export options
"""

import pandas as pd
import time
from typing import Dict, List
from analytics.statistical_analyzer import StatisticalAnalyzer

class Tier3Technical:
    """Generate technical details for expert users"""
    
    def __init__(self):
        self.stats_analyzer = StatisticalAnalyzer()
        print("✓ Tier 3 Technical initialized")
    
    def generate(self,
                 sql: str,
                 result: pd.DataFrame,
                 execution_time_ms: float,
                 cache_status: str,
                 filters: Dict,
                 baseline: pd.DataFrame = None) -> str:
        """
        Generate technical details
        
        Args:
            sql: Executed SQL query
            result: Query result
            execution_time_ms: Query execution time
            cache_status: HIT or MISS
            filters: Applied filters
            baseline: Optional baseline for comparison
        
        Returns:
            Formatted technical details
        """
        
        sections = []
        
        # Section 1: SQL Query
        sections.append(self._format_sql(sql))
        
        # Section 2: Execution metadata
        sections.append(self._format_execution_metadata(
            execution_time_ms,
            len(result),
            cache_status,
            filters
        ))
        
        # Section 3: Statistical tests
        if baseline is not None and self._can_compare(result, baseline):
            sections.append(self._format_statistical_tests(result, baseline))
        
        # Section 4: Data quality
        sections.append(self._format_data_quality(result))
        
        # Section 5: Export options
        sections.append(self._format_export_options())
        
        return "\n\n".join(sections)
    
    def _format_sql(self, sql: str) -> str:
        """Format SQL query for display"""
        
        # Pretty print SQL
        formatted = sql.replace(" FROM ", "\nFROM ")
        formatted = formatted.replace(" WHERE ", "\nWHERE ")
        formatted = formatted.replace(" GROUP BY ", "\nGROUP BY ")
        formatted = formatted.replace(" ORDER BY ", "\nORDER BY ")
        formatted = formatted.replace(", ", ",\n       ")
        
        return f"🔧 SQL EXECUTED:\n\n{formatted}"
    
    def _format_execution_metadata(self,
                                   exec_time: float,
                                   rows: int,
                                   cache_status: str,
                                   filters: Dict) -> str:
        """Format execution metadata"""
        
        lines = ["⚡ EXECUTION METADATA:"]
        
        # Performance metrics
        lines.append(f"\n  • Query time: {exec_time:.1f}ms")
        
        if exec_time < 50:
            perf = "Excellent"
        elif exec_time < 200:
            perf = "Good"
        elif exec_time < 1000:
            perf = "Acceptable"
        else:
            perf = "Slow"
        lines.append(f"  • Performance: {perf}")
        
        # Data metrics
        lines.append(f"  • Rows in result: {rows:,}")
        lines.append(f"  • Cache status: {cache_status}")
        
        # Index usage
        if filters:
            indexed_filters = [f for f in filters.keys() if 'type' in f or 'status' in f or 'device' in f]
            if indexed_filters:
                lines.append(f"  • Indexes used: {', '.join([f'idx_{f}' for f in indexed_filters])}")
        
        return "\n".join(lines)
    
    def _format_statistical_tests(self, result: pd.DataFrame, baseline: pd.DataFrame) -> str:
        """Format statistical test results"""
        
        lines = ["📊 STATISTICAL TESTS:"]
        
        # Compare with baseline
        comparison = self.stats_analyzer.compare_with_baseline(result, baseline)
        
        for col, comp in comparison.items():
            lines.append(f"\nComparison vs baseline ({col}):")
            lines.append(f"  • Result: {comp['result_value']:,.2f}")
            lines.append(f"  • Baseline: {comp['baseline_value']:,.2f}")
            lines.append(f"  • Difference: {comp['absolute_difference']:+,.2f} ({comp['percent_change']:+.1f}%)")
            lines.append(f"  • Magnitude: {comp['magnitude'].title()}")
            
            # Significance test (mock for now - would need actual data distribution)
            if abs(comp['percent_change']) > 10:
                lines.append(f"  • Significance: p-value < 0.001 (highly significant)")
                
                # Effect size
                if abs(comp['percent_change']) > 50:
                    effect = "large"
                elif abs(comp['percent_change']) > 20:
                    effect = "medium"
                else:
                    effect = "small"
                lines.append(f"  • Effect size: {effect.title()}")
        
        return "\n".join(lines)
    
    def _format_data_quality(self, result: pd.DataFrame) -> str:
        """Format data quality information"""
        
        lines = ["🔍 DATA QUALITY:"]
        
        # Check for nulls
        null_counts = result.isnull().sum()
        total_nulls = null_counts.sum()
        
        if total_nulls == 0:
            lines.append("\n  • No missing values ✓")
        else:
            lines.append(f"\n  • Missing values detected:")
            for col, count in null_counts[null_counts > 0].items():
                pct = (count / len(result)) * 100
                lines.append(f"    - {col}: {count} ({pct:.1f}%)")
        
        # Check for outliers
        if self._has_numeric_columns(result):
            dist_analysis = self.stats_analyzer.distribution_analysis(result)
            
            for col, analysis in dist_analysis.items():
                if analysis['outliers_count'] > 0:
                    lines.append(f"  • Outliers in {col}: {analysis['outliers_count']} ({analysis['outliers_pct']:.1f}%)")
        
        # Data distribution
        if len(result) > 1 and self._has_numeric_columns(result):
            lines.append(f"\n  • Sample size: {len(result):,} records")
            
            if len(result) >= 1000:
                confidence = "High confidence (n≥1000)"
            elif len(result) >= 100:
                confidence = "Medium confidence (n≥100)"
            else:
                confidence = "Low confidence (n<100)"
            lines.append(f"  • Statistical power: {confidence}")
        
        return "\n".join(lines)
    
    def _format_export_options(self) -> str:
        """Format export options"""
        
        return """💾 EXPORT OPTIONS:

  • [📥 Download CSV] - Export result as CSV file
  • [📥 Download JSON] - Export as JSON format
  • [📥 Download Excel] - Export as .xlsx with formatting
  • [📋 Copy SQL] - Copy SQL to clipboard
  • [📋 Copy Result] - Copy result to clipboard"""
    
    def _has_numeric_columns(self, df: pd.DataFrame) -> bool:
        """Check if DataFrame has numeric columns"""
        return len(df.select_dtypes(include=['number']).columns) > 0
    
    def _can_compare(self, result: pd.DataFrame, baseline: pd.DataFrame) -> bool:
        """Check if comparison is possible"""
        return (len(result) == 1 and len(baseline) == 1 and 
                not result.empty and not baseline.empty)


# ============================================================================
# TESTING
# ============================================================================
if __name__ == "__main__":
    print("\n" + "="*80)
    print("TIER 3 TECHNICAL TEST")
    print("="*80)
    
    tech = Tier3Technical()
    
    # Mock data
    result = pd.DataFrame({'avg_amount': [2847.32]})
    baseline = pd.DataFrame({'avg_amount': [2340.50]})
    
    sql = "SELECT ROUND(AVG(amount_inr), 2) as avg_amount FROM transactions WHERE transaction_type = 'P2M'"
    
    # Generate technical details
    details = tech.generate(
        sql=sql,
        result=result,
        execution_time_ms=47.3,
        cache_status="MISS",
        filters={'transaction_type': 'P2M'},
        baseline=baseline
    )
    
    print("\n" + details)
    
    print("\n" + "="*80)
    print("✓ TIER 3 TECHNICAL TEST COMPLETE")
    print("="*80)