"""
Complete Response Formatter with 3-Tier Explainability
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from unittest import result
import pandas as pd
import sys
sys.path.append('..')

from explainability.tier2_explainer import Tier2Explainer
from explainability.tier3_technical import Tier3Technical
from explainability.caveat_detector import CaveatDetector
from explainability.hypothesis_generator import HypothesisGenerator
from explainability.plain_language import PlainLanguageTranslator


@dataclass
class Response:
    """Complete formatted response for user"""
    tier1_text: str              # Always visible
    confidence: str              # HIGH, MEDIUM, LOW
    sample_size: int             # Number of records
    tier2_details: str           # Expandable methodology
    tier3_technical: str         # Expert mode details
    caveats: str                 # Warnings and limitations
    hypotheses: str              # Possible explanations
    context_comparison: str      # Comparison with baseline


class ResponseFormatter:
    """Format query results with complete explainability"""
    
    def __init__(self):
        self.tier2 = Tier2Explainer()
        self.tier3 = Tier3Technical()
        self.caveat_detector = CaveatDetector()
        self.hypothesis_gen = HypothesisGenerator()
        self.translator = PlainLanguageTranslator()
        
        print("✓ Response Formatter initialized (Full explainability)")

    def _normalize_metrics(self, metrics) -> List[str]:
        """Normalize metrics to string List"""

        normalized = []
        for m in metrics:
            if isinstance(m, str):
                normalized.append(m)
            elif isinstance(m, dict):
                agg = m.get('aggregation', '')
                col = m.get('column', '')
                if agg and col:
                    normalized.append(f"{agg}_{col.replace('_inr','')}")
                else:
                    normalized.append(str(m))
        
        return normalized
    
    def format(self,
               query: str,
               result: pd.DataFrame,
               confidence: float,
               sql: str = "",
               filters: Dict = None,
               metrics: List[str] = None,
               execution_time_ms: float = 0,
               baseline: pd.DataFrame = None,
               analytics_engine = None) -> Response:
        """
        Format complete response with all 3 tiers
        
        Args:
            query: Original user query
            result: Query result DataFrame
            confidence: Parse confidence (0-1)
            sql: Executed SQL query
            filters: Applied filters
            metrics: Requested metrics
            execution_time_ms: Query execution time
            baseline: Baseline for comparison
        
        Returns:
            Complete Response object
        """
        metrics = self._normalize_metrics(metrics or [])
        filters = filters or {}
        
        # ✅ STORE analytics engine for trust builder
        self._analytics_engine = analytics_engine
    
        # ✅ GET trust builder
        from explainability.trust_builder import TrustBuilder
        trust = TrustBuilder()
    
        # ✅ GET actual sample size
        actual_sample_size = None
        if analytics_engine:
            actual_sample_size = trust.get_actual_sample_size(analytics_engine, filters)
    
        if not actual_sample_size:
            actual_sample_size = self._get_sample_size(result)

        if not actual_sample_size:
            actual_sample_size = 0 

        # TIER 1: Always visible
        tier1 = self._format_tier1(query, result, filters, baseline)
        
        # Confidence badge
        conf_badge = self._confidence_badge(confidence)
        
        quality_badge = trust.get_data_quality_badge(actual_sample_size, confidence)
        
        # TIER 2: Detailed explanation
        tier2 = self.tier2.explain(
            query=query,
            result=result,
            sql=sql,
            filters=filters,
            metrics=metrics
        )
        
        # TIER 3: Technical details
        tier3 = self.tier3.generate(
            sql=sql,
            result=result,
            execution_time_ms=execution_time_ms,
            cache_status="MISS",  # Would track this in production
            filters=filters,
            baseline=baseline
        )
        
        # Caveats
        detected_caveats = self.caveat_detector.detect_all_caveats(
            result=result,
            filters=filters,
            metrics=metrics,
            total_rows=250000
        )
        caveats = self.caveat_detector.format_caveats(detected_caveats)
        sanity_checks = trust.run_sanity_checks(result, filters, metrics, actual_sample_size)
        sanity_text = "\n\n🔍 VALIDATION:\n" + "\n".join([f"  {c}" for c in sanity_checks])
        
        # Hypotheses (for "why" questions)
        hypothesis_list = self.hypothesis_gen.generate_hypotheses(
            query=query,
            result=result,
            filters=filters,
            metrics=metrics
        )
        hypotheses = self.hypothesis_gen.format_hypotheses(hypothesis_list)
        
        # Context comparison
        context = self._format_context_comparison(result, baseline, filters)
        tier1_with_badge = tier1 + f"\n\n📊 {quality_badge}"
        
        return Response(
            tier1_text=tier1_with_badge, 
            confidence=conf_badge,
            sample_size=actual_sample_size,
            tier2_details=tier2,
            tier3_technical=tier3,
            caveats=caveats + sanity_text,
            hypotheses=hypotheses,
            context_comparison=context
        )
    
    def _format_tier1(self,
                  query: str,
                  result: pd.DataFrame,
                  filters: Dict,
                  baseline: pd.DataFrame = None) -> str:
        """Format Tier 1 - Always visible answer with trust indicators"""
    
        lines = []
    
    # Get trust builder
        from explainability.trust_builder import TrustBuilder
        trust = TrustBuilder()
    
    # Get actual sample size
        actual_sample_size = None
        if hasattr(self, '_analytics_engine'):
            actual_sample_size = trust.get_actual_sample_size(self._analytics_engine, filters)
    
    # CASE 1: Single aggregated result
        if len(result) == 1:
            # Prefer amount / rate over count
            priority = ["avg_amount", "total_amount", "median_amount",
                        "success_rate", "failure_rate", "fraud_flag_rate", "count"]
        
            metric_found = None
            value_found = None
        
            for metric in priority:
                if metric in result.columns:
                    metric_found = metric
                    value_found = result[metric].iloc[0]
                
                # Main result display
                    if "amount" in metric:
                        lines.append(f"💰 {self._humanize_column(metric)}: ₹{value_found:,.2f}")
                    
                    # ✅ ADD: Confidence interval
                        if actual_sample_size and actual_sample_size > 30:
                            lower, upper = trust.calculate_confidence_interval(
                                value_found, actual_sample_size
                            )
                            if lower and upper:
                                lines.append(f"   95% Confidence: ₹{lower:,} - ₹{upper:,}")
                    
                    # ✅ ADD: Sample size context
                        if actual_sample_size:
                            lines.append(f"   (Based on {actual_sample_size:,} transactions)")
                
                    elif "rate" in metric:
                        lines.append(f"📊 {self._humanize_column(metric)}: {value_found:.2f}%")
                        if actual_sample_size:
                            lines.append(f"   (Based on {actual_sample_size:,} transactions)")
                
                    else:  # count
                        lines.append(f"📈 {self._humanize_column(metric)}: {value_found:,.0f} transactions")
                
                    break
        
        # ✅ ADD: Reasonableness check
            if metric_found and value_found:
                reasonableness = trust.check_reasonableness(metric_found, value_found, filters)
                if reasonableness:
                    lines.append(f"\n{reasonableness}")
    
    # CASE 2: Small grouped result
        elif len(result) <= 10:
            lines.append("📊 Results:\n")
            lines.append(result.to_string(index=False))
    
    # CASE 3: Large result
        else:
            lines.append(f"📊 Found {len(result):,} records")
            lines.append("\nTop 10 results:")
            lines.append(result.head(10).to_string(index=False))
    
    # Key insight
        insight = self._generate_key_insight(result, filters, baseline)
        if insight:
            lines.append(f"\n\n💡 Key Insight: {insight}")
    
        return "\n".join(lines)

    def _format_context_comparison(self,
                                   result: pd.DataFrame,
                                   baseline: pd.DataFrame,
                                   filters: Dict) -> str:
        """Format comparison with baseline"""
        
        if baseline is None or baseline.empty:
            return "ℹ️  No baseline available for comparison"
        
        lines = ["📊 CONTEXT VS BASELINE:"]
        
        # Compare numeric columns
        for col in result.columns:
            if col in baseline.columns and pd.api.types.is_numeric_dtype(result[col]):
                result_val = result[col].iloc[0] if len(result) == 1 else result[col].mean()
                baseline_val = baseline[col].iloc[0] if len(baseline) == 1 else baseline[col].mean()
                
                if pd.notna(result_val) and pd.notna(baseline_val) and baseline_val != 0:
                    diff = result_val - baseline_val
                    pct_change = (diff / baseline_val) * 100
                    
                    direction = "higher" if diff > 0 else "lower"
                    
                    lines.append(f"\n  • {self._humanize_column(col)}:")
                    lines.append(f"    - Current: {result_val:,.2f}")
                    lines.append(f"    - Baseline: {baseline_val:,.2f}")
                    lines.append(f"    - Difference: {abs(pct_change):.1f}% {direction}")
        
        return "\n".join(lines)
    
    def _generate_key_insight(self,
                             result: pd.DataFrame,
                             filters: Dict,
                             baseline: pd.DataFrame) -> str:
        """Generate a key actionable insight"""
        
        # Check for significant differences
        if baseline is not None and not baseline.empty:
            for col in result.columns:
                if col in baseline.columns and pd.api.types.is_numeric_dtype(result[col]):
                    result_val = result[col].iloc[0] if len(result) == 1 else result[col].mean()
                    baseline_val = baseline[col].iloc[0] if len(baseline) == 1 else baseline[col].mean()
                    
                    if pd.notna(result_val) and pd.notna(baseline_val) and baseline_val != 0:
                        pct_change = ((result_val - baseline_val) / baseline_val) * 100
                        
                        if abs(pct_change) > 20:
                            direction = "higher" if pct_change > 0 else "lower"
                            return f"{self._humanize_column(col)} is {abs(pct_change):.0f}% {direction} than average"
        
        # Check for interesting patterns in grouped data
        if len(result) > 1:
            numeric_cols = [
                c for c in result.columns
                if pd.api.types.is_numeric_dtype(result[c])
            ]

            categorical_cols = [
                c for c in result.columns
               if not pd.api.types.is_numeric_dtype(result[c])
            ]

        # Case 1: Numeric + categorical → normal insight
            if numeric_cols and categorical_cols:
                metric_col = numeric_cols[0]
                category_col = categorical_cols[0]

                max_idx = result[metric_col].idxmax()
                max_val = result.loc[max_idx, metric_col]
                category_val = result.loc[max_idx, category_col]

                return (
                    f"{category_val} has the highest "
                    f"{self._humanize_column(metric_col)} ({max_val:,.0f})"
                )

        # Case 2: Only numeric (like is_weekend = 0/1)
            if numeric_cols and not categorical_cols:
                metric_col = numeric_cols[-1]
                return (
                    f"Transactions vary significantly across values of "
                    f"{self._humanize_column(metric_col)}"
                )

        
        return None
    
    def _confidence_badge(self, confidence: float) -> str:
        """Get confidence badge"""
        if confidence > 0.8:
            return "HIGH ✓"
        elif confidence > 0.6:
            return "MEDIUM ⚠️"
        else:
            return "LOW ⚠️"
    
    def _get_sample_size(self, result: pd.DataFrame) -> int:
        """
        Determine sample size safely.
        Only trust COUNT when explicitly present.
        """

        # Case 1: Explicit COUNT metric
        if "count" in result.columns:
            try:
                return int(result["count"].iloc[0])
            except Exception:
                return 0

        # Case 2: Aggregated metric without count
        # Cannot infer true sample size from result alone
        return None

    def _humanize_column(self, col: str) -> str:
        """Convert column name to human-readable"""
        mapping = {
            'amount_inr': 'Transaction Amount',
            'avg_amount': 'Average Amount',
            'total_amount': 'Total Amount',
            'count': 'Transaction Count',
            'success_rate': 'Success Rate',
            'failure_rate': 'Failure Rate',
            'fraud_flag_rate': 'Fraud Flag Rate',
        }
        return mapping.get(col, col.replace('_', ' ').title())


# ============================================================================
# TESTING
# ============================================================================
if __name__ == "__main__":
    print("\n" + "="*80)
    print("COMPLETE RESPONSE FORMATTER TEST")
    print("="*80)
    
    formatter = ResponseFormatter()
    
    # Test with simple query
    result = pd.DataFrame({
        'avg_amount': [2847.32],
        'count': [62450]
    })
    
    baseline = pd.DataFrame({
        'avg_amount': [2340.50]
    })
    
    sql = "SELECT ROUND(AVG(amount_inr), 2) as avg_amount, COUNT(*) as count FROM transactions WHERE transaction_type = 'P2M'"
    
    response = formatter.format(
        query="What is the average P2M transaction amount?",
        result=result,
        confidence=0.95,
        sql=sql,
        filters={'transaction_type': 'P2M'},
        metrics=['avg_amount'],
        execution_time_ms=47.3,
        baseline=baseline
    )
    
    print("\n" + "="*80)
    print("TIER 1 - ALWAYS VISIBLE")
    print("="*80)
    print(response.tier1_text)
    print(f"\nConfidence: {response.confidence}")
    print(f"Sample Size: {response.sample_size:,}")
    
    print("\n\n" + "="*80)
    print("TIER 2 - DETAILED EXPLANATION")
    print("="*80)
    print(response.tier2_details)
    
    print("\n\n" + "="*80)
    print("CAVEATS")
    print("="*80)
    print(response.caveats)
    
    print("\n\n" + "="*80)
    print("CONTEXT COMPARISON")
    print("="*80)
    print(response.context_comparison)
    
    print("\n\n" + "="*80)
    print("✓ COMPLETE FORMATTER TEST PASSED")
    print("="*80)