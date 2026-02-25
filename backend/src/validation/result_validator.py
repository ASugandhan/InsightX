"""
Result Validator
Validates query results for correctness
"""

class ResultValidator:
    def __init__(self):
        self.validation_rules = {
            'rates': self._validate_rates,
            'amounts': self._validate_amounts,
            'counts': self._validate_counts,
            'percentages': self._validate_percentages
        }
    
    def validate(self, result, metrics, filters) -> dict:
        """
        Validate query result
        
        Returns:
            {
                'is_valid': bool,
                'confidence_adjustment': float,
                'issues': list,
                'warnings': list
            }
        """
        
        issues = []
        warnings = []
        confidence_adjustment = 0.0
        
        # Check for empty result
        if result.empty:
            issues.append("Query returned no results")
            confidence_adjustment -= 0.3
            return {
                'is_valid': False,
                'confidence_adjustment': confidence_adjustment,
                'issues': issues,
                'warnings': warnings
            }
        
        # Validate each metric type
        for metric in metrics:
            if 'rate' in metric:
                rate_issues = self._validate_rates(result, metric)
                issues.extend(rate_issues)
            
            elif 'amount' in metric:
                amount_issues = self._validate_amounts(result, metric, filters)
                warnings.extend(amount_issues)
            
            elif 'count' in metric:
                count_issues = self._validate_counts(result, metric)
                warnings.extend(count_issues)
        
        # Adjust confidence based on issues
        if len(issues) > 0:
            confidence_adjustment -= 0.2
        if len(warnings) > 0:
            confidence_adjustment -= 0.05
        
        is_valid = len(issues) == 0
        
        return {
            'is_valid': is_valid,
            'confidence_adjustment': confidence_adjustment,
            'issues': issues,
            'warnings': warnings
        }
    
    def _validate_rates(self, result, metric):
        """Validate rate metrics (should be 0-100)"""
        issues = []
        
        if metric in result.columns:
            values = result[metric]
            if (values < 0).any() or (values > 100).any():
                issues.append(f"{metric} contains invalid values (must be 0-100)")
        
        return issues
    
    def _validate_amounts(self, result, metric, filters):
        """Validate amount metrics"""
        warnings = []
        
        if metric in result.columns:
            values = result[metric]
            
            # Check for suspiciously low amounts
            if (values < 1).any():
                warnings.append(f"{metric} contains very low values (<Rs.1)")
            
            # Check for suspiciously high amounts
            if (values > 100000).any():
                warnings.append(f"{metric} contains very high values (>Rs.100,000)")
        
        return warnings
    
    def _validate_counts(self, result, metric):
        """Validate count metrics"""
        warnings = []
        
        if metric in result.columns:
            values = result[metric]
            
            # Check for zero counts
            if (values == 0).any():
                warnings.append(f"{metric} contains zero counts - may indicate incorrect filters")
        
        return warnings
    
    def _validate_percentages(self, result, metric):
        """Validate percentage metrics"""
        issues = []
        
        # Check if percentages sum to ~100
        if len(result) > 1 and metric in result.columns:
            total = result[metric].sum()
            if total < 95 or total > 105:
                issues.append(f"Percentages sum to {total:.1f}% (expected ~100%)")
        
        return issues
