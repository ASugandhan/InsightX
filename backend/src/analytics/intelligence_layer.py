"""
Intelligence Layer - The original heart of InsightX.
Analyzes query results, detects anomalies, compares benchmarks,
spots trends. This is what makes InsightX more than a wrapper.
"""

import pandas as pd
import numpy as np


class IntelligenceLayer:
    """
    Analyzes data results and generates insights.
    Compares against benchmarks, detects anomalies, spots trends.
    """

    def __init__(self, precomputed: dict):
        """
        Args:
            precomputed: Dict of pre-computed baseline metrics from AnalyticsEngine
        """
        self.baselines = precomputed
        self.overall = precomputed.get('overall', {})
        print("IntelligenceLayer initialized")

    def analyze(self, result: pd.DataFrame, intent: str, sql: str) -> dict:
        """
        Analyze query results and generate insights.

        Returns dict with:
            - insights: list of insight strings
            - anomalies: list of anomaly strings
            - benchmark_comparison: string comparing to baseline
            - proactive_tips: list of things user didn't ask but should know
        """
        if result is None or result.empty:
            return {
                "insights": ["No data found for this query."],
                "anomalies": [],
                "benchmark_comparison": "",
                "proactive_tips": []
            }

        insights = []
        anomalies = []
        proactive_tips = []
        benchmark_comparison = ""

        # Detect numeric columns
        num_cols = [c for c in result.columns if pd.api.types.is_numeric_dtype(result[c])]
        cat_cols = [c for c in result.columns if result[c].dtype == object]

        # ---- BENCHMARK COMPARISONS ----
        benchmark_comparison = self._compare_to_baseline(result, num_cols)

        # ---- ANOMALY DETECTION ----
        anomalies = self._detect_anomalies(result, num_cols, cat_cols)

        # ---- TREND/PATTERN INSIGHTS ----
        insights = self._generate_insights(result, num_cols, cat_cols, intent)

        # ---- PROACTIVE TIPS ----
        proactive_tips = self._proactive_suggestions(result, intent, sql)

        return {
            "insights": insights,
            "anomalies": anomalies,
            "benchmark_comparison": benchmark_comparison,
            "proactive_tips": proactive_tips
        }

    def _compare_to_baseline(self, result: pd.DataFrame, num_cols: list) -> str:
        """Compare result values to overall dataset baselines."""
        comparisons = []

        if result.shape[0] == 1:
            row = result.iloc[0]

            # Failure rate comparison
            for col in num_cols:
                col_lower = col.lower()

                if 'failure_rate' in col_lower or 'fail_rate' in col_lower:
                    baseline_fail = self.overall.get('failure_rate', None)
                    if baseline_fail is not None:
                        val = float(row[col])
                        diff = val - baseline_fail
                        if abs(diff) > 1.0:
                            direction = "higher" if diff > 0 else "lower"
                            comparisons.append(
                                f"Failure rate ({val:.1f}%) is {abs(diff):.1f}% {direction} than the overall average ({baseline_fail:.1f}%)"
                            )

                elif 'avg_amount' in col_lower or 'average_amount' in col_lower:
                    baseline_avg = self.overall.get('avg_amount', None)
                    if baseline_avg is not None:
                        val = float(row[col])
                        pct_diff = ((val - baseline_avg) / baseline_avg) * 100
                        if abs(pct_diff) > 10:
                            direction = "higher" if pct_diff > 0 else "lower"
                            comparisons.append(
                                f"Average amount (₹{val:,.0f}) is {abs(pct_diff):.0f}% {direction} than overall average (₹{baseline_avg:,.0f})"
                            )

                elif 'fraud' in col_lower and 'rate' in col_lower:
                    baseline_fraud = self.overall.get('fraud_flag_rate', None)
                    if baseline_fraud is not None:
                        val = float(row[col])
                        if val > baseline_fraud * 1.5:
                            comparisons.append(
                                f"Fraud rate ({val:.2f}%) is significantly higher than overall ({baseline_fraud:.2f}%) — needs attention!"
                            )

                elif 'success_rate' in col_lower:
                    baseline_sr = self.overall.get('success_rate', None)
                    if baseline_sr is not None:
                        val = float(row[col])
                        diff = val - baseline_sr
                        if abs(diff) > 2.0:
                            direction = "better" if diff > 0 else "worse"
                            comparisons.append(
                                f"Success rate ({val:.1f}%) is {direction} than overall ({baseline_sr:.1f}%)"
                            )

        return " | ".join(comparisons) if comparisons else ""

    def _detect_anomalies(self, result: pd.DataFrame, num_cols: list, cat_cols: list) -> list:
        """Detect statistical anomalies in grouped results."""
        anomalies = []

        if result.shape[0] < 3:
            return anomalies

        for col in num_cols:
            try:
                values = result[col].dropna().astype(float)
                if len(values) < 3:
                    continue
                mean = values.mean()
                std = values.std()
                if std == 0:
                    continue

                # Find outliers (z-score > 2)
                z_scores = (values - mean) / std
                outlier_idxs = z_scores[abs(z_scores) > 2].index

                for idx in outlier_idxs:
                    val = values[idx]
                    direction = "unusually high" if val > mean else "unusually low"
                    label = ""
                    if cat_cols:
                        label = str(result.loc[idx, cat_cols[0]])
                    anomalies.append(
                        f"{label} has {direction} {col.replace('_', ' ')} ({val:.1f} vs avg {mean:.1f})"
                    )
            except Exception:
                continue

        return anomalies[:3]  # Cap at 3 anomalies

    def _generate_insights(self, result: pd.DataFrame, num_cols: list, cat_cols: list, intent: str) -> list:
        """Generate meaningful insights from the data."""
        insights = []

        if result.shape[0] == 1:
            row = result.iloc[0]
            for col in num_cols:
                val = row[col]
                col_clean = col.replace('_', ' ')
                if 'count' in col.lower() or col.lower() == 'total':
                    total = self.overall.get('total_txns', None)
                    if total and total > 0:
                        pct = (float(val) / total) * 100
                        insights.append(f"This represents {pct:.1f}% of all {total:,} transactions")
            return insights

        if result.shape[0] > 1 and num_cols and cat_cols:
            try:
                val_col = num_cols[0]
                cat_col = cat_cols[0]
                values = result[val_col].astype(float)

                max_idx = values.idxmax()
                min_idx = values.idxmin()
                max_label = result.loc[max_idx, cat_col]
                min_label = result.loc[min_idx, cat_col]
                max_val = values[max_idx]
                min_val = values[min_idx]
                spread = max_val - min_val

                insights.append(
                    f"Highest {val_col.replace('_',' ')}: {max_label} ({max_val:.1f})"
                )
                insights.append(
                    f"Lowest {val_col.replace('_',' ')}: {min_label} ({min_val:.1f})"
                )
                if spread > 0:
                    insights.append(
                        f"Range: {spread:.1f} — {'wide spread, investigate further' if spread > max_val * 0.3 else 'relatively consistent'}"
                    )
            except Exception:
                pass

        return insights

    def _proactive_suggestions(self, result: pd.DataFrame, intent: str, sql: str) -> list:
        """Suggest what user might want to explore next."""
        tips = []
        intent_lower = intent.lower()
        sql_lower = sql.lower()

        if 'failed' in intent_lower or 'failure' in intent_lower:
            if 'device' not in sql_lower:
                tips.append("Want to see failure rates broken down by device type?")
            if 'hour' not in sql_lower:
                tips.append("Want to know which hours have the most failures?")
            if 'bank' not in sql_lower:
                tips.append("Want to check which banks have the highest failure rates?")

        if 'fraud' in intent_lower:
            tips.append("Want to see fraud patterns by age group or state?")

        if 'p2p' in intent_lower or 'p2m' in intent_lower:
            tips.append("Want to compare P2P vs P2M side by side?")

        if 'amount' in intent_lower or 'average' in intent_lower:
            tips.append("Want to see the distribution — min, max, median too?")

        return tips[:2]  # Max 2 tips
