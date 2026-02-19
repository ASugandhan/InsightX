"""
Confidence Interval Calculator
Shows ranges to indicate uncertainty
"""

import numpy as np
from scipy import stats
import pandas as pd


class ConfidenceCalculator:
    """Calculate confidence intervals for metrics"""
    
    def calculate_ci(self, data: pd.Series, confidence_level: float = 0.95) -> dict:
        """
        Calculate confidence interval
        
        Args:
            data: Series of values
            confidence_level: Confidence level (default 95%)
        
        Returns:
            Dict with mean, lower, upper, margin_of_error
        """
        
        if len(data) < 2:
            return None
        
        mean = data.mean()
        std_err = stats.sem(data)  # Standard error
        margin = std_err * stats.t.ppf((1 + confidence_level) / 2, len(data) - 1)
        
        return {
            'mean': round(mean, 2),
            'lower': round(mean - margin, 2),
            'upper': round(mean + margin, 2),
            'margin_of_error': round(margin, 2),
            'confidence_level': confidence_level
        }
    
    def format_with_ci(self, value: float, ci: dict) -> str:
        """Format value with confidence interval"""
        
        if not ci:
            return f"₹{value:,.2f}"
        
        return f"₹{value:,.2f} (95% CI: ₹{ci['lower']:,.2f} - ₹{ci['upper']:,.2f})"